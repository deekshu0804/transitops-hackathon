# TransitOps AI

**AI-powered fleet operations decision engine for smarter dispatch,
vehicle health monitoring, and operational anomaly detection.**

TransitOps AI helps fleet managers move beyond manual fleet tracking. It
combines deterministic operational rules with an intelligence layer that
ranks dispatch options, evaluates vehicle health, detects
fuel-efficiency anomalies, and provides human-readable operational
guidance.

## The Problem

Fleet operations are often fragmented across vehicle records, driver
availability, maintenance logs, fuel data, and trip status. Dispatch
decisions become manual and reactive, while maintenance and efficiency
issues are noticed only after they become expensive.

## Our Solution

TransitOps AI brings core fleet operations into one control center.

-   **Smart Dispatch Recommendation** --- ranks eligible vehicle-driver
    pairs using capacity fit, vehicle health, fuel efficiency,
    availability, and cost efficiency.
-   **Vehicle Health Intelligence** --- generates a health score and
    risk level using odometer, maintenance, and efficiency signals.
-   **Fuel Anomaly Detection** --- identifies significant drops in
    historical fuel efficiency.
-   **Operations Copilot** --- answers fleet operations questions and
    explains recommendations.
-   **AI Command Center** --- live fleet-health, trip, risk, and anomaly
    indicators.
-   **Fleet Management** --- vehicles, drivers, trips, maintenance, fuel
    logs, expenses, reports, authentication, and role-based access.

## Why TransitOps AI Is Different

The system does **not blindly use generative AI to control fleet
dispatch**.

Eligibility is enforced by the same deterministic business rules used by
normal trip dispatch. The intelligence engine only ranks vehicle-driver
pairs that already pass operational validation.

> AI dispatch can never recommend a pair that manual dispatch rules
> would reject.

This creates an explainable, human-in-the-loop decision system: **rules
protect operations; intelligence improves decisions.**

## Dispatch Intelligence

The recommendation engine evaluates valid fleet pairs using a weighted
operational score:

``` text
Dispatch Score =
    30% Capacity Fit
  + 25% Vehicle Health
  + 20% Fuel Efficiency
  + 15% Driver Score
  + 10% Cost Efficiency
```

Before scoring, each pair must pass checks for:

-   Vehicle availability
-   Driver availability
-   Driver suspension
-   Licence expiry
-   Cargo capacity

The fleet manager remains in control of the final dispatch action.

## AI Command Center

The dashboard surfaces:

-   Fleet Health `/100`
-   Active Trips
-   Critical Risk Vehicles
-   Fuel Anomalies
-   Smart Dispatch Recommendations
-   Operations Copilot
-   Live Anomaly Feed

## Architecture

``` text
Frontend
  dashboard.html
        |
        v
FastAPI REST API
  routers_auth.py
  routers_vehicles.py
  routers_drivers.py
  trips.py
  maintenance.py
  fuel_logs.py
  expenses.py
  reports.py
  routers_ai.py
        |
        v
AI Intelligence Layer
  ai_engine/
    dispatch_engine.py
    health_engine.py
    anomaly_engine.py
    copilot.py
        |
        v
Business Rules + SQLAlchemy
  trip_rules.py
  models.py
  database.py
        |
        v
SQLite
```

## AI API Endpoints

  ------------------------------------------------------------------------------------
  Method                  Endpoint                             Purpose
  ----------------------- ------------------------------------ -----------------------
  `POST`                  `/ai/dispatch/recommend`             Rank and recommend
                                                               dispatch pairs

  `GET`                   `/ai/vehicles/{vehicle_id}/health`   Calculate vehicle
                                                               health

  `GET`                   `/ai/anomalies`                      Detect operational
                                                               anomalies

  `POST`                  `/ai/copilot`                        Ask fleet operations
                                                               questions

  `GET`                   `/ai/command-center`                 Get AI dashboard
                                                               metrics
  ------------------------------------------------------------------------------------

Interactive API documentation is available at `/docs` while the backend
is running.

## Tech Stack

-   **Backend:** Python, FastAPI
-   **ORM:** SQLAlchemy
-   **Database:** SQLite
-   **Validation:** Pydantic
-   **Authentication:** JWT
-   **Frontend:** HTML, CSS, Vanilla JavaScript
-   **API Style:** REST

## Run Locally

### 1. Clone the repository

``` bash
git clone https://github.com/deekshu0804/transitops-hackathon.git
cd transitops-hackathon
```

### 2. Install dependencies

``` bash
pip install -r requirements.txt
```

### 3. Start the FastAPI backend

``` bash
uvicorn main:app --reload
```

Backend:

``` text
http://127.0.0.1:8000
```

API docs:

``` text
http://127.0.0.1:8000/docs
```

### 4. Start the frontend

Open another terminal:

``` bash
python -m http.server 5500
```

Then open:

``` text
http://127.0.0.1:5500/dashboard.html
```

## Demo Flow

1.  Create an account and sign in as a fleet manager.
2.  Add vehicles and drivers.
3.  Create and manage trips.
4.  Open **AI Command Center**.
5.  Enter source, destination, cargo weight, and distance.
6.  Click **Analyze Fleet**.
7.  Review the recommended vehicle-driver pair, dispatch score, vehicle
    health, and estimated cost.
8.  Ask the Operations Copilot about dispatch, maintenance, health, or
    fuel risk.
9.  Review detected anomalies in the live feed.

## Project Structure

``` text
transitops-hackathon/
├── ai_engine/
│   ├── __init__.py
│   ├── dispatch_engine.py
│   ├── health_engine.py
│   ├── anomaly_engine.py
│   └── copilot.py
├── ai_schemas.py
├── routers_ai.py
├── auth.py
├── dashboard.html
├── dashboard.py
├── database.py
├── expenses.py
├── fuel_logs.py
├── main.py
├── maintenance.py
├── models.py
├── reports.py
├── routers_auth.py
├── routers_drivers.py
├── routers_vehicles.py
├── schemas.py
├── trip_rules.py
└── trips.py
```

## Future Scope

-   Real-time GPS and telematics integration
-   Route-aware dispatch optimization
-   Predictive maintenance models trained on fleet history
-   Automated alert escalation
-   External LLM integration for richer natural-language explanations
-   PostgreSQL and production deployment
-   Multi-depot fleet optimization

## Built for Hackathon Innovation

TransitOps AI demonstrates how explainable operational intelligence can
augment fleet managers without bypassing safety and business rules.

**From fleet tracking to fleet decision intelligence.**
