from typing import List
from pydantic import BaseModel, Field

class DispatchRequest(BaseModel):
    cargo_weight: float = Field(gt=0)
    distance_km: float = Field(gt=0)
    source: str = Field(min_length=1)
    destination: str = Field(min_length=1)

class DispatchOption(BaseModel):
    vehicle_id: int
    vehicle_registration: str
    driver_id: int
    driver_name: str
    dispatch_score: float
    vehicle_health: float
    capacity_fit_pct: float
    estimated_cost: float
    health_reasons: List[str]

class DispatchResponse(BaseModel):
    recommended_vehicle: str
    recommended_driver: str
    dispatch_score: float
    vehicle_health: float
    estimated_cost: float
    reason: str
    alternatives: List[DispatchOption]

class VehicleHealthResponse(BaseModel):
    vehicle_id: int
    score: float
    risk: str
    reasons: List[str]

class AnomalyItem(BaseModel):
    vehicle_id: int
    trip_id: int
    fuel_log_id: int | None = None
    type: str
    message: str
    severity: str

class CopilotRequest(BaseModel):
    question: str = Field(min_length=1)
    cargo_weight: float | None = Field(default=None, gt=0)
    distance_km: float | None = Field(default=None, gt=0)

class CopilotResponse(BaseModel):
    answer: str

class CommandCenterResponse(BaseModel):
    fleet_health_avg: float
    active_trips: int
    critical_risk_vehicles: int
    fuel_anomalies_count: int
    top_recommendations: List[str]
