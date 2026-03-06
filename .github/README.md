# Sonny

Sonny is the Discord bot for my server.

---

## Current Features

### General

| Command | Description | Restricted |
|---|---|---|
| `/ping` | Returns bot latency | No |
| `/clear <amount>` | Deletes `n` messages from a channel | Manage Messages |

### System

| Command | Description | Restricted |
|---|---|---|
| `/system` | Shows CPU, RAM, disk usage and uptime of the host LXC | No |

### AMP

| Command | Description | Restricted |
|---|---|---|
| `/amp status <instance>` | Show current state of an instance | No |
| `/amp list [show_all]` | List instances — running only by default, all with `show_all:True` | No |
| `/amp start <instance>` | Start an instance | No |
| `/amp stop <instance>` | Stop an instance | No |
| `/amp restart <instance>` | Restart an instance | No |
| `/amp players <instance>` | Show connected players and count | No |
| `/amp stats <instance>` | Show CPU, memory and player metrics | No |
| `/amp console <instance> <command>` | Send a console command, returns last 5 lines of output | NetworkAdmin |
| `/amp kill <instance>` | Force-kill a hung instance | NetworkAdmin |

### Admin

| Command | Description | Restricted |
|---|---|---|
| `/reload <cog>` | Live reload a cog without restarting the bot | NetworkAdmin |

### Events

| Event | Behaviour |
|---|---|
| Member join | Sends a welcome embed and assigns the initial member role |

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
