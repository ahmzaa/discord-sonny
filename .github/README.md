# SONNY

[Sonny](https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fstatic1.srcdn.com%2Fwordpress%2Fwp-content%2Fuploads%2F2016%2F10%2FSonny-irobot.jpeg&f=1&nofb=1&ipt=42bceb8a622cdc5bec43a8dcaf94b535e3811d9ba190de8f3b166bf384f42670)

Sonny is the discord bot for my server.

## Current features:

- Welcome Messages on new user join
- Autorole on new user join
- Ping - returns latency
- Clear - Clears `n` amount of messages from a channel
- live reload of cogs
- amp instance status
- system status
- modular

## Desired features

1. Utility & Information

- /userinfo [@user]: Displays an embed with the user’s join date, server roles, and account age.
- /serverinfo: Shows server stats like total members, boost level, and creation date.
- /remindme [time] [message]: Sets a private timer for the user.
  - Implementation Tip: use asyncio.sleep() for short reminders. For long ones (days/weeks), save them to a file or database.

2. Interaction & Engagement

- /poll [question] [options]: Creates an embed with reaction buttons so people can vote.
- /8ball [question]: A classic "Magic 8-Ball" that gives random funny answers.

3. Moderation & Safety

- /slowmode [seconds]: Quickly changes the chat speed for the current channel to stop spam.
- /lock / /unlock: Instantly prevents everyone from typing in a channel.
- /warn [@user] [reason]: Records a warning for a user. can program the bot to automatically Kick them after 3 warnings.
- /whois [ID]: Look up a user by their ID even if they aren't in the server.

4. Integration

- /amp [instanceid] [options]: control amp game server directly from discord.
  - [x] Get Instance status
  - [ ] Manage Instance Power
- /weather [city]: Uses a free API (like wttr.in) to show the current forecast.
- /stock [symbol] or /crypto [coin]: Fetches real-time prices from a financial API.
- /translate [text] [language]: Uses the Google Translate API to instantly convert messages.
