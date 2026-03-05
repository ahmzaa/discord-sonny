import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from typing import Union
from dotenv import load_dotenv

from ampapi import (
    ActionResultError,
    AMPADSInstance,
    AMPControllerInstance,
    AMPInstance,
    AMPInstanceState,
    AMPMinecraftInstance,
    AnalyticsFilter,
    AnalyticsSummary,
    APIParams,
    Bridge,
    Players,
)

load_dotenv()


AMP_URL = os.getenv("AMP_URL")
AMP_USER = os.getenv("AMP_USER")
AMP_PASS = os.getenv("AMP_PASS")

_params = APIParams(url=AMP_URL, user=AMP_USER, password=AMP_PASS)


class AMP(commands.GroupCog, name="amp"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # -- SLASH COMMAND: status
    @app_commands.command(
        name="status",
        description="check amp instance status. Accepts Friendly name as well as Instance name. i.e Valheim or Valheim01",
    )
    async def ampstatus(self, interaction: discord.Interaction, instance_name: str):
        _bridge = Bridge(api_params=_params)
        session: aiohttp.ClientSession = aiohttp.ClientSession()
        ADS: AMPControllerInstance = AMPControllerInstance(session=session)
        ADS.format_data = False

        await ADS.get_instances(format_data=True)
        ADSinstances = list(ADS.instances)

        selected_instance: Union[AMPInstance, None] = None

        print("--- ADS INSTANCES ---")
        for instance in ADSinstances:
            print(
                f"fname:{instance.friendly_name}, iname:{instance.instance_name}, iid:{instance.instance_id}"
            )
            if isinstance(
                instance, (AMPADSInstance, AMPInstance, AMPMinecraftInstance)
            ):
                if (
                    instance.friendly_name == instance_name
                    or instance.instance_name == instance_name
                ):
                    selected_instance = instance

        if selected_instance is None:
            return

        selected_instance.format_data = True

        selected_instance_name = selected_instance.friendly_name
        selected_instance_state = str(selected_instance.app_state).rsplit(".")

        await interaction.response.send_message(
            f"Instance: `{selected_instance_name}` is `{selected_instance_state[1].capitalize()}`"
        )

        await session.close()


async def setup(bot):
    await bot.add_cog(AMP(bot))
