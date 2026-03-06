import os
from typing import Union

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from ampapi import (
    ActionResultError,
    AMPADSInstance,
    AMPControllerInstance,
    AMPInstance,
    AMPInstanceState,
    AMPMinecraftInstance,
    APIParams,
    Bridge,
    Players,
)

load_dotenv()


AMP_URL = os.getenv("AMP_URL") or ""
AMP_USER = os.getenv("AMP_USER") or ""
AMP_PASS = os.getenv("AMP_PASS") or ""

_params = APIParams(url=AMP_URL, user=AMP_USER, password=AMP_PASS)

NETWORKADMIN_ROLE_ID = int(os.getenv("NETWORKADMIN_ROLE_ID") or 0)

# State labels and corresponding embed colours
_STATE_COLOUR = {
    AMPInstanceState.ready: discord.Color.green(),
    AMPInstanceState.starting: discord.Color.yellow(),
    AMPInstanceState.restarting: discord.Color.yellow(),
    AMPInstanceState.stopping: discord.Color.orange(),
    AMPInstanceState.stopped: discord.Color.red(),
    AMPInstanceState.failed: discord.Color.dark_red(),
}

# States that indicate an instance is already running or coming up
_RUNNING_STATES = {
    AMPInstanceState.ready,
    AMPInstanceState.starting,
    AMPInstanceState.restarting,
}

# States that indicate an instance is already offline or going offline
_STOPPED_STATES = {
    AMPInstanceState.stopped,
    AMPInstanceState.stopping,
}

# States hidden from /amp list by default (not actively running)
_HIDDEN_STATES = {
    AMPInstanceState.stopped,
    AMPInstanceState.failed,
}


def _state_label(instance: AMPInstance) -> str:
    """Return a human-readable state string from an instance's app_state."""
    return str(instance.app_state).split(".")[-1].capitalize()


async def _get_all_instances(session: aiohttp.ClientSession) -> list:
    """Return all ADS instances as a flat list.

    Bridge() must be called first to register the singleton that
    AMPControllerInstance resolves internally via Bridge._get_bridge().
    """
    Bridge(api_params=_params)
    ADS: AMPControllerInstance = AMPControllerInstance(session=session)
    ADS.format_data = False
    await ADS.get_instances(format_data=True)
    return list(ADS.instances)


async def _find_instance(
    instance_name: str, session: aiohttp.ClientSession
) -> Union[AMPInstance, AMPMinecraftInstance, None]:
    """Find an instance by friendly name or instance name. Returns None if not found."""
    for instance in await _get_all_instances(session):
        if isinstance(instance, (AMPADSInstance, AMPInstance, AMPMinecraftInstance)):
            if (
                instance.friendly_name == instance_name
                or instance.instance_name == instance_name
            ):
                instance.format_data = True
                return instance
    return None


