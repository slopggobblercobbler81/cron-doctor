"""Tests for cron-doctor CLI interface."""

import json
from pathlib import Path
import pytest

from cron_doctor.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "cron-doctor" in captured.out


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "cron-doctor" in captured.out


def test_cli_no_args(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out


def test_cli_explain(capsys):
    assert main(["explain", "*/15 * * * *"]) == 0
    captured = capsys.readouterr()
    assert "Every 15 minutes" in captured.out

    # JSON output
    assert main(["explain", "@daily", "--json"]) == 0
    captured_json = capsys.readouterr()
    d = json.loads(captured_json.out)
    assert d["raw"] == "@daily"
    assert "explanation" in d

    # Error handling
    assert main(["explain", "bad * * * *"]) == 1


def test_cli_next(tmp_path: Path, capsys):
    assert main(["next", "0 9 * * 1-5", "-n", "3"]) == 0
    captured = capsys.readouterr()
    assert "Upcoming 3 executions" in captured.out

    # Format JSON
    assert main(["next", "0 9 * * 1-5", "-n", "2", "--format", "json"]) == 0
    captured_json = capsys.readouterr()
    d = json.loads(captured_json.out)
    assert len(d["runs"]) == 2

    # Format ICS to file
    out_ics = tmp_path / "sched.ics"
    assert main(["next", "0 9 * * *", "-n", "2", "--format", "ics", "-o", str(out_ics)]) == 0
    assert out_ics.is_file()
    assert "BEGIN:VCALENDAR" in out_ics.read_text(encoding="utf-8")


def test_cli_match(capsys):
    # Match
    assert main(["match", "* * * * *", "2026-10-20T10:00:00"]) == 0
    captured = capsys.readouterr()
    assert "MATCH" in captured.out

    # No match
    assert main(["match", "0 12 * * *", "2026-10-20T10:00:00"]) == 1
    captured_no = capsys.readouterr()
    assert "NO MATCH" in captured_no.out


def test_cli_generate(capsys):
    assert main(["generate", "every 5 minutes"]) == 0
    captured = capsys.readouterr()
    assert "*/5 * * * *" in captured.out

    # Invalid phrase
    assert main(["generate", "nonsense phrase"]) == 1


def test_cli_lint(capsys):
    assert main(["lint", "0 0 13 * 5"]) == 0
    captured = capsys.readouterr()
    assert "DUAL_DAY_OR_LOGIC" in captured.out

    # JSON output
    assert main(["lint", "0 0 13 * 5", "--json"]) == 0
    captured_json = capsys.readouterr()
    d = json.loads(captured_json.out)
    assert d["has_warnings"] is True

    # Fail on warning
    assert main(["lint", "0 0 13 * 5", "--fail-on-warning"]) == 1


def test_cli_crontab(tmp_path: Path, capsys):
    crontab_file = tmp_path / "sample.cron"
    crontab_file.write_text(
        "# Nightly backup\n"
        "0 2 * * * /usr/local/bin/backup.sh\n"
        "# Sync every 10 min\n"
        "*/10 * * * * /usr/local/bin/sync.sh\n",
        encoding="utf-8",
    )

    assert main(["crontab", str(crontab_file)]) == 0
    captured = capsys.readouterr()
    assert "Analyzed 2 scheduled job(s)" in captured.out
