# Test Suite — Sonny Discord Bot

Quick reference for the Sonny test suite. Tests are split into **unit tests** (pytest, no live connections) and an **integration smoke test** (standalone async script, requires a live AMP panel).

---

## Structure

```
tests/
    conftest.py       # Shared fixtures: mock_bot, mock_interaction, make_mock_instance
    test_bot.py       # Env var validation (4 tests)
    test_amp.py       # AMP cog logic (26 tests)
    test_events.py    # Welcome embed + on_member_join (10 tests)
    test_general.py   # /ping, /clear commands (7 tests)
    test_system.py    # /system command (4 tests)
    test_admins.py    # /reload command (3 tests)
    smoke_test.py     # Integration smoke test — NOT collected by pytest automatically
```

**Total unit tests: 71**

---

## Setup

Dev dependencies are separate from the bot's runtime dependencies:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` contains `pytest` and `pytest-asyncio`.

---

## Running Tests

```bash
# All unit tests
pytest

# Single test file
pytest tests/test_amp.py

# Single test by name
pytest tests/test_amp.py::test_state_label_ready

# Verbose output
pytest -v

# Integration smoke test (requires live .env + AMP instance — see below)
python tests/smoke_test.py
```

---

## Configuration (`pytest.ini`)

| Setting | Value | Effect |
|---|---|---|
| `asyncio_mode` | `auto` | All async test functions are automatically treated as coroutines — no need to decorate with `@pytest.mark.asyncio` (though it is used explicitly for clarity) |
| `testpaths` | `tests` | pytest only collects from the `tests/` directory |

`smoke_test.py` is excluded from automatic collection via `collect_ignore` in the root `conftest.py`.

---

## Shared Fixtures (`tests/conftest.py`)

| Fixture / Helper | Description |
|---|---|
| `mock_bot` | `MagicMock` standing in for `commands.Bot`. Has `.latency = 0.05` and `.user.display_avatar.url` set |
| `mock_interaction` | `MagicMock` for `discord.Interaction`. `.response.defer`, `.response.send_message`, and `.followup.send` are all `AsyncMock`. `.channel` is a `discord.TextChannel` mock with `.purge` as `AsyncMock` returning 3 items |
| `make_mock_instance(name, instance_name, app_state)` | Factory function (not a fixture) returning a configurable mock `AMPInstance` with all async methods as `AsyncMock` |

Command callbacks are invoked directly in tests:

```python
await cog.my_command.callback(cog, mock_interaction, arg1, arg2)
```

---

## Unit Test Coverage

### `test_bot.py` — Env Var Validation
- All required env vars present → no exception raised
- One missing var → `RuntimeError` with the var name in the message
- Multiple missing vars → all missing var names listed in the error
- Empty string treated as missing

### `test_amp.py` — AMP Cog
- `_state_label` parametrised across all `AMPInstanceState` values
- `_find_instance` patches `_get_all_instances` to avoid real AMP connections
- `/amp start` and `/amp stop` parametrised over `_RUNNING_STATES` and `_STOPPED_STATES`
- `/amp stop` `ConnectionError` path asserts `"not available"` (not `"already offline"`)
- `/amp status` asserts embed is returned with correct colour from `_STATE_COLOUR`
- `/amp list` asserts `failed` instances are filtered by default; shown with `show_all=True`
- `/amp console` asserts triple backticks in output are replaced with `'''`

### `test_events.py` — Events Cog
- `member.mention` is present in the welcome embed description
- No `"a<@&"` pattern in output (missing-space bug regression)
- Embed timestamp is timezone-aware (UTC)
- `add_roles` called with the correct role ID
- No exception raised when `get_role` returns `None`
- `discord.Forbidden` on `add_roles` handled gracefully — prints error, does not raise
- `channel.send` not called when channel is not a `TextChannel`
- `/testwelcome` sends an ephemeral embed

### `test_general.py` — General Cog
- `/ping` response contains `"ms"` and reflects `bot.latency`
- `/clear` with amount `0` or negative → ephemeral error, `purge` not called
- `/clear` in wrong channel type → ephemeral error, `purge` not called
- `/clear` success → `purge` called with the correct limit, deleted count reported
- `/clear` exception from `purge` → ephemeral error sent

### `test_system.py` — System Cog
- `response.defer()` called before `followup.send()`
- Embed contains all required fields: CPU, RAM, Disk, OS, LXC Booted Since
- `run_in_executor` called for blocking `cpu_percent` call
- Embed timestamp is timezone-aware

### `test_admins.py` — Admins Cog
- `/reload` success: `reload_extension` called, success message sent
- `ExtensionNotFound`: logs to stdout, sends sanitised message (not the raw exception) to Discord
- Unexpected `RuntimeError`: internal error path not leaked to Discord

---

## Integration Smoke Test (`smoke_test.py`)

Tests the AMP cog's helper functions against a **live AMP installation**. Not run by pytest — execute manually.

### Requirements
1. A populated `.env` file (same one used to run the bot)
2. A running AMP panel reachable at `AMP_URL`
3. At least one registered AMP instance

### Setup

Edit `TEST_INSTANCE_NAME` at the top of `tests/smoke_test.py`:

```python
TEST_INSTANCE_NAME = "YOUR_INSTANCE_NAME_HERE"
```

Replace with the friendly name of a real AMP instance, then run:

```bash
python tests/smoke_test.py
```

### Checks

| # | What it verifies |
|---|---|
| 1 | `_get_all_instances()` returns a non-empty list; prints all instance names and states |
| 2 | `_find_instance(TEST_INSTANCE_NAME)` finds the named instance and returns the correct type |
| 3 | `_find_instance("__nonexistent_xyz__")` returns `None` |
| 4 | `instance.get_status()` returns a valid `Status` object (not `ActionResultError`) |
| 5 | `instance.get_user_list()` returns a `Players` object with a player count |

Each check prints `PASS` or `FAIL` in colour. Exits with code `0` if all pass, `1` if any fail.

### Example Output

```
=== AMP Smoke Test ===

1. Fetching all instances...
  [PASS] _get_all_instances returns instances — 3 found: Minecraft01, Valheim01, ARK01
2. Finding instance 'Minecraft01'...
  [PASS] _find_instance finds 'Minecraft01' — type=AMPMinecraftInstance, state=AMPInstanceState.ready
3. Confirming unknown instance returns None...
  [PASS] _find_instance returns None for unknown name
4. Fetching instance status/metrics...
  [PASS] get_status returns valid Status — metrics=present
5. Fetching player list...
  [PASS] get_user_list returns Players — 2 player(s) online

=== Results: 5/5 passed ===

All checks passed.
```

---

## Adding New Tests

1. Create `tests/test_<cog>.py`
2. Set any required env vars before importing the cog:
   ```python
   import os
   os.environ.setdefault("MY_ENV_VAR", "dummy_value")
   ```
3. Import `make_mock_instance` from `tests/conftest.py` for AMP instance mocks
4. Patch `cogs.amp._find_instance` or `cogs.amp._get_all_instances` to avoid live AMP connections
5. Invoke command callbacks directly:
   ```python
   await cog.my_command.callback(cog, mock_interaction, ...)
   ```
