from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role, get_current_user
import models, schemas
from trip_rules import create_maintenance, close_maintenance

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

@router.get("/", response_model=list[schemas.MaintenanceOut])
def list_maintenance(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.MaintenanceLog).all()

@router.post("/", response_model=schemas.MaintenanceOut)
def open_maintenance(
    body: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(models.UserRole.fleet_manager)),
):
    vehicle = db.query(models.Vehicle).get(body.vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    try:
        create_maintenance(vehicle)
    except ValueError as e:
        raise HTTPException(400, str(e))

    log = models.MaintenanceLog(
        vehicle_id=body.vehicle_id,
        description=body.description,
        cost=body.cost,
        status="active",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.post("/{log_id}/close", response_model=schemas.MaintenanceOut)
def close_maintenance_log(
    log_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(models.UserRole.fleet_manager)),
):
    log = db.query(models.MaintenanceLog).get(log_id)
    if not log:
        raise HTTPException(404, "Maintenance log not found")
    if log.status == "closed":
        raise HTTPException(400, "Already closed")

    vehicle = db.query(models.Vehicle).get(log.vehicle_id)
    close_maintenance(vehicle)
    log.status = "closed"
    db.commit()
    db.refresh(log)
    return log