from cron_doctor.linter import lint_cron

def test_step_divisibility_warning():
    report = lint_cron("*/7 * * * *")
    codes = [i.code for i in report.issues]
    assert "STEP_NOT_DIVISIBLE" in codes

def test_step_divisible_clean():
    report = lint_cron("*/5 * * * *")
    codes = [i.code for i in report.issues]
    assert "STEP_NOT_DIVISIBLE" not in codes
