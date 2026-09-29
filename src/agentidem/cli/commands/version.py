from __future__ import annotations

import typer

from agentidem.cli.constants import AGENTIDEM_CLI_VERSION


def version_command() -> None:
    """
    Show the AgentIdem CLI version.
    """
    typer.echo(AGENTIDEM_CLI_VERSION)