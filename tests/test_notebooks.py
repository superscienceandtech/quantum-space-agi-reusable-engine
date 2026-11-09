import itertools
import json
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    *sorted((ROOT / "src" / "quantum_space_agi" / "scientific").glob("*.ipynb")),
    *sorted((ROOT / "tests" / "scientific").glob("*.ipynb")),
]
TEST_NOTEBOOKS = sorted((ROOT / "tests" / "scientific").glob("test_*.ipynb"))


def validate_notebook(path: Path) -> None:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    nbformat.validate(nbformat.from_dict(data))
    assert data["nbformat"] == 4
    assert data["nbformat_minor"] >= 5
    assert data["cells"]


@pytest.mark.parametrize(
    "notebook_path", NOTEBOOKS, ids=lambda path: str(path.relative_to(ROOT))
)
def test_notebook_executes(notebook_path: Path) -> None:
    validate_notebook(notebook_path)
    with notebook_path.open("r", encoding="utf-8") as file:
        notebook = nbformat.read(file, as_version=4)

    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        allow_errors=False,
    )
    client.execute()


def _expand_notebook_cases(
    notebook_path: Path,
) -> list[tuple[str, object, dict[str, object]]]:
    with notebook_path.open("r", encoding="utf-8") as file:
        notebook = nbformat.read(file, as_version=4)

    namespace = {
        "__name__": f"notebook_tests.{notebook_path.stem}",
        "__file__": str(notebook_path),
    }
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "arc04-test-runner" in cell.metadata.get("tags", []):
            continue
        exec(compile("".join(cell.source), f"{notebook_path}:cell", "exec"), namespace)

    cases: list[tuple[str, object, dict[str, object]]] = []
    for test_name in sorted(name for name in namespace if name.startswith("test_")):
        test_function = namespace[test_name]
        if not callable(test_function):
            continue

        parameter_sets = [{}]
        marks = [
            mark
            for mark in getattr(test_function, "pytestmark", [])
            if getattr(mark, "name", "") == "parametrize"
        ]
        for mark in marks:
            argnames = mark.args[0]
            argvalues = mark.args[1]
            names = (
                [name.strip() for name in argnames.split(",")]
                if isinstance(argnames, str)
                else list(argnames)
            )
            next_sets = []
            for existing, argvalue in itertools.product(parameter_sets, argvalues):
                if len(names) == 1:
                    arguments = {names[0]: argvalue}
                elif isinstance(argvalue, (tuple, list)):
                    arguments = dict(zip(names, argvalue))
                else:
                    raise TypeError(
                        f"{test_name} parameterization requires one value per name"
                    )
                next_sets.append({**existing, **arguments})
            parameter_sets = next_sets

        for case_number, arguments in enumerate(parameter_sets, start=1):
            case_id = (
                test_name if len(parameter_sets) == 1 else f"{test_name}[{case_number}]"
            )
            cases.append((case_id, test_function, arguments))
    return cases


SCIENTIFIC_TEST_CASES = [
    (notebook_path, case_id, test_function, arguments)
    for notebook_path in TEST_NOTEBOOKS
    for case_id, test_function, arguments in _expand_notebook_cases(notebook_path)
]


@pytest.mark.parametrize(
    ("notebook_path", "case_id", "test_function", "arguments"),
    SCIENTIFIC_TEST_CASES,
    ids=[
        f"{notebook_path.relative_to(ROOT)}::{case_id}"
        for notebook_path, case_id, _test_function, _arguments in SCIENTIFIC_TEST_CASES
    ],
)
def test_scientific_notebook_case(
    notebook_path: Path,
    case_id: str,
    test_function: object,
    arguments: dict[str, object],
) -> None:
    del notebook_path, case_id
    test_function(**arguments)
