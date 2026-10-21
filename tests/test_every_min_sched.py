from cron_doctor.schedule import is_every_minute_schedule

def test_is_every_minute_schedule():
    assert is_every_minute_schedule("* * * * *") is True
    assert is_every_minute_schedule("0 * * * *") is False
