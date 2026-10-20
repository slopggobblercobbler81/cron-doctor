"""Coverage boost tests for cron-doctor."""

from cron_doctor.explainer import explain_cron
from cron_doctor.generator import natural_to_cron
from cron_doctor.parser import parse_cron


def test_explainer_branches():
    # Step hours
    exp_step_hr = explain_cron("15 */3 * * *")
    assert "Every 3 hours at minute 15" in exp_step_hr

    # Multiple minutes
    exp_multi_min = explain_cron("10,20,30 * * * *")
    assert "Every hour at minutes 10, 20, 30" in exp_multi_min

    # Hour ranges
    exp_hr_range = explain_cron("0 9-12 * * *")
    assert "every hour from 09:00 AM to 12:00 PM" in exp_hr_range

    # Only month specified
    exp_month_only = explain_cron("0 0 * 5 *")
    assert "only in May" in exp_month_only

    # Three days of week
    exp_3_dow = explain_cron("0 0 * * 1,3,5")
    assert "Monday, Wednesday, and Friday" in exp_3_dow


def test_generator_branches():
    assert natural_to_cron("daily") == "0 0 * * *"
    assert natural_to_cron("hourly") == "0 * * * *"
    assert natural_to_cron("every day at noon") == "0 12 * * *"
    assert natural_to_cron("every day at midnight") == "0 0 * * *"
    assert natural_to_cron("every 4 hours") == "0 */4 * * *"
