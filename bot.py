import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


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
                    print(f"Loeaded: {filename}")
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

        # Syncing commands
        MY_GUILD = discord.Object(id=os.getenv("GUILD_ID"))
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print(f"--- SLASH COMMANDS SYNCED ---")

    async def on_ready(self):
        print(f"--- Logged in as {self.user} ---")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="with penguins 🐧"
            ),
            status=discord.Status.online,
        )


bot = Sonny()
bot.run(os.getenv("TOKEN"))
