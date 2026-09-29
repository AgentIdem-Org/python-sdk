from __future__ import annotations

from typer.testing import CliRunner

from agentidem.cli import app

import json

runner = CliRunner()

def test_cli_e2e_json_output_is_valid_json() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "examples.cli_agents:safe_agent",
            "--json",
        ],
    )

    assert result.exit_code == 0

    data = json.loads(result.stdout)

    assert data["schema_version"] == "1"
    assert data["safe"] is True
    assert data["baseline_succeeded"] is True
    assert data["baseline_failure"] is None
    assert data["fault_count"] == 1
    assert data["unsafe_count"] == 0

    assert data["baseline"]["target"] == (
        "examples.cli_agents:safe_agent"
    )


def test_cli_e2e_out_writes_json_report(
        tmp_path,
) -> None:
    output_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "test",
            "examples.cli_agents:unsafe_agent",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 1

    assert output_path.exists()

    data = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert data["schema_version"] == "1"
    assert data["safe"] is False
    assert data["baseline_succeeded"] is True
    assert data["fault_count"] == 3
    assert data["unsafe_count"] == 1

    duplicate_delivery = next(
        item
        for item in data["results"]
        if item["scenario"] == "duplicate_delivery"
    )

    assert duplicate_delivery["safe"] is False
    assert len(duplicate_delivery["duplicates"]) == 1
    assert len(duplicate_delivery["findings"]) == 1


def test_cli_e2e_async_safe_agent() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "examples.cli_agents:async_safe_agent",
        ],
    )

    assert result.exit_code == 0

    assert "SAFE" in result.stdout
    assert "Fault cases: 1" in result.stdout
    assert "Unsafe: 0" in result.stdout


def test_cli_e2e_async_unsafe_agent() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "examples.cli_agents:async_unsafe_agent",
        ],
    )

    assert result.exit_code == 1

    assert "UNSAFE" in result.stdout
    assert "Fault cases: 3" in result.stdout
    assert "Unsafe: 1" in result.stdout
    assert "duplicate_delivery" in result.stdout


def test_cli_e2e_unsafe_agent() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "tests.fixtures.cli_agents:unsafe_agent",
        ],
    )

    assert result.exit_code == 1

    assert "UNSAFE" in result.stdout
    assert "tests.fixtures.cli_agents:unsafe_agent" in result.stdout
    assert "duplicate_delivery" in result.stdout


def test_cli_e2e_retrying_agent() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "tests.fixtures.cli_agents:retrying_agent",
        ],
    )

    assert result.exit_code == 1

    assert "UNSAFE" in result.stdout
    assert "lost_acknowledgement" in result.stdout
    assert "duplicate_delivery" in result.stdout


def test_cli_e2e_baseline_failure() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "tests.fixtures.cli_agents:failing_agent",
        ],
    )

    assert result.exit_code == 2

    assert "BASELINE FAILED" in result.stderr
    assert "RuntimeError" in result.stderr
    assert "database unavailable" in result.stderr

def test_cli_e2e_async_json_output() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "examples.cli_agents:async_unsafe_agent",
            "--json",
        ],
    )

    assert result.exit_code == 1

    data = json.loads(result.stdout)

    assert data["safe"] is False
    assert data["baseline_succeeded"] is True
    assert data["fault_count"] == 3
    assert data["unsafe_count"] == 1

    scenarios = {
        item["scenario"]
        for item in data["results"]
    }

    assert scenarios == {
        "lost_acknowledgement",
        "before_operation_failure",
        "duplicate_delivery",
    }