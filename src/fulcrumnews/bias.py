"""Lean bucketing and Blindspot computation — the heart of FulcrumNews.

Kept dependency-free (only the ``Lean``/``BlindspotType`` enums) so it is trivially
unit-testable and shared by the pipeline, templates, and seed roster.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models.enums import BlindspotType, Lean

# Map the 5-way lean onto the 3 buckets used by the bias bar.
BUCKET_OF: dict[Lean, str] = {
    Lean.LEFT: "left",
    Lean.LEAN_LEFT: "left",
    Lean.CENTER: "center",
    Lean.LEAN_RIGHT: "right",
    Lean.RIGHT: "right",
}


def bucket_of(lean: Lean) -> str:
    return BUCKET_OF[Lean(lean)]


@dataclass(frozen=True)
class BiasResult:
    left: int
    center: int
    right: int
    blindspot: BlindspotType

    @property
    def total(self) -> int:
        return self.left + self.center + self.right

    def share(self, bucket: str) -> float:
        if self.total == 0:
            return 0.0
        return getattr(self, bucket) / self.total


def compute_bias(
    outlet_leans: Iterable[Lean],
    *,
    min_sources: int = 2,
    min_share: float = 0.15,
) -> BiasResult:
    """Count DISTINCT-outlet leans into buckets and flag a blindspot.

    ``outlet_leans`` should be one entry per distinct outlet covering the story
    (de-duplicate syndicated wire copy before calling this). A side is a blindspot
    when it is under-covered (fewer than ``min_sources`` outlets OR less than
    ``min_share`` of coverage) while the *other* side is not, and the story has
    real coverage overall.
    """
    left = center = right = 0
    for lean in outlet_leans:
        b = bucket_of(lean)
        if b == "left":
            left += 1
        elif b == "center":
            center += 1
        else:
            right += 1

    total = left + center + right
    if total < min_sources:
        return BiasResult(left, center, right, BlindspotType.NONE)

    left_blind = left < min_sources or (left / total) < min_share
    right_blind = right < min_sources or (right / total) < min_share

    blindspot = BlindspotType.NONE
    if left_blind and not right_blind:
        blindspot = BlindspotType.LEFT
    elif right_blind and not left_blind:
        blindspot = BlindspotType.RIGHT

    return BiasResult(left, center, right, blindspot)
