"""
What-If Maritime Scenario Simulator API Endpoints.
Allows operators to test vessel swaps, alternative fuels, and speed changes,
computing live changes to fuel burn, emissions, EU ETS cost, and IMO CII ratings.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.config import FUEL_PRICES_INR_PER_MT, CF_FACTORS
from app.models.physics import calculate_physics_fuel_consumption
from app.models.cii_calculator import calculate_cii_rating, calculate_regulatory_penalties

router = APIRouter(prefix="/api", tags=["Scenario Runner"])

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_data.json"


def _load_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class ScenarioRequest(BaseModel):
    voyage_id: str = Field(..., description="Target voyage ID")
    vessel_id: Optional[str] = Field(None, description="New vessel ID if swapping vessel")
    speed_knots_delta: float = Field(0.0, description="Speed change in knots (-3.0 to +3.0)")
    alternative_fuel: Optional[str] = Field(None, description="HFO, VLSFO, MGO, LNG, Methanol")


@router.post("/scenario")
async def run_scenario(payload: ScenarioRequest):
    """
    Executes a What-If scenario comparing baseline voyage with hypothetical operational choices.
    """
    data = _load_data()
    voyage = next((v for v in data.get("voyages", []) if v["voyage_id"] == payload.voyage_id), None)
    if not voyage:
        raise HTTPException(status_code=404, detail=f"Voyage {payload.voyage_id} not found")

    fleet = data.get("fleet", [])
    ports = data.get("ports", {})

    orig_vessel_id = voyage["vessel_id"]
    base_vessel = next((v for v in fleet if v["id"] == orig_vessel_id), fleet[0])

    target_vessel_id = payload.vessel_id or orig_vessel_id
    sim_vessel = next((v for v in fleet if v["id"] == target_vessel_id), base_vessel)

    # 1. Baseline Metrics
    base_fuel_mt = voyage["actual_fuel_consumed_mt"]
    base_fuel_type = base_vessel.get("fuel_type", "VLSFO")
    base_fuel_price = FUEL_PRICES_INR_PER_MT.get(base_fuel_type, 51460.0)
    base_fuel_cost = base_fuel_mt * base_fuel_price
    base_co2_mt = voyage["co2_emissions_mt"]
    base_cii_rating = voyage["cii_rating"]
    base_speed = voyage.get("stw_knots", 14.0)

    # 2. Simulated Scenario
    sim_speed = max(9.0, min(22.0, base_speed + payload.speed_knots_delta))
    sim_fuel_type = payload.alternative_fuel or sim_vessel.get("fuel_type", "VLSFO")
    sim_fuel_price = FUEL_PRICES_INR_PER_MT.get(sim_fuel_type, 51460.0)

    # Physics simulation for scenario
    cargo_wt = min(voyage.get("cargo_weight_mt", 0.0), sim_vessel["dwt"] * 0.95)
    disp = (sim_vessel["dwt"] * 0.20) + cargo_wt + 2000.0

    phys_sim = calculate_physics_fuel_consumption(
        dwt=sim_vessel["dwt"],
        displacement_mt=disp,
        speed_knots=sim_speed,
        distance_nm=voyage["distance_nm"],
        draft_m=voyage.get("draft_m", sim_vessel["design_draft_m"] * 0.8),
        beam_m=sim_vessel["beam_m"],
        length_m=sim_vessel["length_m"],
        engine_mcr_kw=sim_vessel["engine_mcr_kw"],
        hull_age_years=sim_vessel["hull_age_years"],
        fouling_coeff=sim_vessel["fouling_coeff"],
        propeller_efficiency=sim_vessel["propeller_efficiency"],
        sfoc_g_kwh=sim_vessel["sfoc_g_kwh"],
        wind_speed_knots=voyage.get("wind_speed_knots", 12.0),
        wave_height_m=voyage.get("wave_height_m", 1.5),
        current_knots=voyage.get("current_knots", 0.0),
    )
    sim_fuel_mt = phys_sim["fuel_mt"]
    sim_fuel_cost = sim_fuel_mt * sim_fuel_price

    cf_sim = CF_FACTORS.get(sim_fuel_type, 3.151)
    sim_co2_mt = sim_fuel_mt * cf_sim

    # Regulatory & CII
    sim_cii = calculate_cii_rating(
        vessel_type=sim_vessel["type"],
        dwt=sim_vessel["dwt"],
        fuel_consumption_mt=sim_fuel_mt,
        distance_nm=voyage["distance_nm"],
        fuel_type=sim_fuel_type,
    )

    orig_meta = ports.get(voyage["origin_port"], {"is_eu": False})
    dest_meta = ports.get(voyage["destination_port"], {"is_eu": False})

    reg_sim = calculate_regulatory_penalties(
        co2_emissions_mt=sim_co2_mt,
        is_eu_origin=orig_meta.get("is_eu", False),
        is_eu_destination=dest_meta.get("is_eu", False),
        eexi_compliant=sim_vessel["eexi_compliant"],
        cii_rating=sim_cii["rating"],
    )

    reg_base = calculate_regulatory_penalties(
        co2_emissions_mt=base_co2_mt,
        is_eu_origin=orig_meta.get("is_eu", False),
        is_eu_destination=dest_meta.get("is_eu", False),
        eexi_compliant=base_vessel["eexi_compliant"],
        cii_rating=base_cii_rating,
    )

    # Deltas
    fuel_delta_mt = round(sim_fuel_mt - base_fuel_mt, 2)
    fuel_delta_pct = round((fuel_delta_mt / max(1.0, base_fuel_mt)) * 100.0, 2)
    cost_delta_inr = round(sim_fuel_cost - base_fuel_cost, 2)
    co2_delta_mt = round(sim_co2_mt - base_co2_mt, 2)
    co2_delta_pct = round((co2_delta_mt / max(1.0, base_co2_mt)) * 100.0, 2)
    ets_cost_delta = round(
        reg_sim["eu_ets_cost_inr"] - reg_base["eu_ets_cost_inr"], 2
    )

    return {
        "voyage_id": voyage["voyage_id"],
        "baseline": {
            "vessel_id": base_vessel["id"],
            "vessel_name": base_vessel["name"],
            "speed_knots": base_speed,
            "fuel_type": base_fuel_type,
            "fuel_consumed_mt": round(base_fuel_mt, 2),
            "fuel_cost_inr": round(base_fuel_cost, 2),
            "co2_emissions_mt": round(base_co2_mt, 2),
            "cii_rating": base_cii_rating,
            "attained_cii": voyage.get("attained_cii", 0.0),
            "eu_ets_cost_inr": reg_base["eu_ets_cost_inr"],
            "duration_hours": voyage.get("duration_hours", 0.0),
        },
        "scenario": {
            "vessel_id": sim_vessel["id"],
            "vessel_name": sim_vessel["name"],
            "speed_knots": sim_speed,
            "fuel_type": sim_fuel_type,
            "fuel_consumed_mt": round(sim_fuel_mt, 2),
            "fuel_cost_inr": round(sim_fuel_cost, 2),
            "co2_emissions_mt": round(sim_co2_mt, 2),
            "cii_rating": sim_cii["rating"],
            "attained_cii": sim_cii["attained_cii"],
            "rating_description": sim_cii["rating_description"],
            "eu_ets_cost_inr": reg_sim["eu_ets_cost_inr"],
            "duration_hours": phys_sim["voyage_hours"],
        },
        "comparison_delta": {
            "fuel_delta_mt": fuel_delta_mt,
            "fuel_delta_pct": fuel_delta_pct,
            "fuel_cost_delta_inr": cost_delta_inr,
            "co2_delta_mt": co2_delta_mt,
            "co2_delta_pct": co2_delta_pct,
            "eu_ets_delta_inr": ets_cost_delta,
            "hours_delta": round(phys_sim["voyage_hours"] - voyage.get("duration_hours", 0.0), 1),
            "cii_rating_change": f"{base_cii_rating} -> {sim_cii['rating']}",
            "is_net_positive_reduction": co2_delta_mt < 0,
        },
    }
