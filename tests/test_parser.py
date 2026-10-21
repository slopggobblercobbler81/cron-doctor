"""Tests for cron parser and tokenization."""

import pytest
from cron_doctor.parser import CronSyntaxError, parse_cron


def test_parse_standard_5_part():
    cron = parse_cron("*/15 9-17 1,15 * 1-5")
    assert cron.is_six_part is False
    assert cron.seconds is None
    assert cron.minutes.values == {0, 15, 30, 45}
    assert cron.hours.values == set(range(9, 18))
    assert cron.days_of_month.values == {1, 15}
    assert cron.months.values == set(range(1, 13))
    assert cron.days_of_week.values == {1, 2, 3, 4, 5}


def test_parse_extended_6_part():
    cron = parse_cron("30 */5 12 * * *")
    assert cron.is_six_part is True
    assert cron.seconds is not None
    assert cron.seconds.values == {30}
    assert cron.minutes.values == {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}
    assert cron.hours.values == {12}


def test_parse_macros():
    daily = parse_cron("@daily")
    assert daily.minutes.values == {0}
    assert daily.hours.values == {0}
    assert daily.days_of_month.is_wildcard is True

    hourly = parse_cron("@hourly")
    assert hourly.minutes.values == {0}
    assert hourly.hours.is_wildcard is True

    weekly = parse_cron("@weekly")
    assert weekly.days_of_week.values == {0}

    monthly = parse_cron("@monthly")
    assert monthly.days_of_month.values == {1}

    yearly = parse_cron("@yearly")
    assert yearly.days_of_month.values == {1}
    assert yearly.months.values == {1}


def test_parse_named_values():
    cron = parse_cron("0 0 * JAN,FEB,DEC MON-FRI")
    assert cron.months.values == {1, 2, 12}
    assert cron.days_of_week.values == {1, 2, 3, 4, 5}

    # Sunday as 7 or SUN
    cron_sun = parse_cron("0 0 * * 7")
    assert cron_sun.days_of_week.values == {0}
    cron_sun_name = parse_cron("0 0 * * SUN")
    assert cron_sun_name.days_of_week.values == {0}


def test_parse_to_dict():
    cron = parse_cron("0 12 * * *")
    d = cron.to_dict()
    assert d["raw"] == "0 12 * * *"
    assert d["is_six_part"] is False
    assert len(d["fields"]) == 5


def test_parse_errors():
    # Empty
    with pytest.raises(CronSyntaxError, match="empty"):
        parse_cron("")

    # Too few fields
    with pytest.raises(CronSyntaxError, match="Expected 5 or 6 fields"):
        parse_cron("1 2 3")

    # Too many fields
    with pytest.raises(CronSyntaxError, match="Expected 5 or 6 fields"):
        parse_cron("1 2 3 4 5 6 7")

    # Invalid number
    with pytest.raises(CronSyntaxError, match="Invalid value"):
        parse_cron("abc * * * *")

    # Out of bounds
    with pytest.raises(CronSyntaxError, match="out of bounds"):
        parse_cron("60 * * * *")

    # Inverted range
    with pytest.raises(CronSyntaxError, match="cannot exceed"):
        parse_cron("10-5 * * * *")

    # Invalid step
    with pytest.raises(CronSyntaxError, match="Invalid step"):
        parse_cron("*/abc * * * *")

    # Zero step
    with pytest.raises(CronSyntaxError, match="Step must be > 0"):
        parse_cron("*/0 * * * *")


def test_parse_step_values():
    """Verify validation and expansion of step values in cron fields."""
    # Step with range
    cron_range = parse_cron("10-30/5 * * * *")
    assert cron_range.minutes.values == {10, 15, 20, 25, 30}

    # Step with single offset base
    cron_offset = parse_cron("5/15 * * * *")
    assert cron_offset.minutes.values == {5, 20, 35, 50}

    # Step exceeding maximum bound
    cron_large = parse_cron("*/100 * * * *")
    assert cron_large.minutes.values == {0}

    # Negative step validation
    with pytest.raises(CronSyntaxError, match="Step must be > 0"):
        parse_cron("*/-5 * * * *")

    # Empty step validation
    with pytest.raises(CronSyntaxError, match="Invalid step"):
        parse_cron("*/ * * * *")


def test_parse_day_of_week_ranges_with_sunday_aliases():
    """Verify that ranges ending in 7 (Sunday alias) or SUN expand properly."""
    c1 = parse_cron("0 0 * * 5-7")
    assert c1.days_of_week.values == {0, 5, 6}

    c2 = parse_cron("0 0 * * 1-7")
    assert c2.days_of_week.values == {0, 1, 2, 3, 4, 5, 6}

    c3 = parse_cron("0 0 * * FRI-SUN")
    assert c3.days_of_week.values == {0, 5, 6}

    c4 = parse_cron("0 0 * * 7")
    assert c4.days_of_week.values == {0}
