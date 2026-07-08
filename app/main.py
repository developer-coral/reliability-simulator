"""
FastAPI entry point for the Reliability Simulator.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    SimulationRequest,
    SimulationResult,
)
from .simulator import ReliabilitySimulator


# ==
# Application
# ==

app = FastAPI(
    title="Reliability Simulator",
    version="1.0.0",
    description=(
        "Interactive simulator demonstrating Circuit Breaker, "
        "Retry with Exponential Backoff, and Chaos Engineering."
    ),
)

# ==
# CORS
# ==

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==
# Frontend
# ==

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


# ==
# Routes
# ==

@app.get("/", include_in_schema=False)
async def index():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "reliability-simulator",
        "version": "1.0.0",
    }


@app.get("/config")
async def configuration():

    return {
        "available_services": [
            "auth",
            "payments",
            "notifications",
        ],
        "default_iterations": 50,
        "default_failure_rate": 0.15,
        "default_retry_attempts": 3,
        "default_breaker_threshold": 3,
    }


# ==
# Simulation
# ==

@app.post(
    "/simulate",
    response_model=SimulationResult,
    tags=["Simulation"],
)
async def simulate(
    request: SimulationRequest,
):

    try:

        simulator = ReliabilitySimulator(
            request
        )

        return simulator.run()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ==
# Metadata
# ==

@app.get("/about")
async def about():

    return {
        "project": "Reliability Simulator",
        "patterns": [
            "Circuit Breaker",
            "Retry",
            "Chaos Engineering",
        ],
        "framework": "FastAPI",
    }