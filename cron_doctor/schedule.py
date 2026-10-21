"""Cron schedule simulation, occurrence prediction, and calendar export."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

from cron_doctor.parser import CronExpression, parse_cron


def matches(expr: Union[str, CronExpression], dt: datetime) -> bool:
    """Check if a given datetime matches the cron schedule."""
    cron = parse_cron(expr) if isinstance(expr, str) else expr

    # Check seconds if 6-part cron
    if cron.is_six_part and cron.seconds:
        if not cron.seconds.matches(dt.second):
            return False

    # Check minute
    if not cron.minutes.matches(dt.minute):
        return False

    # Check hour
    if not cron.hours.matches(dt.hour):
        return False

    # Check month
    if not cron.months.matches(dt.month):
        return False

    # Check day of month & day of week (standard POSIX rule: OR if both restricted)
    dom_wild = cron.days_of_month.is_wildcard
    dow_wild = cron.days_of_week.is_wildcard

    # Python weekday(): Monday is 0, Sunday is 6.
    # Standard cron day_of_week: Sunday is 0, Monday is 1 ... Saturday is 6
    py_dow = (dt.weekday() + 1) % 7

    dom_match = cron.days_of_month.matches(dt.day)
    dow_match = cron.days_of_week.matches(py_dow)

    if dom_wild and dow_wild:
        return True
    if not dom_wild and not dow_wild:
        return dom_match or dow_match
    if not dom_wild:
        return dom_match
    return dow_match


def get_next_runs(
    expr: Union[str, CronExpression],
    count: int = 5,
    start_time: Optional[datetime] = None,
    tz_name: Optional[str] = None,
    max_search_days: int = 366 * 4,
) -> List[datetime]:
    """Calculate the next `count` upcoming execution datetimes starting after `start_time`."""
    cron = parse_cron(expr) if isinstance(expr, str) else expr

    # Determine starting datetime and timezone
    if tz_name and ZoneInfo:
        tz = ZoneInfo(tz_name)
    else:
        tz = None

    if start_time is None:
        curr = datetime.now(tz=tz)
    else:
        curr = start_time.astimezone(tz) if (tz and start_time.tzinfo) else (start_time if not tz else start_time.replace(tzinfo=tz))

    # Advance curr to next eligible minute (or second if 6-part)
    if cron.is_six_part:
        curr = curr.replace(microsecond=0) + timedelta(seconds=1)
        step = timedelta(seconds=1)
    else:
        curr = curr.replace(second=0, microsecond=0) + timedelta(minutes=1)
        step = timedelta(minutes=1)

    results: List[datetime] = []
    end_limit = curr + timedelta(days=max_search_days)

    # Search loop
    while len(results) < count and curr <= end_limit:
        # Fast skipping: if month doesn't match, skip to 1st of next month
        if not cron.months.matches(curr.month):
            # Advance to start of next month
            if curr.month == 12:
                curr = curr.replace(year=curr.year + 1, month=1, day=1, hour=0, minute=0, second=0)
            else:
                curr = curr.replace(month=curr.month + 1, day=1, hour=0, minute=0, second=0)
            continue

        # If day doesn't match, skip to next day at 00:00
        dom_wild = cron.days_of_month.is_wildcard
        dow_wild = cron.days_of_week.is_wildcard
        py_dow = (curr.weekday() + 1) % 7
        dom_m = cron.days_of_month.matches(curr.day)
        dow_m = cron.days_of_week.matches(py_dow)

        day_ok = (dom_m or dow_m) if (not dom_wild and not dow_wild) else (dom_m if not dom_wild else dow_m if not dow_wild else True)
        if not day_ok:
            curr = (curr + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            continue

        # If hour doesn't match, skip to next hour at minute 0
        if not cron.hours.matches(curr.hour):
            curr = (curr + timedelta(hours=1)).replace(minute=0, second=0)
            continue

        # If minute doesn't match (for 6-part) or standard
        if not cron.minutes.matches(curr.minute):
            curr = (curr + timedelta(minutes=1)).replace(second=0)
            continue

        # If 6-part, check second
        if cron.is_six_part and cron.seconds and not cron.seconds.matches(curr.second):
            curr += step
            continue

        results.append(curr)
        curr += step

    return results


def calculate_schedule_stats(runs: List[datetime]) -> Dict[str, object]:
    """Calculate frequency metrics across simulated execution runs."""
    if len(runs) < 2:
        return {
            "runs_count": len(runs),
            "min_interval_seconds": 0,
            "max_interval_seconds": 0,
            "avg_interval_seconds": 0,
        }

    intervals = [
        (runs[i + 1] - runs[i]).total_seconds()
        for i in range(len(runs) - 1)
    ]

    return {
        "runs_count": len(runs),
        "min_interval_seconds": min(intervals),
        "max_interval_seconds": max(intervals),
        "avg_interval_seconds": sum(intervals) / len(intervals),
    }


def export_icalendar(expr: Union[str, CronExpression], runs: List[datetime], summary: str = "Cron Job Run") -> str:
    """Generate RFC 5545 iCalendar content for scheduled runs."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//cron-doctor//NONSGML v0.1.0//EN",
        "CALSCALE:GREGORIAN",
    ]

    for idx, dt in enumerate(runs, 1):
        dt_utc = dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo and ZoneInfo else dt
        dt_str = dt_utc.strftime("%Y%m%dT%H%M%SZ")
        end_str = (dt_utc + timedelta(minutes=5)).strftime("%Y%m%dT%H%M%SZ")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:cron-doctor-{idx}-{dt_str}@localhost",
            f"DTSTAMP:{dt_str}",
            f"DTSTART:{dt_str}",
            f"DTEND:{end_str}",
            f"SUMMARY:{summary} (#{idx})",
            f"DESCRIPTION:Scheduled run of cron '{expr}'",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def find_schedule_collisions(expr1: str, expr2: str, start_dt, count: int = 10):
    """Returns timestamps where two schedules run at the exact same minute."""
    runs1 = set(get_next_runs(expr1, count=count, start_time=start_dt))
    runs2 = set(get_next_runs(expr2, count=count, start_time=start_dt))
    return sorted(list(runs1 & runs2))
