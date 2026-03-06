import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

networkadmin_role_id = int(os.getenv("NETWORKADMIN_ROLE_ID") or 0)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload", description="Reloads a specific cog")
    @app_commands.checks.has_role(networkadmin_role_id)
    async def reload(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await interaction.response.send_message(
                f"✅ Extension `{extension}` reloaded!", ephemeral=True
            )
        except commands.ExtensionError as e:
            print(f"Failed to reload extension '{extension}': {e}")
            await interaction.response.send_message(
                f"❌ Failed to reload `{extension}`. Check bot logs for details.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"Unexpected error reloading extension '{extension}': {e}")
            await interaction.response.send_message(
                "❌ An unexpected error occurred. Check bot logs for details.",
                ephemeral=True,
            )

    @reload.error
    async def reload_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(
                "You don't have permission to reload my brains!", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
