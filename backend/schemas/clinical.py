"""
SUGAR — Clinical Pydantic Schemas & Reusable Validators.

Provides:
- Reusable validation helpers for clinical float measurements (finite, positive, non-negative, unit checks).
- FIB-4 input and response schemas for deterministic service requests.
- Nullable clinical observation schema preserving nulls without zero-coercion.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Documented plausible adult clinical input range.
MIN_ADULT_AGE: float = 18.0
MAX_ADULT_AGE: float = 120.0


# ---------------------------------------------------------------------------
# Reusable Clinical Validation Helpers
# ---------------------------------------------------------------------------

def validate_finite_float(value: Optional[float], field_name: str) -> Optional[float]:
    """Ensure a float value is finite (reject NaN, +inf, -inf)."""
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a numerical float/int.")
    if math.isnan(value):
        raise ValueError(f"{field_name} cannot be NaN.")
    if math.isinf(value):
        raise ValueError(f"{field_name} cannot be infinite.")
    return float(value)


def validate_positive_float(value: Optional[float], field_name: str) -> Optional[float]:
    """Ensure a measurement is strictly positive (> 0) and finite."""
    val = validate_finite_float(value, field_name)
    if val is not None and val <= 0:
        raise ValueError(f"{field_name} must be strictly positive (> 0), got {val}.")
    return val


def validate_non_negative_float(value: Optional[float], field_name: str) -> Optional[float]:
    """Ensure a measurement is non-negative (>= 0) and finite."""
    val = validate_finite_float(value, field_name)
    if val is not None and val < 0:
        raise ValueError(f"{field_name} cannot be negative (must be >= 0), got {val}.")
    return val


def validate_adult_age(
    age: Optional[float],
    min_age: float = MIN_ADULT_AGE,
    max_age: float = MAX_ADULT_AGE,
) -> Optional[float]:
    """Validate age within documented adult clinical range [min_age, max_age]."""
    val = validate_finite_float(age, "age")
    if val is not None:
        if val < min_age or val > max_age:
            raise ValueError(
                f"Age must be between {min_age:.0f} and {max_age:.0f} years. "
                f"FIB-4 is validated for adult populations; pediatric assessment requires distinct clinical pathways."
            )
    return val


# ---------------------------------------------------------------------------
# Unit Validation Sets
# ---------------------------------------------------------------------------

ALLOWED_TRANSAMINASE_UNITS = {"U/L", "u/l", "IU/L", "iu/l"}
ALLOWED_PLATELET_UNITS = {
    "10^9/L",
    "10*9/L",
    "10^3/uL",
    "10^3/ul",
    "x10^9/L",
    "G/L",
    "g/l",
    "k/uL",
    "k/ul",
}


# ---------------------------------------------------------------------------
# FIB-4 Input and Output Schemas
# ---------------------------------------------------------------------------

class Fib4InputSchema(BaseModel):
    """
    Standard clinical FIB-4 calculation request payload.

    Units:
        age: years
        ast: U/L
        alt: U/L
        platelets: 10⁹/L (10³/μL)
    """
    age: float = Field(..., description="Patient age in years (adult range 18-120)")
    ast: float = Field(..., description="Aspartate Aminotransferase in U/L (> 0)")
    alt: float = Field(..., description="Alanine Aminotransferase in U/L (> 0)")
    platelets: float = Field(..., description="Platelet count in 10⁹/L (> 0)")

    # Optional unit metadata fields to ensure clinical safety
    ast_unit: Optional[str] = Field("U/L", description="Unit of AST measurement (expected U/L)")
    alt_unit: Optional[str] = Field("U/L", description="Unit of ALT measurement (expected U/L)")
    platelets_unit: Optional[str] = Field("10^9/L", description="Unit of Platelet count (expected 10^9/L or 10^3/uL)")

    model_config = ConfigDict(extra="forbid")

    @field_validator("age")
    @classmethod
    def validate_age_field(cls, v: float) -> float:
        res = validate_adult_age(v)
        assert res is not None
        return res

    @field_validator("ast")
    @classmethod
    def validate_ast_field(cls, v: float) -> float:
        res = validate_positive_float(v, "AST")
        assert res is not None
        return res

    @field_validator("alt")
    @classmethod
    def validate_alt_field(cls, v: float) -> float:
        res = validate_positive_float(v, "ALT")
        assert res is not None
        return res

    @field_validator("platelets")
    @classmethod
    def validate_platelets_field(cls, v: float) -> float:
        res = validate_positive_float(v, "Platelet count")
        assert res is not None
        return res

    @field_validator("ast_unit")
    @classmethod
    def validate_ast_unit_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() not in ALLOWED_TRANSAMINASE_UNITS:
            raise ValueError(
                f"Invalid AST unit '{v}'. Expected U/L (or IU/L). Conventional FIB-4 requires standard enzyme units."
            )
        return v

    @field_validator("alt_unit")
    @classmethod
    def validate_alt_unit_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() not in ALLOWED_TRANSAMINASE_UNITS:
            raise ValueError(
                f"Invalid ALT unit '{v}'. Expected U/L (or IU/L). Conventional FIB-4 requires standard enzyme units."
            )
        return v

    @field_validator("platelets_unit")
    @classmethod
    def validate_platelets_unit_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() not in ALLOWED_PLATELET_UNITS:
            raise ValueError(
                f"Invalid Platelets unit '{v}'. Expected 10^9/L or 10^3/uL. Conventional FIB-4 requires SI platelet concentration."
            )
        return v


class Fib4ThresholdSchema(BaseModel):
    """Metadata describing the specific reference threshold scheme applied."""
    scheme_name: str
    age_group: str
    low_cutoff: float
    high_cutoff: float
    boundary_rules: str
    citation: str


class Fib4ResponseSchema(BaseModel):
    """Structured, transparent clinical FIB-4 response."""
    score: float = Field(..., description="Exact unrounded score (IEEE 754 precision)")
    score_display: float = Field(..., description="Score rounded to two decimal places for display")
    risk_category: Literal["Low Risk", "Indeterminate", "High Risk"]
    threshold_set: Fib4ThresholdSchema
    interpretation: str
    explanation: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Reusable Clinical Observation Schema (Preserves Nulls, Never Coerces to 0)
# ---------------------------------------------------------------------------

class ClinicalObservationSchema(BaseModel):
    """
    Validation schema for multi-analyte clinical observations.
    Ensures missing optional measurements remain None (null) and are never coerced to zero.
    """
    age_years: Optional[float] = None
    bmi: Optional[float] = None
    platelets_10e9_l: Optional[float] = None
    ast_u_l: Optional[float] = None
    alt_u_l: Optional[float] = None
    wbc_10e9_l: Optional[float] = None
    rbc_10e12_l: Optional[float] = None
    hgb_g_dl: Optional[float] = None
    glucose_mg_dl: Optional[float] = None
    cholesterol_mg_dl: Optional[float] = None
    cap_steatosis_dbm: Optional[float] = None
    etiology: Optional[str] = None
    ascites: Optional[bool] = None
    jaundice: Optional[bool] = None
    hepatomegaly: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("age_years")
    @classmethod
    def val_age(cls, v: Optional[float]) -> Optional[float]:
        return validate_adult_age(v)

    @field_validator("bmi", "glucose_mg_dl", "cholesterol_mg_dl", "cap_steatosis_dbm")
    @classmethod
    def val_positive_optional(cls, v: Optional[float], info) -> Optional[float]:
        return validate_positive_float(v, info.field_name)

    @field_validator("platelets_10e9_l", "ast_u_l", "alt_u_l", "wbc_10e9_l", "rbc_10e12_l", "hgb_g_dl")
    @classmethod
    def val_labs(cls, v: Optional[float], info) -> Optional[float]:
        return validate_positive_float(v, info.field_name)
