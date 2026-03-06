# AGENTS.md

Guidelines for agentic coding agents working in this repository.

---

## Project Overview

Sonny is a Discord bot built with `discord.py` using a modular cog architecture.
- Entry point: `bot.py`
- Cogs: `cogs/` — one file per cog, auto-loaded at startup
- Runtime: Python 3.10+, dependencies managed via `pip` with a `.venv`
- Secrets: `.env` file (never committed), loaded per-cog via `python-dotenv`

---

## Running the Bot

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

There is no test suite. The bot must be run against a live Discord application
and guild to verify behaviour. Use `/reload <cog>` to hot-reload a cog after
changes without restarting the bot.

---

## Linting & Formatting

No linter config files are committed. The following tools are recommended and
should produce no errors or warnings before committing:

```bash
# Linting and formatting
pip install ruff pyright

ruff check .
ruff format .
pyright .
```

Ruff rules to follow: default PEP 8 style. Line length is not strictly enforced
but keep lines under 100 characters where practical.

---

## Project Structure

```
bot.py              # Bot entry point, cog loader, guild sync
cogs/
    admins.py       # /reload — admin cog management
    amp.py          # /amp * — AMP game server integration
    events.py       # on_member_join — welcome messages and auto-role
    general.py      # /ping, /clear — general utility commands
    system.py       # /system — host LXC health metrics
requirements.txt
.env                # Secrets — never commit
.github/
    README.md
    workflows/
        deploy.yml  # CD pipeline via GitHub Actions + NetBird + SSH
```

---

## Adding a New Cog

1. Create `cogs/<name>.py`
2. Define a class inheriting `commands.Cog` (or `commands.GroupCog` for grouped
   slash commands)
3. End the file with:
   ```python
   async def setup(bot):
       await bot.add_cog(CogName(bot))
   ```
4. The bot auto-loads all `.py` files in `cogs/` on startup — no registration needed

---

## Code Style

### Imports

Order strictly: stdlib → third-party → local. One blank line between groups.

```python
import os
from datetime import datetime

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
| Module-level constants | `UPPER_SNAKE_CASE` | `AMP_URL`, `networkadmin_role_id` |
| Private helpers | `_snake_case` prefix | `_find_instance`, `_state_label` |
| Error handlers | `<command>_error` | `async def amp_kill_error` |

### Type Annotations

- Always annotate `interaction: discord.Interaction` in command signatures
- Always annotate `bot: commands.Bot` in `setup()` functions
- Use `Union[X, None]` rather than `X | None` (codebase targets Python 3.10,
  but existing style uses `Union` — stay consistent)
- `__init__` `self` and `bot` parameters do not need annotations
- Read env vars with `os.getenv("KEY") or ""` for strings (avoids `str | None`);
  use `int(os.getenv("KEY"))` for integers where the key is guaranteed present

### Environment Variables

```python
# Strings
AMP_URL = os.getenv("AMP_URL") or ""

# Integers (guaranteed present)
networkadmin_role_id = int(os.getenv("NETWORKADMIN_ROLE_ID"))
```

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

Always defer immediately if any async work (API calls, DB, etc.) follows:

```python
async def my_command(self, interaction: discord.Interaction, ...):
    await interaction.response.defer()
    # ... async work ...
    await interaction.followup.send(...)
```

Use `defer(ephemeral=True)` if the entire response should be private.

### Role & Permission Restrictions

```python
# Role-based (use role ID from env)
@app_commands.checks.has_role(networkadmin_role_id)
async def my_command(self, interaction, ...):
    ...

@my_command.error
async def my_command_error(self, interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("...", ephemeral=True)

# Permission-based
@app_commands.checks.has_permissions(manage_messages=True)
```

Always define an `.error` handler immediately after any restricted command.

### Embeds

Use embeds for all structured output. Plain strings for simple one-liners only.

```python
embed = discord.Embed(title="...", color=discord.Color.green())
embed.add_field(name="...", value="...", inline=True)
embed.set_footer(text="...")
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

All commands that call the AMP API follow this pattern:

```python
async def amp_example(self, interaction, instance_name):
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
- Catch `ConnectionError` specifically for AMP API calls — it indicates the
  instance is offline or unreachable
- Check `isinstance(result, ActionResultError)` after AMP calls that return
  typed results before accessing attributes
- Check `instance.app_state` against `AMPInstanceState` enum values (not strings)
  before performing state-dependent operations

### General Error Handling

- Catch specific exceptions — avoid bare `except Exception` unless logging and re-raising
- Print unexpected errors to stdout with context: `print(f"Error in X: {e}")`
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
