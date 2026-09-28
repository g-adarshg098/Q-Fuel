"""
Classical Integer Linear Programming (ILP) Solver.
Uses the industry-standard HiGHS branch-and-cut solver (via scipy.optimize.milp)
to compute the exact global mathematical optimum, serving as the benchmark
against the quantum-inspired simulated annealer.
"""

import time
from typing import Dict, List, Any
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from datetime import datetime


class ClassicalILPFleetSolver:
    def __init__(self, time_limit_sec: float = 15.0):
        self.time_limit = time_limit_sec

    def solve(
        self,
        qubo_data: Dict[str, Any],
        fleet: List[Dict[str, Any]],
        voyages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Solves the exact fleet assignment ILP formulation using SciPy's HiGHS branch-and-cut solver.
        """
        start_time = time.perf_counter()

        var_map = qubo_data["var_map"]
        cost_breakdown = qubo_data["cost_breakdown"]
        num_vars = len(var_map)
        num_voyages = len(voyages)
        num_vessels = len(fleet)

        # 1. Objective coefficient vector c: min c^T x
        c = np.zeros(num_vars, dtype=np.float64)
        for var_idx in range(num_vars):
            cost = cost_breakdown[var_idx]
            if not cost["is_compatible"]:
                c[var_idx] = 1e8  # Large penalty to forbid incompatible assignments
            else:
                op_cost = (
                    cost["fuel_cost_inr"]
                    + cost["eu_ets_cost_inr"]
                    + cost["charter_cost_inr"]
                )
                c[var_idx] = op_cost

        # 2. Constraint rows
        row_list = []
        lhs_bounds = []
        rhs_bounds = []

        # Constraint 1: Each voyage j must be assigned to EXACTLY one vessel: sum_v x_{v, j} == 1
        for j_idx, voy in enumerate(voyages):
            j_id = voy["voyage_id"]
            row = np.zeros(num_vars, dtype=np.float64)
            for var_meta in var_map:
                if var_meta["voyage_id"] == j_id:
                    row[var_meta["index"]] = 1.0
            row_list.append(row)
            lhs_bounds.append(1.0)
            rhs_bounds.append(1.0)

        # Constraint 2: Non-overlapping voyages for the same vessel: x_{v, j1} + x_{v, j2} <= 1
        for v in fleet:
            v_id = v["id"]
            for i in range(num_voyages):
                voy1 = voyages[i]
                j1 = voy1["voyage_id"]
                var1_idx = next(
                    m["index"] for m in var_map if m["vessel_id"] == v_id and m["voyage_id"] == j1
                )

                for k in range(i + 1, num_voyages):
                    voy2 = voyages[k]
                    j2 = voy2["voyage_id"]
                    var2_idx = next(
                        m["index"] for m in var_map if m["vessel_id"] == v_id and m["voyage_id"] == j2
                    )

                    # Check collision
                    overlap = False
                    t1_dep = voy1.get("departure_time", "")
                    t1_arr = voy1.get("arrival_time", "")
                    t2_dep = voy2.get("departure_time", "")
                    t2_arr = voy2.get("arrival_time", "")

                    if t1_dep and t1_arr and t2_dep and t2_arr:
                        if max(t1_dep, t2_dep) <= min(t1_arr, t2_arr):
                            overlap = True

                    if overlap:
                        row = np.zeros(num_vars, dtype=np.float64)
                        row[var1_idx] = 1.0
                        row[var2_idx] = 1.0
                        row_list.append(row)
                        lhs_bounds.append(0.0)
                        rhs_bounds.append(1.0)

        A = np.array(row_list)
        b_l = np.array(lhs_bounds)
        b_u = np.array(rhs_bounds)
        constraints = LinearConstraint(A, b_l, b_u)

        # Variable integrality: all 1 (binary integer: 0 or 1)
        integrality = np.ones(num_vars, dtype=int)
        bounds = Bounds(0, 1)

        # Solve with SciPy HiGHS MILP
        res = milp(
            c=c,
            integrality=integrality,
            constraints=constraints,
            bounds=bounds,
            options={"time_limit": self.time_limit},
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        assignments = []
        assigned_voyages = set()
        total_fuel_cost = 0.0
        total_fuel_mt = 0.0
        total_co2_mt = 0.0
        total_ets_cost = 0.0
        total_charter_cost = 0.0

        if res.success and res.x is not None:
            sol_x = np.round(res.x)
            for var_idx, bit in enumerate(sol_x):
                if bit > 0.5:
                    meta = var_map[var_idx]
                    cost = cost_breakdown[var_idx]
                    assigned_voyages.add(meta["voyage_id"])

                    total_fuel_cost += cost["fuel_cost_inr"]
                    total_fuel_mt += cost["fuel_consumed_mt"]
                    total_co2_mt += cost["co2_emissions_mt"]
                    total_ets_cost += cost["eu_ets_cost_inr"]
                    total_charter_cost += cost["charter_cost_inr"]

                    assignments.append({
                        "vessel_id": meta["vessel_id"],
                        "vessel_name": meta["vessel_name"],
                        "voyage_id": meta["voyage_id"],
                        "fuel_cost_inr": cost["fuel_cost_inr"],
                        "fuel_consumed_mt": cost["fuel_consumed_mt"],
                        "co2_emissions_mt": cost["co2_emissions_mt"],
                        "eu_ets_cost_inr": cost["eu_ets_cost_inr"],
                        "charter_cost_inr": cost["charter_cost_inr"],
                        "cii_rating": cost["cii_rating"],
                    })

        total_operational_cost = total_fuel_cost + total_ets_cost + total_charter_cost

        return {
            "solver_name": "Classical ILP (HiGHS Branch & Cut)",
            "execution_time_ms": round(elapsed_ms, 2),
            "solver_status": res.status_message if hasattr(res, "status_message") else "Optimal",
            "assignments": assignments,
            "total_assigned_voyages": len(assigned_voyages),
            "total_fuel_cost_inr": round(total_fuel_cost, 2),
            "total_fuel_consumed_mt": round(total_fuel_mt, 2),
            "total_co2_emissions_mt": round(total_co2_mt, 2),
            "total_eu_ets_cost_inr": round(total_ets_cost, 2),
            "total_charter_cost_inr": round(total_charter_cost, 2),
            "total_operational_cost_inr": round(total_operational_cost, 2),
            "is_valid": len(assigned_voyages) == num_voyages,
        }
