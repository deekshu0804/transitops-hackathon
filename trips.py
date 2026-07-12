from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from deps import get_current_user, require_role
import models, schemas
from trip_rules import can_dispatch_trip, dispatch_trip, complete_trip, cancel_trip

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("/", response_model=list[schemas.TripOut])
def list_trips(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Trip).all()

@router.post("/", response_model=schemas.TripOut)
def create_trip(
    trip_in: schemas.TripCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["fleet_manager"])),
):
    vehicle = db.query(models.Vehicle).get(trip_in.vehicle_id)
    driver = db.query(models.Driver).get(trip_in.driver_id)
    if not vehicle or not driver:
        raise HTTPException(404, "Vehicle or driver not found")

    trip = models.Trip(**trip_in.dict(), status="draft", created_at=datetime.utcnow())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/dispatch", response_model=schemas.TripOut)
def dispatch(
    trip_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["fleet_manager"])),
):
    trip = db.query(models.Trip).get(trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    if trip.status != "draft":
        raise HTTPException(400, f"Trip is '{trip.status}', can only dispatch from 'draft'")

    vehicle = db.query(models.Vehicle).get(trip.vehicle_id)
    driver = db.query(models.Driver).get(trip.driver_id)

    ok, reason = can_dispatch_trip(vehicle, driver, trip.cargo_weight)
    if not ok:
        raise HTTPException(400, reason)

    dispatch_trip(trip, vehicle, driver)
    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/complete", response_model=schemas.TripOut)
def complete(
    trip_id: int,
    body: schemas.TripCompleteRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role(["fleet_manager", "driver"])),
):
    trip = db.query(models.Trip).get(trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    if trip.status != "dispatched":
        raise HTTPException(400, f"Trip is '{trip.status}', can only complete from 'dispatched'")

    vehicle = db.query(models.Vehicle).get(trip.vehicle_id)
    driver = db.query(models.Driver).get(trip.driver_id)

    if body.final_odometer < vehicle.odometer:
        raise HTTPException(400, "final_odometer cannot be less than current odometer")

    complete_trip(trip, vehicle, driver, body.final_odometer, body.fuel_consumed)
    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/cancel", response_model=schemas.TripOut)
def cancel(
    trip_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["fleet_manager"])),
):
    trip = db.query(models.Trip).get(trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    if trip.status in ("completed", "cancelled"):
        raise HTTPException(400, f"Trip already '{trip.status}', cannot cancel")

    vehicle = db.query(models.Vehicle).get(trip.vehicle_id)
    driver = db.query(models.Driver).get(trip.driver_id)

    cancel_trip(trip, vehicle, driver)
    db.commit()
    db.refresh(trip)
    return trip