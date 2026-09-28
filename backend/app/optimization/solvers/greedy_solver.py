"""
Naive / Greedy Operational Baseline Assignment Solver.
Simulates current unoptimized fleet scheduling (first-available vessel allocation),
providing the reference benchmark to quantify cost and emission reductions achieved by the optimizer.
"""

import time
from typing import Dict, List, Any


class GreedyFleetSolver:
    def solve(
        self,
        qubo_data: Dict[str, Any],
        fleet: List[Dict[str, Any]],
        voyages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Sequentially assigns each voyage to the first compatible vessel that does not
        have a direct schedule collision, without multi-objective cost/emission optimization.
        """
        start_time = time.perf_counter()

        var_map = qubo_data["var_map"]
        cost_breakdown = qubo_data["cost_breakdown"]

        assignments = []
        assigned_vessels = {}  # vessel_id -> list of assigned voyage intervals
        assigned_voyages = set()

        total_fuel_cost = 0.0
        total_fuel_mt = 0.0
        total_co2_mt = 0.0
        total_ets_cost = 0.0
        total_charter_cost = 0.0

        for voy in voyages:
            j_id = voy["voyage_id"]
            dep = voy.get("departure_time", "")
            arr = voy.get("arrival_time", "")

            best_var = None
            # Pick first compatible vessel without strict cost minimization (simulating naive operator heuristics)
            for var_meta in var_map:
                if var_meta["voyage_id"] != j_id:
                    continue

                v_id = var_meta["vessel_id"]
                cost = cost_breakdown[var_meta["index"]]
                if not cost["is_compatible"]:
                    continue

                # Check schedule conflict
                conflict = False
                for prev_dep, prev_arr in assigned_vessels.get(v_id, []):
                    if dep and arr and prev_dep and prev_arr:
                        if max(dep, prev_dep) <= min(arr, prev_arr):
                            conflict = True
                            break

                if not conflict:
                    best_var = var_meta
                    break  # Take first available vessel!

            # If no conflict-free vessel, pick any compatible fallback
            if best_var is None:
                for var_meta in var_map:
                    if var_meta["voyage_id"] == j_id and cost_breakdown[var_meta["index"]]["is_compatible"]:
                        best_var = var_meta
                        break

            if best_var:
                v_id = best_var["vessel_id"]
                var_idx = best_var["index"]
                cost = cost_breakdown[var_idx]

                assigned_voyages.add(j_id)
                assigned_vessels.setdefault(v_id, []).append((dep, arr))

                total_fuel_cost += cost["fuel_cost_inr"]
                total_fuel_mt += cost["fuel_consumed_mt"]
                total_co2_mt += cost["co2_emissions_mt"]
                total_ets_cost += cost["eu_ets_cost_inr"]
                total_charter_cost += cost["charter_cost_inr"]

                assignments.append({
                    "vessel_id": v_id,
                    "vessel_name": best_var["vessel_name"],
                    "voyage_id": j_id,
                    "fuel_cost_inr": cost["fuel_cost_inr"],
                    "fuel_consumed_mt": cost["fuel_consumed_mt"],
                    "co2_emissions_mt": cost["co2_emissions_mt"],
                    "eu_ets_cost_inr": cost["eu_ets_cost_inr"],
                    "charter_cost_inr": cost["charter_cost_inr"],
                    "cii_rating": cost["cii_rating"],
                })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        total_operational_cost = total_fuel_cost + total_ets_cost + total_charter_cost

        return {
            "solver_name": "Naive / Greedy Operational Baseline",
            "execution_time_ms": round(elapsed_ms, 2),
            "assignments": assignments,
            "total_assigned_voyages": len(assigned_voyages),
            "total_fuel_cost_inr": round(total_fuel_cost, 2),
            "total_fuel_consumed_mt": round(total_fuel_mt, 2),
            "total_co2_emissions_mt": round(total_co2_mt, 2),
            "total_eu_ets_cost_inr": round(total_ets_cost, 2),
            "total_charter_cost_inr": round(total_charter_cost, 2),
            "total_operational_cost_inr": round(total_operational_cost, 2),
            "is_valid": len(assigned_voyages) == len(voyages),
        }
