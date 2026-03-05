import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

admin_role_id = int(os.getenv("ADMIN_MEMBER_ROLE_ID"))


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload", description="Reloads a specific cog")
    @app_commands.checks.has_role(admin_role_id)  # Only the bot creator can run this
    async def reload(self, interaction: discord.Interaction, extension: str):
        try:
            # We use the internal load/unload logic
            await self.bot.reload_extension(f"cogs.{extension}")
            await interaction.response.send_message(
                f"✅ Extension `{extension}` reloaded!", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    # Simple error handler if someone else tries to use it
    @reload.error
    async def reload_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(
                "You don't have permission to reload my brains!", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Admin(bot))
