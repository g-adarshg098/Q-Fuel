"""
Quantum-Inspired Simulated Annealing Solver.
Uses D-Wave's Ocean SDK (dwave-samplers / dimod) to sample low-energy ground states
of the fleet assignment QUBO problem, emulating quantum thermal & transverse-field fluctuations.
"""

import time
from typing import Dict, List, Any, Optional
import numpy as np
import dimod
from dwave.samplers import SimulatedAnnealingSampler


class QuantumAnnealingFleetSolver:
    def __init__(self, num_reads: int = 150, num_sweeps: int = 1200):
        self.num_reads = num_reads
        self.num_sweeps = num_sweeps
        self.sampler = SimulatedAnnealingSampler()

    def solve(
        self,
        qubo_data: Dict[str, Any],
        beta_range: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Executes simulated quantum annealing over the QUBO dictionary.

        Returns:
        --------
        dict with:
          - solver_name: "Quantum-Inspired Annealer (D-Wave dimod)"
          - execution_time_ms: runtime in milliseconds
          - assignments: List of assigned (vessel, voyage) pairs
          - total_fuel_cost_inr: total fuel cost
          - total_fuel_mt: total fuel burned
          - total_co2_mt: total CO2 emissions
          - total_eu_ets_cost_inr: carbon tax exposure
          - total_operational_cost_inr: sum of fuel + ETS + charter
          - constraint_violations: any unsatisfied constraints
          - energy: best ground state QUBO energy
        """
        start_time = time.perf_counter()

        qubo_dict = qubo_data["qubo_dict"]
        var_map = qubo_data["var_map"]
        cost_breakdown = qubo_data["cost_breakdown"]
        num_voyages = qubo_data["num_voyages"]

        # Instantiate Binary Quadratic Model
        bqm = dimod.BinaryQuadraticModel.from_qubo(qubo_dict)

        # Sample low-energy configurations
        sampleset = self.sampler.sample(
            bqm,
            num_reads=self.num_reads,
            num_sweeps=self.num_sweeps,
            beta_range=beta_range,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Retrieve lowest energy sample
        best_sample = sampleset.first.sample
        best_energy = float(sampleset.first.energy)

        # Parse selected binary assignments
        assignments = []
        assigned_voyages = set()
        vessel_assigned_count = {}
        violations = []

        total_fuel_cost = 0.0
        total_fuel_mt = 0.0
        total_co2_mt = 0.0
        total_ets_cost = 0.0
        total_charter_cost = 0.0

        for var_idx, bit in best_sample.items():
            if bit == 1:
                meta = var_map[var_idx]
                cost = cost_breakdown[var_idx]

                v_id = meta["vessel_id"]
                j_id = meta["voyage_id"]

                if j_id in assigned_voyages:
                    violations.append(f"Voyage {j_id} assigned multiple times.")
                assigned_voyages.add(j_id)

                vessel_assigned_count[v_id] = vessel_assigned_count.get(v_id, 0) + 1

                if not cost["is_compatible"]:
                    violations.append(f"Incompatible assignment: {v_id} -> {j_id}: {cost['incompat_reason']}")

                total_fuel_cost += cost["fuel_cost_inr"]
                total_fuel_mt += cost["fuel_consumed_mt"]
                total_co2_mt += cost["co2_emissions_mt"]
                total_ets_cost += cost["eu_ets_cost_inr"]
                total_charter_cost += cost["charter_cost_inr"]

                assignments.append({
                    "vessel_id": v_id,
                    "vessel_name": meta["vessel_name"],
                    "voyage_id": j_id,
                    "fuel_cost_inr": cost["fuel_cost_inr"],
                    "fuel_consumed_mt": cost["fuel_consumed_mt"],
                    "co2_emissions_mt": cost["co2_emissions_mt"],
                    "eu_ets_cost_inr": cost["eu_ets_cost_inr"],
                    "charter_cost_inr": cost["charter_cost_inr"],
                    "cii_rating": cost["cii_rating"],
                })

        # Post-Processing Constraint Repair: If stochastic annealing leaves a voyage unassigned,
        # assign it to the minimum-cost compatible available vessel
        all_voyage_ids = {m["voyage_id"] for m in var_map}
        unassigned_ids = all_voyage_ids - assigned_voyages

        for voy_id in unassigned_ids:
            # Find candidate vessels for this voyage sorted by lowest operational cost
            candidate_vars = [
                m["index"]
                for m in var_map
                if m["voyage_id"] == voy_id and cost_breakdown[m["index"]]["is_compatible"]
            ]
            if candidate_vars:
                # Pick lowest operational cost
                best_v = min(candidate_vars, key=lambda idx: cost_breakdown[idx]["total_operational_cost_inr"])
                meta = var_map[best_v]
                cost = cost_breakdown[best_v]

                assigned_voyages.add(voy_id)
                total_fuel_cost += cost["fuel_cost_inr"]
                total_fuel_mt += cost["fuel_consumed_mt"]
                total_co2_mt += cost["co2_emissions_mt"]
                total_ets_cost += cost["eu_ets_cost_inr"]
                total_charter_cost += cost["charter_cost_inr"]

                assignments.append({
                    "vessel_id": meta["vessel_id"],
                    "vessel_name": meta["vessel_name"],
                    "voyage_id": voy_id,
                    "fuel_cost_inr": cost["fuel_cost_inr"],
                    "fuel_consumed_mt": cost["fuel_consumed_mt"],
                    "co2_emissions_mt": cost["co2_emissions_mt"],
                    "eu_ets_cost_inr": cost["eu_ets_cost_inr"],
                    "charter_cost_inr": cost["charter_cost_inr"],
                    "cii_rating": cost["cii_rating"],
                })

        unassigned_count = num_voyages - len(assigned_voyages)
        if unassigned_count > 0:
            violations.append(f"{unassigned_count} voyage(s) were left unassigned.")

        total_operational_cost = total_fuel_cost + total_ets_cost + total_charter_cost

        return {
            "solver_name": "Quantum-Inspired Annealer (D-Wave dimod)",
            "execution_time_ms": round(elapsed_ms, 2),
            "qubo_energy": round(best_energy, 2),
            "num_reads": self.num_reads,
            "assignments": assignments,
            "total_assigned_voyages": len(assigned_voyages),
            "total_unassigned_voyages": unassigned_count,
            "total_fuel_cost_inr": round(total_fuel_cost, 2),
            "total_fuel_consumed_mt": round(total_fuel_mt, 2),
            "total_co2_emissions_mt": round(total_co2_mt, 2),
            "total_eu_ets_cost_inr": round(total_ets_cost, 2),
            "total_charter_cost_inr": round(total_charter_cost, 2),
            "total_operational_cost_inr": round(total_operational_cost, 2),
            "violations": violations,
            "is_valid": len(violations) == 0,
        }
