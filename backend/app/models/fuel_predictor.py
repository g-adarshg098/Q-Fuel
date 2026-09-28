"""
Machine Learning Fuel Consumption Prediction Engine.
Combines naval physics priors with Gradient Boosted Trees (XGBoost)
to achieve high-accuracy voyage and leg-by-leg fuel burn prediction.

Success Criteria:
- Holdout test MAPE < 8.0%
- Quantified confidence bounds (90% prediction interval)
- Feature importance attribution
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

from app.config import CF_FACTORS
from app.models.physics import calculate_physics_fuel_consumption
from app.models.cii_calculator import calculate_cii_rating


FEATURE_NAMES = [
    "vessel_dwt",
    "distance_nm",
    "cargo_weight_mt",
    "draft_m",
    "trim_m",
    "stw_knots",
    "sog_knots",
    "wind_speed_knots",
    "wind_angle_deg",
    "wave_height_m",
    "wave_direction_deg",
    "current_knots",
    "hull_age_years",
    "fouling_coeff",
    "propeller_efficiency",
    "physics_predicted_fuel_mt",
]


class FuelPredictionEngine:
    def __init__(self, data_path: Optional[str] = None):
        self.model: Optional[xgb.XGBRegressor] = None
        self.metrics: Dict[str, float] = {}
        self.feature_importance: Dict[str, float] = {}
        self.residual_std: float = 8.5  # Standard deviation of residuals for confidence bounds
        self.data_path = (
            Path(data_path)
            if data_path
            else Path(__file__).resolve().parent.parent / "data" / "synthetic_data.json"
        )
        self._load_and_train()

    def _load_and_train(self) -> None:
        """Loads voyage data, extracts features, trains XGBoost, and validates holdout set."""
        if not self.data_path.exists():
            from app.data.generator import save_synthetic_data
            save_synthetic_data(str(self.data_path))

        with open(self.data_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        voyages = raw.get("voyages", [])
        if not voyages:
            raise ValueError("No voyage records found in dataset.")

        df = pd.DataFrame(voyages)

        # Prepare X and y
        X = df[FEATURE_NAMES].copy()
        y = df["actual_fuel_consumed_mt"].values

        # 80/20 train/holdout split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )

        # Train XGBoost Regressor with log-scale target for optimal percentage error
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.04,
            subsample=0.90,
            colsample_bytree=0.90,
            random_state=42,
            n_jobs=-1,
        )
        # Fitting on log(y) naturally minimizes Mean Absolute Percentage Error (MAPE)
        self.model.fit(X_train, np.log(y_train))

        # Evaluate on holdout test set
        log_preds = self.model.predict(X_test)
        y_pred = np.exp(log_preds)
        mape = float(mean_absolute_percentage_error(y_test, y_pred) * 100.0)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        residuals = y_test - y_pred
        self.residual_std = float(np.std(residuals))

        self.metrics = {
            "mape_pct": round(mape, 2),
            "rmse_mt": round(rmse, 2),
            "mae_mt": round(mae, 2),
            "r2_score": round(r2, 4),
            "sample_size_train": int(len(X_train)),
            "sample_size_test": int(len(X_test)),
            "residual_std": round(self.residual_std, 2),
        }

        # Feature Importance
        importances = self.model.feature_importances_
        sorted_idx = np.argsort(importances)[::-1]
        self.feature_importance = {
            FEATURE_NAMES[i]: round(float(importances[i]) * 100.0, 2)
            for i in sorted_idx
        }

    def predict_voyage_fuel(
        self,
        vessel_dwt: float,
        distance_nm: float,
        cargo_weight_mt: float,
        draft_m: float,
        trim_m: float,
        stw_knots: float,
        sog_knots: float,
        wind_speed_knots: float,
        wind_angle_deg: float,
        wave_height_m: float,
        wave_direction_deg: float,
        current_knots: float,
        hull_age_years: float,
        fouling_coeff: float,
        propeller_efficiency: float,
        fuel_type: str = "VLSFO",
        beam_m: float = 32.2,
        length_m: float = 200.0,
        engine_mcr_kw: float = 12000.0,
        sfoc_g_kwh: float = 180.0,
        vessel_type: str = "Bulk Carrier",
    ) -> Dict[str, Any]:
        """
        Predicts total voyage fuel consumption with 90% confidence interval,
        CO2e emissions, and IMO CII rating.
        """
        # 1. Physics baseline
        displacement = (vessel_dwt * 0.2) + cargo_weight_mt + 2500.0
        phys = calculate_physics_fuel_consumption(
            dwt=vessel_dwt,
            displacement_mt=displacement,
            speed_knots=stw_knots,
            distance_nm=distance_nm,
            draft_m=draft_m,
            beam_m=beam_m,
            length_m=length_m,
            engine_mcr_kw=engine_mcr_kw,
            hull_age_years=hull_age_years,
            fouling_coeff=fouling_coeff,
            propeller_efficiency=propeller_efficiency,
            sfoc_g_kwh=sfoc_g_kwh,
            wind_speed_knots=wind_speed_knots,
            wind_angle_deg=wind_angle_deg,
            wave_height_m=wave_height_m,
            wave_direction_deg=wave_direction_deg,
            current_knots=current_knots,
        )
        physics_fuel_mt = phys["fuel_mt"]

        # 2. Tabular ML inference
        row = np.array([[
            vessel_dwt,
            distance_nm,
            cargo_weight_mt,
            draft_m,
            trim_m,
            stw_knots,
            sog_knots,
            wind_speed_knots,
            wind_angle_deg,
            wave_height_m,
            wave_direction_deg,
            current_knots,
            hull_age_years,
            fouling_coeff,
            propeller_efficiency,
            physics_fuel_mt,
        ]])

        log_pred = float(self.model.predict(row)[0])
        pred_fuel_mt = float(np.exp(log_pred))
        # Safe bound check
        pred_fuel_mt = max(0.5, pred_fuel_mt)

        # 3. 90% Confidence Interval (z = 1.645)
        margin = 1.645 * self.residual_std
        ci_lower = max(0.1, pred_fuel_mt - margin)
        ci_upper = pred_fuel_mt + margin

        # 4. CO2e and CII Rating
        cf = CF_FACTORS.get(fuel_type, 3.151)
        co2_emissions_mt = pred_fuel_mt * cf
        cii_result = calculate_cii_rating(
            vessel_type=vessel_type,
            dwt=vessel_dwt,
            fuel_consumption_mt=pred_fuel_mt,
            distance_nm=distance_nm,
            fuel_type=fuel_type,
        )

        return {
            "predicted_fuel_mt": round(pred_fuel_mt, 2),
            "physics_baseline_fuel_mt": round(physics_fuel_mt, 2),
            "ci_lower_mt": round(ci_lower, 2),
            "ci_upper_mt": round(ci_upper, 2),
            "confidence_level_pct": 90,
            "co2_emissions_mt": round(co2_emissions_mt, 2),
            "fuel_type": fuel_type,
            "carbon_factor_cf": cf,
            "cii_rating": cii_result["rating"],
            "attained_cii": cii_result["attained_cii"],
            "required_cii": cii_result["required_cii"],
            "rating_description": cii_result["rating_description"],
            "status_color": cii_result["status_color"],
            "voyage_duration_hours": phys["voyage_hours"],
            "weather_penalty_pct": phys["weather_penalty_pct"],
        }

    def predict_leg_by_leg(
        self,
        legs: List[Dict[str, Any]],
        vessel_dwt: float,
        draft_m: float,
        trim_m: float,
        hull_age_years: float,
        fouling_coeff: float,
        propeller_efficiency: float,
        fuel_type: str = "VLSFO",
    ) -> List[Dict[str, Any]]:
        """
        Time-series leg-by-leg fuel burn simulation along a multi-waypoint voyage track.
        """
        results = []
        cumulative_fuel = 0.0
        cf = CF_FACTORS.get(fuel_type, 3.151)

        for leg in legs:
            dist = leg.get("distance_nm", 500.0)
            stw = leg.get("speed_knots", 14.0)
            wave = leg.get("wave_height_m", 1.5)
            wind = leg.get("wind_speed_knots", 12.0)
            current = leg.get("current_knots", 0.0)
            sog = max(4.0, stw + current)

            # Leg physics
            disp = vessel_dwt * 0.85
            phys = calculate_physics_fuel_consumption(
                dwt=vessel_dwt,
                displacement_mt=disp,
                speed_knots=stw,
                distance_nm=dist,
                draft_m=draft_m,
                beam_m=32.0,
                length_m=200.0,
                engine_mcr_kw=12000.0,
                hull_age_years=hull_age_years,
                fouling_coeff=fouling_coeff,
                propeller_efficiency=propeller_efficiency,
                wind_speed_knots=wind,
                wave_height_m=wave,
                current_knots=current,
            )
            leg_fuel = phys["fuel_mt"]
            cumulative_fuel += leg_fuel

            results.append({
                "leg_index": leg.get("leg_index", len(results) + 1),
                "distance_nm": dist,
                "speed_knots": stw,
                "wave_height_m": wave,
                "wind_speed_knots": wind,
                "leg_fuel_mt": round(leg_fuel, 2),
                "cumulative_fuel_mt": round(cumulative_fuel, 2),
                "leg_co2_mt": round(leg_fuel * cf, 2),
                "duration_hours": round(dist / sog, 1),
            })

        return results


# Global singleton predictor instance
_predictor_instance: Optional[FuelPredictionEngine] = None


def get_prediction_engine() -> FuelPredictionEngine:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = FuelPredictionEngine()
    return _predictor_instance


if __name__ == "__main__":
    engine = get_prediction_engine()
    print("--- Fuel Prediction Model Metrics ---")
    print(json.dumps(engine.metrics, indent=2))
    print("\n--- Top Feature Importances ---")
    for feat, imp in list(engine.feature_importance.items())[:6]:
        print(f"  {feat}: {imp}%")
