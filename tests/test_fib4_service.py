"""
SUGAR — Phase 3 Clinical FIB-4 Service Tests.

Verifies:
- Standard formula correctness using known numerical example:
  age 45, AST 42 U/L, ALT 38 U/L, platelets 180 × 10⁹/L -> expected ~1.70.
- Adequate precision (unrounded float preserved; rounded display value provided).
- Threshold boundary behavior for adults under 65:
  < 1.30 (Low Risk), 1.30-2.67 (Indeterminate), > 2.67 (High Risk).
- Explicit boundary tests at exactly 1.30 and 2.67.
- Age-adjusted threshold scheme for adults 65 or older:
  < 2.00 (Low Risk), 2.00-2.67 (Indeterminate), > 2.67 (High Risk).
- Zero and negative AST, ALT, and platelet values rejected with ValueError.
- Non-finite inputs (NaN, +inf, -inf) rejected with ValueError.
- Missing required inputs (None) rejected with TypeError.
- Documented adult age policy validation ([18, 120] years; pediatric & implausible rejected).
- Safe division and sqrt domain handling (guaranteed non-zero, non-negative).
- Transparent clinical interpretation text and disclaimers.
"""
import math
import pytest

from backend.services.fib4 import (
    calculate_fib4,
    interpret_fib4,
    calculate_and_interpret_fib4,
    STANDARD_ADULT_THRESHOLDS,
    ELDERLY_ADJUSTED_THRESHOLDS,
    MIN_ADULT_AGE,
    MAX_ADULT_AGE,
)


# ---------------------------------------------------------------------------
# 1. Known Numerical Example & Determinism
# ---------------------------------------------------------------------------

def test_fib4_known_numerical_example():
    """
    Standard benchmark:
    age = 45 years
    AST = 42 U/L
    ALT = 38 U/L
    platelets = 180 × 10⁹/L
    FIB-4 = (45 * 42) / (180 * sqrt(38))
          = 1890 / (180 * 6.164414...)
          ≈ 1.703325...
    """
    age = 45.0
    ast = 42.0
    alt = 38.0
    platelets = 180.0

    score = calculate_fib4(age=age, ast=ast, alt=alt, platelets=platelets)

    # Verify unrounded precision
    expected_exact = (45.0 * 42.0) / (180.0 * math.sqrt(38.0))
    assert math.isclose(score, expected_exact, rel_tol=1e-12)
    assert pytest.approx(score, abs=1e-2) == 1.70

    # Interpretation verification
    interp = interpret_fib4(score=score, age=age)
    assert interp.score == score
    assert interp.score_display == 1.70
    assert interp.risk_category == "Indeterminate"
    assert interp.threshold_set.scheme_name == STANDARD_ADULT_THRESHOLDS.scheme_name
    assert interp.threshold_set.low_cutoff == 1.30
    assert interp.threshold_set.high_cutoff == 2.67
    assert "screening" in interp.explanation.lower() or "triage" in interp.explanation.lower()
    assert "not a" in interp.disclaimer.lower() or "not provide" in interp.disclaimer.lower()


# ---------------------------------------------------------------------------
# 2. Threshold Boundary Behavior for Adults < 65
# ---------------------------------------------------------------------------

def test_fib4_threshold_boundaries_under_65():
    """
    For age < 65:
    - score < 1.30 -> Low Risk
    - 1.30 <= score <= 2.67 -> Indeterminate
    - score > 2.67 -> High Risk
    """
    age = 40.0

    # Strictly below lower cutoff
    low = interpret_fib4(score=1.29999, age=age)
    assert low.risk_category == "Low Risk"

    # Exact lower cutoff boundary -> Indeterminate
    boundary_low = interpret_fib4(score=1.30, age=age)
    assert boundary_low.risk_category == "Indeterminate"

    # Middle of indeterminate zone
    mid = interpret_fib4(score=1.95, age=age)
    assert mid.risk_category == "Indeterminate"

    # Exact upper cutoff boundary -> Indeterminate
    boundary_high = interpret_fib4(score=2.67, age=age)
    assert boundary_high.risk_category == "Indeterminate"

    # Strictly above upper cutoff -> High Risk
    high = interpret_fib4(score=2.67001, age=age)
    assert high.risk_category == "High Risk"

    extreme_high = interpret_fib4(score=5.50, age=age)
    assert extreme_high.risk_category == "High Risk"


# ---------------------------------------------------------------------------
# 3. Applicable Threshold Scheme for Age >= 65
# ---------------------------------------------------------------------------

def test_fib4_threshold_scheme_age_65_and_older():
    """
    For age >= 65:
    - Age-adjusted threshold scheme (McPherson et al.) applied.
    - Lower cutoff is 2.00 (instead of 1.30).
    - score < 2.00 -> Low Risk
    - 2.00 <= score <= 2.67 -> Indeterminate
    - score > 2.67 -> High Risk
    """
    elderly_age = 65.0

    # Score of 1.70: in adult <65 it would be Indeterminate, but for >=65 it is Low Risk!
    interp_170 = interpret_fib4(score=1.70, age=elderly_age)
    assert interp_170.risk_category == "Low Risk"
    assert interp_170.threshold_set.scheme_name == ELDERLY_ADJUSTED_THRESHOLDS.scheme_name
    assert interp_170.threshold_set.low_cutoff == 2.00
    assert interp_170.threshold_set.high_cutoff == 2.67

    # Just below 2.00 cutoff
    low = interpret_fib4(score=1.999, age=elderly_age)
    assert low.risk_category == "Low Risk"

    # Exact cutoff 2.00 -> Indeterminate
    boundary_low = interpret_fib4(score=2.00, age=elderly_age)
    assert boundary_low.risk_category == "Indeterminate"

    # Exact upper cutoff 2.67 -> Indeterminate
    boundary_high = interpret_fib4(score=2.67, age=elderly_age)
    assert boundary_high.risk_category == "Indeterminate"

    # Above 2.67 -> High Risk
    high = interpret_fib4(score=2.6701, age=elderly_age)
    assert high.risk_category == "High Risk"


