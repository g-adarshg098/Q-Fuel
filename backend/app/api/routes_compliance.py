"""
IMO CII, EEXI, and EU ETS Regulatory Compliance Scorecard API Endpoints.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from fastapi import APIRouter

from app.models.cii_calculator import calculate_cii_rating, calculate_regulatory_penalties

router = APIRouter(prefix="/api", tags=["Compliance Scorecard"])

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_data.json"


def _load_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/compliance")
async def get_compliance_scorecard():
    """
    Returns fleet-wide IMO CII rating distribution, EEXI compliance audit,
    and cumulative EU ETS / FuelEU Maritime financial exposure.
    """
    data = _load_data()
    fleet = data.get("fleet", [])
    voyages = data.get("voyages", [])

    # Calculate per-vessel annual performance
    vessel_stats = {}
    for v in fleet:
        vessel_stats[v["id"]] = {
            "vessel_id": v["id"],
            "vessel_name": v["name"],
            "vessel_type": v["type"],
            "subtype": v.get("subtype", ""),
            "dwt": v["dwt"],
            "fuel_type": v["fuel_type"],
            "eexi_compliant": v["eexi_compliant"],
            "total_distance_nm": 0.0,
            "total_fuel_mt": 0.0,
            "total_co2_mt": 0.0,
            "total_eu_ets_cost_usd": 0.0,
            "voyage_count": 0,
            "ratings_list": [],
        }

    for voy in voyages:
        v_id = voy["vessel_id"]
        if v_id in vessel_stats:
            st = vessel_stats[v_id]
            st["total_distance_nm"] += voy["distance_nm"]
            st["total_fuel_mt"] += voy["actual_fuel_consumed_mt"]
            st["total_co2_mt"] += voy["co2_emissions_mt"]
            st["total_eu_ets_cost_usd"] += voy.get("eu_ets_cost_usd", 0.0)
            st["voyage_count"] += 1
            st["ratings_list"].append(voy["cii_rating"])

    # Compute annual aggregated CII rating for each vessel
    rating_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    scorecard = []
    total_fleet_co2 = 0.0
    total_fleet_ets = 0.0
    total_fleet_fuel = 0.0

    for v_id, st in vessel_stats.items():
        if st["total_distance_nm"] > 0:
            annual_cii = calculate_cii_rating(
                vessel_type=st["vessel_type"],
                dwt=st["dwt"],
                fuel_consumption_mt=st["total_fuel_mt"],
                distance_nm=st["total_distance_nm"],
                fuel_type=st["fuel_type"],
            )
            final_rating = annual_cii["rating"]
            rating_desc = annual_cii["rating_description"]
            status_color = annual_cii["status_color"]
            attained = annual_cii["attained_cii"]
            required = annual_cii["required_cii"]
        else:
            final_rating = "C"
            rating_desc = "Moderate (No active sea miles)"
            status_color = "#f59e0b"
            attained = 0.0
            required = 0.0

        rating_counts[final_rating] = rating_counts.get(final_rating, 0) + 1
        total_fleet_co2 += st["total_co2_mt"]
        total_fleet_ets += st["total_eu_ets_cost_usd"]
        total_fleet_fuel += st["total_fuel_mt"]

        # Recommended corrective action for D or E
        corrective_action = None
        if final_rating == "D":
            corrective_action = "Implement 5-8% slow-steaming and schedule propeller polish / hull biofouling inspection."
        elif final_rating == "E":
            corrective_action = "Mandatory SEEMP Part III Corrective Action Plan: install Engine Power Limiter (EPL) and drydock coating."

        scorecard.append({
            "vessel_id": st["vessel_id"],
            "vessel_name": st["vessel_name"],
            "vessel_type": st["vessel_type"],
            "subtype": st["subtype"],
            "dwt": st["dwt"],
            "fuel_type": st["fuel_type"],
            "annual_attained_cii": attained,
            "annual_required_cii": required,
            "annual_rating": final_rating,
            "rating_description": rating_desc,
            "status_color": status_color,
            "eexi_compliant": st["eexi_compliant"],
            "total_distance_nm": round(st["total_distance_nm"], 1),
            "total_fuel_mt": round(st["total_fuel_mt"], 1),
            "total_co2_mt": round(st["total_co2_mt"], 1),
            "total_eu_ets_cost_inr": round(st["total_eu_ets_cost_usd"], 2),
            "total_eu_ets_cost_usd": round(st["total_eu_ets_cost_usd"], 2),
            "corrective_action": corrective_action,
        })

    eexi_compliant_count = sum(1 for v in fleet if v.get("eexi_compliant", True))

    return {
        "fleet_summary": {
            "total_vessels": len(fleet),
            "eexi_compliance_rate_pct": round((eexi_compliant_count / len(fleet)) * 100.0, 1),
            "total_fuel_consumed_mt": round(total_fleet_fuel, 2),
            "total_co2_emissions_mt": round(total_fleet_co2, 2),
            "total_eu_ets_cost_inr": round(total_fleet_ets, 2),
            "total_eu_ets_cost_usd": round(total_fleet_ets, 2),
            "rating_distribution": rating_counts,
            "compliant_vessels_count": rating_counts.get("A", 0) + rating_counts.get("B", 0) + rating_counts.get("C", 0),
            "at_risk_vessels_count": rating_counts.get("D", 0) + rating_counts.get("E", 0),
        },
        "vessel_scorecards": scorecard,
    }
