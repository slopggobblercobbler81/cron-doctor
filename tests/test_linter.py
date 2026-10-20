"""Tests for cron linter and anti-pattern rules."""

import pytest
from cron_doctor.linter import LintSeverity, lint_cron


def test_clean_cron():
    report = lint_cron("15 4 * * 1-5")
    assert len(report.issues) == 0
    assert report.has_warnings is False
    assert "Clean cron expression" in report.to_terminal(use_color=False)


def test_high_frequency_warning():
    rep_sec = lint_cron("* * * * * *")
    assert any(i.code == "HIGH_FREQUENCY_SECONDS" for i in rep_sec.issues)

    rep_min = lint_cron("* * * * *")
    assert any(i.code == "HIGH_FREQUENCY_MINUTES" for i in rep_min.issues)


def test_midnight_thundering_herd():
    rep = lint_cron("0 0 * * *")
    assert any(i.code == "MIDNIGHT_THUNDERING_HERD" for i in rep.issues)


def test_dual_day_or_logic():
    # Both day of month (13) and day of week (5 = Friday)
    rep = lint_cron("0 0 13 * 5")
    assert any(i.code == "DUAL_DAY_OR_LOGIC" for i in rep.issues)
    assert any(i.code == "AWS_EVENTBRIDGE_INCOMPATIBLE" for i in rep.issues)


def test_impossible_calendar_dates():
    # Feb 30
    rep_feb = lint_cron("0 0 30 2 *")
    assert any(i.code == "IMPOSSIBLE_CALENDAR_DATE" for i in rep_feb.issues)

    # April 31
    rep_apr = lint_cron("0 0 31 4 *")
    assert any(i.code == "DAY_31_IN_30_DAY_MONTH" for i in rep_apr.issues)


def test_lint_report_to_dict_and_terminal():
    rep = lint_cron("0 0 13 * 5")
    d = rep.to_dict()
    assert d["issue_count"] > 0
    assert d["has_warnings"] is True

    term = rep.to_terminal(use_color=False)
    assert "DUAL_DAY_OR_LOGIC" in term
    assert "Recommendation" in term
