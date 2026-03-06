# AGENTS.md

Guidelines for agentic coding agents working in this repository.

---

## Project Overview

Sonny is a Discord bot built with `discord.py` using a modular cog architecture.
- Entry point: `bot.py`
- Cogs: `cogs/` — one file per cog, auto-loaded at startup
- Runtime: Python 3.10+, dependencies managed via `pip` with a `.venv`
- Secrets: `.env` file (never committed), loaded per-cog via `python-dotenv`
- All required env vars are validated at startup in `bot.py` — the bot raises
  `RuntimeError` with a clear message if any are missing

---

## Running the Bot

```bash
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Use `/reload <cog>` to hot-reload a cog after changes without restarting the bot.

---

## Testing

```bash
# Install dev dependencies (first time only)
pip install -r requirements-dev.txt

# Run all unit tests
pytest

# Run a single test file
pytest tests/test_amp.py

# Run a single test by name
pytest tests/test_amp.py::test_state_label_ready

# Verbose output
pytest -v

# Integration smoke test (requires live .env + running AMP panel)
# Edit TEST_INSTANCE_NAME at the top of the file first
python tests/smoke_test.py
```

Unit tests use `unittest.mock` — no live Discord or AMP connections required.
See `tests/README.md` for full details on the test suite.

---

## Linting & Formatting

```bash
pip install ruff pyright
ruff check .
ruff format .
pyright .
```

Default PEP 8 style. Keep lines under 100 characters where practical.

---

## Project Structure

```
bot.py                   # Entry point — cog loader, guild sync, env var validation
cogs/
    admins.py            # /reload — admin cog management
    amp.py               # /amp * — AMP game server integration
    events.py            # on_member_join — welcome messages and auto-role; /testwelcome
    general.py           # /ping, /clear — general utility commands
    system.py            # /system — host LXC health metrics
tests/
    conftest.py          # Shared fixtures: mock_bot, mock_interaction, make_mock_instance
    test_amp.py          # AMP cog unit tests (34 test functions)
    test_admins.py       # Admin cog unit tests (3 tests)
    test_bot.py          # Env var validation tests (4 tests)
    test_events.py       # Events cog unit tests (10 tests)
    test_general.py      # General cog unit tests (9 tests)
    test_system.py       # System cog unit tests (4 tests)
    smoke_test.py        # Integration test — NOT run by pytest automatically
    README.md            # Test suite documentation
conftest.py              # Root pytest config — adds project root to sys.path
pytest.ini               # asyncio_mode=auto, testpaths=tests
requirements.txt         # Runtime dependencies
requirements-dev.txt     # pytest, pytest-asyncio
.env                     # Secrets — never commit
.github/
    README.md
    workflows/
        deploy.yml       # CI: unit tests (test job) then deploy via NetBird + SSH (deploy job)
```

---

## Adding a New Cog

1. Create `cogs/<name>.py`
2. Define a class inheriting `commands.Cog` (or `commands.GroupCog` for grouped
   slash commands)
3. End the file with:
   ```python
   async def setup(bot: commands.Bot):
       await bot.add_cog(CogName(bot))
   ```
4. Add any new required env var keys to `_REQUIRED_ENV` in `bot.py`
5. The bot auto-loads all `.py` files in `cogs/` on startup — no registration needed

---

## Code Style

### Imports

Order strictly: stdlib → third-party → local. One blank line between groups.

```python
import os
from typing import Union

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from ampapi import APIParams, Bridge
```

- Always use `from discord import app_commands` — never `import discord.app_commands`
- Always use `from discord.ext import commands` — never `import discord.ext.commands`
- Call `load_dotenv()` at module level in every cog that reads env vars

### Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Cog classes | `PascalCase` | `class AMP`, `class Events` |
| Command methods | `snake_case` | `async def amp_status` |
| Module-level constants | `UPPER_SNAKE_CASE` | `AMP_URL`, `NETWORKADMIN_ROLE_ID` |
| Private helpers | `_snake_case` prefix | `_find_instance`, `_state_label` |
| Error handlers | `<command>_error` | `async def amp_kill_error` |

### Type Annotations

- Always annotate `interaction: discord.Interaction` in command signatures
- Always annotate `bot: commands.Bot` in `setup()` functions
- Use `Union[X, None]` rather than `X | None` (stay consistent with existing style)
- `__init__` `self` and `bot` parameters do not need annotations
- Read env vars with `os.getenv("KEY") or ""` for strings (avoids `str | None`);
  use `int(os.getenv("KEY") or 0)` for integers

### Environment Variables

```python
# Strings
AMP_URL = os.getenv("AMP_URL") or ""

