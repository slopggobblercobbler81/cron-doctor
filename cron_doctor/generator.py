"""Natural language to Cron expression generator."""

import re
from typing import Optional, Tuple

DAY_MAP = {
    "monday": "1", "mon": "1",
    "tuesday": "2", "tue": "2",
    "wednesday": "3", "wed": "3",
    "thursday": "4", "thu": "4",
    "friday": "5", "fri": "5",
    "saturday": "6", "sat": "6",
    "sunday": "0", "sun": "0",
}


def parse_time_component(time_str: str) -> Tuple[int, int]:
    """Parse time string like '3pm', '04:30', '14:00', '9:15am' into (hour, minute)."""
    s = time_str.strip().lower()
    if s in ("midnight", "12am", "12:00am"):
        return 0, 0
    if s in ("noon", "12pm", "12:00pm"):
        return 12, 0

    match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", s)
    if not match:
        raise ValueError(f"Could not parse time from '{time_str}'")

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    meridiem = match.group(3)

    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    return hour, minute


def natural_to_cron(phrase: str) -> str:
    """Convert natural language phrases to valid cron expressions."""
    p = phrase.strip().lower()

    # Direct keyword matches
    if p in ("every minute", "each minute"):
        return "* * * * *"
    if p in ("hourly", "every hour"):
        return "0 * * * *"
    if p in ("daily", "every day", "each day"):
        return "0 0 * * *"
    if p in ("weekly", "every week"):
        return "0 0 * * 0"
    if p in ("monthly", "every month"):
        return "0 0 1 * *"
    if p in ("yearly", "annually", "every year"):
        return "0 0 1 1 *"

    # "every N minutes"
    m_min = re.match(r"^every\s+(\d+)\s+min(?:ute)?s?$", p)
    if m_min:
        n = int(m_min.group(1))
        return f"*/{n} * * * *"

    # "every N seconds"
    m_sec = re.match(r"^every\s+(\d+)\s+sec(?:ond)?s?$", p)
    if m_sec:
        n = int(m_sec.group(1))
        return f"*/{n} * * * * *"

    # "every N hours"
    m_hr = re.match(r"^every\s+(\d+)\s+hours?$", p)
    if m_hr:
        n = int(m_hr.group(1))
        return f"0 */{n} * * *"

    # "every day at <time>" or "daily at <time>"
    m_daily_at = re.match(r"^(?:every\s+day|daily)\s+at\s+(.+)$", p)
    if m_daily_at:
        h, m = parse_time_component(m_daily_at.group(1))
        return f"{m} {h} * * *"

    # "every weekday at <time>"
    m_weekday = re.match(r"^every\s+weekday\s+at\s+(.+)$", p)
    if m_weekday:
        h, m = parse_time_component(m_weekday.group(1))
        return f"{m} {h} * * 1-5"

    # "every weekend at <time>"
    m_weekend = re.match(r"^every\s+weekend\s+at\s+(.+)$", p)
    if m_weekend:
        h, m = parse_time_component(m_weekend.group(1))
        return f"{m} {h} * * 0,6"

    # "every <day_name> at <time>"
    m_day = re.match(r"^every\s+([a-z]+)\s+at\s+(.+)$", p)
    if m_day and m_day.group(1) in DAY_MAP:
        dow = DAY_MAP[m_day.group(1)]
        h, m = parse_time_component(m_day.group(2))
        return f"{m} {h} * * {dow}"

    # "every month on day <N> at <time>"
    m_month_day = re.match(r"^every\s+month\s+on\s+(?:day\s+)?(\d+)(?:st|nd|rd|th)?\s+at\s+(.+)$", p)
    if m_month_day:
        dom = int(m_month_day.group(1))
        h, m = parse_time_component(m_month_day.group(2))
        return f"{m} {h} {dom} * *"

    raise ValueError(f"Could not convert phrase '{phrase}' into a cron expression.")
