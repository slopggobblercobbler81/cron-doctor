from datetime import datetime
from cron_doctor.schedule import get_next_run_iso

def test_get_next_run_iso():
    base = datetime(2026, 1, 1, 0, 0, 0)
    iso_str = get_next_run_iso("0 1 * * *", start_time=base)
    assert iso_str is not None
    assert "2026-01-01T01:00:00" in iso_str
