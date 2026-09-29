from __future__ import annotations

import typer

from agentidem.cli.commands.record import record_command
from agentidem.cli.commands.test import test_command
from agentidem.cli.commands.replay import replay_command
from agentidem.cli.commands.version import version_command

app = typer.Typer(
    name="agentidem",
    help="Reliability testing for state-changing AI agents.",
    no_args_is_help=True,
)


app.command(
    "test",
    help="Test an agent for unsafe side effects.",
)(test_command)


app.command(
    "record",
    help="Run an agent once and record its execution trace.",
)(record_command)
app.command(
    "version",
    help="Show the AgentIdem CLI version.",
)(version_command)


app.command(
    "replay",
    help="Re-run a recorded trace and compare the execution.",
)(replay_command)


@app.callback()
def main() -> None:
    """
    AgentIdem command-line interface.
    """