# Reliability Simulator

A production-inspired reliability engineering simulator demonstrating three fundamental resilience patterns used in distributed systems:

- Circuit Breaker
- Retry with Exponential Backoff
- Chaos Injection

The simulator exposes a FastAPI REST API and an interactive frontend for experimenting with service failures and observing resilience behavior.

---

## Architecture

```
                  Frontend
                      │
                      ▼
               FastAPI REST API
                      │
                      ▼
          Reliability Simulator
                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼
Chaos Injector   Retry Handler   Circuit Breaker
      │               │               │
      └───────────────┴───────────────┘
                      │
                      ▼
                Mock Service
                      │
                      ▼
                  Metrics Engine
```

---

## Features

### Circuit Breaker

- Closed
- Open
- Half-Open
- Automatic recovery
- Failure threshold configuration

### Retry

- Configurable retry count
- Exponential backoff
- Retry statistics

### Chaos Engineering

Injects realistic failures including

- Network timeout
- Connection failure
- HTTP 500
- Random latency

### Metrics

The simulator collects

- Success rate
- Failure rate
- Retry count
- Circuit opens
- Average latency
- Total requests

---

## Repository Structure

```
reliability-simulator/
│
├── README.md
├── pyproject.toml
├── Dockerfile
│
├── app/
│   ├── main.py
│   ├── simulator.py
│   ├── circuit_breaker.py
│   ├── retry.py
│   ├── chaos.py
│   ├── models.py
│   └── metrics.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
└── tests/
    ├── test_breaker.py
    ├── test_retry.py
    └── test_simulator.py
```

---

## Installation

### Clone

```bash
git clone https://github.com/username/reliability-simulator.git
cd reliability_simulator
```

### Create Virtual Environment

```bash
python3 -m venv .venv
```

Linux/macOS

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

### Install

```bash
pip install -e .
```

---

## Run

```bash
uvicorn app.main:app --reload
```

Open

```
http://localhost:8000
```

---

## API

### POST /simulate

Example request

```json
{
  "services": [
    "auth",
    "payments",
    "notifications"
  ],
  "iterations": 100,
  "failure_rate": 0.15,
  "retry_attempts": 3,
  "breaker_threshold": 3
}
```

Example response

```json
{
  "success_rate": 0.94,
  "failure_rate": 0.06,
  "average_latency_ms": 81.2,
  "total_requests": 300,
  "retries": 21,
  "circuit_opens": 4
}
```

---

## Running Tests

```bash
pytest
```

Coverage

```bash
pytest --cov=app
```

---

## Technologies

- Python 3.12
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- Docker

---

## Learning Objectives

This project demonstrates

- Distributed systems fundamentals
- Fault tolerance
- Resilience engineering
- Clean architecture
- Test-driven development
- API design
- Software observability

---

## Future Improvements

- Service dependency graph
- Bulkhead isolation
- Adaptive circuit breaker
- Rate limiter
- Prometheus metrics
- OpenTelemetry tracing
- Kubernetes deployment

---

## License

MIT