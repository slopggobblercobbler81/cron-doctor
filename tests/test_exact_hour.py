from datetime import datetime
from cron_doctor.schedule import is_running_at_exact_hour

def test_is_running_at_exact_hour():
    assert is_running_at_exact_hour(datetime(2026, 1, 1, 14, 0, 0)) is True
    assert is_running_at_exact_hour(datetime(2026, 1, 1, 14, 15, 0)) is False
