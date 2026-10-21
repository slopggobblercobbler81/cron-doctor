from datetime import datetime
from cron_doctor.schedule import find_schedule_collisions

def test_find_schedule_collisions():
    base = datetime(2026, 1, 1, 0, 0, 0)
    collisions = find_schedule_collisions("0 * * * *", "0 */2 * * *", base, count=5)
    assert len(collisions) > 0
