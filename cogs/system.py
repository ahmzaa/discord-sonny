import discord
from discord import app_commands
from discord.ext import commands
import psutil
import platform
import datetime


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="system", description="Check the LXC container health")
    async def system_status(self, interaction: discord.Interaction):
        # Gathering system data
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Creating the status embed
        embed = discord.Embed(
            title="🖥️ System Status (LXC)",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )

        embed.add_field(name="CPU Usage", value=f"**{cpu_usage}%**", inline=True)
        embed.add_field(
            name="RAM Usage",
            value=f"**{ram.percent}%** ({round(ram.used / (1024**2))}MB / {round(ram.total / (1024**2))}MB)",
            inline=True,
        )
        embed.add_field(
            name="Disk Space", value=f"**{disk.percent}%** used", inline=True
        )
        embed.add_field(
            name="OS", value=f"{platform.system()} {platform.release()}", inline=False
        )
        embed.add_field(name="LXC Booted Since", value=uptime, inline=False)

        embed.set_footer(text=f"Bot Latency: {round(self.bot.latency * 1000)}ms")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(System(bot))