class AMP(commands.GroupCog, name="amp"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    # ------------------------------------------------------------------ #
    #  /amp status                                                         #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="status",
        description="Check AMP instance status. Accepts friendly name or instance name.",
    )
    async def amp_status(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return
            state = _state_label(instance)
            colour = _STATE_COLOUR.get(instance.app_state, discord.Color.greyple())
            embed = discord.Embed(
                title=instance.friendly_name,
                description=f"State: **{state}**",
                color=colour,
            )
            await interaction.followup.send(embed=embed)
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp list                                                           #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="list",
        description="List AMP instances. Use show_all to include stopped/failed instances.",
    )
    async def amp_list(
        self,
        interaction: discord.Interaction,
        show_all: bool = False,
    ):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instances = await _get_all_instances(session)

            rows = []
            for instance in instances:
                if not isinstance(
                    instance, (AMPADSInstance, AMPInstance, AMPMinecraftInstance)
                ):
                    continue
                state_enum = instance.app_state
                if not show_all and state_enum in _HIDDEN_STATES:
                    continue
                state = _state_label(instance)
                colour_indicator = (
                    "🟢"
                    if state_enum == AMPInstanceState.ready
                    else "🔴"
                    if state_enum in _HIDDEN_STATES
                    else "🟡"
                )
                rows.append(
                    f"{colour_indicator} **{instance.friendly_name}** — {state}"
                )

            if not rows:
                label = "instances" if show_all else "running instances"
                await interaction.followup.send(f"No {label} found.", ephemeral=True)
                return

            embed = discord.Embed(
                title="AMP Instances",
                description="\n".join(rows),
                color=discord.Color.blurple(),
            )
            embed.set_footer(
                text=f"{'All' if show_all else 'Running'} instances • {len(rows)} shown"
            )
            await interaction.followup.send(embed=embed)
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp start                                                          #
    # ------------------------------------------------------------------ #
    @app_commands.command(name="start", description="Start an AMP instance.")
    async def amp_start(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state in _RUNNING_STATES:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is already running or starting.",
                    ephemeral=True,
                )
                return

            try:
                await instance.start_instance()
                await interaction.followup.send(
                    f"Starting instance `{instance.friendly_name}`..."
                )
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` could not be started.",
                    ephemeral=True,
                )
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp stop                                                           #
    # ------------------------------------------------------------------ #
    @app_commands.command(name="stop", description="Stop an AMP instance.")
    async def amp_stop(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state in _STOPPED_STATES:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is already offline or stopping.",
                    ephemeral=True,
                )
                return

            try:
                await instance.stop_instance()
                await interaction.followup.send(
                    f"Stopping instance `{instance.friendly_name}`..."
                )
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not available.",
                    ephemeral=True,
                )
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp restart                                                        #
    # ------------------------------------------------------------------ #
    @app_commands.command(name="restart", description="Restart an AMP instance.")
    async def amp_restart(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            try:
                await instance.restart_instance()
                await interaction.followup.send(
                    f"Restarting instance `{instance.friendly_name}`..."
                )
            except ConnectionError:
                msg = (
                    f"Instance `{instance.friendly_name}` is offline and cannot be "
                    "restarted. Use `/amp start` instead."
                )
                await interaction.followup.send(msg, ephemeral=True)
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp players                                                        #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="players",
        description="Show players currently connected to an AMP instance.",
    )
    async def amp_players(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state != AMPInstanceState.ready:
                state = _state_label(instance)
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not ready "
                    f"(current state: **{state}**).",
                    ephemeral=True,
                )
                return

            try:
                players: Union[
                    Players, ActionResultError
                ] = await instance.get_user_list(format_data=True)
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not available.",
                    ephemeral=True,
                )
                return

            if isinstance(players, ActionResultError) or players is None:
                await interaction.followup.send(
                    f"Could not retrieve player list for `{instance.friendly_name}`.",
                    ephemeral=True,
                )
                return

            player_list = players.sorted
            count = len(player_list)

            embed = discord.Embed(
                title=f"Players on {instance.friendly_name}",
                color=discord.Color.green() if count > 0 else discord.Color.greyple(),
            )

            if count == 0:
                embed.description = "No players currently connected."
            else:
                embed.description = "\n".join(f"• {p.name}" for p in player_list)

            embed.set_footer(text=f"{count} player{'s' if count != 1 else ''} online")
            await interaction.followup.send(embed=embed)
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp stats                                                          #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="stats",
        description="Show CPU, memory and player metrics for an AMP instance.",
    )
    async def amp_stats(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state != AMPInstanceState.ready:
                state = _state_label(instance)
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not ready "
                    f"(current state: **{state}**).",
                    ephemeral=True,
                )
                return

            try:
                status = await instance.get_status(format_data=True)
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not available.",
                    ephemeral=True,
                )
                return

            if isinstance(status, ActionResultError):
                await interaction.followup.send(
                    f"Could not retrieve stats for `{instance.friendly_name}`.",
                    ephemeral=True,
                )
                return

            metrics = status.metrics
            colour = _STATE_COLOUR.get(instance.app_state, discord.Color.greyple())
            embed = discord.Embed(
                title=f"Stats — {instance.friendly_name}",
                color=colour,
            )

            if metrics:
                if metrics.cpu_usage:
                    cpu = metrics.cpu_usage
                    embed.add_field(
                        name="CPU Usage",
                        value=f"**{cpu.percent}%** ({cpu.raw_value} / {cpu.max_value} {cpu.units})",
                        inline=True,
                    )
                if metrics.memory_usage:
                    mem = metrics.memory_usage
                    embed.add_field(
                        name="Memory Usage",
                        value=f"**{mem.percent}%** ({mem.raw_value} / {mem.max_value} {mem.units})",
                        inline=True,
                    )
                if metrics.active_users:
                    users = metrics.active_users
                    embed.add_field(
                        name="Active Players",
                        value=f"**{users.raw_value}** / {users.max_value}",
                        inline=True,
                    )
            else:
                embed.description = "No metrics available."

            embed.add_field(name="State", value=_state_label(instance), inline=False)
            await interaction.followup.send(embed=embed)
        finally:
            await session.close()

    # ------------------------------------------------------------------ #
    #  /amp console                                                        #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="console",
        description="[Admin] Send a console command to an AMP instance.",
    )
    @app_commands.checks.has_role(NETWORKADMIN_ROLE_ID)
    async def amp_console(
        self,
        interaction: discord.Interaction,
        instance_name: str,
        command: str,
    ):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state != AMPInstanceState.ready:
                state = _state_label(instance)
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not ready "
                    f"(current state: **{state}**).",
                    ephemeral=True,
                )
                return

            try:
                await instance.send_console_message(msg=command)
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not available.",
                    ephemeral=True,
                )
                return

            # Fetch recent console output for confirmation
            console_block: str
            try:
                updates = await instance.get_updates(format_data=True)
                if isinstance(updates, ActionResultError):
                    console_block = "*Could not retrieve console output.*"
                else:
                    entries = (
                        updates.console_entries[-5:] if updates.console_entries else []
                    )
                    if entries:
                        output = "\n".join(
                            f"[{e.source}] {e.contents}" for e in entries
                        )
                        # Sanitise triple backticks to prevent markdown escape
                        output = output.replace("```", "'''")
                        console_block = f"```\n{output}\n```"
                    else:
                        console_block = "*No console output returned.*"
            except Exception as e:
                print(
                    f"Error fetching console updates for {instance.friendly_name}: {e}"
                )
                console_block = "*Could not retrieve console output.*"

            # Sanitise user-supplied command string before displaying in embed
            safe_command = command.replace("`", "'")
            embed = discord.Embed(
                title=f"Console — {instance.friendly_name}",
                color=discord.Color.blurple(),
            )
            embed.add_field(
                name="Command sent", value=f"`{safe_command}`", inline=False
            )
            embed.add_field(name="Recent output", value=console_block, inline=False)
            await interaction.followup.send(embed=embed)
        finally:
            await session.close()

    @amp_console.error
    async def amp_console_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(
                "You don't have permission to send console commands.", ephemeral=True
            )

    # ------------------------------------------------------------------ #
    #  /amp kill                                                           #
    # ------------------------------------------------------------------ #
    @app_commands.command(
        name="kill",
        description="[Admin] Force-kill a hung AMP instance.",
    )
    @app_commands.checks.has_role(NETWORKADMIN_ROLE_ID)
    async def amp_kill(self, interaction: discord.Interaction, instance_name: str):
        await interaction.response.defer()
        session = aiohttp.ClientSession()
        try:
            instance = await _find_instance(instance_name, session)
            if instance is None:
                await interaction.followup.send(
                    f"Instance `{instance_name}` not found.", ephemeral=True
                )
                return

            if instance.app_state in _STOPPED_STATES:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is already offline or stopping.",
                    ephemeral=True,
                )
                return

            try:
                await instance.kill_application()
                await interaction.followup.send(
                    f"Force-killed instance `{instance.friendly_name}`."
                )
            except ConnectionError:
                await interaction.followup.send(
                    f"Instance `{instance.friendly_name}` is not available.",
                    ephemeral=True,
                )
        finally:
            await session.close()

    @amp_kill.error
    async def amp_kill_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(
                "You don't have permission to force-kill instances.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AMP(bot))
