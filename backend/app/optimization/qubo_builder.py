"""
QUBO (Quadratic Unconstrained Binary Optimization) Formulation for Green Fleet Assignment.

Maps maritime fleet operational constraints and objectives into Ising / QUBO matrices:
min x^T Q x + c
where x_{v,j} ∈ {0, 1} indicates whether vessel v is assigned to voyage j.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from datetime import datetime

from app.config import FUEL_PRICES_INR_PER_MT, CF_FACTORS, EU_ETS_CARBON_PRICE_INR_PER_TON
from app.models.physics import calculate_physics_fuel_consumption
from app.models.cii_calculator import calculate_cii_rating, calculate_regulatory_penalties


class FleetQUBOBuilder:
    def __init__(
        self,
        cost_scale: float = 0.001,  # Scale rupees to kilo-INR for numerical stability
        penalty_unassigned: float = 4000.0,  # ₹4M penalty for leaving voyage unassigned
        penalty_overlap: float = 5000.0,     # ₹5M penalty for concurrent voyage collision
        penalty_incompatible: float = 10000.0, # ₹10M penalty for cargo/vessel incompatibility
        penalty_blackout: float = 8000.0,    # ₹8M penalty for drydock blackout breach
        penalty_bad_cii: float = 300.0,      # ₹300k penalty for D/E CII rating
    ):
        self.cost_scale = cost_scale
        self.p_unassigned = penalty_unassigned
        self.p_overlap = penalty_overlap
        self.p_incompatible = penalty_incompatible
        self.p_blackout = penalty_blackout
        self.p_bad_cii = penalty_bad_cii

    def build_qubo(
        self,
        fleet: List[Dict[str, Any]],
        voyages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Constructs the QUBO matrix for a given fleet subset and set of unassigned voyages.

        Returns:
        --------
        dict with:
          - qubo_dict: Dict[Tuple[int, int], float] compatible with D-Wave dimod
          - Q_matrix: 2D numpy array of shape (N, N)
          - var_map: list of {"index": i, "vessel_id": ..., "voyage_id": ...}
          - cost_breakdown: detailed precomputed cost of each (vessel, voyage) pair
          - num_variables: total binary decision variables
        """
        num_vessels = len(fleet)
        num_voyages = len(voyages)
        num_vars = num_vessels * num_voyages

        var_map = []
        rev_map = {}
        for v_idx, v in enumerate(fleet):
            for j_idx, voy in enumerate(voyages):
                var_idx = v_idx * num_voyages + j_idx
                meta = {
                    "index": var_idx,
                    "vessel_index": v_idx,
                    "voyage_index": j_idx,
                    "vessel_id": v["id"],
                    "vessel_name": v["name"],
                    "voyage_id": voy["voyage_id"],
                }
                var_map.append(meta)
                rev_map[(v["id"], voy["voyage_id"])] = var_idx

        # Initialize QUBO matrix
        Q = np.zeros((num_vars, num_vars), dtype=np.float64)
        cost_breakdown: Dict[int, Dict[str, Any]] = {}

        # 1. Linear Operational Cost for assigning vessel v to voyage j
        for v_idx, v in enumerate(fleet):
            for j_idx, voy in enumerate(voyages):
                var_i = v_idx * num_voyages + j_idx

                # Compute voyage duration and fuel consumption
                dist = voy["distance_nm"]
                speed = voy.get("stw_knots", 13.5)
                cargo_wt = voy.get("cargo_weight_mt", 0.0)
                disp = (v["dwt"] * 0.20) + cargo_wt + 2000.0

                phys = calculate_physics_fuel_consumption(
                    dwt=v["dwt"],
                    displacement_mt=disp,
                    speed_knots=speed,
                    distance_nm=dist,
                    draft_m=voy.get("draft_m", v["design_draft_m"] * 0.8),
                    beam_m=v["beam_m"],
                    length_m=v["length_m"],
                    engine_mcr_kw=v["engine_mcr_kw"],
                    hull_age_years=v["hull_age_years"],
                    fouling_coeff=v["fouling_coeff"],
                    propeller_efficiency=v["propeller_efficiency"],
                    sfoc_g_kwh=v["sfoc_g_kwh"],
                    wind_speed_knots=voy.get("wind_speed_knots", 12.0),
                    wave_height_m=voy.get("wave_height_m", 1.5),
                )
                fuel_mt = phys["fuel_mt"]
                fuel_type = v.get("fuel_type", "VLSFO")
                fuel_price = FUEL_PRICES_INR_PER_MT.get(fuel_type, 51460.0)
                fuel_cost_inr = fuel_mt * fuel_price

                # EU ETS carbon cost
                cf = CF_FACTORS.get(fuel_type, 3.151)
                co2_mt = fuel_mt * cf
                is_eu_trade = voy.get("is_eu_trade", False)
                ets_scope = 0.5 if is_eu_trade else 0.0
                eu_ets_cost_inr = co2_mt * ets_scope * EU_ETS_CARBON_PRICE_INR_PER_TON

                # Time-charter hire cost
                duration_days = phys["voyage_hours"] / 24.0
                charter_cost_inr = duration_days * v.get("daily_charter_rate_inr", 1660000.0)

                # IMO CII rating impact
                cii = calculate_cii_rating(
                    vessel_type=v["type"],
                    dwt=v["dwt"],
                    fuel_consumption_mt=fuel_mt,
                    distance_nm=dist,
                    fuel_type=fuel_type,
                )
                cii_penalty = 0.0
                if cii["rating"] in ["D", "E"]:
                    cii_penalty = self.p_bad_cii

                # Compatibility Check (Cargo & Vessel Class)
                is_compatible = True
                incompat_reason = ""
                voy_type = voy.get("vessel_type")
                if voy_type and v["type"] != voy_type:
                    is_compatible = False
                    incompat_reason = f"Type mismatch: {v['type']} cannot haul {voy_type} cargo."
                elif cargo_wt > v["dwt"] * 1.02:
                    is_compatible = False
                    incompat_reason = f"Capacity overload: cargo {cargo_wt} MT exceeds DWT {v['dwt']} MT."

                compat_penalty = 0.0 if is_compatible else self.p_incompatible

                # Drydock Blackout Check
                blackout_penalty = 0.0
                blackout_start = v.get("drydock_blackout_start")
                blackout_end = v.get("drydock_blackout_end")
                voy_dept = voy.get("departure_time", "")
                if blackout_start and blackout_end and voy_dept:
                    try:
                        dep_date = datetime.strptime(voy_dept.split()[0], "%Y-%m-%d")
                        bk_s = datetime.strptime(blackout_start, "%Y-%m-%d")
                        bk_e = datetime.strptime(blackout_end, "%Y-%m-%d")
                        if bk_s <= dep_date <= bk_e:
                            blackout_penalty = self.p_blackout
                    except Exception:
                        pass

                operational_cost_scaled = (
                    fuel_cost_inr + eu_ets_cost_inr + charter_cost_inr
                ) * self.cost_scale

                total_linear_cost = (
                    operational_cost_scaled
                    + cii_penalty
                    + compat_penalty
                    + blackout_penalty
                )

                cost_breakdown[var_i] = {
                    "vessel_id": v["id"],
                    "vessel_name": v["name"],
                    "voyage_id": voy["voyage_id"],
                    "fuel_cost_inr": round(fuel_cost_inr, 2),
                    "fuel_consumed_mt": round(fuel_mt, 2),
                    "co2_emissions_mt": round(co2_mt, 2),
                    "eu_ets_cost_inr": round(eu_ets_cost_inr, 2),
                    "charter_cost_inr": round(charter_cost_inr, 2),
                    "cii_rating": cii["rating"],
                    "is_compatible": is_compatible,
                    "incompat_reason": incompat_reason,
                    "total_operational_cost_inr": round(
                        fuel_cost_inr + eu_ets_cost_inr + charter_cost_inr, 2
                    ),
                }

                # Add to diagonal Q[var_i, var_i]
                Q[var_i, var_i] += total_linear_cost

        # 2. Constraint: Each voyage j must be assigned to EXACTLY one vessel
        # Penalty: P_unassigned * (sum_v x_{v,j} - 1)^2
        # = P_unassigned * [ sum_v x_{v,j} + 2 sum_{v < u} x_{v,j} x_{u,j} - 2 sum_v x_{v,j} + 1 ]
        # = P_unassigned * [ - sum_v x_{v,j} + 2 sum_{v < u} x_{v,j} x_{u,j} + const ]
        for j_idx in range(num_voyages):
            # Diagonal terms: -P_unassigned
            for v_idx in range(num_vessels):
                var_i = v_idx * num_voyages + j_idx
                Q[var_i, var_i] -= self.p_unassigned

            # Quadratic cross-terms: + 2 * P_unassigned
            for v1 in range(num_vessels):
                var_1 = v1 * num_voyages + j_idx
                for v2 in range(v1 + 1, num_vessels):
                    var_2 = v2 * num_voyages + j_idx
                    Q[var_1, var_2] += 2.0 * self.p_unassigned

        # 3. Constraint: Vessel schedule overlap
        # A single vessel cannot perform two overlapping voyages simultaneously
        # Penalty: P_overlap * x_{v, j1} * x_{v, j2}
        for v_idx in range(num_vessels):
            for j1 in range(num_voyages):
                var_1 = v_idx * num_voyages + j1
                voy1 = voyages[j1]
                t1_dep = voy1.get("departure_time", "")
                t1_arr = voy1.get("arrival_time", "")

                for j2 in range(j1 + 1, num_voyages):
                    var_2 = v_idx * num_voyages + j2
                    voy2 = voyages[j2]
                    t2_dep = voy2.get("departure_time", "")
                    t2_arr = voy2.get("arrival_time", "")

                    # Check time interval collision
                    overlap = False
                    if t1_dep and t1_arr and t2_dep and t2_arr:
                        try:
                            d1 = datetime.strptime(t1_dep, "%Y-%m-%d %H:%M")
                            a1 = datetime.strptime(t1_arr, "%Y-%m-%d %H:%M")
                            d2 = datetime.strptime(t2_dep, "%Y-%m-%d %H:%M")
                            a2 = datetime.strptime(t2_arr, "%Y-%m-%d %H:%M")
                            # Interval overlap condition
                            if max(d1, d2) <= min(a1, a2):
                                overlap = True
                        except Exception:
                            pass

                    if overlap:
                        Q[var_1, var_2] += self.p_overlap

        # Convert to dictionary format for D-Wave / dimod samplers
        qubo_dict: Dict[Tuple[int, int], float] = {}
        for r in range(num_vars):
            for c in range(r, num_vars):
                val = float(Q[r, c])
                if abs(val) > 1e-4:
                    qubo_dict[(r, c)] = val

        return {
            "qubo_dict": qubo_dict,
            "Q_matrix": Q,
            "var_map": var_map,
            "cost_breakdown": cost_breakdown,
            "num_variables": num_vars,
            "num_vessels": num_vessels,
            "num_voyages": num_voyages,
        }
