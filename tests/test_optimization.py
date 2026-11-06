import unittest

from examples.synthetic_optimization import build_problem
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
    def test_synthetic_problem_finds_best_feasible_assignment(self):
        result = EnumerativeSolver().solve(build_problem())
        self.assertEqual(result.status, OptimizationStatus.OPTIMAL)
        self.assertEqual(dict(result.solution), {"alpha": 1.0, "beta": 1.0, "delta": 0.0, "gamma": 0.0})
        self.assertEqual(result.objective_value, 14.0)
        self.assertEqual(result.evaluated_candidates, 16)
        self.assertTrue(all(check.feasible for check in result.constraint_checks))

    def test_infeasible_problem_returns_no_solution(self):
        problem = OptimizationProblem(
            FunctionalObjective("min", ObjectiveSense.MINIMIZE, lambda x: x["x"]),
            {"x": (0, 1)},
            (FunctionalConstraint("must_be_two", lambda x: x["x"], ConstraintRelation.GE, 2),),
        )
        result = EnumerativeSolver().solve(problem)
        self.assertEqual(result.status, OptimizationStatus.INFEASIBLE)
        self.assertIsNone(result.solution)
        self.assertEqual(result.evaluated_candidates, 2)

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
        problem = build_problem()
        with self.assertRaisesRegex(ValueError, "missing variables"):
            problem.validate_solution({"alpha": 1})
        with self.assertRaisesRegex(ValueError, "outside the domain"):
            problem.validate_solution({"alpha": 2, "beta": 0, "gamma": 0, "delta": 0})

    def test_benchmark_repeats_and_reports_solver_results(self):
        report = benchmark_solver(EnumerativeSolver(), build_problem(), repetitions=2)
        self.assertEqual(report.repetitions, 2)
        self.assertEqual(len(report.elapsed_seconds), 2)
        self.assertTrue(all(result.objective_value == 14 for result in report.results))

    def test_zero_benchmark_repetitions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            benchmark_solver(EnumerativeSolver(), build_problem(), repetitions=0)


if __name__ == "__main__":
    unittest.main()
