"""
health_engine.py
Deterministic vehicle health scoring — matched to TransitOps' real models.py.

Data sources used (real fields):
  Vehicle: odometer, max_load_capacity
  MaintenanceLog: vehicle_id, date, status (active/closed)  -- no odometer_at_service
  Trip: vehicle_id, status, actual_distance, fuel_consumed  -- used for efficiency,
        since FuelLog has no distance field to compute km/l from directly.

Design notes:
- Maintenance overdue is time-based (days since last closed service), not
  odometer-based, because MaintenanceLog doesn't store odometer_at_service.
- An OPEN (status=active) maintenance log is treated as a serious risk signal
  on its own, independent of the time-based check.
"""

from datetime import date
from typing import List, Tuple

import models


def _odometer_penalty(odometer: float) -> float:
    """Higher odometer -> higher wear penalty. Caps around 100k km."""
    return min(odometer / 1000, 100) * 0.25  # up to 25 pts


def _maintenance_penalty(
    maintenance_logs: List["models.MaintenanceLog"],
    max_interval_days: int = 180,
) -> Tuple[float, List[str]]:
    reasons = []
    penalty = 0.0

    open_logs = [m for m in maintenance_logs if m.status == models.MaintenanceStatus.active]
    if open_logs:
        penalty += 30.0
        reasons.append(f"{len(open_logs)} unresolved maintenance issue(s) open")

    closed_logs = [m for m in maintenance_logs if m.status == models.MaintenanceStatus.closed]
    if not closed_logs:
        penalty += 15.0
        reasons.append("No completed maintenance history on record")
    else:
        last_service = max(closed_logs, key=lambda m: m.date)
        days_since = (date.today() - last_service.date).days
        if days_since > max_interval_days:
            overdue_ratio = days_since / max_interval_days
            penalty += min((overdue_ratio - 1.0) * 30, 30.0)
            reasons.append(f"{days_since} days since last completed service")

    return penalty, reasons


def _fuel_efficiency_penalty(completed_trips: List["models.Trip"]) -> Tuple[float, List[str]]:
    """
    Compares the last 3 completed trips' km/l against the vehicle's own prior
    trip history. A meaningful drop indicates mechanical wear or bad driving.
    """
    usable = [
        t for t in completed_trips
        if t.actual_distance and t.fuel_consumed and t.fuel_consumed > 0
    ]
    if len(usable) < 4:
        return 0.0, []

    usable_sorted = sorted(usable, key=lambda t: t.created_at)

    def kmpl(t):
        return t.actual_distance / t.fuel_consumed

    recent = usable_sorted[-3:]
    baseline = usable_sorted[:-3]

    recent_avg = sum(kmpl(t) for t in recent) / len(recent)
    baseline_avg = sum(kmpl(t) for t in baseline) / len(baseline)

    if baseline_avg == 0:
        return 0.0, []

    drop_pct = max(0.0, (baseline_avg - recent_avg) / baseline_avg)
    penalty = min(drop_pct * 100, 30.0)
    reasons = ["Recent trips show a fuel efficiency drop vs. this vehicle's own history"] if penalty > 5 else []
    return penalty, reasons


def compute_vehicle_health(
    vehicle: "models.Vehicle",
    maintenance_logs: List["models.MaintenanceLog"],
    completed_trips: List["models.Trip"],
    max_interval_days: int = 180,
) -> dict:
    """
    Returns:
      {"vehicle_id": ..., "score": 0-100, "risk": "LOW"|"MEDIUM"|"HIGH", "reasons": [...]}
    """
    reasons = []

    odo_penalty = _odometer_penalty(vehicle.odometer)
    if odo_penalty > 10:
        reasons.append(f"High odometer reading ({vehicle.odometer:,.0f} km)")

    maint_penalty, maint_reasons = _maintenance_penalty(maintenance_logs, max_interval_days)
    reasons.extend(maint_reasons)

    fuel_penalty, fuel_reasons = _fuel_efficiency_penalty(completed_trips)
    reasons.extend(fuel_reasons)

    score = max(0.0, 100.0 - odo_penalty - maint_penalty - fuel_penalty)

    if score >= 75:
        risk = "LOW"
    elif score >= 50:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    if not reasons:
        reasons.append("No significant risk factors detected")

    return {
        "vehicle_id": vehicle.id,
        "score": round(score, 1),
        "risk": risk,
        "reasons": reasons,
    }