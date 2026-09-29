from __future__ import annotations

import json

from typer.testing import CliRunner

from agentidem.cli import app


runner = CliRunner()


def test_record_command_writes_sync_trace(
        tmp_path,
) -> None:
    output_path = tmp_path / "trace.json"

    result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:unsafe_agent",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()

    data = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert data["target"] == (
        "examples.cli_agents:unsafe_agent"
    )

    assert len(data["operations"]) == 1

    operation = data["operations"][0]

    assert operation["name"] == "save_order"
    assert operation["kind"] == "write"
    assert operation["status"] == "success"
    assert operation["observation"] == "received"

    assert operation["args"] == {
        "args": ["ord_42"],
        "kwargs": {},
    }

    assert "Recorded trace to" in result.stdout


def test_record_command_writes_async_trace(
        tmp_path,
) -> None:
    output_path = tmp_path / "async-trace.json"

    result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:async_unsafe_agent",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()

    data = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert data["target"] == (
        "examples.cli_agents:async_unsafe_agent"
    )

    assert len(data["operations"]) == 1

    operation = data["operations"][0]

    assert operation["name"] == "async_save_order"
    assert operation["kind"] == "write"
    assert operation["status"] == "success"
    assert operation["observation"] == "received"


def test_record_command_writes_partial_trace_on_failure(
        tmp_path,
) -> None:
    output_path = tmp_path / "failed-trace.json"

    result = runner.invoke(
        app,
        [
            "record",
            "examples.cli_agents:failing_agent",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 2
    assert output_path.exists()

    data = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert data["target"] == (
        "examples.cli_agents:failing_agent"
    )

    assert len(data["operations"]) == 1

    operation = data["operations"][0]

    assert operation["name"] == "failing_write"
    assert operation["status"] == "failed"
    assert operation["observation"] == "failed"

    assert "RuntimeError" in result.stderr
    assert "database unavailable" in result.stderr


def test_record_command_rejects_invalid_target(
        tmp_path,
) -> None:
    output_path = tmp_path / "trace.json"

    result = runner.invoke(
        app,
        [
            "record",
            "not-a-valid-target",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 2
    assert output_path.exists() is False

    assert "ERROR" in result.stderr
    assert "module.path:function" in result.stderr