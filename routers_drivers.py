"""
routers_drivers.py
Driver profile CRUD + the /available endpoint Trip dispatch depends on.

Access rules:
- Anyone authenticated can view drivers.
- Only safety_officer or fleet_manager can register/edit drivers
  (Safety Officer tracks license validity per spec).
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[schemas.DriverOut])
def list_drivers(
    status_filter: Optional[models.DriverStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Driver)
    if status_filter:
        query = query.filter(models.Driver.status == status_filter)
    return query.all()


@router.get("/available", response_model=List[schemas.DriverOut])
def list_available_drivers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Drivers eligible for trip dispatch. Mandatory business rules enforced here:
    - status must be 'available' (not on_trip/off_duty/suspended)
    - license must not be expired
    """
    today = date.today()
    return db.query(models.Driver).filter(
        models.Driver.status == models.DriverStatus.available,
        models.Driver.license_expiry_date >= today,
    ).all()


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


@router.post("/", response_model=schemas.DriverOut, status_code=status.HTTP_201_CREATED)
def register_driver(
    payload: schemas.DriverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role(models.UserRole.fleet_manager, models.UserRole.safety_officer)
    ),
):
    existing = db.query(models.Driver).filter(
        models.Driver.license_number == payload.license_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A driver with license number '{payload.license_number}' already exists",
        )

    if payload.license_expiry_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register a driver with an already-expired license",
        )

    driver = models.Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.put("/{driver_id}", response_model=schemas.DriverOut)
def update_driver(
    driver_id: int,
    payload: schemas.DriverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_role(models.UserRole.fleet_manager, models.UserRole.safety_officer)
    ),
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    if driver.status == models.DriverStatus.on_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a driver who is currently on a trip",
        )

    for field, value in payload.model_dump().items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


@router.post("/{driver_id}/suspend", response_model=schemas.DriverOut)
def suspend_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.safety_officer)),
):
    """Safety Officer can suspend a driver (e.g., for safety violations)."""
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    if driver.status == models.DriverStatus.on_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend a driver who is currently on a trip",
        )
    driver.status = models.DriverStatus.suspended
    db.commit()
    db.refresh(driver)
    return driver