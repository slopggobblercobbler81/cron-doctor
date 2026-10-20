# cron-doctor 🕒🩺

[![CI](https://github.com/slopggobblercobbler81/cron-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/cron-doctor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](https://github.com/slopggobblercobbler81/cron-doctor)

**cron-doctor** is a high-speed CLI tool and Python library for parsing, explaining in fluent English, simulating execution timelines, and linting Cron expressions.

Zero third-party dependencies. Built purely on modern Python.

---

## 🌟 Key Features

- 🗣️ **Plain English Explanations**: Converts complex cron schedules (`*/15 9-17 * * 1-5`) into readable human explanations ("Every 15 minutes, every hour from 09:00 AM to 05:00 PM, Monday through Friday").
- ⏱️ **Next Run Simulator**: Computes exact upcoming execution datetimes with human-friendly countdowns (`in 15 min`, `in 2 hr 30 min`).
- 📅 **iCalendar (.ics) Export**: Export upcoming schedules directly into `.ics` files for Google Calendar, Apple Calendar, or Outlook.
- 💬 **Natural Language to Cron**: Converts human requests like "every weekday at 9am" or "every 10 minutes" directly into cron syntax.
- 🔬 **Smart Linter & Anti-Pattern Detection**: Detects common scheduler traps such as the "midnight thundering herd", runaway sub-minute loops, POSIX dual-day OR logic gotchas, and AWS EventBridge compatibility issues.
- 📜 **Crontab File Auditor**: Lint and audit entire system crontabs with syntax validation and schedule summaries.

---

## 📦 Installation

```bash
pip install cron-doctor
```

Or from source:
```bash
git clone https://github.com/slopggobblercobbler81/cron-doctor.git
cd cron-doctor
pip install .
```

---

## 🚀 Quickstart CLI

### 1. Explain Cron Expressions
```bash
# Translate cron to plain English
cron-doctor explain "*/15 9-17 * * 1-5"

# Output detailed token breakdown as JSON
cron-doctor explain "@weekly" --json
```

### 2. View Next Execution Runs
```bash
# List next 5 upcoming executions
cron-doctor next "0 2 * * *" -n 5

# Calculate upcoming runs in a specific timezone
cron-doctor next "0 9 * * 1-5" --tz America/New_York

# Export upcoming occurrences to iCalendar (.ics) file
cron-doctor next "30 14 1 * *" -n 12 --format ics -o schedule.ics
```

### 3. Check if a Datetime Matches Schedule
```bash
# Check if current timestamp matches schedule
cron-doctor match "0 * * * *" now

# Check specific ISO timestamp
cron-doctor match "0 9 * * 1" 2026-10-26T09:00:00
```

### 4. Generate Cron from Natural Language
```bash
cron-doctor generate "every weekday at 9:30am"
# Generated Cron:  30 9 * * 1-5
# Explanation:     At 09:30 AM, Monday through Friday

cron-doctor generate "every 15 minutes"
# Generated Cron:  */15 * * * *
```

### 5. Lint Cron Expressions for Subtle Traps
```bash
cron-doctor lint "* * * * *"
# [INFO] HIGH_FREQUENCY_MINUTES: Runs every minute.

cron-doctor lint "0 0 * * *"
# [INFO] MIDNIGHT_THUNDERING_HERD: Scheduled exactly at midnight (00:00)...

cron-doctor lint "0 0 13 * 5"
# [WARNING] DUAL_DAY_OR_LOGIC: Both Day-of-Month and Day-of-Week are restricted...
```

### 6. Audit an Entire Crontab File
```bash
cron-doctor crontab /etc/crontab
```

---

## 💻 Python Library Usage

### Explain and Parse
```python
from cron_doctor import parse_cron, explain_cron

cron = parse_cron("*/30 8-18 * * 1-5")
print(explain_cron(cron))
# "Every 30 minutes, every hour from 08:00 AM to 06:00 PM, Monday through Friday"
```

### Calculate Next Occurrences
```python
from cron_doctor import get_next_runs
from datetime import datetime

runs = get_next_runs("0 9 * * 1-5", count=3, start_time=datetime(2026, 1, 1, 0, 0))
for run in runs:
    print(run)
# 2026-01-01 09:00:00 (Thursday)
# 2026-01-02 09:00:00 (Friday)
# 2026-01-05 09:00:00 (Monday)
```

### Natural Language Generation
```python
from cron_doctor import natural_to_cron

expr = natural_to_cron("every day at 2:45pm")
print(expr)  # "45 14 * * *"
```

### Linting
```python
from cron_doctor import lint_cron

report = lint_cron("0 0 1,15 * 1")
for issue in report.issues:
    print(f"[{issue.severity.value}] {issue.code}: {issue.message}")
```

---

## 🧪 Testing

Run pytest suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=cron_doctor --cov-report=term-missing
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
