from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role, get_current_user
import models, schemas

router = APIRouter(prefix="/fuel-logs", tags=["fuel-logs"])

@router.get("/", response_model=list[schemas.FuelLogOut])
def list_fuel_logs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.FuelLog).all()

@router.post("/", response_model=schemas.FuelLogOut)
def create_fuel_log(
    body: schemas.FuelLogCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(models.UserRole.fleet_manager, models.UserRole.driver_role)),
):
    vehicle = db.query(models.Vehicle).get(body.vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    log = models.FuelLog(**body.dict())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log