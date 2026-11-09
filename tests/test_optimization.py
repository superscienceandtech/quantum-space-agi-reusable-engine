import unittest
from itertools import product

from examples.qiskit_qaoa_experiment import run_qaoa_case
from examples.qubo_heuristics import (
    discrete_simulated_bifurcation_qubo,
    feasibility_guided_dsb,
    qubo_to_ising,
    simulated_annealing_qubo,
)
from examples.synthetic_optimization import (
    REPETITIONS,
    build_cases,
    build_scaling_cases,
    run_annealing_case,
    run_case,
    run_qubo_case,
)

from quantum_space_agi.optimization import (
    ConstraintRelation,
    EnumerativeSolver,
    FunctionalConstraint,
    FunctionalObjective,
    ObjectiveSense,
    OptimizationProblem,
    benchmark_solver,
)
from quantum_space_agi.optimization.qubo import LinearConstraintSpec, build_qubo


class OptimizationTests(unittest.TestCase):
    def test_qubo_to_ising_preserves_every_small_fixture_energy(self):
        case = build_cases()[0]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        constant, fields, couplings = qubo_to_ising(model)
        for bits in product((0, 1), repeat=len(model.variable_order)):
            state = dict(zip(model.variable_order, bits))
            spins = tuple(1 - 2 * bit for bit in bits)
            ising_energy = constant + sum(
                fields[i] * spins[i] for i in range(len(spins))
            )
            ising_energy += sum(
                couplings[i][j] * spins[i] * spins[j]
                for i in range(len(spins))
                for j in range(i + 1, len(spins))
            )
            self.assertAlmostEqual(model.energy(state), ising_energy)

    def test_discrete_simulated_bifurcation_is_seeded(self):
        case = build_cases()[0]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        first = discrete_simulated_bifurcation_qubo(model, seed=29, agents=4, steps=32)
        second = discrete_simulated_bifurcation_qubo(model, seed=29, agents=4, steps=32)
        self.assertEqual(dict(first.state), dict(second.state))
        self.assertEqual(first.energy, second.energy)
        self.assertEqual(first.updates_evaluated, 4 * 32)
        self.assertEqual(first.energy, model.energy(first.state))

    def test_feasibility_guided_dsb_repairs_feasible_fixture(self):
        case = build_cases()[0]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        result = feasibility_guided_dsb(
            model,
            case.problem,
            case.qubo_constraints,
            seed=13,
            agents=4,
            steps=32,
            max_flip_size=2,
        )
        self.assertTrue(result.feasible)
        self.assertEqual(result.objective_value, 10.0)
        self.assertEqual(result.energy, model.energy(result.state))
        self.assertGreaterEqual(result.repair_candidates_evaluated, result.repair_moves)

    def test_feasibility_guided_dsb_does_not_falsify_infeasibility(self):
        case = build_cases()[2]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        result = feasibility_guided_dsb(
            model,
            case.problem,
            case.qubo_constraints,
            seed=13,
            agents=4,
            steps=32,
            max_flip_size=2,
        )
        self.assertFalse(result.feasible)
        self.assertIsNone(result.objective_value)
        self.assertGreater(max(result.violations.values()), 0.0)

    def test_simulated_annealing_is_seeded_and_reports_work(self):
        case = build_cases()[0]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        first = simulated_annealing_qubo(model, seed=41, sweeps=8, restarts=2)
        second = simulated_annealing_qubo(model, seed=41, sweeps=8, restarts=2)
        self.assertEqual(dict(first.state), dict(second.state))
        self.assertEqual(first.energy, second.energy)
        self.assertEqual(first.proposals_evaluated, 2 * 8 * len(model.variable_order))
        self.assertLessEqual(first.accepted_moves, first.proposals_evaluated)
        self.assertEqual(first.energy, model.energy(first.state))

    def test_annealing_report_compares_with_exact_baselines(self):
        report = run_annealing_case(build_cases()[0], seeds=(3, 7, 11))
        self.assertEqual(report["reference"]["original_solver_status"], "optimal")
        self.assertEqual(report["summary"]["run_count"], 3)
        self.assertEqual(report["configuration"]["proposals_per_run"], 4 * 64 * 8)
        self.assertGreaterEqual(report["summary"]["optimal_energy_rate"], 0.0)
        self.assertLessEqual(report["summary"]["optimal_energy_rate"], 1.0)
        self.assertGreaterEqual(
            report["summary"]["exact_enumeration_mean_seconds"], 0.0
        )
        self.assertTrue(
            all("exact_enumeration_runtime_seconds" in run for run in report["runs"])
        )

    def test_simulated_annealing_rejects_invalid_schedule(self):
        case = build_cases()[0]
        model = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            case.problem.objective.sense,
            case.qubo_constraints,
        )
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            simulated_annealing_qubo(
                model, seed=1, initial_temperature=1, final_temperature=2
            )

    def test_qiskit_qaoa_simulation_is_seeded_and_preserves_infeasibility(self):
        try:
            import qiskit  # noqa: F401
        except ImportError:
            self.skipTest("optional Qiskit experiment extra is not installed")
        case = build_cases()[2]
        report = run_qaoa_case(case, seed=17, shots=32, grid_size=2)
        repeated = run_qaoa_case(case, seed=17, shots=32, grid_size=2)
        self.assertEqual(report["method"].split(",")[0], "Qiskit StatevectorSampler")
        self.assertEqual(report["enumerative_solver"]["status"], "infeasible")
        self.assertFalse(report["simulator_result"]["feasible"])
        self.assertIsNone(report["simulator_result"]["objective_value"])
        self.assertTrue(report["comparison"]["feasibility_agrees"])
        self.assertEqual(report["configuration"]["seed"], 17)
        self.assertEqual(report["configuration"]["total_shots"], 128)
        self.assertEqual(
            report["simulator_result"]["sampled_bitstring_qubo_order"],
            repeated["simulator_result"]["sampled_bitstring_qubo_order"],
        )
        self.assertEqual(
            report["configuration"]["selected_gamma"],
            repeated["configuration"]["selected_gamma"],
        )
        self.assertEqual(
            report["simulator_result"]["qubo_energy"],
            repeated["simulator_result"]["qubo_energy"],
        )
        self.assertGreaterEqual(report["runtime"]["seconds"], 0)

    def test_feasible_case_is_repeatable_and_satisfies_constraints(self):
        report = run_case(build_cases()[0])
        result = report["result"]
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["objective_value"], 10.0)
        self.assertEqual(result["solution"], {"alpha": 1.0, "beta": 1.0, "gamma": 0.0})
        self.assertEqual(result["candidates_evaluated_per_solve"], 8)
        self.assertEqual(result["objective_evaluations_per_solve"], 7)
        self.assertTrue(
            all(check["feasible"] for check in result["constraint_results"])
        )
        benchmark = report["benchmark"]
        samples = benchmark["timing_samples_seconds"]
        self.assertEqual(benchmark["repetitions"], REPETITIONS)
        self.assertEqual(len(samples), REPETITIONS)
        self.assertAlmostEqual(benchmark["mean_seconds"], sum(samples) / REPETITIONS)
        self.assertIn("median_seconds", benchmark)
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
        self.assertTrue(
            all(check["feasible"] for check in result["constraint_results"])
        )

    def test_scaling_series_grows_deterministically(self):
        cases = build_scaling_cases()
        sizes = (3, 6, 9, 12)
        self.assertEqual(tuple(len(case.problem.variables) for case in cases), sizes)
        reports = [run_case(case, repetitions=1) for case in cases]
        candidate_counts = [
            report["result"]["candidates_evaluated_per_solve"] for report in reports
        ]
        self.assertEqual(candidate_counts, [2**size for size in sizes])
        self.assertTrue(
            all(report["result"]["status"] == "optimal" for report in reports)
        )
        self.assertTrue(
            all(
                report["result"]["objective_evaluations_per_solve"] > 0
                for report in reports
            )
        )

    def test_infeasible_case_reports_diagnostic_resource_violations(self):
        report = run_case(build_cases()[2])
        result = report["result"]
        self.assertEqual(result["status"], "infeasible")
        self.assertIsNone(result["objective_value"])
        self.assertIsNone(result["solution"])
        self.assertEqual(result["candidates_evaluated_per_solve"], 8)
        self.assertEqual(result["objective_evaluations_per_solve"], 0)
        self.assertEqual(
            result["constraint_diagnostic_source"], "explicit_diagnostic_witness"
        )
        violations = {
            check["name"]: check["violation"] for check in result["constraint_results"]
        }
        self.assertEqual(
            violations, {"budget": 3.0, "capacity": 1.0, "minimum_selected": 0.0}
        )

    def test_constraint_tolerance_is_applied(self):
        constraint = FunctionalConstraint(
            "limit", lambda x: x["x"], ConstraintRelation.LE, 1, tolerance=0.1
        )
        check = constraint.check({"x": 1.05})
        self.assertTrue(check.feasible)
        self.assertEqual(check.violation, 0.0)

    def test_invalid_empty_domain_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            OptimizationProblem(
                FunctionalObjective("min", ObjectiveSense.MINIMIZE, lambda x: 0),
                {"x": ()},
            )

    def test_candidate_requires_exact_allowed_variables(self):
        problem = build_cases()[0].problem
        with self.assertRaisesRegex(ValueError, "missing variables"):
            problem.validate_solution({"alpha": 1})
        with self.assertRaisesRegex(ValueError, "outside the domain"):
            problem.validate_solution({"alpha": 2, "beta": 0, "gamma": 0})

    def test_benchmark_repeats_and_reports_solver_results(self):
        report = benchmark_solver(
            EnumerativeSolver(), build_cases()[0].problem, repetitions=2
        )
        self.assertEqual(report.repetitions, 2)
        self.assertEqual(len(report.elapsed_seconds), 2)
        self.assertTrue(all(result.objective_value == 10 for result in report.results))
        self.assertTrue(all(value >= 0 for value in report.elapsed_seconds))

    def test_zero_benchmark_repetitions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            benchmark_solver(
                EnumerativeSolver(), build_cases()[0].problem, repetitions=0
            )

    def test_qubo_feasible_minimum_matches_exact_classical_baseline(self):
        report = run_qubo_case(build_cases()[0])
        self.assertTrue(report["decoded"]["feasible"])
        self.assertEqual(report["decoded"]["objective_value"], 10.0)
        self.assertEqual(report["exact_enumerative_baseline"]["status"], "optimal")
        self.assertTrue(report["comparison"]["same_feasible_solution"])
        self.assertEqual(report["qubo"]["penalty_coefficient"], 14)
        self.assertEqual(report["qubo"]["minimum_energy"], -10.0)

    def test_qubo_resource_constrained_minimum_matches_exact_baseline(self):
        report = run_qubo_case(build_cases()[1])
        self.assertTrue(report["decoded"]["feasible"])
        self.assertEqual(report["decoded"]["objective_value"], 7.0)
        self.assertEqual(report["exact_enumerative_baseline"]["objective_value"], 7.0)
        self.assertTrue(report["comparison"]["feasibility_agrees"])
        self.assertTrue(
            all(c["violation"] == 0 for c in report["decoded"]["constraint_results"])
        )

    def test_qubo_does_not_turn_infeasible_input_into_feasible_result(self):
        report = run_qubo_case(build_cases()[2])
        self.assertEqual(report["exact_enumerative_baseline"]["status"], "infeasible")
        self.assertFalse(report["decoded"]["feasible"])
        self.assertTrue(report["comparison"]["feasibility_agrees"])
        self.assertIsNone(report["decoded"]["objective_value"])
        self.assertGreater(
            max(c["violation"] for c in report["decoded"]["constraint_results"]), 0
        )

    def test_qubo_slack_bits_decode_as_integer_and_bitstring_is_validated(self):
        case = build_cases()[0]
        qubo = build_qubo(
            tuple(sorted(case.problem.variables)),
            {"alpha": 6, "beta": 4, "gamma": 3},
            ObjectiveSense.MAXIMIZE,
            case.qubo_constraints,
        )
        report = run_qubo_case(case)
        bitstring = report["qubo"]["bitstring"]
        self.assertEqual(qubo.decode_slacks(bitstring), {"budget": 0, "capacity": 0})
        with self.assertRaisesRegex(ValueError, "bitstring"):
            qubo.decode("not-a-bitstring")

    def test_greater_equal_constraint_uses_negative_binary_slack(self):
        qubo = build_qubo(
            ("x",),
            {"x": 1},
            ObjectiveSense.MAXIMIZE,
            (LinearConstraintSpec("lower_bound", {"x": 1}, ConstraintRelation.GE, 0),),
        )
        self.assertEqual(
            qubo.slack_variables["lower_bound"], ("__slack__lower_bound__0",)
        )
        self.assertEqual(qubo.decode_slacks("10"), {"lower_bound": 0})
        self.assertEqual(qubo.decode_slacks("11"), {"lower_bound": 1})
        self.assertEqual(qubo.energy("11"), -1.0)

    def test_qubo_type_validation_raises_type_error(self):
        with self.assertRaisesRegex(TypeError, "bounds must be integers"):
            LinearConstraintSpec("budget", {"x": 1}, ConstraintRelation.LE, 1.0)
        with self.assertRaisesRegex(TypeError, "relation must be a ConstraintRelation"):
            LinearConstraintSpec("budget", {"x": 1}, "<=", 1)
        with self.assertRaisesRegex(TypeError, "coefficients must be integers"):
            LinearConstraintSpec("budget", {"x": 1.0}, ConstraintRelation.LE, 1)
        with self.assertRaisesRegex(
            TypeError, "objective_sense must be an ObjectiveSense"
        ):
            build_qubo(("x",), {"x": 1}, "maximize", ())


if __name__ == "__main__":
    unittest.main()
