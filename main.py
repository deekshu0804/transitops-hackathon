"""
main.py
Entry point. Creates DB tables on startup (fine for hackathon scope —
in production you'd use Alembic migrations instead).
"""

from fastapi import FastAPI

from database import engine, Base
import models  # noqa: F401 — needed so Base knows about all tables before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TransitOps API")


@app.get("/")
def root():
    return {"status": "running", "service": "TransitOps"}