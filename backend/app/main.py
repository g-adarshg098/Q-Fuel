"""
FastAPI Backend Application Entrypoint.
Quantum-Inspired Fuel Consumption Prediction and Green Fleet Optimization Platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_fleet import router as fleet_router
from app.api.routes_predict import router as predict_router
from app.api.routes_optimize import router as optimize_router
from app.api.routes_scenario import router as scenario_router
from app.api.routes_compliance import router as compliance_router

app = FastAPI(
    title="Quantum Green Fleet Maritime Optimization API",
    description=(
        "Full-Stack Maritime Intelligence Platform providing physics-informed machine learning "
        "fuel consumption prediction (XGBoost) and quantum-inspired QUBO fleet assignment optimization "
        "(Simulated Annealing, QAOA circuit emulation, and Classical HiGHS ILP)."
    ),
    version="1.0.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(fleet_router)
app.include_router(predict_router)
app.include_router(optimize_router)
app.include_router(scenario_router)
app.include_router(compliance_router)


@app.get("/")
async def root():
    return {
        "platform": "Quantum Green Fleet Maritime Optimization API",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": [
            "/api/fleet",
            "/api/voyages",
            "/api/ports",
            "/api/predict",
            "/api/predict/legs",
            "/api/model/metrics",
            "/api/optimize",
            "/api/benchmark",
            "/api/route-optimize",
            "/api/scenario",
            "/api/compliance",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
