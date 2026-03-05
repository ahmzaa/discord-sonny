import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bots latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 ({latency}ms)")

    @app_commands.command(name="clear", description="Delete Messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.channel.purge(limit=amount, bulk=True)
        await interaction.response.send_message(
            "Channel Purged of heresey !!", ephemeral=True
        )

    @clear.error
    async def clear_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(General(bot))
