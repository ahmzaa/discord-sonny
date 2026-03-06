# Sonny

Sonny is the Discord bot for my server.

---

## Current Features

### General

| Command | Description | Restricted |
|---|---|---|
| `/ping` | Returns bot latency | No |
| `/clear <amount>` | Deletes `n` messages from a channel | Manage Messages permission |

### System

| Command | Description | Restricted |
|---|---|---|
| `/system` | Shows CPU, RAM, disk usage, OS, and uptime of the host LXC | No |

### AMP

| Command | Description | Restricted |
|---|---|---|
| `/amp status <instance_name>` | Show current state of an instance | No |
| `/amp list [show_all]` | List instances — running only by default, all with `show_all:True` | No |
| `/amp start <instance_name>` | Start an instance | No |
| `/amp stop <instance_name>` | Stop an instance | No |
| `/amp restart <instance_name>` | Restart an instance | No |
| `/amp players <instance_name>` | Show players currently connected to an instance | No |
| `/amp stats <instance_name>` | Show CPU, memory, and active player metrics for an instance | No |
| `/amp console <instance_name> <command>` | Send a console command; returns last 5 lines of output | NetworkAdmin role |
| `/amp kill <instance_name>` | Force-kill a hung instance (no-op if already stopped or stopping) | NetworkAdmin role |

### Admin

| Command | Description | Restricted |
|---|---|---|
| `/reload <extension>` | Live reload a cog without restarting the bot | NetworkAdmin role |

### Events

| Event / Command | Behaviour |
|---|---|
| `on_member_join` | Assigns the initial member role and sends a welcome embed to the welcome channel |
| `/testwelcome` | Preview the welcome embed (administrator permission only, ephemeral) |

---

## Deployment

Pushes to `main` trigger a two-job GitHub Actions workflow:

1. **test** — installs dependencies and runs the full `pytest` unit test suite on Python 3.10.
2. **deploy** — runs only if `test` passes; connects to the server over NetBird, then pulls the latest code and restarts the `discord-sonny` systemd service via SSH.

---

## Desired Features

### Utility & Information

- `/userinfo [@user]` — Embed showing join date, roles and account age
- `/serverinfo` — Server stats: member count, boost level, creation date
- `/remindme [time] [message]` — Private reminder timer

### Interaction & Engagement

- `/poll [question] [options]` — Embed with reaction buttons for voting
- `/8ball [question]` — Magic 8-Ball with random responses

### Moderation & Safety

- `/slowmode [seconds]` — Set channel slowmode to reduce spam
- `/lock` / `/unlock` — Prevent or allow messages in a channel
- `/warn [@user] [reason]` — Record a warning; auto-kick after 3
- `/whois [ID]` — Look up a user by ID even if not in the server

### Integration

- `/weather [city]` — Current forecast via wttr.in
- `/stock [symbol]` / `/crypto [coin]` — Real-time prices from a financial API
- `/translate [text] [language]` — Translate text via Google Translate API
