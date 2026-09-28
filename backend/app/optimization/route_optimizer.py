"""
Secondary Continuous Speed & Weather Route Optimizer.
Optimizes the leg-by-leg speed profile v_1, v_2, ..., v_M along voyage waypoints
to minimize hydrodynamic resistance in heavy weather while strictly honoring the arrival ETA.
"""

import time
import math
from typing import Dict, List, Any, Tuple
import numpy as np

from app.config import CF_FACTORS
from app.models.physics import calculate_physics_fuel_consumption


class WeatherRouteSpeedOptimizer:
    def __init__(self, eta_penalty_per_hour: float = 3000.0):
        self.eta_penalty = eta_penalty_per_hour

    def optimize_speed_profile(
        self,
        legs: List[Dict[str, Any]],
        vessel: Dict[str, Any],
        max_eta_hours: float,
        min_speed_knots: float = 10.0,
        max_speed_knots: float = 18.0,
        iterations: int = 1500,
    ) -> Dict[str, Any]:
        """
        Uses Continuous Simulated Annealing to find the optimal speed through water
        for each leg that minimizes total fuel consumption while satisfying ETA <= max_eta_hours.
        """
        start_time = time.perf_counter()
        num_legs = len(legs)
        if num_legs == 0:
            return {}

        # Initial baseline: constant speed that meets ETA exactly
        total_dist = sum(l.get("distance_nm", 500.0) for l in legs)
        avg_speed = max(min_speed_knots, min(max_speed_knots, total_dist / max(1.0, max_eta_hours)))
        current_speeds = np.full(num_legs, avg_speed)

        fuel_type = vessel.get("fuel_type", "VLSFO")
        cf = CF_FACTORS.get(fuel_type, 3.151)

        def eval_profile(speeds: np.ndarray) -> Tuple[float, float, float]:
            total_fuel = 0.0
            total_hours = 0.0

            for i, leg in enumerate(legs):
                dist = leg.get("distance_nm", 500.0)
                spd = speeds[i]
                wave = leg.get("wave_height_m", 1.5)
                wind = leg.get("wind_speed_knots", 12.0)
                current = leg.get("current_knots", 0.0)
                sog = max(4.0, spd + current)
                hrs = dist / sog
                total_hours += hrs

                phys = calculate_physics_fuel_consumption(
                    dwt=vessel["dwt"],
                    displacement_mt=vessel["dwt"] * 0.85,
                    speed_knots=spd,
                    distance_nm=dist,
                    draft_m=vessel.get("design_draft_m", 12.0) * 0.85,
                    beam_m=vessel.get("beam_m", 32.0),
                    length_m=vessel.get("length_m", 200.0),
                    engine_mcr_kw=vessel.get("engine_mcr_kw", 14000.0),
                    hull_age_years=vessel.get("hull_age_years", 3.0),
                    fouling_coeff=vessel.get("fouling_coeff", 1.05),
                    propeller_efficiency=vessel.get("propeller_efficiency", 0.68),
                    wind_speed_knots=wind,
                    wave_height_m=wave,
                    current_knots=current,
                )
                total_fuel += phys["fuel_mt"]

            # Penalty for ETA delay
            eta_delay = max(0.0, total_hours - max_eta_hours)
            penalty = eta_delay * self.eta_penalty
            cost = total_fuel * 620.0 + penalty
            return cost, total_fuel, total_hours

        # Compute baseline with flat speed
        base_cost, base_fuel, base_hours = eval_profile(current_speeds)

        # Simulated Annealing parameters
        temp = 100.0
        cooling_rate = 0.995
        best_speeds = current_speeds.copy()
        best_cost = base_cost
        best_fuel = base_fuel
        best_hours = base_hours

        curr_cost = base_cost

        for step in range(iterations):
            # Perturb a random leg speed
            idx = np.random.randint(0, num_legs)
            candidate_speeds = current_speeds.copy()
            candidate_speeds[idx] += np.random.normal(0, 0.4)
            candidate_speeds[idx] = max(min_speed_knots, min(max_speed_knots, candidate_speeds[idx]))

            cand_cost, cand_fuel, cand_hours = eval_profile(candidate_speeds)
            delta = cand_cost - curr_cost

            # Metropolis acceptance criterion
            if delta < 0 or math.exp(-delta / max(0.01, temp)) > np.random.rand():
                current_speeds = candidate_speeds
                curr_cost = cand_cost

                if cand_cost < best_cost and cand_hours <= max_eta_hours + 0.1:
                    best_cost = cand_cost
                    best_speeds = candidate_speeds.copy()
                    best_fuel = cand_fuel
                    best_hours = cand_hours

            temp *= cooling_rate

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Construct leg-by-leg comparative output
        optimized_legs = []
        for i, leg in enumerate(legs):
            opt_spd = round(float(best_speeds[i]), 1)
            flat_spd = round(float(avg_speed), 1)
            wave = leg.get("wave_height_m", 1.5)
            wind = leg.get("wind_speed_knots", 12.0)
            dist = leg.get("distance_nm", 500.0)
            optimized_legs.append({
                "leg_index": leg.get("leg_index", i + 1),
                "distance_nm": dist,
                "wave_height_m": wave,
                "wind_speed_knots": wind,
                "flat_speed_knots": flat_spd,
                "optimized_speed_knots": opt_spd,
                "speed_delta_knots": round(opt_spd - flat_spd, 1),
                "weather_strategy": "Slow-steaming through heavy sea" if wave > 2.5 else "Accelerating in calm water",
            })

        fuel_saved_mt = max(0.0, round(base_fuel - best_fuel, 2))
        fuel_saved_pct = round((fuel_saved_mt / max(1.0, base_fuel)) * 100.0, 2)
        co2_saved_mt = round(fuel_saved_mt * cf, 2)
        cost_saved_inr = round(fuel_saved_mt * 51460.0, 2)

        return {
            "execution_time_ms": round(elapsed_ms, 2),
            "max_allowed_eta_hours": round(max_eta_hours, 1),
            "baseline_flat_speed_knots": round(avg_speed, 1),
            "baseline_fuel_consumed_mt": round(base_fuel, 2),
            "baseline_voyage_hours": round(base_hours, 1),
            "optimized_fuel_consumed_mt": round(best_fuel, 2),
            "optimized_voyage_hours": round(best_hours, 1),
            "fuel_saved_mt": fuel_saved_mt,
            "fuel_saved_pct": fuel_saved_pct,
            "co2_saved_mt": co2_saved_mt,
            "cost_saved_inr": cost_saved_inr,
            "eta_honored": best_hours <= max_eta_hours + 0.2,
            "legs": optimized_legs,
        }
