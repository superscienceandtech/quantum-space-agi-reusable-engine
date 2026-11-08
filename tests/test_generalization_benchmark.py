from __future__ import annotations

import json
import tempfile
import unittest
from itertools import product
from pathlib import Path

from examples.generalization_benchmark import (
    build_instance,
    run_benchmark,
    load_public_kipu_maxcut,
    load_public_gset_maxcut,
    run_public_maxcut_instance,
    evaluate_gset_cut,
)


class GeneralizationBenchmarkTests(unittest.TestCase):
    def test_generated_instances_are_deterministic_for_fixed_seed(self):
        first = build_instance("maxcut_sparse", 6, 1234)
        second = build_instance("maxcut_sparse", 6, 1234)

        self.assertEqual(first.metadata, second.metadata)
        self.assertEqual(first.qubo.terms, second.qubo.terms)
        self.assertEqual(first.qubo.offset, second.qubo.offset)

    def test_maxcut_qubo_energy_equals_negative_cut_weight(self):
        instance = build_instance("maxcut_dense", 6, 55)
        names = tuple(instance.problem.variables)

        for bits in product((0, 1), repeat=len(names)):
            state = dict(zip(names, bits))
            objective = instance.problem.objective.evaluate(state)
            self.assertAlmostEqual(instance.qubo.energy(state), -objective)

    def test_knapsack_qubo_encodes_each_feasible_assignment(self):
        instance = build_instance("knapsack", 6, 77)
        names = tuple(instance.problem.variables)
        weights = instance.metadata["weights"]
        capacity = instance.metadata["capacity"]

        for bits in product((0, 1), repeat=len(names)):
            decisions = dict(zip(names, bits))
            candidate = instance.problem.validate_solution(decisions)
            checks = tuple(
                constraint.check(candidate)
                for constraint in instance.problem.constraints
            )
            if not all(check.feasible for check in checks):
                continue

            slack = capacity - sum(weights[name] * decisions[name] for name in names)
            complete_state = dict(decisions)
            for index, slack_name in enumerate(
                instance.qubo.slack_variables["weight_capacity"]
            ):
                complete_state[slack_name] = (slack >> index) & 1

            self.assertAlmostEqual(
                instance.qubo.energy(complete_state),
                -instance.problem.objective.evaluate(candidate),
            )

    def test_public_ising_json_conversion_preserves_energy(self):
        source = {
            "()": "1.5",
            "(0,)": "0.2",
            "(1,)": "-0.4",
            "(0, 1)": "0.5",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            instance = load_public_kipu_maxcut(path)

        self.assertEqual(instance.vertex_count, 2)
        self.assertEqual(instance.edge_count, 1)
        for bits in product((0, 1), repeat=2):
            spin0, spin1 = (1 - 2 * bit for bit in bits)
            ising_energy = (
                1.5 + 0.2 * spin0 - 0.4 * spin1 + 0.5 * spin0 * spin1
            )
            state = {name: bit for name, bit in zip(instance.qubo.variable_order, bits)}
            self.assertAlmostEqual(instance.qubo.energy(state), ising_energy)

    def test_public_gset_conversion_matches_negative_cut_for_every_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "G4"
            path.write_text("4 4\n1 2 1\n2 3 1\n3 4 1\n4 1 1\n", encoding="utf-8")
            instance = load_public_gset_maxcut(path, best_known_cut=4)
            direct_cut = evaluate_gset_cut(path, "0101")
            with self.assertRaisesRegex(ValueError, "one 0/1 character"):
                evaluate_gset_cut(path, "010")

        self.assertEqual(instance.vertex_count, 4)
        self.assertEqual(instance.edge_count, 4)
        self.assertEqual(instance.published_reference_energy, -4.0)
        self.assertEqual(direct_cut, 4)
        report = run_public_maxcut_instance(
            instance,
            reference_energy=instance.published_reference_energy,
            seeds=(0,),
            evaluation_budget=64,
            reference_interpretation="Test best-known cut converted to negative QUBO energy.",
        )
        self.assertEqual(
            report["reference"]["interpretation"],
            "Test best-known cut converted to negative QUBO energy.",
        )
        names = instance.qubo.variable_order
        for bits in product((0, 1), repeat=len(names)):
            cut = sum(
                1 for left, right in ((0, 1), (1, 2), (2, 3), (3, 0))
                if bits[left] != bits[right]
            )
            state = dict(zip(names, bits))
            self.assertAlmostEqual(instance.qubo.energy(state), -float(cut))

    def test_public_gset_header_must_match_edge_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-Gset"
            path.write_text("3 2\n1 2 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match the header"):
                load_public_gset_maxcut(path, best_known_cut=1)

    def test_small_report_uses_paired_seeds_and_reports_repair_overhead(self):
        report = run_benchmark(
            families=("knapsack", "maxcut_sparse"),
            sizes=(4,),
            instances_per_setting=1,
            seed_count=2,
            seed_start=5,
            evaluation_budget=64,
        )

        self.assertEqual(report["design"]["paired_solver_seeds"], (5, 6))
        results = report["results"]
        self.assertEqual(len(results), 2)
        knapsack = next(item for item in results if item["instance"]["family"] == "knapsack")
        maxcut = next(item for item in results if item["instance"]["family"] == "maxcut_sparse")
        self.assertIn("fg_dsb", knapsack["methods"])
        self.assertNotIn("fg_dsb", maxcut["methods"])
        for method in knapsack["methods"].values():
            self.assertEqual(method["summary"]["runs"], 2)
        self.assertGreaterEqual(
            knapsack["methods"]["fg_dsb"]["summary"]["mean_repair_candidates_evaluated"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
