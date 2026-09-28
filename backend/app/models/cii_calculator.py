"""
IMO Carbon Intensity Indicator (CII), EEXI, and EU ETS Compliance Engine.

Standards Reference:
- IMO Resolution MEPC.337(76): Guidelines on the operational carbon intensity rating.
- IMO MEPC.328(76): 2021 Revised MARPOL Annex VI (CII & EEXI requirements).
- EU Directive 2023/959: Inclusion of maritime transport in EU ETS (2024-2026 phase-in).
"""

from typing import Dict, Any, Optional
from app.config import (
    CF_FACTORS,
    CII_REF_PARAMS,
    CII_EXP_VECTORS,
    EU_ETS_CARBON_PRICE_INR_PER_TON,
)


def calculate_cii_rating(
    vessel_type: str,
    dwt: float,
    fuel_consumption_mt: float,
    distance_nm: float,
    fuel_type: str = "VLSFO",
    year: int = 2026,
) -> Dict[str, Any]:
    """
    Computes the IMO Operational CII Rating (A through E band) for a voyage or annual period.

    Formula:
    AER = (Fuel Consumption (MT) * Cf * 10^6) / (Capacity * Distance NM)  [g CO2 / dwt-nm]
    Required CII = Reference CII * (1 - Z / 100)
    where Z is the reduction factor (e.g., 11% in 2026).
    """
    # Fallback to Bulk Carrier if custom type provided
    ship_category = vessel_type if vessel_type in CII_REF_PARAMS else "Bulk Carrier"
    params = CII_REF_PARAMS[ship_category]
    exp = CII_EXP_VECTORS[ship_category]
    cf = CF_FACTORS.get(fuel_type, 3.151)

    # 1. Total CO2 produced in Metric Tons
    co2_emissions_mt = fuel_consumption_mt * cf

    # 2. Attained Carbon Intensity Indicator (AER in g CO2 / (DWT * nm))
    capacity_transport_work = dwt * max(10.0, distance_nm)
    attained_cii = (co2_emissions_mt * 1_000_000.0) / max(1.0, capacity_transport_work)

    # 3. Reference CII Benchmark
    cii_ref = params["a"] * pow(max(1000.0, dwt), -params["c"])

    # Reduction factor Z (2023: 5%, 2024: 7%, 2025: 9%, 2026: 11%, +2%/yr)
    z_factor = 5.0 + max(0, year - 2023) * 2.0
    required_cii = cii_ref * (1.0 - z_factor / 100.0)

    # 4. Rating Boundaries Calculation
    exp_d1 = required_cii * exp["d1"]
    exp_d2 = required_cii * exp["d2"]
    exp_d3 = required_cii * exp["d3"]
    exp_d4 = required_cii * exp["d4"]

    # Determine Rating Band
    if attained_cii <= exp_d1:
        rating = "A"
        rating_desc = "Superior Efficiency"
        status_color = "#10b981"  # Emerald
    elif attained_cii <= exp_d2:
        rating = "B"
        rating_desc = "Minor Superior"
        status_color = "#3b82f6"  # Blue
    elif attained_cii <= exp_d3:
        rating = "C"
        rating_desc = "Moderate (Compliant)"
        status_color = "#f59e0b"  # Amber
    elif attained_cii <= exp_d4:
        rating = "D"
        rating_desc = "Minor Inferior (Risk of Corrective Action)"
        status_color = "#ff5722"  # Coral Red
    else:
        rating = "E"
        rating_desc = "Inferior (Immediate Corrective Plan Required)"
        status_color = "#ef4444"  # Red

    ratio = attained_cii / max(0.01, required_cii)

    return {
        "attained_cii": round(attained_cii, 2),
        "required_cii": round(required_cii, 2),
        "cii_reference": round(cii_ref, 2),
        "ratio_to_required": round(ratio, 3),
        "rating": rating,
        "rating_description": rating_desc,
        "status_color": status_color,
        "boundaries": {
            "A_max": round(exp_d1, 2),
            "B_max": round(exp_d2, 2),
            "C_max": round(exp_d3, 2),
            "D_max": round(exp_d4, 2),
        },
        "co2_emissions_mt": round(co2_emissions_mt, 2),
    }


def calculate_regulatory_penalties(
    co2_emissions_mt: float,
    is_eu_origin: bool = False,
    is_eu_destination: bool = False,
    eexi_compliant: bool = True,
    cii_rating: str = "C",
) -> Dict[str, Any]:
    """
    Computes EU ETS cost exposure and IMO compliance status.

    EU ETS Scope:
    - 100% of emissions between two EU ports.
    - 50% of emissions on voyages starting or ending at an EU port.
    - 0% for voyages wholly outside the European Economic Area.
    """
    if is_eu_origin and is_eu_destination:
        ets_scope = 1.0  # 100%
        route_scope_desc = "Intra-EU (100% ETS scope)"
    elif is_eu_origin or is_eu_destination:
        ets_scope = 0.5  # 50%
        route_scope_desc = "Extra-EU / Port of Call (50% ETS scope)"
    else:
        ets_scope = 0.0  # 0%
        route_scope_desc = "Non-EU Trade Lane (0% ETS scope)"

    taxable_co2_mt = co2_emissions_mt * ets_scope
    eu_ets_cost_inr = taxable_co2_mt * EU_ETS_CARBON_PRICE_INR_PER_TON

    # IMO CII Non-compliance risk charge estimation in INR
    # Vessels rated D face charter discounts (~₹10 Lakh); E ratings face mandatory SEEMP plan (~₹38 Lakh)
    cii_penalty_risk_inr = 0.0
    if cii_rating == "D":
        cii_penalty_risk_inr = 10_50_000.0
    elif cii_rating == "E":
        cii_penalty_risk_inr = 37_80_000.0

    # EEXI compliance surcharge if power limiter required
    eexi_penalty_inr = 0.0 if eexi_compliant else 21_00_000.0

    total_regulatory_exposure = eu_ets_cost_inr + cii_penalty_risk_inr + eexi_penalty_inr

    return {
        "eu_ets_scope_pct": int(ets_scope * 100),
        "eu_ets_scope_desc": route_scope_desc,
        "taxable_co2_mt": round(taxable_co2_mt, 2),
        "eu_ets_cost_inr": round(eu_ets_cost_inr, 2),
        "eu_ets_cost_usd": round(eu_ets_cost_inr, 2),  # Backward compatibility
        "cii_penalty_risk_inr": round(cii_penalty_risk_inr, 2),
        "eexi_penalty_inr": round(eexi_penalty_inr, 2),
        "total_regulatory_exposure_inr": round(total_regulatory_exposure, 2),
        "total_regulatory_exposure_usd": round(total_regulatory_exposure, 2),
    }
