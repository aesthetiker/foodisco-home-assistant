from datetime import datetime, timezone

from custom_components.foodisco.logic import detect_new_meal, last_meal, parse_timestamp


def status(meal_type=None, logged_at=None):
    return {"last_meal": {"type": meal_type, "logged_at": logged_at} if meal_type else None}


def test_parse_timestamp_accepts_the_formats_foodisco_sends():
    assert parse_timestamp("2026-10-05T17:04:57.588555+00:00") == datetime(2026, 10, 5, 17, 4, 57, 588555, tzinfo=timezone.utc)
    assert parse_timestamp("2026-10-05T17:04:57Z") == datetime(2026, 10, 5, 17, 4, 57, tzinfo=timezone.utc)
    assert parse_timestamp(None) is None
    assert parse_timestamp("not a date") is None


def test_last_meal_handles_a_day_without_meals():
    assert last_meal({"last_meal": None}) == (None, None)
    assert last_meal(None) == (None, None)


def test_the_first_refresh_never_fires_an_event():
    # A restart or a fresh setup is not a meal.
    assert detect_new_meal(None, status("dinner", "2026-10-05T17:00:00Z")) is None


def test_a_newer_meal_fires_with_its_type():
    before = status("lunch", "2026-10-05T11:00:00Z")
    after = status("dinner", "2026-10-05T17:00:00Z")
    assert detect_new_meal(before, after) == "dinner"


def test_the_same_meal_again_does_not_fire():
    s = status("dinner", "2026-10-05T17:00:00Z")
    assert detect_new_meal(s, s) is None


def test_an_older_entry_appearing_does_not_fire():
    # e.g. the newest meal was deleted and an earlier one is now the latest
    assert detect_new_meal(status("dinner", "2026-10-05T17:00:00Z"), status("lunch", "2026-10-05T11:00:00Z")) is None


def test_the_first_meal_of_the_day_fires():
    assert detect_new_meal(status(), status("breakfast", "2026-10-06T07:00:00Z")) == "breakfast"


def test_a_meal_that_disappears_does_not_fire():
    assert detect_new_meal(status("dinner", "2026-10-05T17:00:00Z"), status()) is None


def test_an_unknown_meal_type_does_not_fire():
    assert detect_new_meal(status(), status("midnight_feast", "2026-10-06T00:30:00Z")) is None
