"""
SUGAR — Clinical FIB-4 Service Module.

Standard Clinical Formula:
    FIB-4 = (Age [years] × AST [U/L]) / (Platelet count [10⁹/L] × √ALT [U/L])

Expected Input Units:
    - Age: years (adult clinical input range: 18 to 120)
    - AST (Aspartate Aminotransferase): U/L (strictly positive)
    - ALT (Alanine Aminotransferase): U/L (strictly positive)
    - Platelet count: 10⁹/L (equivalent to 10³/μL, strictly positive)

Evidence-Based Threshold Configurations:
    1. Standard Adult (< 65 years):
       - Score < 1.30: Low Risk (high negative predictive value for advanced fibrosis, F3-F4)
       - 1.30 <= Score <= 2.67: Indeterminate zone (secondary testing required, e.g., VCTE/FibroScan)
       - Score > 2.67: High Risk (high positive predictive value for advanced fibrosis / cirrhosis)
    2. Age-Adjusted (>= 65 years, McPherson et al. Gut 2017):
       - Score < 2.00: Low Risk (higher lower cutoff avoids excessive false-positive triaging in elderly)
       - 2.00 <= Score <= 2.67: Indeterminate zone
       - Score > 2.67: High Risk

Scientific Safeguard & Clinical Governance:
    - FIB-4 is an indirect biomarker-based risk-stratification tool, NOT a definitive diagnosis.
    - It does not confirm a histological fibrosis stage (F0-F4) and cannot replace clinical judgment.
    - Missing laboratory values must never be coerced to zero.
    - Research ML models (Egyptian HCV dataset) use dataset-specific ratio features ('AST 1', 'ALT 1')
      and must remain completely decoupled from this standard clinical calculation.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Literal


# Documented plausible adult clinical input range.
# Pediatric fibrosis requires specialized pediatric scoring (e.g. APRI / PNFI); FIB-4 is not validated <18.
# Ages >120 are biologically implausible and rejected rather than silently clamped.
MIN_ADULT_AGE: float = 18.0
MAX_ADULT_AGE: float = 120.0

RiskCategory = Literal["Low Risk", "Indeterminate", "High Risk"]


@dataclass(frozen=True)
class Fib4ThresholdSet:
    """Explicit threshold set metadata used in clinical interpretation."""
    scheme_name: str
    age_group: str
    low_cutoff: float
    high_cutoff: float
    boundary_rules: str
    citation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


STANDARD_ADULT_THRESHOLDS = Fib4ThresholdSet(
    scheme_name="Standard Adult Reference Scheme (AASLD/EASL)",
    age_group="age < 65",
    low_cutoff=1.30,
    high_cutoff=2.67,
    boundary_rules="Low: score < 1.30; Indeterminate: 1.30 <= score <= 2.67; High: score > 2.67",
    citation="Sterling RK, et al. Hepatology 2006; 43(6):1317-1325",
)

ELDERLY_ADJUSTED_THRESHOLDS = Fib4ThresholdSet(
    scheme_name="Age-Adjusted Reference Scheme (McPherson et al.)",
    age_group="age >= 65",
    low_cutoff=2.00,
    high_cutoff=2.67,
    boundary_rules="Low: score < 2.00; Indeterminate: 2.00 <= score <= 2.67; High: score > 2.67",
    citation="McPherson S, et al. Gut 2017; 66(11):2014-2023",
)


@dataclass(frozen=True)
class Fib4Interpretation:
    """Structured, transparent clinical interpretation of a FIB-4 score."""
    score: float
    score_display: float
    risk_category: RiskCategory
    threshold_set: Fib4ThresholdSet
    interpretation: str
    explanation: str
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "score_display": self.score_display,
            "risk_category": self.risk_category,
            "threshold_set": self.threshold_set.to_dict(),
            "interpretation": self.interpretation,
            "explanation": self.explanation,
            "disclaimer": self.disclaimer,
        }


def validate_fib4_inputs(
    age: float,
    ast: float,
    alt: float,
    platelets: float,
    min_age: float = MIN_ADULT_AGE,
    max_age: float = MAX_ADULT_AGE,
) -> None:
    """
    Validate all inputs required for FIB-4 calculation.

    Raises:
        TypeError: If an input is None or not a numerical value.
        ValueError: If an input is NaN, infinite, non-positive, or outside clinical bounds.
    """
    for name, val in [("age", age), ("ast", ast), ("alt", alt), ("platelets", platelets)]:
        if val is None:
            raise TypeError(f"Missing required clinical input: '{name}' cannot be None.")
        if not isinstance(val, (int, float)):
            raise TypeError(f"Invalid type for '{name}': expected float/int, got {type(val).__name__}.")
        if math.isnan(val):
            raise ValueError(f"Invalid non-finite input: '{name}' cannot be NaN.")
        if math.isinf(val):
            raise ValueError(f"Invalid non-finite input: '{name}' cannot be infinite.")

    # Clinical range validation for age
    if age < min_age or age > max_age:
        raise ValueError(
            f"Implausible or unvalidated age: {age}. "
            f"FIB-4 is validated for adult populations aged {min_age:.0f} to {max_age:.0f} years. "
            f"Pediatric and non-adult patients require alternative scoring tools."
        )

    # Strictly positive requirements for laboratory indices
    if ast <= 0:
        raise ValueError(f"AST must be strictly positive (> 0 U/L), got {ast}.")
    if alt <= 0:
        raise ValueError(f"ALT must be strictly positive (> 0 U/L), got {alt}.")
    if platelets <= 0:
        raise ValueError(
            f"Platelet count must be strictly positive (> 0 × 10⁹/L), got {platelets}."
        )


def calculate_fib4(
    age: float,
    ast: float,
    alt: float,
    platelets: float,
    min_age: float = MIN_ADULT_AGE,
    max_age: float = MAX_ADULT_AGE,
) -> float:
    """
    Calculate deterministic FIB-4 index at full IEEE 754 precision.

    Formula:
        FIB-4 = (age * ast) / (platelets * sqrt(alt))

    Units:
        age: years
        ast: U/L
        alt: U/L
        platelets: 10⁹/L (10³/μL)

    Returns:
        float: Exact calculated score without premature rounding.
    """
    validate_fib4_inputs(age, ast, alt, platelets, min_age=min_age, max_age=max_age)

    # Note: alt > 0 and platelets > 0 guaranteed by validate_fib4_inputs,
    # preventing sqrt domain error and division by zero.
    sqrt_alt = math.sqrt(alt)
    denominator = platelets * sqrt_alt
    return (age * ast) / denominator


def interpret_fib4(
    score: float,
    age: float,
) -> Fib4Interpretation:
    """
    Provide transparent, evidence-based clinical risk stratification for a FIB-4 score.

    Boundary Rules:
        Under 65:
            - score < 1.30: Low Risk
            - 1.30 <= score <= 2.67: Indeterminate
            - score > 2.67: High Risk
        65 or Older:
            - score < 2.00: Low Risk
            - 2.00 <= score <= 2.67: Indeterminate
            - score > 2.67: High Risk
    """
    if score is None or not math.isfinite(score):
        raise ValueError(f"FIB-4 score must be a finite number, got {score}.")
    if age is None or not math.isfinite(age):
        raise ValueError(f"Age must be a finite number, got {age}.")

    if age >= 65.0:
        threshold_set = ELDERLY_ADJUSTED_THRESHOLDS
        low_cutoff = threshold_set.low_cutoff
        high_cutoff = threshold_set.high_cutoff
        if score < low_cutoff:
            risk_category: RiskCategory = "Low Risk"
            interp_text = (
                f"FIB-4 of {score:.2f} is below the age-adjusted low-risk cutoff of {low_cutoff:.2f}. "
                "Suggests low probability of advanced fibrosis (F3-F4) in patients aged 65 and older. "
                "Negative predictive value depends on cohort prevalence and is not universally guaranteed."
            )
        elif score <= high_cutoff:
            risk_category = "Indeterminate"
            interp_text = (
                f"FIB-4 of {score:.2f} falls within the indeterminate zone ({low_cutoff:.2f}–{high_cutoff:.2f}). "
                "Routine liver panel and platelet indices alone cannot reliably triage risk; secondary non-invasive testing is recommended."
            )
        else:
            risk_category = "High Risk"
            interp_text = (
                f"FIB-4 of {score:.2f} exceeds the high-risk threshold of {high_cutoff:.2f}. "
                "Suggests elevated probability of advanced fibrosis (F3-F4) or cirrhosis; specialized hepatology evaluation recommended."
            )
    else:
        threshold_set = STANDARD_ADULT_THRESHOLDS
        low_cutoff = threshold_set.low_cutoff
        high_cutoff = threshold_set.high_cutoff
        if score < low_cutoff:
            risk_category = "Low Risk"
            interp_text = (
                f"FIB-4 of {score:.2f} is below the standard low-risk cutoff of {low_cutoff:.2f}. "
                "Suggests low probability of advanced liver fibrosis (F3-F4) in primary care populations. "
                "Note that negative predictive value depends on disease prevalence and is not universally guaranteed."
            )
        elif score <= high_cutoff:
            risk_category = "Indeterminate"
            interp_text = (
                f"FIB-4 of {score:.2f} falls within the indeterminate zone ({low_cutoff:.2f}–{high_cutoff:.2f}). "
                "FIB-4 alone cannot reliably confirm or exclude advanced fibrosis; secondary testing (e.g., VCTE/FibroScan or ELF) is recommended."
            )
        else:
            risk_category = "High Risk"
            interp_text = (
                f"FIB-4 of {score:.2f} exceeds the high-risk cutoff of {high_cutoff:.2f}. "
                "High specificity for advanced fibrosis (F3-F4); formal hepatology assessment and clinical staging recommended."
            )

    explanation = (
        "FIB-4 is a guideline-recommended (AASLD/EASL) clinical triage and risk-stratification "
        "screening marker based on age, aminotransferases, and platelet count. It provides probabilistic "
        "risk category assignment and is not a histological or definitive diagnosis."
    )

    disclaimer = (
        "FIB-4 score results must be evaluated alongside patient etiology, medical history, and clinical signs. "
        "Acute hepatitis, strenuous exercise, hemolysis, or extrahepatic thrombocytopenia can alter score accuracy. "
        "This tool does not provide medical diagnosis or treatment confirmation."
    )

    return Fib4Interpretation(
        score=score,
        score_display=round(score, 2),
        risk_category=risk_category,
        threshold_set=threshold_set,
        interpretation=interp_text,
        explanation=explanation,
        disclaimer=disclaimer,
    )


def calculate_and_interpret_fib4(
    age: float,
    ast: float,
    alt: float,
    platelets: float,
    min_age: float = MIN_ADULT_AGE,
    max_age: float = MAX_ADULT_AGE,
) -> Fib4Interpretation:
    """
    Combined convenience entrypoint: validates inputs, computes score,
    and returns complete structured interpretation.
    """
    score = calculate_fib4(age, ast, alt, platelets, min_age=min_age, max_age=max_age)
    return interpret_fib4(score=score, age=age)
