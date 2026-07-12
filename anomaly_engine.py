"""
anomaly_engine.py
Rule-based anomaly detection — matched to TransitOps' real models.py.

FuelLog has no distance field, so fuel efficiency anomalies are detected on
COMPLETED TRIPS (actual_distance / fuel_consumed), not on fuel_logs directly.
fuel_logs (liters, cost, date) is left for expense-side anomalies if you want
them later (e.g. price-per-liter spikes) — not implemented here yet.
"""

from typing import List

import models


def _kmpl(trip: "models.Trip") -> float:
    return trip.actual_distance / trip.fuel_consumed if trip.fuel_consumed else 0


def detect_fuel_anomalies(vehicle_id: int, completed_trips: List["models.Trip"]) -> List[dict]:
    """
    Flags a completed trip if its km/l is 25%+ worse than the vehicle's
    trailing average across its own prior completed trips.
    """
    anomalies = []
    usable = [
        t for t in completed_trips
        if t.vehicle_id == vehicle_id and t.actual_distance and t.fuel_consumed
    ]
    trips_sorted = sorted(usable, key=lambda t: t.created_at)

    for i in range(3, len(trips_sorted)):
        history = trips_sorted[max(0, i - 5):i]
        current = trips_sorted[i]

        history_avg = sum(_kmpl(t) for t in history) / len(history)
        current_kmpl = _kmpl(current)

        if history_avg == 0:
            continue

        drop_pct = (history_avg - current_kmpl) / history_avg * 100
        if drop_pct >= 25:
            anomalies.append({
                "vehicle_id": vehicle_id,
                "trip_id": current.id,
                "fuel_log_id": None,
                "type": "FUEL_EFFICIENCY_DROP",
                "message": f"Fuel consumption {drop_pct:.0f}% above expected "
                           f"({current_kmpl:.1f} km/l vs {history_avg:.1f} km/l expected)",
                "severity": "HIGH" if drop_pct >= 40 else "MEDIUM",
            })

    return anomalies


def detect_trip_anomalies(trip: "models.Trip") -> List[dict]:
    """Flags trips where actual distance significantly exceeds planned distance."""
    anomalies = []

    if trip.planned_distance and trip.actual_distance:
        overrun_pct = (
            (trip.actual_distance - trip.planned_distance)
            / trip.planned_distance * 100
        )
        if overrun_pct >= 15:
            anomalies.append({
                "trip_id": trip.id,
                "vehicle_id": trip.vehicle_id,
                "fuel_log_id": None,
                "type": "DISTANCE_OVERRUN",
                "message": f"Actual distance exceeds planned distance by {overrun_pct:.0f}%",
                "severity": "HIGH" if overrun_pct >= 30 else "MEDIUM",
            })

    return anomalies


def get_all_anomalies(vehicle_ids: List[int], completed_trips: List["models.Trip"]) -> List[dict]:
    """Aggregates fuel + trip anomalies for the /ai/anomalies endpoint."""
    all_anomalies = []
    for vid in vehicle_ids:
        all_anomalies.extend(detect_fuel_anomalies(vid, completed_trips))
    for trip in completed_trips:
        all_anomalies.extend(detect_trip_anomalies(trip))
    return all_anomalies