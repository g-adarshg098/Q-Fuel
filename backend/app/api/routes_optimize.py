"""
Quantum and Classical Fleet Optimization API Endpoints.
Supports swappable solvers: Quantum Annealer, QAOA Circuit, Classical ILP, and Greedy Baseline.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.optimization.qubo_builder import FleetQUBOBuilder
from app.optimization.solvers.simulated_annealing import QuantumAnnealingFleetSolver
from app.optimization.solvers.qaoa_solver import QAOAFleetSolver
from app.optimization.solvers.classical_ilp import ClassicalILPFleetSolver
from app.optimization.solvers.greedy_solver import GreedyFleetSolver
from app.optimization.route_optimizer import WeatherRouteSpeedOptimizer

router = APIRouter(prefix="/api", tags=["Optimization Engine"])

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_data.json"


def _load_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class OptimizeRequest(BaseModel):
    solver_backend: str = Field(
        "quantum_annealing",
        description="Options: 'quantum_annealing', 'qaoa', 'classical_ilp', 'greedy_baseline'",
    )
    voyage_count: int = Field(6, ge=2, le=15, description="Number of voyages to optimize")
    num_reads: int = Field(100, description="Number of quantum annealer reads/samples")
    num_sweeps: int = Field(1200, description="Number of annealing Monte Carlo sweeps")


class RouteOptimizeRequest(BaseModel):
    voyage_id: Optional[str] = None
    vessel_id: Optional[str] = None
    max_eta_hours: Optional[float] = None
    legs: Optional[List[Dict[str, Any]]] = None


@router.post("/optimize")
async def run_fleet_optimization(payload: OptimizeRequest):
    """
    Executes fleet-to-voyage assignment using the configured solver backend.
    """
    data = _load_data()
    fleet = data.get("fleet", [])
    all_voyages = data.get("voyages", [])
    voyages = all_voyages[: payload.voyage_count]

    # Build QUBO representation
    builder = FleetQUBOBuilder()
    qubo_data = builder.build_qubo(fleet, voyages)

    backend = payload.solver_backend.lower()

    # Always compute Greedy baseline for comparison
    greedy_solver = GreedyFleetSolver()
    greedy_result = greedy_solver.solve(qubo_data, fleet, voyages)

    if backend in ["quantum_annealing", "dwave", "annealer"]:
        solver = QuantumAnnealingFleetSolver(
            num_reads=payload.num_reads, num_sweeps=payload.num_sweeps
        )
        result = solver.solve(qubo_data)
    elif backend in ["qaoa", "quantum_circuit"]:
        solver = QAOAFleetSolver(p_layers=2, max_qubits=12)
        result = solver.solve(qubo_data)
    elif backend in ["classical_ilp", "ilp", "highs", "pulp"]:
        solver = ClassicalILPFleetSolver()
        result = solver.solve(qubo_data, fleet, voyages)
    elif backend in ["greedy_baseline", "greedy", "baseline"]:
        result = greedy_result
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown solver backend '{payload.solver_backend}'. Must be one of: quantum_annealing, qaoa, classical_ilp, greedy_baseline",
        )

    # Compute savings vs baseline
    fuel_saved_mt = max(0.0, greedy_result["total_fuel_consumed_mt"] - result["total_fuel_consumed_mt"])
    cost_saved_inr = max(0.0, greedy_result["total_operational_cost_inr"] - result["total_operational_cost_inr"])
    co2_saved_mt = max(0.0, greedy_result["total_co2_emissions_mt"] - result["total_co2_emissions_mt"])
    pct_savings = round(
        (cost_saved_inr / max(1.0, greedy_result["total_operational_cost_inr"])) * 100.0, 2
    )

    return {
        "status": "success",
        "solver_backend": payload.solver_backend,
        "active_result": result,
        "baseline_greedy_result": greedy_result,
        "savings": {
            "fuel_saved_mt": round(fuel_saved_mt, 2),
            "cost_saved_inr": round(cost_saved_inr, 2),
            "co2_saved_mt": round(co2_saved_mt, 2),
            "cost_savings_pct": pct_savings,
        },
    }


@router.get("/benchmark")
async def run_solver_benchmark(voyage_count: int = 6):
    """
    Executes all 4 solver backends side-by-side to benchmark quantum vs classical
    speed, solution quality, energy, and cost savings.
    """
    data = _load_data()
    fleet = data.get("fleet", [])
    voyages = data.get("voyages", [])[:voyage_count]

    builder = FleetQUBOBuilder()
    qubo_data = builder.build_qubo(fleet, voyages)

    # 1. Greedy Baseline
    greedy_solver = GreedyFleetSolver()
    greedy_res = greedy_solver.solve(qubo_data, fleet, voyages)

    # 2. Classical ILP (HiGHS)
    ilp_solver = ClassicalILPFleetSolver()
    ilp_res = ilp_solver.solve(qubo_data, fleet, voyages)

    # 3. Quantum-Inspired Annealer (D-Wave dimod)
    sa_solver = QuantumAnnealingFleetSolver(num_reads=80, num_sweeps=1000)
    sa_res = sa_solver.solve(qubo_data)

    # 4. QAOA Circuit Emulator
    qaoa_solver = QAOAFleetSolver(p_layers=2, max_qubits=10)
    qaoa_res = qaoa_solver.solve(qubo_data)

    baseline_cost = greedy_res["total_operational_cost_inr"]

    def compute_metric(res):
        saved = max(0.0, baseline_cost - res["total_operational_cost_inr"])
        return {
            "solver_name": res["solver_name"],
            "execution_time_ms": res["execution_time_ms"],
            "total_fuel_mt": res["total_fuel_consumed_mt"],
            "total_fuel_cost_inr": res["total_fuel_cost_inr"],
            "total_co2_mt": res["total_co2_emissions_mt"],
            "total_operational_cost_inr": res["total_operational_cost_inr"],
            "savings_vs_greedy_inr": round(saved, 2),
            "savings_pct": round((saved / max(1.0, baseline_cost)) * 100.0, 2),
            "is_valid": res.get("is_valid", True),
        }

    return {
        "problem_dimensions": {
            "num_vessels": len(fleet),
            "num_voyages": len(voyages),
            "qubo_binary_variables": qubo_data["num_variables"],
        },
        "benchmark_comparison": [
            compute_metric(greedy_res),
            compute_metric(ilp_res),
            compute_metric(sa_res),
            compute_metric(qaoa_res),
        ],
    }


@router.post("/route-optimize")
async def optimize_weather_route(payload: RouteOptimizeRequest):
    """
    Optimizes speed curve along waypoints to minimize heavy-weather fuel burn under ETA constraint.
    """
    data = _load_data()
    voyage = None
    vessel = None

    if payload.voyage_id:
        voyage = next((v for v in data.get("voyages", []) if v["voyage_id"] == payload.voyage_id), None)
    if not voyage:
        voyage = data.get("voyages", [])[0]

    vessel_id = payload.vessel_id or voyage.get("vessel_id")
    vessel = next((v for v in data.get("fleet", []) if v["id"] == vessel_id), data.get("fleet", [])[0])

    legs = payload.legs or voyage.get("legs", [])
    max_eta = payload.max_eta_hours or (voyage.get("duration_hours", 200.0) * 1.05)

    optimizer = WeatherRouteSpeedOptimizer()
    result = optimizer.optimize_speed_profile(
        legs=legs,
        vessel=vessel,
        max_eta_hours=max_eta,
    )

    return {
        "voyage_id": voyage["voyage_id"],
        "vessel_name": vessel["name"],
        "origin_port": voyage["origin_port"],
        "destination_port": voyage["destination_port"],
        "optimization": result,
    }