# ---------------------------------------------------------------------------
# 4. Zero and Negative Values Rejection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ast_val", [0.0, -1.0, -42.5])
def test_reject_zero_and_negative_ast(ast_val):
    with pytest.raises(ValueError, match="AST must be strictly positive"):
        calculate_fib4(age=45.0, ast=ast_val, alt=30.0, platelets=200.0)


@pytest.mark.parametrize("alt_val", [0.0, -0.5, -35.0])
def test_reject_zero_and_negative_alt(alt_val):
    with pytest.raises(ValueError, match="ALT must be strictly positive"):
        calculate_fib4(age=45.0, ast=35.0, alt=alt_val, platelets=200.0)


@pytest.mark.parametrize("plat_val", [0.0, -5.0, -180.0])
def test_reject_zero_and_negative_platelets(plat_val):
    with pytest.raises(ValueError, match="Platelet count must be strictly positive"):
        calculate_fib4(age=45.0, ast=35.0, alt=30.0, platelets=plat_val)


# ---------------------------------------------------------------------------
# 5. Missing Required Inputs (No Coercion to Zero)
# ---------------------------------------------------------------------------

def test_reject_none_for_required_inputs():
    with pytest.raises(TypeError, match="cannot be None"):
        calculate_fib4(age=None, ast=35.0, alt=30.0, platelets=200.0)

    with pytest.raises(TypeError, match="cannot be None"):
        calculate_fib4(age=45.0, ast=None, alt=30.0, platelets=200.0)

    with pytest.raises(TypeError, match="cannot be None"):
        calculate_fib4(age=45.0, ast=35.0, alt=None, platelets=200.0)

    with pytest.raises(TypeError, match="cannot be None"):
        calculate_fib4(age=45.0, ast=35.0, alt=30.0, platelets=None)


# ---------------------------------------------------------------------------
# 6. NaN and Infinity Rejection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
def test_reject_nan_and_inf(bad_val):
    with pytest.raises(ValueError, match="cannot be"):
        calculate_fib4(age=bad_val, ast=35.0, alt=30.0, platelets=200.0)

    with pytest.raises(ValueError, match="cannot be"):
        calculate_fib4(age=45.0, ast=bad_val, alt=30.0, platelets=200.0)

    with pytest.raises(ValueError, match="cannot be"):
        calculate_fib4(age=45.0, ast=35.0, alt=bad_val, platelets=200.0)

    with pytest.raises(ValueError, match="cannot be"):
        calculate_fib4(age=45.0, ast=35.0, alt=30.0, platelets=bad_val)


# ---------------------------------------------------------------------------
# 7. Documented Adult Age Range Policy Validation
# ---------------------------------------------------------------------------

def test_adult_age_policy_boundaries():
    # Boundary tests for acceptable adult ages [18, 120]
    score_18 = calculate_fib4(age=18.0, ast=30.0, alt=25.0, platelets=250.0)
    assert score_18 > 0

    score_120 = calculate_fib4(age=120.0, ast=30.0, alt=25.0, platelets=250.0)
    assert score_120 > 0

    # Pediatric age (< 18) rejected with clear explanation
    with pytest.raises(ValueError, match="FIB-4 is validated for adult populations"):
        calculate_fib4(age=17.9, ast=30.0, alt=25.0, platelets=250.0)

    with pytest.raises(ValueError, match="FIB-4 is validated for adult populations"):
        calculate_fib4(age=12.0, ast=30.0, alt=25.0, platelets=250.0)

    # Implausible extreme age (> 120) rejected without silent clamping
    with pytest.raises(ValueError, match="FIB-4 is validated for adult populations"):
        calculate_fib4(age=121.0, ast=30.0, alt=25.0, platelets=250.0)

    with pytest.raises(ValueError, match="FIB-4 is validated for adult populations"):
        calculate_fib4(age=-5.0, ast=30.0, alt=25.0, platelets=250.0)


# ---------------------------------------------------------------------------
# 8. Combined calculate_and_interpret_fib4 Entrypoint
# ---------------------------------------------------------------------------

def test_calculate_and_interpret_fib4_end_to_end():
    result = calculate_and_interpret_fib4(age=50.0, ast=60.0, alt=40.0, platelets=150.0)
    # expected = (50 * 60) / (150 * sqrt(40)) = 3000 / (150 * 6.324555) = 3.162277...
    assert pytest.approx(result.score, abs=1e-2) == 3.16
    assert result.score_display == 3.16
    assert result.risk_category == "High Risk"
    assert "FIB-4 of 3.16 exceeds" in result.interpretation

    as_dict = result.to_dict()
    assert isinstance(as_dict, dict)
    assert as_dict["score"] == result.score
    assert as_dict["risk_category"] == "High Risk"
    assert as_dict["threshold_set"]["low_cutoff"] == 1.30
