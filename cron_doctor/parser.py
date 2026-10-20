"""Cron expression parsing and tokenization engine."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

MONTH_NAMES: Dict[str, int] = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}

DAY_NAMES: Dict[str, int] = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6
}

CRON_MACROS: Dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


class CronSyntaxError(ValueError):
    """Raised when a cron expression cannot be parsed or contains invalid values."""

    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name
        self.field_value = field_value


@dataclass
class CronField:
    name: str
    raw: str
    min_val: int
    max_val: int
    values: Set[int]

    @property
    def is_wildcard(self) -> bool:
        return self.raw in ("*", "?")

    @property
    def sorted_values(self) -> List[int]:
        return sorted(list(self.values))

    def matches(self, value: int) -> bool:
        if self.name == "day_of_week" and value == 7:
            value = 0
        return value in self.values


class CronExpression:
    """Represents a validated and parsed Cron schedule."""

    def __init__(
        self,
        raw: str,
        fields: List[CronField],
        is_six_part: bool = False,
    ):
        self.raw = raw
        self.fields = fields
        self.is_six_part = is_six_part

        if is_six_part:
            self.seconds = fields[0]
            self.minutes = fields[1]
            self.hours = fields[2]
            self.days_of_month = fields[3]
            self.months = fields[4]
            self.days_of_week = fields[5]
        else:
            self.seconds = None
            self.minutes = fields[0]
            self.hours = fields[1]
            self.days_of_month = fields[2]
            self.months = fields[3]
            self.days_of_week = fields[4]

    def to_dict(self) -> Dict[str, object]:
        return {
            "raw": self.raw,
            "is_six_part": self.is_six_part,
            "fields": [
                {
                    "name": f.name,
                    "raw": f.raw,
                    "min": f.min_val,
                    "max": f.max_val,
                    "match_count": len(f.values),
                    "values": f.sorted_values,
                }
                for f in self.fields
            ],
        }


def parse_cron(expression: str) -> CronExpression:
    """Parse standard 5-part or 6-part cron expression or macro."""
    trimmed = expression.strip()
    if not trimmed:
        raise CronSyntaxError("Cron expression cannot be empty.")

    # Expand macro if applicable
    lower = trimmed.lower()
    if lower in CRON_MACROS:
        raw_expr = CRON_MACROS[lower]
        original_macro = trimmed
    else:
        raw_expr = trimmed
        original_macro = None

    parts = raw_expr.split()
    if len(parts) == 5:
        # Standard: minute hour day-of-month month day-of-week
        is_six = False
        field_specs = [
            ("minute", parts[0], 0, 59),
            ("hour", parts[1], 0, 23),
            ("day_of_month", parts[2], 1, 31),
            ("month", parts[3], 1, 12),
            ("day_of_week", parts[4], 0, 6),
        ]
    elif len(parts) == 6:
        # Extended: second minute hour day-of-month month day-of-week
        is_six = True
        field_specs = [
            ("second", parts[0], 0, 59),
            ("minute", parts[1], 0, 59),
            ("hour", parts[2], 0, 23),
            ("day_of_month", parts[3], 1, 31),
            ("month", parts[4], 1, 12),
            ("day_of_week", parts[5], 0, 6),
        ]
    else:
        raise CronSyntaxError(
            f"Expected 5 or 6 fields, got {len(parts)} in '{expression}'.",
            field_name="format",
        )

    parsed_fields: List[CronField] = []
    for name, part_str, min_v, max_v in field_specs:
        values = _parse_field_tokens(part_str, name, min_v, max_v)
        parsed_fields.append(
            CronField(
                name=name,
                raw=part_str,
                min_val=min_v,
                max_val=max_v,
                values=values,
            )
        )

    return CronExpression(
        raw=original_macro or trimmed,
        fields=parsed_fields,
        is_six_part=is_six,
    )


def _parse_field_tokens(token: str, field_name: str, min_val: int, max_val: int) -> Set[int]:
    """Parse comma-separated sub-expressions for a single cron field."""
    result: Set[int] = set()

    for sub in token.split(","):
        sub = sub.strip()
        if not sub:
            raise CronSyntaxError(f"Empty sub-token in {field_name}: '{token}'", field_name, token)

        result.update(_parse_single_sub(sub, field_name, min_val, max_val))

    if not result:
        raise CronSyntaxError(f"No valid values produced for {field_name} from '{token}'", field_name, token)

    return result


def _parse_single_sub(sub: str, field_name: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a single sub-expression with optional step and range."""
    # Handle step syntax
    step = 1
    base = sub
    if "/" in sub:
        parts = sub.split("/", 1)
        base = parts[0]
        step_str = parts[1]
        try:
            step = int(step_str)
        except ValueError:
            raise CronSyntaxError(f"Invalid step '{step_str}' in {field_name}", field_name, sub)
        if step <= 0:
            raise CronSyntaxError(f"Step must be > 0 in {field_name}, got '{step}'", field_name, sub)

    # Base could be *, ?, number, or range
    if base in ("*", "?"):
        start = min_val
        end = max_val
    elif "-" in base:
        range_parts = base.split("-", 1)
        start = _convert_value(range_parts[0], field_name, min_val, max_val)
        end = _convert_value(range_parts[1], field_name, min_val, max_val)
        if start > end:
            raise CronSyntaxError(
                f"Range start ({start}) cannot exceed end ({end}) in {field_name}",
                field_name,
                sub,
            )
    else:
        # Single value with optional step
        val = _convert_value(base, field_name, min_val, max_val)
        if "/" in sub:
            start = val
            end = max_val
        else:
            return {val}

    matched = set()
    curr = start
    while curr <= end:
        matched.add(curr)
        curr += step

    return matched


def _convert_value(val_str: str, field_name: str, min_val: int, max_val: int) -> int:
    """Normalize text names (e.g. MON, JAN) or parse integer, validating range."""
    clean = val_str.strip().upper()

    if field_name == "month" and clean in MONTH_NAMES:
        return MONTH_NAMES[clean]

    if field_name == "day_of_week":
        if clean in DAY_NAMES:
            return DAY_NAMES[clean]
        if clean == "7":
            return 0  # 7 is Sunday, normalized to 0

    try:
        val = int(clean)
    except ValueError:
        raise CronSyntaxError(
            f"Invalid value '{val_str}' for field {field_name}.",
            field_name=field_name,
            field_value=val_str,
        )

    # For day_of_week, 7 is valid (alias for 0)
    effective_max = 7 if field_name == "day_of_week" else max_val
    if val < min_val or val > effective_max:
        raise CronSyntaxError(
            f"Value {val} out of bounds [{min_val}-{max_val}] for {field_name}.",
            field_name=field_name,
            field_value=str(val),
        )

    if field_name == "day_of_week" and val == 7:
        return 0

    return val
