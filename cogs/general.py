import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 ({latency}ms)")

    @app_commands.command(name="clear", description="Delete Messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        if amount < 1:
            await interaction.followup.send(
                "Please specify a number greater than 0.", ephemeral=True
            )
            return
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.followup.send(
                "This command can only be used in a text channel.", ephemeral=True
            )
            return
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(
                f"Successfully purged {len(deleted)} messages of heresy!",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to delete messages here.", ephemeral=True
            )
        except discord.HTTPException as e:
            print(f"Error in /clear purge: {e}")
            await interaction.followup.send(
                "Failed to purge messages. Check bot logs for details.", ephemeral=True
            )

    @clear.error
    async def clear_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            if interaction.response.is_done():
                await interaction.followup.send(
                    "You lack permission to purge heresy!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You lack permission to purge heresy!", ephemeral=True
                )
        else:
            print(f"Clear Command Error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
