"""Tests for natural language to cron generator."""

import pytest
from cron_doctor.generator import natural_to_cron


def test_natural_to_cron():
    assert natural_to_cron("every minute") == "* * * * *"
    assert natural_to_cron("every 5 minutes") == "*/5 * * * *"
    assert natural_to_cron("every 30 seconds") == "*/30 * * * * *"
    assert natural_to_cron("every hour") == "0 * * * *"
    assert natural_to_cron("every 3 hours") == "0 */3 * * *"
    assert natural_to_cron("every day") == "0 0 * * *"
    assert natural_to_cron("every day at 3am") == "0 3 * * *"
    assert natural_to_cron("every day at 14:30") == "30 14 * * *"
    assert natural_to_cron("daily at 2:30pm") == "30 14 * * *"
    assert natural_to_cron("every weekday at 9am") == "0 9 * * 1-5"
    assert natural_to_cron("every weekend at 10am") == "0 10 * * 0,6"
    assert natural_to_cron("every monday at 8am") == "0 8 * * 1"
    assert natural_to_cron("weekly") == "0 0 * * 0"
    assert natural_to_cron("monthly") == "0 0 1 * *"
    assert natural_to_cron("yearly") == "0 0 1 1 *"


def test_natural_to_cron_invalid():
    with pytest.raises(ValueError):
        natural_to_cron("random unsupported gibberish phrase")
