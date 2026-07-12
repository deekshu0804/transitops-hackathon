"""
routers_vehicles.py
Vehicle registry CRUD + the /available endpoint that Trip dispatch depends on.

Access rules:
- Anyone authenticated can view vehicles.
- Only fleet_manager can register/edit vehicles (per spec: Fleet Manager
  oversees fleet assets).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user, require_role

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=List[schemas.VehicleOut])
def list_vehicles(
    type: Optional[str] = None,
    status_filter: Optional[models.VehicleStatus] = None,
    sort_by: Optional[str] = None,   # "odometer", "acquisition_cost", "name"
    order: str = "asc",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Vehicle)
    if type:
        query = query.filter(models.Vehicle.type == type)
    if status_filter:
        query = query.filter(models.Vehicle.status == status_filter)

    if sort_by and hasattr(models.Vehicle, sort_by):
        column = getattr(models.Vehicle, sort_by)
        query = query.order_by(column.desc() if order == "desc" else column.asc())

    return query.all()


@router.get("/available", response_model=List[schemas.VehicleOut])
def list_available_vehicles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Vehicles eligible for trip dispatch. Retired/in_shop/on_trip vehicles
    must NEVER appear here — this is a mandatory business rule.
    """
    return db.query(models.Vehicle).filter(
        models.Vehicle.status == models.VehicleStatus.available
    ).all()


@router.get("/{vehicle_id}", response_model=schemas.VehicleOut)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.post("/", response_model=schemas.VehicleOut, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    payload: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.fleet_manager)),
):
    existing = db.query(models.Vehicle).filter(
        models.Vehicle.registration_number == payload.registration_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A vehicle with registration number '{payload.registration_number}' already exists",
        )

    vehicle = models.Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.put("/{vehicle_id}", response_model=schemas.VehicleOut)
def update_vehicle(
    vehicle_id: int,
    payload: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.fleet_manager)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Prevent editing a vehicle currently on a trip into a conflicting state
    if vehicle.status == models.VehicleStatus.on_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a vehicle that is currently on a trip",
        )

    for field, value in payload.model_dump().items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle