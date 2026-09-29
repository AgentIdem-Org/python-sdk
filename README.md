# AgentIdem

Reliability testing for state-changing AI agents.

> Agents retry. Side effects do not rewind.

AgentIdem tests whether an agent behaves safely when execution is retried, interrupted, duplicated, or partially observed.

---

## Installation

Requires Python 3.11 or newer.

```bash
pip install agentidem
```

Verify the CLI:

```bash
agentidem version
```

Expected output:

```text
v1.0.0
```

---

## CLI

AgentIdem v1 provides four commands:

```text
agentidem test
agentidem record
agentidem replay
agentidem version
```

---

## `agentidem test`

Test an agent for retry and side effect safety.

```bash
agentidem test module.path:function
```

Example:

```bash
agentidem test examples.cli_agents:unsafe_agent
```

AgentIdem automatically detects synchronous and asynchronous targets.

### JSON output

```bash
agentidem test examples.cli_agents:unsafe_agent --json
```

### Save a report

```bash
agentidem test examples.cli_agents:unsafe_agent --out report.json
```

You can use both together:

```bash
agentidem test examples.cli_agents:unsafe_agent \
  --json \
  --out report.json
```

### Exit codes

| Exit code | Meaning |
|---:|---|
| `0` | All tested scenarios were safe |
| `1` | At least one scenario was unsafe |
| `2` | Target loading or baseline execution failed |

---

## `agentidem record`

Run an agent once and save its execution trace.

```bash
agentidem record module.path:function --out trace.json
```

Example:

```bash
agentidem record examples.cli_agents:unsafe_agent --out trace.json
```

The trace includes the target, operations, arguments, results, errors, statuses, and observation state.

If the target fails, AgentIdem still writes the partial trace and exits with code `2`.

---

## `agentidem replay`

Re-run a recorded target and compare it with the saved trace.

```bash
agentidem replay trace.json
```

Matching replay:

```text
REPLAY MATCH: examples.cli_agents:unsafe_agent
```

Mismatching replay:

```text
REPLAY MISMATCH: examples.cli_agents:unsafe_agent
```

### Exit codes

| Exit code | Meaning |
|---:|---|
| `0` | Replay matched |
| `1` | Replay differed |
| `2` | Trace or target could not be loaded |

Replay ignores nondeterministic trace IDs and timestamps.

---

## `agentidem version`

Show the AgentIdem CLI version.

```bash
agentidem version
```

Output:

```text
v1.0.0
```

---

## Target format

CLI targets use:

```text
module.path:function
```

Example:

```text
my-project/
├── agents/
│   ├── __init__.py
│   └── refund.py
└── ...
```

With:

```python
# agents/refund.py

def run() -> None:
    ...
```

Run:

```bash
agentidem test agents.refund:run
```

For v1, CLI targets should be zero-argument functions.

If your agent requires arguments, create a small wrapper:

```python
from myapp.agent import process_order


def run() -> str:
    return process_order(
        order_id="ord_42",
        amount=100,
    )
```

Then run:

```bash
agentidem test myapp.agent_test:run
```

---

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest -v
```

---

## License

Licensed under Apache License 2.0. See `LICENSE`.