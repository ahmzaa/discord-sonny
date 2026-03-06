"""Shared fixtures for all test modules."""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock

from ampapi import AMPInstance, AMPInstanceState


@pytest.fixture
def mock_bot():
    """A minimal mock of commands.Bot."""
    bot = MagicMock()
    bot.latency = 0.05
    bot.user = MagicMock(spec=discord.ClientUser)
    bot.user.display_avatar = MagicMock()
    bot.user.display_avatar.url = "https://example.com/avatar.png"
    return bot


@pytest.fixture
def mock_interaction():
    """A mock discord.Interaction with async response/followup methods."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    # Default to a TextChannel so purge/send are available
    channel = MagicMock(spec=discord.TextChannel)
    channel.purge = AsyncMock(return_value=[MagicMock() for _ in range(3)])
    interaction.channel = channel

    user = MagicMock(spec=discord.Member)
    user.mention = "<@123456789>"
    interaction.user = user

    return interaction


def make_mock_instance(
    friendly_name: str = "TestInstance",
    instance_name: str = "test_instance",
    app_state: AMPInstanceState = AMPInstanceState.ready,
) -> MagicMock:
    """
    Factory for a mock AMPInstance with configurable name and state.
    Can be used directly in tests without going through a fixture.
    """
    instance = MagicMock(spec=AMPInstance)
    instance.friendly_name = friendly_name
    instance.instance_name = instance_name
    instance.app_state = app_state
    instance.format_data = True
    instance.start_instance = AsyncMock()
    instance.stop_instance = AsyncMock()
    instance.restart_instance = AsyncMock()
    instance.kill_application = AsyncMock()
    instance.get_user_list = AsyncMock()
    instance.get_status = AsyncMock()
    instance.get_updates = AsyncMock()
    instance.send_console_message = AsyncMock()
    return instance
