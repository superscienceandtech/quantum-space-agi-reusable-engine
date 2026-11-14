"""Execute a source notebook in one Python process without starting Jupyter.

This is a custom runner, not a Jupyter kernel. It captures cell stdout/stderr,
the final expression, and Matplotlib figures. It stops after the first failed
code cell and preserves unexecuted cells without claiming they ran.
"""

from __future__ import annotations

import ast
import base64
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import nbformat


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb"
OUTPUT = HERE / "ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution.ipynb"
CHART_DIR = HERE / "custom-python-runner-charts-legend-final"


def require_absent(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing path: {path}")


def expression_result(value: Any) -> dict[str, Any]:
    """Create a useful plain-text representation, plus HTML when available."""
    data: dict[str, Any] = {"text/plain": repr(value)}
    html_repr = getattr(value, "_repr_html_", None)
    if callable(html_repr):
        try:
            html_value = html_repr()
            if html_value:
                data["text/html"] = html_value
        except Exception:
            # A rich representation is optional; plain text remains captured.
            pass
    return data


def main() -> int:
    require_absent(OUTPUT)
    require_absent(CHART_DIR)
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Source notebook not found: {SOURCE}")

    notebook = nbformat.read(SOURCE, as_version=4)
    nbformat.validate(notebook)
    CHART_DIR.mkdir()

    namespace: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(SOURCE),
    }
    execution_count = 0
    successful_cells = 0
    failed_cells = 0
    skipped_cells = 0
    generated_figures = 0
    stop_after_failure = False
    patched_show = False

    for cell_index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        if stop_after_failure:
            skipped_cells += 1
            cell.execution_count = None
            cell.outputs = []
            cell.metadata["custom_python_runner"] = "not run: prior code cell failed"
            continue

        execution_count += 1
        cell.execution_count = execution_count
        outputs: list[nbformat.NotebookNode] = []
        cell.outputs = outputs
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        source = cell.source

        if any(line.lstrip().startswith(("%", "!")) for line in source.splitlines()):
            failed_cells += 1
            outputs.append(nbformat.v4.new_output(
                "error", ename="UnsupportedNotebookSyntax",
                evalue="IPython magic or shell syntax is unsupported by this custom Python runner.",
                traceback=[],
            ))
            cell.metadata["custom_python_runner"] = "failed: unsupported notebook syntax"
            stop_after_failure = True
            continue

        try:
            tree = ast.parse(source, filename=f"cell-{cell_index}", mode="exec")
            final_expression = None
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                final_expression = tree.body.pop()

            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                if tree.body:
                    exec(compile(tree, f"cell-{cell_index}", "exec"), namespace, namespace)
                if final_expression is not None:
                    expression_code = compile(
                        ast.Expression(final_expression.value),
                        f"cell-{cell_index}-result",
                        "eval",
                    )
                    result = eval(expression_code, namespace, namespace)
                    if result is not None:
                        outputs.append(nbformat.v4.new_output(
                            "execute_result",
                            data=expression_result(result),
                            execution_count=execution_count,
                            metadata={},
                        ))

            if stdout_buffer.getvalue():
                outputs.insert(0, nbformat.v4.new_output(
                    "stream", name="stdout", text=stdout_buffer.getvalue()
                ))
            if stderr_buffer.getvalue():
                outputs.append(nbformat.v4.new_output(
                    "stream", name="stderr", text=stderr_buffer.getvalue()
                ))

            # Set a non-interactive backend before pyplot is imported by the
            # notebook, then replace show() after the notebook imports it.
            if not patched_show and "plt" in namespace:
                import matplotlib
                matplotlib.use("Agg", force=True)
                plt = namespace["plt"]

                def capture_show(*args: Any, **kwargs: Any) -> None:
                    nonlocal generated_figures
                    for figure_number in list(plt.get_fignums()):
                        figure = plt.figure(figure_number)
                        generated_figures += 1
                        chart_path = CHART_DIR / (
                            f"chart-cell-{cell_index}-figure-{generated_figures}.png"
                        )
                        image_buffer = io.BytesIO()
                        figure.savefig(image_buffer, format="png", dpi=150, bbox_inches="tight")
                        image_bytes = image_buffer.getvalue()
                        chart_path.write_bytes(image_bytes)
                        outputs.append(nbformat.v4.new_output(
                            "display_data",
                            data={
                                "image/png": base64.b64encode(image_bytes).decode("ascii"),
                                "text/plain": f"Generated chart image: {chart_path.name}",
                            },
                            metadata={"custom_python_runner": {"chart_file": chart_path.name}},
                        ))
                        plt.close(figure)

                plt.show = capture_show
                patched_show = True

            successful_cells += 1
            cell.metadata["custom_python_runner"] = "success"
        except BaseException as exc:
            failed_cells += 1
            if stdout_buffer.getvalue():
                outputs.append(nbformat.v4.new_output(
                    "stream", name="stdout", text=stdout_buffer.getvalue()
                ))
            if stderr_buffer.getvalue():
                outputs.append(nbformat.v4.new_output(
                    "stream", name="stderr", text=stderr_buffer.getvalue()
                ))
            outputs.append(nbformat.v4.new_output(
                "error",
                ename=type(exc).__name__,
                evalue=str(exc),
                traceback=traceback.format_exception(type(exc), exc, exc.__traceback__),
            ))
            cell.metadata["custom_python_runner"] = "failed"
            stop_after_failure = True

    notebook.metadata["custom_python_runner"] = {
        "runner": Path(__file__).name,
        "execution_type": "custom in-process Python cell runner; not Jupyter",
        "source_notebook": SOURCE.name,
        "successful_code_cells": successful_cells,
        "failed_code_cells": failed_cells,
        "skipped_code_cells": skipped_cells,
        "generated_matplotlib_figures": generated_figures,
        "matplotlib_backend": "Agg",
    }
    nbformat.validate(notebook)
    nbformat.write(notebook, OUTPUT)

    print(f"Source notebook: {SOURCE}")
    print(f"Executed notebook: {OUTPUT}")
    print(f"Chart directory: {CHART_DIR}")
    print(f"Successful code cells: {successful_cells}")
    print(f"Failed code cells: {failed_cells}")
    print(f"Skipped code cells: {skipped_cells}")
    print(f"Generated figures: {generated_figures}")
    print(f"Runner Python: {sys.version.split()[0]}")
    print("Execution mode: custom Python runner; not Jupyter")
    return 1 if failed_cells else 0


if __name__ == "__main__":
    raise SystemExit(main())
