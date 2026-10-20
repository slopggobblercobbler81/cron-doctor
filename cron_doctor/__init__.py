"""cron-doctor: A high-speed CLI and library for parsing, explaining, linting, and simulating Cron schedules."""

from cron_doctor.explainer import explain_cron
from cron_doctor.generator import natural_to_cron
from cron_doctor.linter import LintIssue, LintReport, LintSeverity, lint_cron
from cron_doctor.parser import (
    CronExpression,
    CronField,
    CronSyntaxError,
    parse_cron,
)
from cron_doctor.schedule import (
    calculate_schedule_stats,
    export_icalendar,
    get_next_runs,
    matches,
)

__version__ = "0.1.0"

__all__ = [
    "parse_cron",
    "CronExpression",
    "CronField",
    "CronSyntaxError",
    "explain_cron",
    "get_next_runs",
    "matches",
    "calculate_schedule_stats",
    "export_icalendar",
    "natural_to_cron",
    "lint_cron",
    "LintReport",
    "LintIssue",
    "LintSeverity",
    "__version__",
]
