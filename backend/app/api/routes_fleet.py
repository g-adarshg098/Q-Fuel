"""
Fleet, Voyages, and Ports Information API Endpoints.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api", tags=["Fleet & Voyages"])

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_data.json"


def _load_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        from app.data.generator import save_synthetic_data
        save_synthetic_data(str(DATA_PATH))
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/fleet")
async def get_fleet(vessel_type: Optional[str] = None):
    """Returns the list of all fleet vessels with current positions and specifications."""
    data = _load_data()
    fleet = data.get("fleet", [])
    if vessel_type:
        fleet = [v for v in fleet if v["type"].lower() == vessel_type.lower()]
    return {
        "total_vessels": len(fleet),
        "fleet": fleet,
    }


@router.get("/fleet/{vessel_id}")
async def get_vessel_details(vessel_id: str):
    """Returns detailed specifications and performance data for a single vessel."""
    data = _load_data()
    vessel = next((v for v in data.get("fleet", []) if v["id"] == vessel_id), None)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
    return vessel


@router.get("/voyages")
async def get_voyages(
    limit: int = Query(50, ge=1, le=200),
    vessel_id: Optional[str] = None,
    cii_rating: Optional[str] = None,
):
    """Returns historical and scheduled voyages with environmental and fuel burn metrics."""
    data = _load_data()
    voyages = data.get("voyages", [])
    if vessel_id:
        voyages = [v for v in voyages if v["vessel_id"] == vessel_id]
    if cii_rating:
        voyages = [v for v in voyages if v["cii_rating"].upper() == cii_rating.upper()]
    return {
        "total_voyages": len(data.get("voyages", [])),
        "filtered_count": len(voyages),
        "voyages": voyages[:limit],
    }


@router.get("/voyages/{voyage_id}")
async def get_voyage_details(voyage_id: str):
    """Returns comprehensive leg-by-leg telemetry for a specific voyage."""
    data = _load_data()
    voyage = next((v for v in data.get("voyages", []) if v["voyage_id"] == voyage_id), None)
    if not voyage:
        raise HTTPException(status_code=404, detail=f"Voyage {voyage_id} not found")
    return voyage


@router.get("/ports")
async def get_ports():
    """Returns global major ports metadata and coordinates."""
    data = _load_data()
    return {
        "ports": data.get("ports", {})
    }
