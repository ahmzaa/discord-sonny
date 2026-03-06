import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

_REQUIRED_ENV = [
    "TOKEN",
    "GUILD_ID",
    "NETWORKADMIN_ROLE_ID",
    "WELCOME_CHANNEL_ID",
    "INITIAL_MEMBER_ROLE_ID",
    "GENERAL_CHANNEL_ID",
    "SUPPORT_CHANNEL_ID",
    "VC_TEXT_CHANNEL_ID",
    "DCADMIN_ROLE_ID",
    "AMP_URL",
    "AMP_USER",
    "AMP_PASS",
]

_missing = [k for k in _REQUIRED_ENV if not os.getenv(k)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")


class Sonny(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This loads every .py file in the 'cogs' folder
        print("--- LOADING COGS ---")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded: {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

        # Syncing commands
        MY_GUILD = discord.Object(id=int(os.getenv("GUILD_ID") or 0))
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print("--- SLASH COMMANDS SYNCED ---")

    async def on_ready(self):
        print(f"--- Logged in as {self.user} ---")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="with penguins 🐧"
            ),
            status=discord.Status.online,
        )


bot = Sonny()
bot.run(os.getenv("TOKEN") or "")
