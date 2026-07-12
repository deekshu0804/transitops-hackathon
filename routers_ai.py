"""
routers_ai.py
Matched to TransitOps' real models.py, database.py, and auth.py.
Follows the same access pattern as your other routers: read endpoints open
to any authenticated user, dispatch recommendation gated to fleet_manager
(same role that owns trip creation/dispatch in routers_trips.py).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_role
import models

from ai_engine.dispatch_engine import recommend_top_dispatch
from ai_engine.health_engine import compute_vehicle_health
from ai_engine.anomaly_engine import get_all_anomalies
from ai_engine.copilot import explain_dispatch_recommendation, answer_copilot_question
from ai_schemas import (
    DispatchRequest, DispatchResponse, DispatchOption,
    VehicleHealthResponse, AnomalyItem,
    CopilotRequest, CopilotResponse, CommandCenterResponse,
)

router = APIRouter(prefix="/ai", tags=["AI Operations"])


def _load_fleet_data(db: Session):
    vehicles = db.query(models.Vehicle).all()
    drivers = db.query(models.Driver).all()

    maintenance_by_vehicle = {}
    completed_trips_by_vehicle = {}
    fuel_logs_by_vehicle = {}

    for v in vehicles:
        maintenance_by_vehicle[v.id] = (
            db.query(models.MaintenanceLog)
            .filter(models.MaintenanceLog.vehicle_id == v.id)
            .all()
        )
        completed_trips_by_vehicle[v.id] = (
            db.query(models.Trip)
            .filter(models.Trip.vehicle_id == v.id, models.Trip.status == models.TripStatus.completed)
            .all()
        )
        fuel_logs_by_vehicle[v.id] = (
            db.query(models.FuelLog).filter(models.FuelLog.vehicle_id == v.id).all()
        )

    return vehicles, drivers, maintenance_by_vehicle, completed_trips_by_vehicle, fuel_logs_by_vehicle


@router.post("/dispatch/recommend", response_model=DispatchResponse)
def dispatch_recommend(
    payload: DispatchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.fleet_manager)),
):
    vehicles, drivers, maint, completed_trips, fuel = _load_fleet_data(db)

    ranked = recommend_top_dispatch(
        vehicles=vehicles,
        drivers=drivers,
        cargo_weight=payload.cargo_weight,
        distance_km=payload.distance_km,
        maintenance_by_vehicle=maint,
        completed_trips_by_vehicle=completed_trips,
        fuel_logs_by_vehicle=fuel,
        top_n=3,
    )

    if not ranked:
        raise HTTPException(status_code=404, detail="No suitable vehicle/driver pair found")

    top = ranked[0]
    reason = explain_dispatch_recommendation(ranked, payload.source, payload.destination)

    return DispatchResponse(
        recommended_vehicle=top["vehicle_registration"],
        recommended_driver=top["driver_name"],
        dispatch_score=top["dispatch_score"],
        vehicle_health=top["vehicle_health"],
        estimated_cost=top["estimated_cost"],
        reason=reason,
        alternatives=[DispatchOption(**o) for o in ranked],
    )


@router.get("/vehicles/{vehicle_id}/health", response_model=VehicleHealthResponse)
def vehicle_health(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    maintenance_logs = (
        db.query(models.MaintenanceLog)
        .filter(models.MaintenanceLog.vehicle_id == vehicle_id)
        .all()
    )
    completed_trips = (
        db.query(models.Trip)
        .filter(models.Trip.vehicle_id == vehicle_id, models.Trip.status == models.TripStatus.completed)
        .all()
    )

    result = compute_vehicle_health(vehicle, maintenance_logs, completed_trips)
    return VehicleHealthResponse(**result)


@router.get("/anomalies", response_model=list[AnomalyItem])
def anomalies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vehicles = db.query(models.Vehicle).all()
    vehicle_ids = [v.id for v in vehicles]
    completed_trips = (
        db.query(models.Trip).filter(models.Trip.status == models.TripStatus.completed).all()
    )

    results = get_all_anomalies(vehicle_ids, completed_trips)
    return [AnomalyItem(**a) for a in results]


@router.post("/copilot", response_model=CopilotResponse)
def copilot(
    payload: CopilotRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ranked = []
    if payload.cargo_weight and payload.distance_km:
        vehicles, drivers, maint, completed_trips, fuel = _load_fleet_data(db)
        ranked = recommend_top_dispatch(
            vehicles=vehicles,
            drivers=drivers,
            cargo_weight=payload.cargo_weight,
            distance_km=payload.distance_km,
            maintenance_by_vehicle=maint,
            completed_trips_by_vehicle=completed_trips,
            fuel_logs_by_vehicle=fuel,
            top_n=3,
        )

    answer = answer_copilot_question(payload.question, ranked)
    return CopilotResponse(answer=answer)


@router.get("/command-center", response_model=CommandCenterResponse)
def command_center(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vehicles = db.query(models.Vehicle).all()
    active_trips = (
        db.query(models.Trip).filter(models.Trip.status == models.TripStatus.dispatched).count()
    )

    health_scores = []
    critical_count = 0
    for v in vehicles:
        maintenance_logs = (
            db.query(models.MaintenanceLog).filter(models.MaintenanceLog.vehicle_id == v.id).all()
        )
        completed_trips = (
            db.query(models.Trip)
            .filter(models.Trip.vehicle_id == v.id, models.Trip.status == models.TripStatus.completed)
            .all()
        )
        result = compute_vehicle_health(v, maintenance_logs, completed_trips)
        health_scores.append(result["score"])
        if result["risk"] == "HIGH":
            critical_count += 1

    all_completed_trips = (
        db.query(models.Trip).filter(models.Trip.status == models.TripStatus.completed).all()
    )
    fuel_anomaly_count = len(
        [a for a in get_all_anomalies([v.id for v in vehicles], all_completed_trips)
         if a["type"] == "FUEL_EFFICIENCY_DROP"]
    )

    fleet_health_avg = round(sum(health_scores) / len(health_scores), 1) if health_scores else 0.0

    return CommandCenterResponse(
        fleet_health_avg=fleet_health_avg,
        active_trips=active_trips,
        critical_risk_vehicles=critical_count,
        fuel_anomalies_count=fuel_anomaly_count,
        top_recommendations=[],
    )