"""Tests for lean bucketing and Blindspot computation (pure logic, no network/DB)."""

from fulcrumnews.bias import bucket_of, compute_bias
from fulcrumnews.models.enums import BlindspotType, Lean


def test_bucket_mapping():
    assert bucket_of(Lean.LEFT) == "left"
    assert bucket_of(Lean.LEAN_LEFT) == "left"
    assert bucket_of(Lean.CENTER) == "center"
    assert bucket_of(Lean.LEAN_RIGHT) == "right"
    assert bucket_of(Lean.RIGHT) == "right"


def test_balanced_coverage_has_no_blindspot():
    leans = [Lean.LEFT, Lean.LEAN_LEFT, Lean.CENTER, Lean.LEAN_RIGHT, Lean.RIGHT]
    result = compute_bias(leans)
    assert result.left == 2
    assert result.center == 1
    assert result.right == 2
    assert result.blindspot == BlindspotType.NONE


def test_right_under_covered_flags_blindspot_for_right():
    # 3 left + 2 center, zero right → right is the blindspot
    leans = [Lean.LEFT, Lean.LEAN_LEFT, Lean.LEFT, Lean.CENTER, Lean.CENTER]
    result = compute_bias(leans)
    assert result.right == 0
    assert result.blindspot == BlindspotType.RIGHT


def test_left_under_covered_flags_blindspot_for_left():
    leans = [Lean.RIGHT, Lean.LEAN_RIGHT, Lean.CENTER, Lean.CENTER, Lean.RIGHT]
    result = compute_bias(leans)
    assert result.left == 0
    assert result.blindspot == BlindspotType.LEFT


def test_single_source_never_blindspot():
    result = compute_bias([Lean.LEFT], min_sources=2)
    assert result.blindspot == BlindspotType.NONE


def test_min_share_threshold():
    # 9 left + 1 right: right share = 0.1 < 0.15 AND right_count 1 < 2 → blindspot for right
    leans = [Lean.LEFT] * 9 + [Lean.RIGHT]
    result = compute_bias(leans, min_sources=2, min_share=0.15)
    assert result.blindspot == BlindspotType.RIGHT


def test_both_sides_thin_is_not_a_one_sided_blindspot():
    # center-dominated with one left and one right that both miss the threshold:
    # neither side is singled out, so no blindspot.
    leans = [Lean.CENTER] * 8 + [Lean.LEFT, Lean.RIGHT]
    result = compute_bias(leans, min_sources=2, min_share=0.15)
    assert result.blindspot == BlindspotType.NONE


def test_share_property():
    result = compute_bias([Lean.LEFT, Lean.LEFT, Lean.CENTER, Lean.RIGHT])
    assert result.total == 4
    assert abs(result.share("left") - 0.5) < 1e-9
