"""Human-readable English explainer for Cron expressions."""

from typing import List, Optional, Union

from cron_doctor.parser import CronExpression, CronField, parse_cron

MONTH_LABELS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

DAY_LABELS = {
    0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday",
    4: "Thursday", 5: "Friday", 6: "Saturday"
}


def explain_cron(expr: Union[str, CronExpression]) -> str:
    """Generate a fluent English explanation of a cron expression."""
    cron = parse_cron(expr) if isinstance(expr, str) else expr

    # Handle standard macros & common presets
    raw_lower = cron.raw.lower()
    if raw_lower in ("@yearly", "@annually"):
        return "Every year on January 1st at midnight (12:00 AM)"
    if raw_lower == "@monthly":
        return "On the first day of every month at midnight (12:00 AM)"
    if raw_lower == "@weekly":
        return "Every Sunday at midnight (12:00 AM)"
    if raw_lower in ("@daily", "@midnight"):
        return "Every day at midnight (12:00 AM)"
    if raw_lower == "@hourly":
        return "Every hour at minute 0"
    if raw_lower == "@minutely":
        return "Every minute"

    parts: List[str] = []

    # Seconds (if 6-part)
    sec_desc = _explain_seconds(cron.seconds) if cron.is_six_part and cron.seconds else ""

    # Time of day (hours and minutes)
    time_desc = _explain_time(cron.minutes, cron.hours, cron.seconds)

    # Days of Month and Months
    date_desc = _explain_date(cron.days_of_month, cron.months)

    # Days of Week
    dow_desc = _explain_day_of_week(cron.days_of_week)

    # Combine nicely
    if sec_desc and not time_desc:
        parts.append(sec_desc)
    elif time_desc:
        parts.append(time_desc)

    if date_desc:
        parts.append(date_desc)

    if dow_desc:
        parts.append(dow_desc)

    if not parts:
        return "Every minute"

    return ", ".join(parts)


def _explain_seconds(sec: CronField) -> str:
    if sec.raw == "*":
        return "Every second"
    if "/" in sec.raw and sec.raw.startswith("*/"):
        step = sec.raw.split("/")[1]
        return f"Every {step} seconds"
    if len(sec.values) == 1:
        val = next(iter(sec.values))
        return f"At second {val}"
    return f"At seconds {', '.join(str(s) for s in sec.sorted_values)}"


def _explain_time(min_f: CronField, hr_f: CronField, sec_f: Optional[CronField] = None) -> str:
    # Six-part cron sub-minute checks
    if sec_f and min_f.raw == "*" and hr_f.raw == "*":
        if sec_f.raw == "*":
            return "Every second"
        if "/" in sec_f.raw and sec_f.raw.startswith("*/"):
            step = sec_f.raw.split("/")[1]
            return f"Every {step} seconds"
        return _explain_seconds(sec_f)

    # Every minute
    if min_f.raw == "*" and hr_f.raw == "*":
        return "Every minute"

    # Every X minutes
    if "/" in min_f.raw and min_f.raw.startswith("*/") and hr_f.raw == "*":
        step = min_f.raw.split("/")[1]
        return f"Every {step} minutes"

    # Specific minutes, every hour
    if hr_f.raw == "*":
        if len(min_f.values) == 1:
            val = next(iter(min_f.values))
            return f"Every hour at minute {val}"
        return f"Every hour at minutes {', '.join(str(m) for m in min_f.sorted_values)}"

    # Specific time(s)
    if len(min_f.values) == 1 and len(hr_f.values) == 1:
        m = next(iter(min_f.values))
        h = next(iter(hr_f.values))
        s = next(iter(sec_f.values)) if (sec_f and len(sec_f.values) == 1) else None
        if s is not None and s != 0:
            return f"At {_format_ampm(h, m, s)}, At second {s}"
        return f"At {_format_ampm(h, m)}"

    # Step hours (e.g. */2)
    if "/" in hr_f.raw and hr_f.raw.startswith("*/"):
        step = hr_f.raw.split("/")[1]
        m = min_f.raw if min_f.raw != "*" else "0"
        return f"Every {step} hours at minute {m}"

    # Hour ranges or multiple hours
    hr_desc = _format_hours(hr_f)
    if min_f.raw == "0":
        return f"At minute 0 of {hr_desc}"
    if len(min_f.values) == 1:
        m = next(iter(min_f.values))
        return f"At minute {m} past {hr_desc}"

    return f"At minutes {', '.join(str(m) for m in min_f.sorted_values)} past {hr_desc}"


def _explain_date(dom_f: CronField, mon_f: CronField) -> str:
    dom_wild = dom_f.raw in ("*", "?")
    mon_wild = mon_f.raw in ("*", "?")

    if dom_wild and mon_wild:
        return ""

    if dom_wild and not mon_wild:
        months_str = ", ".join(MONTH_LABELS.get(m, str(m)) for m in mon_f.sorted_values)
        return f"only in {months_str}"

    if not dom_wild and mon_wild:
        days_str = ", ".join(_ordinal(d) for d in dom_f.sorted_values)
        return f"on the {days_str} of every month"

    days_str = ", ".join(_ordinal(d) for d in dom_f.sorted_values)
    months_str = ", ".join(MONTH_LABELS.get(m, str(m)) for m in mon_f.sorted_values)
    return f"on the {days_str} of {months_str}"


def _explain_day_of_week(dow_f: CronField) -> str:
    if dow_f.raw in ("*", "?"):
        return ""

    sorted_vals = dow_f.sorted_values
    if sorted_vals == [1, 2, 3, 4, 5]:
        return "Monday through Friday"
    if sorted_vals == [0, 6]:
        return "on Saturday and Sunday"

    names = [DAY_LABELS.get(d, str(d)) for d in sorted_vals]
    if len(names) == 1:
        return f"only on {names[0]}"
    if len(names) == 2:
        return f"on {names[0]} and {names[1]}"
    return f"on {', '.join(names[:-1])}, and {names[-1]}"


def _format_ampm(hour: int, minute: int, second: Optional[int] = None) -> str:
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    if second is not None:
        return f"{display_hour:02d}:{minute:02d}:{second:02d} {period}"
    return f"{display_hour:02d}:{minute:02d} {period}"


def _format_hours(hr_f: CronField) -> str:
    sorted_hrs = hr_f.sorted_values
    if len(sorted_hrs) == 1:
        return _format_ampm(sorted_hrs[0], 0)
    # Check if continuous range
    if sorted_hrs == list(range(sorted_hrs[0], sorted_hrs[-1] + 1)):
        start = _format_ampm(sorted_hrs[0], 0)
        end = _format_ampm(sorted_hrs[-1], 0)
        return f"every hour from {start} to {end}"

    formatted = [_format_ampm(h, 0) for h in sorted_hrs]
    return f"hours ({', '.join(formatted)})"


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
