from __future__ import annotations

import json

from typer.testing import CliRunner

from agentidem.cli import app


runner = CliRunner()


def test_replay_command_matches_recorded_trace(
        tmp_path,
) -> None:
    trace_path = tmp_path / "trace.json"

    record_result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:unsafe_agent",
            "--out",
            str(trace_path),
        ],
    )

    assert record_result.exit_code == 0
    assert trace_path.exists()

    replay_result = runner.invoke(
        app,
        [
            "replay",
            str(trace_path),
        ],
    )

    assert replay_result.exit_code == 0
    assert "REPLAY MATCH" in replay_result.stdout
    assert "examples.cli_agents:unsafe_agent" in replay_result.stdout


def test_replay_command_detects_mismatch(
        tmp_path,
) -> None:
    trace_path = tmp_path / "trace.json"

    record_result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:unsafe_agent",
            "--out",
            str(trace_path),
        ],
    )

    assert record_result.exit_code == 0

    data = json.loads(
        trace_path.read_text(encoding="utf-8")
    )

    data["operations"][0]["result"] = "different-result"

    trace_path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )

    replay_result = runner.invoke(
        app,
        [
            "replay",
            str(trace_path),
        ],
    )

    assert replay_result.exit_code == 1
    assert "REPLAY MISMATCH" in replay_result.stdout
    assert "examples.cli_agents:unsafe_agent" in replay_result.stdout


def test_replay_command_rejects_invalid_trace(
        tmp_path,
) -> None:
    trace_path = tmp_path / "invalid.json"

    trace_path.write_text(
        "this is not valid json",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "replay",
            str(trace_path),
        ],
    )

    assert result.exit_code == 2
    assert "ERROR" in result.stderr
    assert "Failed to load trace" in result.stderr


def test_replay_command_rejects_missing_trace(
        tmp_path,
) -> None:
    trace_path = tmp_path / "missing.json"

    result = runner.invoke(
        app,
        [
            "replay",
            str(trace_path),
        ],
    )

    assert result.exit_code == 2
    assert "ERROR" in result.stderr
    assert "Failed to load trace" in result.stderr


def test_replay_command_matches_async_trace(
        tmp_path,
) -> None:
    trace_path = tmp_path / "async-trace.json"

    record_result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:async_unsafe_agent",
            "--out",
            str(trace_path),
        ],
    )

    assert record_result.exit_code == 0
    assert trace_path.exists()

    replay_result = runner.invoke(
        app,
        [
            "replay",
            str(trace_path),
        ],
    )

    assert replay_result.exit_code == 0
    assert "REPLAY MATCH" in replay_result.stdout
    assert "examples.cli_agents:async_unsafe_agent" in replay_result.stdout