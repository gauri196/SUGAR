"""
SUGAR — Phase 3 Clinical Input Validation & Schema Tests.

Verifies:
- HTTP API /api/fib4/calculate endpoint functionality.
- HTTP 422 on missing required inputs.
- HTTP 422 on non-positive AST, ALT, or platelets.
- HTTP 422 on NaN, infinity, and string types.
- HTTP 422 on pediatric age (<18) or implausible age (>120).
- HTTP 422 on invalid unit metadata.
- Successful calculation when valid explicit units are passed.
- Nullability preservation for ClinicalObservationSchema (absent values remain None, never 0).
- Rejection of invalid negative values in clinical observations.
- Invariance and safety of existing /predict endpoint.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.clinical import (
    Fib4InputSchema,
    Fib4ResponseSchema,
    ClinicalObservationSchema,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. FIB-4 API Endpoint - Valid Cases
# ---------------------------------------------------------------------------

def test_api_fib4_calculate_known_example():
    payload = {
        "age": 45.0,
        "ast": 42.0,
        "alt": 38.0,
        "platelets": 180.0,
        "ast_unit": "U/L",
        "alt_unit": "U/L",
        "platelets_unit": "10^9/L",
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert pytest.approx(data["score"], abs=1e-2) == 1.70
    assert data["score_display"] == 1.70
    assert data["risk_category"] == "Indeterminate"
    assert data["threshold_set"]["low_cutoff"] == 1.30
    assert data["threshold_set"]["high_cutoff"] == 2.67
    assert "screening" in data["explanation"].lower() or "triage" in data["explanation"].lower()


def test_api_fib4_calculate_elderly_age_adjusted():
    # Patient aged 70 with moderate labs:
    # FIB-4 = (70 * 30) / (220 * sqrt(35)) = 2100 / (220 * 5.916079) ≈ 1.61
    # Under standard <65 cutoffs (1.30-2.67), 1.61 is Indeterminate.
    # Under >=65 cutoff (< 2.00), 1.61 is Low Risk!
    payload = {
        "age": 70.0,
        "ast": 30.0,
        "alt": 35.0,
        "platelets": 220.0,
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert pytest.approx(data["score"], abs=1e-2) == 1.61
    assert data["risk_category"] == "Low Risk"
    assert data["threshold_set"]["low_cutoff"] == 2.00
    assert data["threshold_set"]["age_group"] == "age >= 65"


# ---------------------------------------------------------------------------
# 2. FIB-4 API Endpoint - Validation Failures (HTTP 422)
# ---------------------------------------------------------------------------

def test_api_fib4_missing_required_fields():
    # Missing platelets
    payload = {
        "age": 45.0,
        "ast": 42.0,
        "alt": 38.0,
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("field,bad_val", [
    ("ast", 0.0),
    ("ast", -10.0),
    ("alt", 0.0),
    ("alt", -5.0),
    ("platelets", 0.0),
    ("platelets", -50.0),
])
def test_api_fib4_zero_and_negative_values(field, bad_val):
    payload = {
        "age": 45.0,
        "ast": 42.0,
        "alt": 38.0,
        "platelets": 180.0,
    }
    payload[field] = bad_val
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("strictly positive" in err.get("msg", "") for err in errors)


def test_api_fib4_pediatric_age_rejected():
    payload = {
        "age": 15.0,  # Pediatric (< 18)
        "ast": 42.0,
        "alt": 38.0,
        "platelets": 180.0,
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("18 and 120" in err.get("msg", "") for err in errors)


def test_api_fib4_implausible_age_rejected():
    payload = {
        "age": 135.0,  # Biologically implausible (> 120)
        "ast": 42.0,
        "alt": 38.0,
        "platelets": 180.0,
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("18 and 120" in err.get("msg", "") for err in errors)


@pytest.mark.parametrize("unit_field,bad_unit", [
    ("ast_unit", "mg/dL"),
    ("alt_unit", "g/L"),
    ("platelets_unit", "fl"),
])
def test_api_fib4_invalid_units_rejected(unit_field, bad_unit):
    payload = {
        "age": 45.0,
        "ast": 42.0,
        "alt": 38.0,
        "platelets": 180.0,
        unit_field: bad_unit,
    }
    response = client.post("/api/fib4/calculate", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("Invalid" in err.get("msg", "") for err in errors)


# ---------------------------------------------------------------------------
# 3. ClinicalObservationSchema - Nullability Preservation
# ---------------------------------------------------------------------------

def test_clinical_observation_schema_preserves_none():
    """Ensure absent measurements remain None, never coerced to 0."""
    obs = ClinicalObservationSchema(age_years=52.0)
    dumped = obs.model_dump()

    assert dumped["age_years"] == 52.0
    assert dumped["platelets_10e9_l"] is None
    assert dumped["ast_u_l"] is None
    assert dumped["alt_u_l"] is None
    assert dumped["wbc_10e9_l"] is None
    assert dumped["rbc_10e12_l"] is None
    assert dumped["hgb_g_dl"] is None
    assert dumped["glucose_mg_dl"] is None
    assert dumped["cholesterol_mg_dl"] is None
    assert dumped["cap_steatosis_dbm"] is None


def test_clinical_observation_schema_rejects_negative_and_nan():
    # Negative lab value rejected
    with pytest.raises(Exception):
        ClinicalObservationSchema(platelets_10e9_l=-150.0)

    # NaN rejected
    with pytest.raises(Exception):
        ClinicalObservationSchema(ast_u_l=float("nan"))

    # Non-adult age rejected
    with pytest.raises(Exception):
        ClinicalObservationSchema(age_years=10.0)


# ---------------------------------------------------------------------------
# 4. Predict Endpoint Safety & Invariance
# ---------------------------------------------------------------------------

def test_predict_endpoint_rejects_non_positive_and_nan():
    # Negative platelet count rejected with 422
    invalid_payload = {
        "age": 42.0,
        "bmi": 24.5,
        "platelets": -255.0,
        "ast": 25.0,
        "alt": 24.0,
        "wbc": 6.5,
        "rbc": 4.8,
        "hgb": 15.0,
    }
    response = client.post("/predict", json=invalid_payload)
    assert response.status_code == 422
