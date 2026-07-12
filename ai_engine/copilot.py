from typing import List

def explain_dispatch_recommendation(ranked: List[dict], source: str, destination: str) -> str:
    if not ranked:
        return "No eligible vehicle and driver pair is currently available."
    top = ranked[0]
    return (
        f"For {source} to {destination}, recommend vehicle "
        f"{top['vehicle_registration']} with driver {top['driver_name']}. "
        f"The pair scored {top['dispatch_score']}/100 with "
        f"{top['vehicle_health']}/100 vehicle health and an estimated "
        f"operating cost of ₹{top['estimated_cost']:,.0f}."
    )

def answer_copilot_question(question: str, ranked: List[dict]) -> str:
    q = question.lower().strip()
    if ranked and any(word in q for word in ("vehicle", "dispatch", "assign", "recommend", "trip", "driver")):
        top = ranked[0]
        return (
            f"I recommend {top['vehicle_registration']} with {top['driver_name']}. "
            f"Dispatch score: {top['dispatch_score']}/100, vehicle health: "
            f"{top['vehicle_health']}/100, estimated cost: ₹{top['estimated_cost']:,.0f}."
        )
    if "anomal" in q or "fuel" in q:
        return "Use the anomaly feed to inspect fuel-efficiency drops and distance overruns."
    if "health" in q or "risk" in q or "maintenance" in q:
        return "Vehicle health combines odometer wear, maintenance history, and recent fuel-efficiency change."
    if "dispatch" in q or "recommend" in q:
        return "Provide cargo weight and distance so I can rank eligible vehicle-driver pairs."
    return "I can explain dispatch recommendations, vehicle health, maintenance risk, and fuel anomalies."
