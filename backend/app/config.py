"""
Configuration and Maritime Domain Constants.
Includes IMO Emission Factors, CII Reference Parameters (MEPC.337(76)),
and Fuel & Carbon pricing constants denominated in Indian Rupees (INR / ₹).
"""

from typing import Dict, Any

# Currency Conversion Factor (USD to Indian Rupees)
USD_TO_INR: float = 84.0

# IMO Resolution MEPC.308(73) Carbon Conversion Factors (t-CO2 / t-fuel)
CF_FACTORS: Dict[str, float] = {
    "HFO": 3.114,       # Heavy Fuel Oil
    "VLSFO": 3.151,     # Very Low Sulphur Fuel Oil (0.50% S)
    "MGO": 3.206,       # Marine Gas Oil
    "LNG": 2.750,       # Liquefied Natural Gas
    "Methanol": 1.375,  # Green/Bio-Methanol (Net fossil equivalent 1.375)
}

# Average Global Bunker Fuel Prices denominated in Indian Rupees (₹ / Metric Ton)
# (Calculated from international benchmarks converted at USD/INR = 84.0)
FUEL_PRICES_INR_PER_MT: Dict[str, float] = {
    "HFO": round(510.0 * USD_TO_INR, 2),        # ~₹42,840 / MT
    "VLSFO": round(620.0 * USD_TO_INR, 2),      # ~₹52,080 / MT
    "MGO": round(830.0 * USD_TO_INR, 2),        # ~₹69,720 / MT
    "LNG": round(690.0 * USD_TO_INR, 2),        # ~₹57,960 / MT
    "Methanol": round(780.0 * USD_TO_INR, 2),   # ~₹65,520 / MT
}

# Carbon Tax & Regulatory Penalties in Indian Rupees (₹ / Metric Ton CO2)
EU_ETS_CARBON_PRICE_EUR_PER_TON = 85.0
EUR_TO_USD_EXCHANGE_RATE = 1.08
EU_ETS_CARBON_PRICE_INR_PER_TON = round(
    EU_ETS_CARBON_PRICE_EUR_PER_TON * EUR_TO_USD_EXCHANGE_RATE * USD_TO_INR, 2
)  # ~₹7,711 / MT CO2

# Backward compatibility alias
FUEL_PRICES_USD_PER_MT = FUEL_PRICES_INR_PER_MT

# IMO Carbon Intensity Indicator (CII) Reference Parameters
# Formula: CII_ref = a * Capacity^(-c) [g CO2 / (dwt * nautical mile)]
CII_REF_PARAMS: Dict[str, Dict[str, float]] = {
    "Bulk Carrier": {"a": 4745.0, "c": 0.322},
    "Tanker": {"a": 5247.0, "c": 0.345},
    "Container": {"a": 1984.0, "c": 0.489},
    "LNG Carrier": {"a": 9827.0, "c": 0.000},
    "General Cargo": {"a": 31948.0, "c": 0.792},
}

# CII Rating Boundaries (d1, d2, d3, d4 multipliers around benchmark)
CII_EXP_VECTORS: Dict[str, Dict[str, float]] = {
    "Bulk Carrier": {"d1": 0.86, "d2": 0.94, "d3": 1.06, "d4": 1.18},
    "Tanker": {"d1": 0.82, "d2": 0.93, "d3": 1.08, "d4": 1.25},
    "Container": {"d1": 0.83, "d2": 0.95, "d3": 1.07, "d4": 1.19},
    "LNG Carrier": {"d1": 0.85, "d2": 0.95, "d3": 1.06, "d4": 1.21},
    "General Cargo": {"d1": 0.84, "d2": 0.94, "d3": 1.06, "d4": 1.20},
}
