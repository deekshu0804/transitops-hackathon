from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db), user=Depends(get_current_user)):
    vehicles = db.query(models.Vehicle).all()
    drivers = db.query(models.Driver).all()
    trips = db.query(models.Trip).all()

    total_vehicles = len(vehicles)
    available_vehicles = sum(1 for v in vehicles if v.status == "available")
    on_trip_vehicles = sum(1 for v in vehicles if v.status == "on_trip")
    in_maintenance = sum(1 for v in vehicles if v.status == "in_shop")
    retired_vehicles = sum(1 for v in vehicles if v.status == "retired")

    drivers_on_duty = sum(1 for d in drivers if d.status == "on_trip")
    drivers_available = sum(1 for d in drivers if d.status == "available")

    active_trips = sum(1 for t in trips if t.status == "dispatched")
    pending_trips = sum(1 for t in trips if t.status == "draft")
    completed_trips = sum(1 for t in trips if t.status == "completed")

    # Fleet utilization: active (non-retired) vehicles currently on_trip
    active_fleet = total_vehicles - retired_vehicles
    fleet_utilization = round((on_trip_vehicles / active_fleet) * 100, 1) if active_fleet else 0.0

    return {
        "total_vehicles": total_vehicles,
        "available_vehicles": available_vehicles,
        "on_trip_vehicles": on_trip_vehicles,
        "in_maintenance": in_maintenance,
        "retired_vehicles": retired_vehicles,
        "drivers_on_duty": drivers_on_duty,
        "drivers_available": drivers_available,
        "active_trips": active_trips,
        "pending_trips": pending_trips,
        "completed_trips": completed_trips,
        "fleet_utilization_pct": fleet_utilization,
    }