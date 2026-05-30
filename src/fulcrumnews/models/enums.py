"""Shared enums for the FulcrumNews data model."""

from __future__ import annotations

from enum import IntEnum


class Lean(IntEnum):
    """Five-way political lean of an outlet (buckets to left/center/right)."""

    LEFT = 0
    LEAN_LEFT = 1
    CENTER = 2
    LEAN_RIGHT = 3
    RIGHT = 4

    @property
    def label(self) -> str:
        return {
            Lean.LEFT: "Left",
            Lean.LEAN_LEFT: "Lean Left",
            Lean.CENTER: "Center",
            Lean.LEAN_RIGHT: "Lean Right",
            Lean.RIGHT: "Right",
        }[self]

    @property
    def slug(self) -> str:
        return {
            Lean.LEFT: "left",
            Lean.LEAN_LEFT: "lean-left",
            Lean.CENTER: "center",
            Lean.LEAN_RIGHT: "lean-right",
            Lean.RIGHT: "right",
        }[self]


class BlindspotType(IntEnum):
    """Which side of the spectrum is under-covering a story."""

    NONE = 0
    LEFT = 1  # "Blindspot for the Left" — left under-covers
    RIGHT = 2  # "Blindspot for the Right" — right under-covers


class FeedType(IntEnum):
    RSS = 0
    GUARDIAN_API = 1
