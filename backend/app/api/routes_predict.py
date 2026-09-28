"""
Fuel Consumption Prediction and ML Model Metrics API Endpoints.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.models.fuel_predictor import get_prediction_engine

router = APIRouter(prefix="/api", tags=["Prediction Engine"])


class PredictionRequest(BaseModel):
    vessel_dwt: float = Field(82000.0, description="Deadweight Tonnage (MT)")
    distance_nm: float = Field(5000.0, description="Voyage distance in nautical miles")
    cargo_weight_mt: float = Field(65000.0, description="Cargo payload in MT")
    draft_m: float = Field(13.5, description="Operating draft (m)")
    trim_m: float = Field(0.5, description="Stern trim (m)")
    stw_knots: float = Field(14.0, description="Speed Through Water (knots)")
    sog_knots: float = Field(14.0, description="Speed Over Ground (knots)")
    wind_speed_knots: float = Field(14.0, description="Wind speed (knots)")
    wind_angle_deg: float = Field(30.0, description="Relative wind angle (deg, 0=headwind)")
    wave_height_m: float = Field(1.8, description="Significant wave height Hs (m)")
    wave_direction_deg: float = Field(25.0, description="Relative wave direction (deg)")
    current_knots: float = Field(0.0, description="Current speed along ship heading (knots)")
    hull_age_years: float = Field(3.0, description="Years since last drydock cleaning")
    fouling_coeff: float = Field(1.05, description="Hull fouling multiplier")
    propeller_efficiency: float = Field(0.68, description="Propeller open-water efficiency")
    fuel_type: str = Field("VLSFO", description="Fuel type: HFO, VLSFO, MGO, LNG, Methanol")
    vessel_type: str = Field("Bulk Carrier", description="Vessel category for IMO CII reference")
    engine_mcr_kw: Optional[float] = Field(12000.0, description="Engine MCR in kW")
    sfoc_g_kwh: Optional[float] = Field(180.0, description="Specific fuel consumption (g/kWh)")


class LegPredictionRequest(BaseModel):
    vessel_dwt: float = 82000.0
    draft_m: float = 13.5
    trim_m: float = 0.5
    hull_age_years: float = 3.0
    fouling_coeff: float = 1.05
    propeller_efficiency: float = 0.68
    fuel_type: str = "VLSFO"
    legs: List[Dict[str, Any]] = []


@router.post("/predict")
async def predict_voyage_fuel(payload: PredictionRequest):
    """
    Predicts voyage fuel consumption, 90% confidence bands, CO2e emissions,
    and IMO Operational CII rating.
    """
    engine = get_prediction_engine()
    result = engine.predict_voyage_fuel(
        vessel_dwt=payload.vessel_dwt,
        distance_nm=payload.distance_nm,
        cargo_weight_mt=payload.cargo_weight_mt,
        draft_m=payload.draft_m,
        trim_m=payload.trim_m,
        stw_knots=payload.stw_knots,
        sog_knots=payload.sog_knots,
        wind_speed_knots=payload.wind_speed_knots,
        wind_angle_deg=payload.wind_angle_deg,
        wave_height_m=payload.wave_height_m,
        wave_direction_deg=payload.wave_direction_deg,
        current_knots=payload.current_knots,
        hull_age_years=payload.hull_age_years,
        fouling_coeff=payload.fouling_coeff,
        propeller_efficiency=payload.propeller_efficiency,
        fuel_type=payload.fuel_type,
        vessel_type=payload.vessel_type,
        engine_mcr_kw=payload.engine_mcr_kw or 12000.0,
        sfoc_g_kwh=payload.sfoc_g_kwh or 180.0,
    )
    return result


@router.post("/predict/legs")
async def predict_legs_timeseries(payload: LegPredictionRequest):
    """
    Simulates leg-by-leg time-series fuel burn along waypoint track.
    """
    engine = get_prediction_engine()
    results = engine.predict_leg_by_leg(
        legs=payload.legs,
        vessel_dwt=payload.vessel_dwt,
        draft_m=payload.draft_m,
        trim_m=payload.trim_m,
        hull_age_years=payload.hull_age_years,
        fouling_coeff=payload.fouling_coeff,
        propeller_efficiency=payload.propeller_efficiency,
        fuel_type=payload.fuel_type,
    )
    return {
        "total_legs": len(results),
        "legs": results,
    }


@router.get("/model/metrics")
async def get_model_metrics():
    """
    Returns holdout validation metrics (MAPE, RMSE, MAE, R2) and SHAP/tree feature importances.
    """
    engine = get_prediction_engine()
    return {
        "model_name": "Physics-Informed XGBoost Regressor",
        "evaluation_metrics": engine.metrics,
        "feature_importance": engine.feature_importance,
        "success_criteria_target": "MAPE < 8.0%",
        "criteria_achieved": engine.metrics.get("mape_pct", 100.0) < 8.0,
    }
