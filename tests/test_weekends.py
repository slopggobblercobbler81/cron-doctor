from datetime import datetime
from cron_doctor.schedule import is_running_on_weekends

def test_is_running_on_weekends():
    # Saturday
    assert is_running_on_weekends(datetime(2026, 1, 3, 12, 0, 0)) is True
    # Monday
    assert is_running_on_weekends(datetime(2026, 1, 5, 12, 0, 0)) is False
