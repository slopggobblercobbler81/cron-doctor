"""Tests for schedule simulation, matches, and iCalendar export."""

from datetime import datetime
import pytest

from cron_doctor.schedule import (
    calculate_schedule_stats,
    export_icalendar,
    get_next_runs,
    matches,
)


def test_matches():
    # 2026-10-20 09:30:00 (Tuesday)
    dt_tue = datetime(2026, 10, 20, 9, 30, 0)

    assert matches("30 9 * * *", dt_tue) is True
    assert matches("30 9 * * 2", dt_tue) is True   # Tuesday = 2
    assert matches("30 9 * * 1", dt_tue) is False  # Monday = 1
    assert matches("0 9 * * *", dt_tue) is False   # minute mismatch
    assert matches("30 10 * * *", dt_tue) is False  # hour mismatch

    # 6-part cron
    assert matches("0 30 9 * * *", dt_tue) is True
    assert matches("15 30 9 * * *", dt_tue) is False


def test_get_next_runs():
    start = datetime(2026, 1, 1, 0, 0, 0)
    runs = get_next_runs("0 9 * * *", count=3, start_time=start)

    assert len(runs) == 3
    assert runs[0] == datetime(2026, 1, 1, 9, 0, 0)
    assert runs[1] == datetime(2026, 1, 2, 9, 0, 0)
    assert runs[2] == datetime(2026, 1, 3, 9, 0, 0)


def test_get_next_runs_month_skipping():
    # Only in December
    start = datetime(2026, 1, 1, 0, 0, 0)
    runs = get_next_runs("0 0 1 12 *", count=2, start_time=start)

    assert len(runs) == 2
    assert runs[0] == datetime(2026, 12, 1, 0, 0, 0)
    assert runs[1] == datetime(2027, 12, 1, 0, 0, 0)


def test_get_next_runs_six_part():
    start = datetime(2026, 1, 1, 0, 0, 0)
    runs = get_next_runs("*/20 * * * * *", count=4, start_time=start)

    assert len(runs) == 4
    assert runs[0] == datetime(2026, 1, 1, 0, 0, 20)
    assert runs[1] == datetime(2026, 1, 1, 0, 0, 40)
    assert runs[2] == datetime(2026, 1, 1, 0, 1, 0)
    assert runs[3] == datetime(2026, 1, 1, 0, 1, 20)


def test_calculate_schedule_stats():
    runs = [
        datetime(2026, 1, 1, 0, 0, 0),
        datetime(2026, 1, 1, 1, 0, 0),
        datetime(2026, 1, 1, 2, 0, 0),
    ]
    stats = calculate_schedule_stats(runs)
    assert stats["runs_count"] == 3
    assert stats["min_interval_seconds"] == 3600
    assert stats["max_interval_seconds"] == 3600
    assert stats["avg_interval_seconds"] == 3600

    # Under 2 runs
    assert calculate_schedule_stats([runs[0]])["runs_count"] == 1


def test_export_icalendar():
    runs = [
        datetime(2026, 1, 1, 9, 0, 0),
        datetime(2026, 1, 2, 9, 0, 0),
    ]
    ics = export_icalendar("0 9 * * *", runs)
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "END:VCALENDAR" in ics
    assert "20260101T090000Z" in ics
