from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role, get_current_user
import models, schemas

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/", response_model=list[schemas.ExpenseOut])
def list_expenses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Expense).all()

@router.post("/", response_model=schemas.ExpenseOut)
def create_expense(
    body: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["fleet_manager", "driver"])),
):
    vehicle = db.query(models.Vehicle).get(body.vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    expense = models.Expense(**body.dict())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense