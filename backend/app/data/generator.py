"""
Maritime Dataset Generator.
Generates realistic fleet specifications (16 vessels across 4 classes)
and 120+ historical/active voyages across major international maritime trade lanes.
"""

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from app.models.physics import calculate_physics_fuel_consumption
from app.models.cii_calculator import calculate_cii_rating, calculate_regulatory_penalties

# Major Maritime Global Ports with Coordinates and EU ETS Flag
GLOBAL_PORTS: Dict[str, Dict[str, Any]] = {
    "Rotterdam": {"lat": 51.95, "lon": 4.13, "country": "Netherlands", "is_eu": True},
    "Antwerp": {"lat": 51.28, "lon": 4.33, "country": "Belgium", "is_eu": True},
    "Hamburg": {"lat": 53.54, "lon": 9.98, "country": "Germany", "is_eu": True},
    "Singapore": {"lat": 1.28, "lon": 103.85, "country": "Singapore", "is_eu": False},
    "Shanghai": {"lat": 31.23, "lon": 121.47, "country": "China", "is_eu": False},
    "Ningbo-Zhoushan": {"lat": 29.87, "lon": 121.55, "country": "China", "is_eu": False},
    "Busan": {"lat": 35.10, "lon": 129.04, "country": "South Korea", "is_eu": False},
    "Yokohama": {"lat": 35.44, "lon": 139.64, "country": "Japan", "is_eu": False},
    "Port Hedland": {"lat": -20.31, "lon": 118.57, "country": "Australia", "is_eu": False},
    "Ras Tanura": {"lat": 26.64, "lon": 50.16, "country": "Saudi Arabia", "is_eu": False},
    "Houston": {"lat": 29.76, "lon": -95.36, "country": "USA", "is_eu": False},
    "Santos": {"lat": -23.96, "lon": -46.33, "country": "Brazil", "is_eu": False},
    "Dubai (Jebel Ali)": {"lat": 24.98, "lon": 55.06, "country": "UAE", "is_eu": False},
    "Suez Canal": {"lat": 29.97, "lon": 32.56, "country": "Egypt", "is_eu": False},
    "Panama Canal": {"lat": 8.95, "lon": -79.55, "country": "Panama", "is_eu": False},
    "Algeciras": {"lat": 36.13, "lon": -5.44, "country": "Spain", "is_eu": True},
}

