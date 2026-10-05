"""Pure helpers (no Home Assistant imports), so they can be tested anywhere."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .const import MEAL_TYPES


def parse_timestamp(value: str | None) -> datetime | None:
    """ISO timestamp from Foodisco ('2026-10-05T17:04:57.5+00:00' or '…Z') → aware datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def last_meal(data: dict[str, Any] | None) -> tuple[str | None, datetime | None]:
    """(meal type, logged_at) of the last meal, or (None, None)."""
    meal = (data or {}).get("last_meal") or {}
    return meal.get("type"), parse_timestamp(meal.get("logged_at"))


def detect_new_meal(previous: dict[str, Any] | None, current: dict[str, Any]) -> str | None:
    """The meal type to fire an event for, or None.

    Only a meal logged AFTER the last one we saw counts, and never on the first
    refresh (previous is None): a restart or a first setup must not look like a meal,
    otherwise every reload would start whatever the user hung on it (the vacuum).
    """
    if previous is None:
        return None
    _, before = last_meal(previous)
    meal_type, after = last_meal(current)
    if after is None or meal_type not in MEAL_TYPES:
        return None
    if before is not None and after <= before:
        return None
    return meal_type
