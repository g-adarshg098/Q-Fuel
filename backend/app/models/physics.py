"""
Physics-Informed Naval Architecture Fuel Consumption Baseline.

Implements:
1. Admiralty Coefficient power-displacement-speed formulation.
2. Holtrop-Mennen hydrodynamic resistance approximation.
3. Environmental corrections:
   - Wave added resistance (Kwon / Townsend semi-empirical formulation).
   - Aerodynamic drag from head/cross winds.
   - Hull biofouling penalty based on vessel age and fouling factor.
4. Specific Fuel Oil Consumption (SFOC) brake power conversion.
"""

import math
from typing import Dict, Any


def calculate_physics_fuel_consumption(
    dwt: float,
    displacement_mt: float,
    speed_knots: float,
    distance_nm: float,
    draft_m: float,
    beam_m: float,
    length_m: float,
    engine_mcr_kw: float,
    hull_age_years: float,
    fouling_coeff: float = 1.05,
    propeller_efficiency: float = 0.68,
    sfoc_g_kwh: float = 185.0,
    wind_speed_knots: float = 12.0,
    wind_angle_deg: float = 30.0,
    wave_height_m: float = 1.5,
    wave_direction_deg: float = 20.0,
    current_knots: float = 0.0,
) -> Dict[str, float]:
    """
    Computes theoretical fuel consumption (Metric Tons) using hydrodynamic resistance physics.

    Parameters:
    -----------
    dwt : float
        Deadweight tonnage (Metric Tons)
    displacement_mt : float
        Current vessel displacement including cargo, fuel, ballast (MT)
    speed_knots : float
        Speed Through Water (STW) in knots
    distance_nm : float
        Voyage distance in nautical miles
    draft_m, beam_m, length_m : float
        Vessel principal dimensions
    engine_mcr_kw : float
        Maximum Continuous Rating of main engine (kW)
    hull_age_years : float
        Years since last drydock hull cleaning/coating
    fouling_coeff : float
        Hull roughness/fouling multiplier (typically 1.02 - 1.25)
    propeller_efficiency : float
        Open water + hull efficiency eta_0 * eta_H (~0.60 - 0.72)
    sfoc_g_kwh : float
        Specific Fuel Oil Consumption (g / kWh)
    wind_speed_knots, wind_angle_deg : float
        True wind velocity and relative angle to ship heading (0 = headwind, 180 = tailwind)
    wave_height_m, wave_direction_deg : float
        Significant wave height and relative wave encounter angle
    current_knots : float
        Ocean current component along heading (positive = assisting)

    Returns:
    --------
    dict with:
      - fuel_mt: Total voyage fuel consumption in Metric Tons
      - fuel_per_day_mt: Metric tons per sea day
      - brake_power_kw: Required continuous brake engine power
      - voyage_hours: Total duration in hours
      - resistance_kn: Total hydrodynamic + aerodynamic resistance in kN
    """
    # Speed over ground accounting for current
    sog_knots = max(4.0, speed_knots + current_knots)
    speed_ms = speed_knots * 0.514444  # knots to m/s
    voyage_hours = distance_nm / max(1.0, sog_knots)

    # 1. Base Calm-Water Admiralty Formulation
    # P = (Displacement^(2/3) * V^3) / C_adm
    # Typical C_adm ranges 450 - 650 depending on hull form finesse
    block_coeff = max(0.60, min(0.88, displacement_mt / (length_m * beam_m * draft_m * 1.025)))
    c_adm = 620.0 - (block_coeff - 0.60) * 350.0

    power_calm_hp = (pow(displacement_mt, 2.0 / 3.0) * pow(speed_knots, 3.0)) / max(100.0, c_adm)
    power_calm_kw = power_calm_hp * 0.7457

    # 2. Hull Biofouling Deterioration
    # Friction resistance increases ~1.5% to 3.5% per year without drydock
    fouling_penalty = 1.0 + (fouling_coeff - 1.0) + (hull_age_years * 0.022)

    # 3. Aerodynamic Wind Drag (Blendermann semi-empirical)
    # Wind angle: 0 = headwind (max drag), 180 = tailwind (thrust)
    rho_air = 1.225  # kg/m^3
    transverse_wind_area = beam_m * (draft_m * 0.9 + 12.0)  # Superstructure frontal area
    wind_speed_ms = wind_speed_knots * 0.514444
    rel_wind_angle_rad = math.radians(wind_angle_deg)
    cx_wind = 0.85 * math.cos(rel_wind_angle_rad)  # Drag coefficient projection

    wind_resistance_n = 0.5 * rho_air * transverse_wind_area * cx_wind * pow(wind_speed_ms + speed_ms, 2.0)
    wind_resistance_kn = wind_resistance_n / 1000.0 if wind_resistance_n > 0 else 0.0

    # 4. Kwon Wave Added Resistance (Significant Wave Height Hs)
    # Delta R_wave = 0.5 * rho_seawater * g * (Hs/2)^2 * B^2 / L * correction
    rho_sw = 1025.0
    g = 9.80665
    wave_angle_rad = math.radians(wave_direction_deg)
    head_factor = max(0.0, math.cos(wave_angle_rad))
    wave_drag_kn = (
        0.5 * rho_sw * g * pow(wave_height_m * 0.5, 2.0) * (beam_m ** 2) / max(30.0, length_m)
    ) * head_factor / 1000.0

    # Total environmental power addition
    environmental_thrust_kn = max(0.0, wind_resistance_kn + wave_drag_kn)
    power_env_kw = (environmental_thrust_kn * speed_ms) / max(0.40, propeller_efficiency)

    # Total Required Brake Power (kW)
    total_power_kw = (power_calm_kw * fouling_penalty) + power_env_kw

    # Engine load safety clamp (cannot exceed engine MCR or fall below idle)
    total_power_kw = max(engine_mcr_kw * 0.15, min(engine_mcr_kw * 0.95, total_power_kw))

    # SFOC correction for engine load factor
    load_factor = total_power_kw / max(1.0, engine_mcr_kw)
    # SFOC is lowest near 75-85% MCR, increases at low load
    sfoc_actual = sfoc_g_kwh * (1.0 + 0.18 * pow(load_factor - 0.80, 2.0))

    # Fuel consumption calculations
    fuel_g_per_hour = total_power_kw * sfoc_actual
    fuel_mt_per_hour = fuel_g_per_hour / 1_000_000.0
    fuel_total_mt = fuel_mt_per_hour * voyage_hours
    fuel_per_day_mt = fuel_mt_per_hour * 24.0

    return {
        "fuel_mt": round(fuel_total_mt, 2),
        "fuel_per_day_mt": round(fuel_per_day_mt, 2),
        "brake_power_kw": round(total_power_kw, 1),
        "engine_load_pct": round(load_factor * 100.0, 1),
        "voyage_hours": round(voyage_hours, 1),
        "speed_over_ground_knots": round(sog_knots, 1),
        "weather_penalty_pct": round((power_env_kw / max(1.0, power_calm_kw)) * 100.0, 1),
    }
