"""
Integration and API tests for Review 3 scope in Veyra Visual Compiler.
Tests /api/compile, /api/cfg, /api/optimize, /api/debug, /api/health endpoints,
and verifies CFG, Optimizer, and Debugger integration.
"""

import pytest
import json
from app import app
from backend.compiler import VeyraCompiler


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert data["phase"] == 3
    assert len(data["features"]) >= 6


def test_api_compile_contains_phase3_artifacts(client):
    payload = {
        "source": """
        let score = 20;
        let bonus = 5;
        let result = score + bonus * 2;
        if (result >= 30) {
            print(result);
        } else {
            print(0);
        }
        """
    }
    response = client.post("/api/compile", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["output"] == "30"
    # CFG artifact
    assert data["cfg"] is not None
    assert len(data["cfg"]["blocks"]) >= 3
    assert len(data["cfg"]["edges"]) >= 2
    assert data["cfg"]["is_valid"] is True

    # Optimizer artifact
    assert data["optimized_ir"] is not None
    assert data["optimization_report"] is not None
    assert data["optimization_report"]["is_valid"] is True
    assert data["optimization_report"]["reduction_count"] >= 0

    # Debugger trace artifact
    assert data["debug_trace"] is not None
    assert data["debug_trace"]["completed_normally"] is True
    assert data["debug_trace"]["total_steps"] >= 5


def test_api_cfg_endpoint(client):
    payload = {
        "source": "let a = 10; if (a > 5) { print(a); }"
    }
    response = client.post("/api/cfg", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["cfg"] is not None
    assert data["cfg"]["block_count"] >= 2


def test_api_optimize_endpoint(client):
    payload = {
        "source": "let x = 10 + 5 * 2; print(x);"
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["original_ir"] is not None
    assert data["optimized_ir"] is not None
    assert data["optimization_report"] is not None
    # 5 * 2 and 10 + 10 folded into 20
    assert data["optimization_report"]["transformation_count"] > 0


def test_api_debug_endpoint(client):
    payload = {
        "source": "let count = 1; count = count + 2; print(count);"
    }
    response = client.post("/api/debug", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["debug_trace"] is not None
    assert data["output"] == "3"
    events = data["debug_trace"]["events"]
    assert any(e["event_type"] == "var_declare" for e in events)
    assert any(e["event_type"] == "assignment" for e in events)
    assert any(e["event_type"] == "print" for e in events)


def test_api_error_diagnostics(client):
    payload = {"source": "let x = ;"}
    response = client.post("/api/compile", json=payload)
    data = response.get_json()
    assert data["success"] is False
    assert len(data["diagnostics"]) > 0
    assert data["diagnostics"][0]["stage"] == "Syntax Error"


def test_api_invalid_payload(client):
    response = client.post("/api/compile", json={"source": 12345})
    assert response.status_code == 400


def test_api_security_headers(client):
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_api_payload_limit(client):
    oversized_source = "let x = 1;\n" * 15000  # >100,000 characters
    response = client.post("/api/compile", json={"source": oversized_source})
    assert response.status_code == 413