# Standard Vessel Fleet Master Template (16 Vessels)
FLEET_TEMPLATES: List[Dict[str, Any]] = [
    # Capesize Bulk Carriers (Iron ore, coal)
    {
        "id": "VESSEL-001",
        "name": "Pacific Titan",
        "type": "Bulk Carrier",
        "subtype": "Capesize",
        "dwt": 182000,
        "gt": 94000,
        "length_m": 292.0,
        "beam_m": 45.0,
        "design_draft_m": 18.2,
        "engine_mcr_kw": 18600,
        "sfoc_g_kwh": 178.0,
        "hull_age_years": 3.2,
        "fouling_coeff": 1.05,
        "propeller_efficiency": 0.69,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 24500,
        "daily_charter_rate_inr": 2058000,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-11-01",
        "drydock_blackout_end": "2026-11-20",
    },
    {
        "id": "VESSEL-002",
        "name": "Atlantic Ore",
        "type": "Bulk Carrier",
        "subtype": "Capesize",
        "dwt": 176000,
        "gt": 91000,
        "length_m": 289.0,
        "beam_m": 45.0,
        "design_draft_m": 18.0,
        "engine_mcr_kw": 18200,
        "sfoc_g_kwh": 186.0,
        "hull_age_years": 6.8,
        "fouling_coeff": 1.14,
        "propeller_efficiency": 0.65,
        "fuel_type": "HFO",
        "daily_charter_rate_usd": 21000,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-12-05",
        "drydock_blackout_end": "2026-12-28",
    },
    # Panamax & Ultramax Bulk Carriers (Grains, minerals)
    {
        "id": "VESSEL-003",
        "name": "Nordic Pioneer",
        "type": "Bulk Carrier",
        "subtype": "Panamax",
        "dwt": 82000,
        "gt": 44000,
        "length_m": 229.0,
        "beam_m": 32.2,
        "design_draft_m": 14.5,
        "engine_mcr_kw": 9800,
        "sfoc_g_kwh": 172.0,
        "hull_age_years": 2.1,
        "fouling_coeff": 1.03,
        "propeller_efficiency": 0.70,
        "fuel_type": "LNG",
        "daily_charter_rate_usd": 18500,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-004",
        "name": "Baltic Trader",
        "type": "Bulk Carrier",
        "subtype": "Ultramax",
        "dwt": 63500,
        "gt": 36000,
        "length_m": 199.9,
        "beam_m": 32.2,
        "design_draft_m": 13.3,
        "engine_mcr_kw": 8300,
        "sfoc_g_kwh": 183.0,
        "hull_age_years": 4.5,
        "fouling_coeff": 1.09,
        "propeller_efficiency": 0.67,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 15000,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-10-15",
        "drydock_blackout_end": "2026-10-30",
    },
    # Ultra-Large & Neo-Panamax Container Ships
    {
        "id": "VESSEL-005",
        "name": "Apex Horizon",
        "type": "Container",
        "subtype": "ULCS (20k TEU)",
        "dwt": 200000,
        "gt": 210000,
        "length_m": 399.0,
        "beam_m": 58.8,
        "design_draft_m": 16.0,
        "engine_mcr_kw": 62000,
        "sfoc_g_kwh": 169.0,
        "hull_age_years": 1.8,
        "fouling_coeff": 1.02,
        "propeller_efficiency": 0.71,
        "fuel_type": "Methanol",
        "daily_charter_rate_usd": 42000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-006",
        "name": "Starlight Express",
        "type": "Container",
        "subtype": "Neo-Panamax (14k TEU)",
        "dwt": 145000,
        "gt": 140000,
        "length_m": 366.0,
        "beam_m": 51.0,
        "design_draft_m": 15.5,
        "engine_mcr_kw": 51000,
        "sfoc_g_kwh": 181.0,
        "hull_age_years": 3.9,
        "fouling_coeff": 1.08,
        "propeller_efficiency": 0.68,
        "fuel_type": "LNG",
        "daily_charter_rate_usd": 34000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-007",
        "name": "Orient Navigator",
        "type": "Container",
        "subtype": "Post-Panamax (9k TEU)",
        "dwt": 105000,
        "gt": 95000,
        "length_m": 334.0,
        "beam_m": 42.8,
        "design_draft_m": 14.5,
        "engine_mcr_kw": 43000,
        "sfoc_g_kwh": 189.0,
        "hull_age_years": 7.4,
        "fouling_coeff": 1.17,
        "propeller_efficiency": 0.64,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 27000,
        "eexi_compliant": False,
        "drydock_blackout_start": "2026-10-20",
        "drydock_blackout_end": "2026-11-10",
    },
    {
        "id": "VESSEL-008",
        "name": "Seaspan Glory",
        "type": "Container",
        "subtype": "Feedermax (4k TEU)",
        "dwt": 50000,
        "gt": 42000,
        "length_m": 240.0,
        "beam_m": 32.2,
        "design_draft_m": 12.0,
        "engine_mcr_kw": 24000,
        "sfoc_g_kwh": 184.0,
        "hull_age_years": 4.1,
        "fouling_coeff": 1.07,
        "propeller_efficiency": 0.68,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 19000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    # Crude & Product Tankers
    {
        "id": "VESSEL-009",
        "name": "Solaris Glory",
        "type": "Tanker",
        "subtype": "VLCC (300k DWT)",
        "dwt": 318000,
        "gt": 162000,
        "length_m": 333.0,
        "beam_m": 60.0,
        "design_draft_m": 21.5,
        "engine_mcr_kw": 27100,
        "sfoc_g_kwh": 177.0,
        "hull_age_years": 2.9,
        "fouling_coeff": 1.04,
        "propeller_efficiency": 0.70,
        "fuel_type": "LNG",
        "daily_charter_rate_usd": 38000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-010",
        "name": "Arabian Dawn",
        "type": "Tanker",
        "subtype": "Suezmax (160k DWT)",
        "dwt": 158000,
        "gt": 84000,
        "length_m": 274.0,
        "beam_m": 48.0,
        "design_draft_m": 17.1,
        "engine_mcr_kw": 16800,
        "sfoc_g_kwh": 182.0,
        "hull_age_years": 5.1,
        "fouling_coeff": 1.11,
        "propeller_efficiency": 0.67,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 28000,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-11-15",
        "drydock_blackout_end": "2026-12-02",
    },
    {
        "id": "VESSEL-011",
        "name": "Gulf Voyager",
        "type": "Tanker",
        "subtype": "Aframax (115k DWT)",
        "dwt": 114000,
        "gt": 62000,
        "length_m": 249.0,
        "beam_m": 44.0,
        "design_draft_m": 15.0,
        "engine_mcr_kw": 13900,
        "sfoc_g_kwh": 185.0,
        "hull_age_years": 8.2,
        "fouling_coeff": 1.18,
        "propeller_efficiency": 0.63,
        "fuel_type": "HFO",
        "daily_charter_rate_usd": 23500,
        "eexi_compliant": False,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-012",
        "name": "Bering Sea",
        "type": "Tanker",
        "subtype": "MR2 Product Tanker",
        "dwt": 49990,
        "gt": 29800,
        "length_m": 183.0,
        "beam_m": 32.2,
        "design_draft_m": 11.0,
        "engine_mcr_kw": 7800,
        "sfoc_g_kwh": 179.0,
        "hull_age_years": 3.4,
        "fouling_coeff": 1.06,
        "propeller_efficiency": 0.69,
        "fuel_type": "MGO",
        "daily_charter_rate_usd": 17000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    # Liquefied Natural Gas (LNG) Carriers
    {
        "id": "VESSEL-013",
        "name": "Arctic Frost",
        "type": "LNG Carrier",
        "subtype": "Q-Flex (216k cbm)",
        "dwt": 108000,
        "gt": 135000,
        "length_m": 315.0,
        "beam_m": 50.0,
        "design_draft_m": 12.5,
        "engine_mcr_kw": 31000,
        "sfoc_g_kwh": 168.0,
        "hull_age_years": 2.5,
        "fouling_coeff": 1.03,
        "propeller_efficiency": 0.72,
        "fuel_type": "LNG",
        "daily_charter_rate_usd": 55000,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-014",
        "name": "Polar Crystal",
        "type": "LNG Carrier",
        "subtype": "Conventional (174k cbm)",
        "dwt": 87000,
        "gt": 112000,
        "length_m": 299.0,
        "beam_m": 46.4,
        "design_draft_m": 11.5,
        "engine_mcr_kw": 25500,
        "sfoc_g_kwh": 171.0,
        "hull_age_years": 4.8,
        "fouling_coeff": 1.09,
        "propeller_efficiency": 0.68,
        "fuel_type": "LNG",
        "daily_charter_rate_usd": 48000,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-12-10",
        "drydock_blackout_end": "2026-12-30",
    },
    # General Cargo / Multi-Purpose
    {
        "id": "VESSEL-015",
        "name": "Transglobe Star",
        "type": "General Cargo",
        "subtype": "Heavy Lift / MPP",
        "dwt": 32000,
        "gt": 22000,
        "length_m": 168.0,
        "beam_m": 26.0,
        "design_draft_m": 10.2,
        "engine_mcr_kw": 6800,
        "sfoc_g_kwh": 182.0,
        "hull_age_years": 3.7,
        "fouling_coeff": 1.07,
        "propeller_efficiency": 0.68,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 13500,
        "eexi_compliant": True,
        "drydock_blackout_start": None,
        "drydock_blackout_end": None,
    },
    {
        "id": "VESSEL-016",
        "name": "Ocean Odyssey",
        "type": "General Cargo",
        "subtype": "Handysize MPP",
        "dwt": 28000,
        "gt": 19500,
        "length_m": 160.0,
        "beam_m": 25.0,
        "design_draft_m": 9.8,
        "engine_mcr_kw": 6100,
        "sfoc_g_kwh": 188.0,
        "hull_age_years": 8.9,
        "fouling_coeff": 1.19,
        "propeller_efficiency": 0.63,
        "fuel_type": "VLSFO",
        "daily_charter_rate_usd": 11800,
        "eexi_compliant": True,
        "drydock_blackout_start": "2026-10-05",
        "drydock_blackout_end": "2026-10-22",
    },
]

# Trade Lane Route Template Definitions with Approximate Nautical Distances
TRADE_LANES = [
    # Far East - Europe (Container & Bulk)
    ("Shanghai", "Rotterdam", 10520, ["Container", "Bulk Carrier"]),
    ("Ningbo-Zhoushan", "Antwerp", 10600, ["Container"]),
    ("Singapore", "Rotterdam", 8290, ["Container", "Tanker"]),
    ("Yokohama", "Hamburg", 11200, ["Container"]),
    # Transpacific (Container & Bulk)
    ("Shanghai", "Houston", 9750, ["Container", "General Cargo"]),
    ("Busan", "Panama Canal", 8240, ["Container"]),
    # Middle East Crude to Asia & Europe
    ("Ras Tanura", "Ningbo-Zhoushan", 5950, ["Tanker"]),
    ("Ras Tanura", "Rotterdam", 6440, ["Tanker"]),
    ("Ras Tanura", "Yokohama", 6650, ["Tanker"]),
    ("Dubai (Jebel Ali)", "Singapore", 3380, ["Tanker", "General Cargo"]),
    # Australian Iron Ore to Asia
    ("Port Hedland", "Shanghai", 3540, ["Bulk Carrier"]),
    ("Port Hedland", "Busan", 3800, ["Bulk Carrier"]),
    ("Port Hedland", "Yokohama", 4020, ["Bulk Carrier"]),
    # South American Grain & Ore to Europe / Asia
    ("Santos", "Rotterdam", 5350, ["Bulk Carrier", "General Cargo"]),
    ("Santos", "Shanghai", 11300, ["Bulk Carrier"]),
    # US Gulf Energy to Europe & Asia
    ("Houston", "Rotterdam", 4880, ["Tanker", "LNG Carrier"]),
    ("Houston", "Yokohama", 9200, ["LNG Carrier", "Tanker"]),
    ("Houston", "Santos", 4720, ["Tanker", "General Cargo"]),
    # European Short-Sea & Feeder
    ("Rotterdam", "Algeciras", 1280, ["Container", "General Cargo"]),
    ("Antwerp", "Hamburg", 450, ["Container", "General Cargo"]),
]


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in nautical miles between coordinates."""
    r_nm = 3440.065
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_nm * c


def generate_fleet_and_voyages(
    num_voyages: int = 135,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Generates synthetic but physics-validated fleet dataset and voyage history.
    """
    random.seed(seed)
    fleet = [dict(v) for v in FLEET_TEMPLATES]

    # Initialize current fleet geographic positions and operational status
    ports_keys = list(GLOBAL_PORTS.keys())
    for idx, v in enumerate(fleet):
        port_assigned = ports_keys[idx % len(ports_keys)]
        port_meta = GLOBAL_PORTS[port_assigned]
        # Jitter slightly to simulate vessel anchoring near port
        v["current_location"] = {
            "lat": round(port_meta["lat"] + random.uniform(-0.4, 0.4), 3),
            "lon": round(port_meta["lon"] + random.uniform(-0.4, 0.4), 3),
            "nearest_port": port_assigned,
        }
        v["status"] = random.choice(["At Port", "In Transit", "Anchored", "Awaiting Cargo"])
        v["available_from_date"] = (
            datetime.now() + timedelta(days=random.randint(0, 10))
        ).strftime("%Y-%m-%d")

    voyages = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(num_voyages):
        voyage_id = f"VOY-2026-{1000 + i}"
        route = random.choice(TRADE_LANES)
        origin_port, dest_port, approx_dist, compatible_types = route

        # Pick random vessel matching route compatibility
        vessel = random.choice([v for v in fleet if v["type"] in compatible_types])

        # Laden vs Ballast
        is_laden = random.random() < 0.70
        condition = "Laden" if is_laden else "Ballast"
        cargo_weight = (
            round(vessel["dwt"] * random.uniform(0.75, 0.96)) if is_laden else 0.0
        )
        displacement = (
            vessel["gt"] * 1.1 + cargo_weight + random.uniform(1500, 4000)
        )

        draft = (
            vessel["design_draft_m"] * random.uniform(0.85, 0.98)
            if is_laden
            else vessel["design_draft_m"] * random.uniform(0.48, 0.62)
        )
        trim = round(random.uniform(-0.2, 1.2), 2)  # positive = stern trim

        # Speed profile: normal cruising speed (knots)
        stw_knots = round(random.uniform(11.5, 17.2), 1)

        # Realistic oceanic weather conditions
        wind_speed_knots = round(random.uniform(5.0, 32.0), 1)  # Calm to Beaufort 7
        wind_angle_deg = round(random.uniform(0.0, 180.0), 1)
        wave_height_m = round(
            max(0.6, 0.08 * (wind_speed_knots ** 1.15) + random.uniform(-0.4, 0.8)), 2
        )
        wave_direction_deg = round(random.uniform(0.0, 180.0), 1)
        current_knots = round(random.uniform(-1.5, 1.5), 1)

        # Distance with minor seasonal route variation
        distance_nm = round(approx_dist * random.uniform(0.97, 1.03))

        # Calculate baseline physics fuel consumption
        phys = calculate_physics_fuel_consumption(
            dwt=vessel["dwt"],
            displacement_mt=displacement,
            speed_knots=stw_knots,
            distance_nm=distance_nm,
            draft_m=draft,
            beam_m=vessel["beam_m"],
            length_m=vessel["length_m"],
            engine_mcr_kw=vessel["engine_mcr_kw"],
            hull_age_years=vessel["hull_age_years"],
            fouling_coeff=vessel["fouling_coeff"],
            propeller_efficiency=vessel["propeller_efficiency"],
            sfoc_g_kwh=vessel["sfoc_g_kwh"],
            wind_speed_knots=wind_speed_knots,
            wind_angle_deg=wind_angle_deg,
            wave_height_m=wave_height_m,
            wave_direction_deg=wave_direction_deg,
            current_knots=current_knots,
        )

        # Actual observed fuel with realistic empirical sensor noise (+/- 3.5%)
        empirical_noise = random.gauss(1.0, 0.032)
        actual_fuel_mt = round(phys["fuel_mt"] * empirical_noise, 2)

        # Schedule dates
        departure_dt = base_date + timedelta(days=int(i * 0.8) + random.randint(0, 3))
        hours_taken = phys["voyage_hours"]
        arrival_dt = departure_dt + timedelta(hours=hours_taken)

        origin_meta = GLOBAL_PORTS[origin_port]
        dest_meta = GLOBAL_PORTS[dest_port]

        # Calculate CII & Regulatory exposure
        cii_result = calculate_cii_rating(
            vessel_type=vessel["type"],
            dwt=vessel["dwt"],
            fuel_consumption_mt=actual_fuel_mt,
            distance_nm=distance_nm,
            fuel_type=vessel["fuel_type"],
            year=departure_dt.year,
        )

        reg_penalties = calculate_regulatory_penalties(
            co2_emissions_mt=cii_result["co2_emissions_mt"],
            is_eu_origin=origin_meta["is_eu"],
            is_eu_destination=dest_meta["is_eu"],
            eexi_compliant=vessel["eexi_compliant"],
            cii_rating=cii_result["rating"],
        )

        # Waypoints for leg-by-leg simulation (4 to 6 legs per voyage)
        num_legs = random.randint(4, 6)
        legs = []
        seg_dist = distance_nm / num_legs
        for leg_idx in range(num_legs):
            leg_wave = round(max(0.5, wave_height_m + random.uniform(-0.6, 0.6)), 2)
            leg_wind = round(max(4.0, wind_speed_knots + random.uniform(-5.0, 5.0)), 1)
            leg_speed = round(stw_knots + random.uniform(-0.4, 0.4), 1)
            leg_fuel = round((actual_fuel_mt / num_legs) * random.uniform(0.92, 1.08), 2)
            legs.append({
                "leg_index": leg_idx + 1,
                "distance_nm": round(seg_dist, 1),
                "speed_knots": leg_speed,
                "wave_height_m": leg_wave,
                "wind_speed_knots": leg_wind,
                "fuel_consumed_mt": leg_fuel,
            })

        voyages.append({
            "voyage_id": voyage_id,
            "vessel_id": vessel["id"],
            "vessel_name": vessel["name"],
            "vessel_type": vessel["type"],
            "vessel_dwt": vessel["dwt"],
            "origin_port": origin_port,
            "origin_lat": origin_meta["lat"],
            "origin_lon": origin_meta["lon"],
            "destination_port": dest_port,
            "dest_lat": dest_meta["lat"],
            "dest_lon": dest_meta["lon"],
            "distance_nm": distance_nm,
            "cargo_weight_mt": cargo_weight,
            "cargo_condition": condition,
            "draft_m": round(draft, 2),
            "trim_m": trim,
            "stw_knots": stw_knots,
            "sog_knots": phys["speed_over_ground_knots"],
            "wind_speed_knots": wind_speed_knots,
            "wind_angle_deg": wind_angle_deg,
            "wave_height_m": wave_height_m,
            "wave_direction_deg": wave_direction_deg,
            "current_knots": current_knots,
            "hull_age_years": vessel["hull_age_years"],
            "fouling_coeff": vessel["fouling_coeff"],
            "propeller_efficiency": vessel["propeller_efficiency"],
            "fuel_type": vessel["fuel_type"],
            "physics_predicted_fuel_mt": phys["fuel_mt"],
            "actual_fuel_consumed_mt": actual_fuel_mt,
            "co2_emissions_mt": cii_result["co2_emissions_mt"],
            "departure_time": departure_dt.strftime("%Y-%m-%d %H:%M"),
            "arrival_time": arrival_dt.strftime("%Y-%m-%d %H:%M"),
            "duration_hours": round(hours_taken, 1),
            "cii_rating": cii_result["rating"],
            "attained_cii": cii_result["attained_cii"],
            "required_cii": cii_result["required_cii"],
            "eu_ets_cost_inr": reg_penalties["eu_ets_cost_inr"],
            "eu_ets_cost_usd": reg_penalties["eu_ets_cost_inr"],  # for compat
            "is_eu_trade": origin_meta["is_eu"] or dest_meta["is_eu"],
            "legs": legs,
        })

    return {
        "fleet": fleet,
        "voyages": voyages,
        "ports": GLOBAL_PORTS,
    }


def save_synthetic_data(output_path: str = None) -> str:
    """Generates and writes synthetic dataset to JSON file."""
    if output_path is None:
        output_path = str(Path(__file__).parent / "synthetic_data.json")

    data = generate_fleet_and_voyages(num_voyages=135, seed=42)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output_path


if __name__ == "__main__":
    out = save_synthetic_data()
    print(f"Successfully generated synthetic dataset at: {out}")
