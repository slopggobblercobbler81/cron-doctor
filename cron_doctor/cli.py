"""Command line interface for cron-doctor."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cron_doctor import __version__
from cron_doctor.explainer import explain_cron
from cron_doctor.generator import natural_to_cron
from cron_doctor.linter import lint_cron
from cron_doctor.parser import CronSyntaxError, parse_cron
from cron_doctor.schedule import export_icalendar, get_next_runs, matches


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cron-doctor",
        description="cron-doctor: A high-speed CLI and library for parsing, explaining, linting, and simulating Cron schedules.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: explain
    explain_p = subparsers.add_parser(
        "explain",
        aliases=["desc", "parse"],
        help="Translate cron expression to plain English and display field breakdown.",
    )
    explain_p.add_argument("expression", help="Cron expression or macro (e.g., '*/15 * * * *', '@daily')")
    explain_p.add_argument("--json", action="store_true", help="Output breakdown as JSON")

    # Command: next
    next_p = subparsers.add_parser(
        "next",
        aliases=["runs", "upcoming"],
        help="Calculate and display upcoming execution runs.",
    )
    next_p.add_argument("expression", help="Cron expression or macro")
    next_p.add_argument("-n", "--count", type=int, default=5, help="Number of runs to compute (default: 5)")
    next_p.add_argument("--tz", help="Timezone name (e.g., 'UTC', 'America/New_York')")
    next_p.add_argument(
        "--format",
        choices=["terminal", "json", "ics"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    next_p.add_argument("-o", "--output", help="Write output to file instead of stdout")

    # Command: match
    match_p = subparsers.add_parser(
        "match",
        help="Check whether a specific datetime matches the cron schedule.",
    )
    match_p.add_argument("expression", help="Cron expression")
    match_p.add_argument("timestamp", nargs="?", default="now", help="ISO timestamp (or 'now')")

    # Command: generate
    gen_p = subparsers.add_parser(
        "generate",
        aliases=["from-text"],
        help="Convert human natural language phrase to a cron expression.",
    )
    gen_p.add_argument("phrase", help="Natural language phrase (e.g. 'every 5 minutes', 'every weekday at 9am')")

    # Command: lint
    lint_p = subparsers.add_parser(
        "lint",
        aliases=["check"],
        help="Inspect cron expression for performance traps, anti-patterns, and platform issues.",
    )
    lint_p.add_argument("expression", help="Cron expression")
    lint_p.add_argument("--fail-on-warning", action="store_true", help="Exit with code 1 if warnings are found")
    lint_p.add_argument("--json", action="store_true", help="Output lint report as JSON")

    # Command: crontab
    crontab_p = subparsers.add_parser(
        "crontab",
        help="Lint and summarize an entire crontab file.",
    )
    crontab_p.add_argument("file", help="Path to crontab file")

    return parser


def handle_explain(args: argparse.Namespace) -> int:
    try:
        cron = parse_cron(args.expression)
        desc = explain_cron(cron)
    except CronSyntaxError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        payload = cron.to_dict()
        payload["explanation"] = desc
        print(json.dumps(payload, indent=2))
        return 0

    print("=== Cron Doctor: Expression Breakdown ===")
    print(f"Raw Expression:  {cron.raw}")
    print(f"Explanation:     {desc}")
    print("\nField Details:")
    for f in cron.fields:
        vals_str = f.raw if len(f.values) > 10 else f"{f.raw} -> {f.sorted_values}"
        print(f"  • {f.name:<13} [{f.min_val}-{f.max_val}]: {vals_str}")
    return 0


def handle_next(args: argparse.Namespace) -> int:
    try:
        cron = parse_cron(args.expression)
        runs = get_next_runs(cron, count=args.count, tz_name=args.tz)
    except Exception as e:
        print(f"Error calculating next runs: {e}", file=sys.stderr)
        return 1

    if args.format == "json":
        data = {
            "expression": cron.raw,
            "timezone": args.tz or "local",
            "runs": [r.isoformat() for r in runs],
        }
        out_text = json.dumps(data, indent=2)
    elif args.format == "ics":
        out_text = export_icalendar(cron.raw, runs)
    else:
        now = datetime.now(runs[0].tzinfo if (runs and runs[0].tzinfo) else None)
        lines = [
            f"Upcoming {len(runs)} executions for '{cron.raw}':",
            f"Explanation: {explain_cron(cron)}",
            "",
        ]
        for i, dt in enumerate(runs, 1):
            delta = dt - now
            mins = int(delta.total_seconds() // 60)
            if mins < 60:
                rel = f"in {mins} min"
            elif mins < 1440:
                rel = f"in {mins // 60} hr {mins % 60} min"
            else:
                rel = f"in {mins // 1440} day(s)"
            lines.append(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} ({rel})")
        out_text = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(out_text, encoding="utf-8")
        print(f"Schedule written to: {args.output}")
    else:
        print(out_text)

    return 0


def handle_match(args: argparse.Namespace) -> int:
    try:
        cron = parse_cron(args.expression)
        if args.timestamp == "now":
            dt = datetime.now()
        else:
            dt = datetime.fromisoformat(args.timestamp)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    is_match = matches(cron, dt)
    if is_match:
        print(f"✔ MATCH: '{dt.isoformat()}' matches schedule '{cron.raw}'.")
        return 0
    else:
        print(f"✖ NO MATCH: '{dt.isoformat()}' does NOT match schedule '{cron.raw}'.")
        return 1


def handle_generate(args: argparse.Namespace) -> int:
    try:
        expr = natural_to_cron(args.phrase)
        print(f"Generated Cron:  {expr}")
        print(f"Explanation:     {explain_cron(expr)}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_lint(args: argparse.Namespace) -> int:
    try:
        report = lint_cron(args.expression)
    except CronSyntaxError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_terminal(use_color=sys.stdout.isatty()))

    if args.fail_on_warning and report.has_warnings:
        return 1
    return 0


def handle_crontab(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {args.file}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8").splitlines()
    print(f"=== Crontab Analysis: {args.file} ===")
    total_entries = 0
    errors = 0

    for line_num, line in enumerate(lines, 1):
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue

        parts = clean.split()
        # In a crontab file, line is: * * * * * command
        if len(parts) >= 6:
            cron_part = " ".join(parts[:5])
            cmd_part = " ".join(parts[5:])
        else:
            cron_part = parts[0]
            cmd_part = " ".join(parts[1:])

        total_entries += 1
        try:
            cron = parse_cron(cron_part)
            desc = explain_cron(cron)
            rep = lint_cron(cron)
            status_badge = "⚠" if rep.has_warnings else "✔"
            print(f"Line {line_num}: {status_badge} [{cron_part}] -> {cmd_part}")
            print(f"        Schedule: {desc}")
            if rep.has_warnings:
                for issue in rep.issues:
                    print(f"        Warning: {issue.message}")
        except Exception as e:
            errors += 1
            print(f"Line {line_num}: ✖ Invalid cron [{cron_part}]: {e}")

    print(f"\nAnalyzed {total_entries} scheduled job(s) ({errors} errors).")
    return 1 if errors > 0 else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command in ("explain", "desc", "parse"):
        return handle_explain(args)
    elif args.command in ("next", "runs", "upcoming"):
        return handle_next(args)
    elif args.command == "match":
        return handle_match(args)
    elif args.command in ("generate", "from-text"):
        return handle_generate(args)
    elif args.command in ("lint", "check"):
        return handle_lint(args)
    elif args.command == "crontab":
        return handle_crontab(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
