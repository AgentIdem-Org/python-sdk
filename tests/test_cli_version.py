from __future__ import annotations

from typer.testing import CliRunner

from agentidem.cli import app
from agentidem.cli.constants import AGENTIDEM_CLI_VERSION


runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(
        app,
        ["version"],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == AGENTIDEM_CLI_VERSION