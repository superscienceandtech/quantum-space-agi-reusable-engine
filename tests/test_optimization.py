import unittest

from examples.synthetic_optimization import REPETITIONS, build_cases, run_case
from quantum_space_agi.optimization import (
    ConstraintRelation,
    EnumerativeSolver,
    FunctionalConstraint,
    FunctionalObjective,
    ObjectiveSense,
    OptimizationProblem,
    OptimizationStatus,
    benchmark_solver,
)


class OptimizationTests(unittest.TestCase):
    def test_feasible_case_is_repeatable_and_satisfies_constraints(self):
        report = run_case(build_cases()[0])
        result = report["result"]
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["objective_value"], 10.0)
        self.assertEqual(result["solution"], {"alpha": 1.0, "beta": 1.0, "gamma": 0.0})
        self.assertEqual(result["candidates_evaluated_per_solve"], 8)
        self.assertEqual(result["objective_evaluations_per_solve"], 7)
        self.assertTrue(all(check["feasible"] for check in result["constraint_results"]))
        benchmark = report["benchmark"]
        samples = benchmark["timing_samples_seconds"]
        self.assertEqual(benchmark["repetitions"], REPETITIONS)
        self.assertEqual(len(samples), REPETITIONS)
        self.assertAlmostEqual(benchmark["mean_seconds"], sum(samples) / REPETITIONS)
        self.assertEqual(benchmark["min_seconds"], min(samples))
        self.assertIn("time.perf_counter", benchmark["timing_method"])
        self.assertIsNone(benchmark["seed"])
        self.assertEqual(benchmark["output_format"], "JSON, sorted keys")

    def test_resource_constrained_case_remains_feasible(self):
        report = run_case(build_cases()[1])
        result = report["result"]
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["objective_value"], 7.0)
        self.assertEqual(result["solution"], {"alpha": 0.0, "beta": 1.0, "gamma": 1.0})
        self.assertEqual(result["candidates_evaluated_per_solve"], 8)
        self.assertTrue(all(check["feasible"] for check in result["constraint_results"]))

    def test_infeasible_case_reports_diagnostic_resource_violations(self):
        report = run_case(build_cases()[2])
        result = report["result"]
        self.assertEqual(result["status"], "infeasible")
        self.assertIsNone(result["objective_value"])
        self.assertIsNone(result["solution"])
        self.assertEqual(result["candidates_evaluated_per_solve"], 8)
        self.assertEqual(result["objective_evaluations_per_solve"], 0)
        self.assertEqual(result["constraint_diagnostic_source"], "explicit_diagnostic_witness")
        violations = {check["name"]: check["violation"] for check in result["constraint_results"]}
        self.assertEqual(violations, {"budget": 3.0, "capacity": 1.0, "minimum_selected": 0.0})

    def test_constraint_tolerance_is_applied(self):
        constraint = FunctionalConstraint("limit", lambda x: x["x"], ConstraintRelation.LE, 1, tolerance=0.1)
        check = constraint.check({"x": 1.05})
        self.assertTrue(check.feasible)
        self.assertEqual(check.violation, 0.0)

    def test_invalid_empty_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            OptimizationProblem(
                FunctionalObjective("min", ObjectiveSense.MINIMIZE, lambda x: 0), {"x": ()}
            )

    def test_candidate_requires_exact_allowed_variables(self):
        problem = build_cases()[0].problem
        with self.assertRaisesRegex(ValueError, "missing variables"):
            problem.validate_solution({"alpha": 1})
        with self.assertRaisesRegex(ValueError, "outside the domain"):
            problem.validate_solution({"alpha": 2, "beta": 0, "gamma": 0})

    def test_benchmark_repeats_and_reports_solver_results(self):
        report = benchmark_solver(EnumerativeSolver(), build_cases()[0].problem, repetitions=2)
        self.assertEqual(report.repetitions, 2)
        self.assertEqual(len(report.elapsed_seconds), 2)
        self.assertTrue(all(result.objective_value == 10 for result in report.results))
        self.assertTrue(all(value >= 0 for value in report.elapsed_seconds))

    def test_zero_benchmark_repetitions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            benchmark_solver(EnumerativeSolver(), build_cases()[0].problem, repetitions=0)


if __name__ == "__main__":
    unittest.main()
