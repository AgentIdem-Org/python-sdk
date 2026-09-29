from __future__ import annotations

from typer.testing import CliRunner

from agentidem.cli import app


runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0
    assert "Reliability testing for state-changing AI agents." in result.stdout
    assert "test" in result.stdout


def test_test_command_rejects_invalid_target() -> None:
    result = runner.invoke(
        app,
        [
            "test",
            "not-a-valid-target",
        ],
    )

    assert result.exit_code == 2
    assert "ERROR" in result.stderr
    assert "module.path:function" in result.stderr


def test_test_command_returns_safe_exit_code(
        monkeypatch,
) -> None:
    class FakeReport:
        baseline_failure = None
        safe = True
        fault_count = 3
        unsafe_count = 0
        results = ()

    monkeypatch.setattr(
        "agentidem.cli.commands.test.load_target",
        lambda target: lambda: None,
    )

    monkeypatch.setattr(
        "agentidem.cli.commands.test.test_agent",
        lambda target, func: FakeReport(),
    )

    result = runner.invoke(
        app,
        [
            "test",
            "example.agent:run",
        ],
    )

    assert result.exit_code == 0

    assert "SAFE" in result.stdout
    assert "example.agent:run" in result.stdout
    assert "Fault cases: 3" in result.stdout
    assert "Unsafe: 0" in result.stdout


def test_test_command_returns_unsafe_exit_code(
        monkeypatch,
) -> None:
    class FakeCase:
        scenario = "duplicate_delivery"

    class FakeResult:
        case = FakeCase()
        safe = False
        failed = False
        findings = [object()]

    class FakeReport:
        baseline_failure = None
        safe = False
        fault_count = 3
        unsafe_count = 1
        results = (FakeResult(),)

    monkeypatch.setattr(
        "agentidem.cli.commands.test.load_target",
        lambda target: lambda: None,
    )

    monkeypatch.setattr(
        "agentidem.cli.commands.test.test_agent",
        lambda target, func: FakeReport(),
    )

    result = runner.invoke(
        app,
        [
            "test",
            "example.agent:run",
        ],
    )

    assert result.exit_code == 1

    assert "UNSAFE" in result.stdout
    assert "example.agent:run" in result.stdout
    assert "Fault cases: 3" in result.stdout
    assert "Unsafe: 1" in result.stdout

    assert "duplicate_delivery" in result.stdout
    assert "COMPLETED" in result.stdout


def test_test_command_returns_baseline_failure_exit_code(
        monkeypatch,
) -> None:
    class FakeFailure:
        error_type = "RuntimeError"
        message = "database unavailable"

    class FakeReport:
        baseline_failure = FakeFailure()
        safe = False
        fault_count = 0
        unsafe_count = 0
        results = ()

    monkeypatch.setattr(
        "agentidem.cli.commands.test.load_target",
        lambda target: lambda: None,
    )

    monkeypatch.setattr(
        "agentidem.cli.commands.test.test_agent",
        lambda target, func: FakeReport(),
    )

    result = runner.invoke(
        app,
        [
            "test",
            "example.agent:run",
        ],
    )

    assert result.exit_code == 2

    assert "BASELINE FAILED" in result.stderr
    assert "example.agent:run" in result.stderr
    assert "RuntimeError" in result.stderr
    assert "database unavailable" in result.stderr