# Integers
NETWORKADMIN_ROLE_ID = int(os.getenv("NETWORKADMIN_ROLE_ID") or 0)
```

All required env vars must also be listed in `_REQUIRED_ENV` in `bot.py` so the
bot fails fast with a clear message on misconfiguration rather than crashing mid-run.

---

## Discord Patterns

### Slash Commands

- Use `@app_commands.command(name=..., description=...)` for all new commands
- Prefix commands (`@commands.command`) are legacy — do not add new ones
- Grouped commands use `commands.GroupCog`:
  ```python
  class AMP(commands.GroupCog, name="amp"):
  ```

### Deferred Responses

Always defer immediately if any async work (API calls, etc.) follows:

```python
async def my_command(self, interaction: discord.Interaction, ...):
    await interaction.response.defer()
    # ... async work ...
    await interaction.followup.send(...)
```

Use `defer(ephemeral=True)` if the entire response should be private.
Never call `psutil` or other blocking I/O directly in a coroutine — every
blocking call (e.g. `cpu_percent`, `virtual_memory`, `disk_usage`, `boot_time`)
must be offloaded via `run_in_executor`. Use `asyncio.get_running_loop()` (not
the deprecated `asyncio.get_event_loop()`) and `asyncio.gather` when dispatching
multiple blocking calls concurrently:

```python
loop = asyncio.get_running_loop()
cpu_usage, ram, disk, boot_time = await asyncio.gather(
    loop.run_in_executor(None, psutil.cpu_percent, 1),
    loop.run_in_executor(None, psutil.virtual_memory),
    loop.run_in_executor(None, psutil.disk_usage, "/"),
    loop.run_in_executor(None, psutil.boot_time),
)
```

### Role & Permission Restrictions

```python
@app_commands.checks.has_role(NETWORKADMIN_ROLE_ID)
async def my_command(self, interaction: discord.Interaction, ...):
    ...

@my_command.error
async def my_command_error(self, interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("...", ephemeral=True)
```

Always define an `.error` handler immediately after any restricted command.

### Embeds

Use embeds for all structured output. Plain strings for simple one-liners only.
Use `discord.utils.utcnow()` for embed timestamps — never `datetime.now()`.

```python
embed = discord.Embed(title="...", color=discord.Color.green(),
                      timestamp=discord.utils.utcnow())
embed.add_field(name="...", value="...", inline=True)
await interaction.followup.send(embed=embed)
```

### Ephemeral Responses

All error and warning messages must be ephemeral:

```python
await interaction.followup.send("Something went wrong.", ephemeral=True)
```

---

## Error Handling

### AMP API Commands

```python
async def amp_example(self, interaction: discord.Interaction, instance_name: str):
    await interaction.response.defer()
    session = aiohttp.ClientSession()
    try:
        instance = await _find_instance(instance_name, session)
        if instance is None:
            await interaction.followup.send(
                f"Instance `{instance_name}` not found.", ephemeral=True
            )
            return
        try:
            await instance.some_action()
            await interaction.followup.send("Done.")
        except ConnectionError:
            await interaction.followup.send(
                "Instance is not available.", ephemeral=True
            )
    finally:
        await session.close()  # always close — use finally, never rely on return paths
```

Key rules:
- `aiohttp.ClientSession` must always be closed in a `finally` block
- Catch `ConnectionError` specifically for AMP API calls
- Check `isinstance(result, ActionResultError)` after AMP calls that return typed
  results before accessing attributes
- Check `instance.app_state` against `AMPInstanceState` enum values (never strings)
- Use `_RUNNING_STATES` / `_STOPPED_STATES` sets in `amp.py` for transitional state guards
- Never expose raw exception messages to Discord users — log to stdout and send a
  sanitised message: `print(f"Error in X: {e}")` then `followup.send("Check logs.")`

### General Error Handling

- Catch specific exceptions — avoid bare `except Exception` unless logging
- Catch `discord.Forbidden` before `discord.HTTPException` for Discord permission errors
- Use `except discord.HTTPException` as the fallback for other Discord API failures
- Log the raw exception to stdout, then send a sanitised message to Discord — never
  forward raw exception text to users
- Never silently swallow errors

---

## Section Comments in Large Cogs

Use divider comments to separate command definitions in files with many commands:

```python
    # ------------------------------------------------------------------ #
    #  /amp status                                                         #
    # ------------------------------------------------------------------ #
    @app_commands.command(...)
```

---

## Writing Tests

- Set required env vars before importing the cog under test:
  ```python
  os.environ.setdefault("NETWORKADMIN_ROLE_ID", "111")
  from cogs.admins import Admin
  ```
- Use `make_mock_instance()` from `tests/conftest.py` for AMP instance mocks
- Patch `cogs.amp._find_instance` or `cogs.amp._get_all_instances` to avoid
  live AMP connections
- Invoke command callbacks directly:
  ```python
  await cog.my_command.callback(cog, mock_interaction, arg1, arg2)
  ```
