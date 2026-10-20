"""Tests for cron English explainer."""

from cron_doctor.explainer import explain_cron
from cron_doctor.parser import parse_cron


def test_explain_common_patterns():
    assert explain_cron("* * * * *") == "Every minute"
    assert explain_cron("*/15 * * * *") == "Every 15 minutes"
    assert explain_cron("0 * * * *") == "Every hour at minute 0"
    assert explain_cron("30 4 * * *") == "At 04:30 AM"
    assert explain_cron("0 12 * * 1-5") == "At 12:00 PM, Monday through Friday"
    assert explain_cron("0 0 1,15 * *") == "At 12:00 AM, on the 1st, 15th of every month"
    assert explain_cron("0 0 1 1 *") == "At 12:00 AM, on the 1st of January"


def test_explain_macros():
    assert "Every year" in explain_cron("@yearly")
    assert "first day of every month" in explain_cron("@monthly")
    assert "Every Sunday" in explain_cron("@weekly")
    assert "Every day at midnight" in explain_cron("@daily")
    assert "Every hour at minute 0" in explain_cron("@hourly")


def test_explain_weekdays_and_weekends():
    assert "Monday through Friday" in explain_cron("0 9 * * 1-5")
    assert "on Saturday and Sunday" in explain_cron("0 9 * * 0,6")
    assert "only on Monday" in explain_cron("0 9 * * 1")
    assert "on Monday and Friday" in explain_cron("0 9 * * 1,5")


def test_explain_six_part_cron():
    assert "Every second" in explain_cron("* * * * * *")
    assert "Every 10 seconds" in explain_cron("*/10 * * * * *")
    assert "At second 30" in explain_cron("30 0 12 * * *")
