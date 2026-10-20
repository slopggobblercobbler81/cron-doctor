"""Linting and anti-pattern detection for Cron expressions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

from cron_doctor.parser import CronExpression, parse_cron


class LintSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class LintIssue:
    code: str
    severity: LintSeverity
    message: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation,
        }


class LintReport:
    """Aggregated findings from cron schedule linting."""

    def __init__(self, issues: List[LintIssue]):
        self.issues = issues

    @property
    def has_warnings(self) -> bool:
        return any(i.severity in (LintSeverity.WARNING, LintSeverity.ERROR) for i in self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_count": len(self.issues),
            "has_warnings": self.has_warnings,
            "issues": [i.to_dict() for i in self.issues],
        }

    def to_terminal(self, use_color: bool = True) -> str:
        YELLOW = "\033[93m" if use_color else ""
        CYAN = "\033[96m" if use_color else ""
        GREEN = "\033[92m" if use_color else ""
        BOLD = "\033[1m" if use_color else ""
        RESET = "\033[0m" if use_color else ""

        if not self.issues:
            return f"{GREEN}{BOLD}✔ Clean cron expression:{RESET} No anti-patterns or compatibility warnings found."

        lines = [
            f"{BOLD}=== Cron Doctor Lint Analysis ==={RESET}",
            f"Found {len(self.issues)} issue(s):",
            "",
        ]

        for idx, issue in enumerate(self.issues, 1):
            badge = f"{YELLOW}[WARNING]{RESET}" if issue.severity == LintSeverity.WARNING else f"{CYAN}[INFO]{RESET}"
            lines.append(f"  {idx}. {badge} {BOLD}{issue.code}{RESET}: {issue.message}")
            lines.append(f"     💡 Recommendation: {issue.recommendation}")
            lines.append("")

        return "\n".join(lines)


def lint_cron(expr: Union[str, CronExpression]) -> LintReport:
    """Analyze cron expression for anti-patterns and platform gotchas."""
    cron = parse_cron(expr) if isinstance(expr, str) else expr
    issues: List[LintIssue] = []

    # 1. High frequency check
    if cron.is_six_part and cron.seconds and cron.seconds.raw == "*":
        issues.append(
            LintIssue(
                code="HIGH_FREQUENCY_SECONDS",
                severity=LintSeverity.WARNING,
                message="Runs every second. This can easily saturate server CPU or cause thread exhaustion.",
                recommendation="Consider increasing interval to at least every minute or use a persistent worker daemon.",
            )
        )
    elif cron.minutes.raw == "*" and cron.hours.raw == "*":
        issues.append(
            LintIssue(
                code="HIGH_FREQUENCY_MINUTES",
                severity=LintSeverity.INFO,
                message="Runs every minute.",
                recommendation="Verify if sub-hourly execution is truly necessary to prevent unnecessary database load.",
            )
        )

    # 2. Midnight thundering herd
    if cron.minutes.raw == "0" and cron.hours.raw == "0":
        issues.append(
            LintIssue(
                code="MIDNIGHT_THUNDERING_HERD",
                severity=LintSeverity.INFO,
                message="Scheduled exactly at midnight (00:00). High contention with OS log rotations, backups, and cron jobs.",
                recommendation="Add jitter or stagger start time to an off-peak minute (e.g., 03:17).",
            )
        )

    # 3. Both Day-of-Month and Day-of-Week specified (POSIX OR rule gotcha)
    dom_restricted = not cron.days_of_month.is_wildcard
    dow_restricted = not cron.days_of_week.is_wildcard

    if dom_restricted and dow_restricted:
        issues.append(
            LintIssue(
                code="DUAL_DAY_OR_LOGIC",
                severity=LintSeverity.WARNING,
                message="Both Day-of-Month and Day-of-Week are restricted. POSIX cron executes when EITHER matches (OR logic), NOT both (AND).",
                recommendation="If you intended AND logic (e.g. Friday the 13th), handle the day check inside the script itself.",
            )
        )

    # 4. February 30/31 impossible dates
    if 2 in cron.months.values:
        impossible_feb = {30, 31} & cron.days_of_month.values
        if impossible_feb and cron.months.values == {2}:
            issues.append(
                LintIssue(
                    code="IMPOSSIBLE_CALENDAR_DATE",
                    severity=LintSeverity.WARNING,
                    message=f"February does not have days {sorted(list(impossible_feb))}.",
                    recommendation="Adjust Day-of-Month to <= 29.",
                )
            )

    # 5. Months with only 30 days
    months_with_30 = {4, 6, 9, 11}  # Apr, Jun, Sep, Nov
    if cron.days_of_month.values == {31} and cron.months.values.issubset(months_with_30):
        issues.append(
            LintIssue(
                code="DAY_31_IN_30_DAY_MONTH",
                severity=LintSeverity.WARNING,
                message="Day 31 specified for months that only have 30 days.",
                recommendation="Change day of month to 30 or check month selection.",
            )
        )

    # 6. AWS CloudWatch / EventBridge compatibility check
    if not cron.days_of_month.is_wildcard and not cron.days_of_week.is_wildcard:
        issues.append(
            LintIssue(
                code="AWS_EVENTBRIDGE_INCOMPATIBLE",
                severity=LintSeverity.INFO,
                message="AWS EventBridge requires '?' in either day-of-month or day-of-week field.",
                recommendation="Replace either day-of-month or day-of-week with '?' when deploying to AWS EventBridge.",
            )
        )

    return LintReport(issues=issues)
