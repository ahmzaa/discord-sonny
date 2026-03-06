import asyncio
import platform

import discord
import psutil
from discord import app_commands
from discord.ext import commands


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="system", description="Check the LXC container health")
    async def system_status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Run blocking psutil calls off the event loop
        loop = asyncio.get_event_loop()
        cpu_usage = await loop.run_in_executor(None, psutil.cpu_percent, 1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = discord.utils.format_dt(
            discord.utils.utcnow()
            .replace(second=0, microsecond=0)
            .__class__.fromtimestamp(psutil.boot_time()),
            style="F",
        )

        embed = discord.Embed(
            title="🖥️ System Status (LXC)",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
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

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(System(bot))
