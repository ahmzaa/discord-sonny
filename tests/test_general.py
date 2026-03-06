"""Unit tests for cogs/general.py."""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock

from cogs.general import General


# ------------------------------------------------------------------ #
#  /ping                                                               #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_ping_response_contains_ms(mock_bot, mock_interaction):
    cog = General(mock_bot)
    await cog.ping.callback(cog, mock_interaction)
    call_args = mock_interaction.response.send_message.call_args
    assert "ms" in call_args.args[0]


@pytest.mark.asyncio
async def test_ping_uses_bot_latency(mock_bot, mock_interaction):
    mock_bot.latency = 0.123
    cog = General(mock_bot)
    await cog.ping.callback(cog, mock_interaction)
    call_args = mock_interaction.response.send_message.call_args
    assert "123" in call_args.args[0]


# ------------------------------------------------------------------ #
#  /clear                                                              #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_clear_amount_zero_sends_ephemeral(mock_bot, mock_interaction):
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 0)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "greater than 0" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_clear_amount_negative_sends_ephemeral(mock_bot, mock_interaction):
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, -5)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_clear_wrong_channel_type_sends_ephemeral(mock_bot, mock_interaction):
    """Ephemeral error when channel is not a TextChannel."""
    mock_interaction.channel = MagicMock(spec=discord.VoiceChannel)
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 5)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    # purge should not have been called
    assert (
        not hasattr(mock_interaction.channel, "purge")
        or not mock_interaction.channel.purge.called
    )


@pytest.mark.asyncio
async def test_clear_success_calls_purge(mock_bot, mock_interaction):
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 5)
    mock_interaction.channel.purge.assert_called_once_with(limit=5)


@pytest.mark.asyncio
async def test_clear_success_reports_count(mock_bot, mock_interaction):
    # purge returns 3 deleted messages by default from the fixture
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 5)
    call_kwargs = mock_interaction.followup.send.call_args
    assert "3" in call_kwargs.args[0]


@pytest.mark.asyncio
async def test_clear_forbidden_sends_ephemeral(mock_bot, mock_interaction):
    mock_interaction.channel.purge = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "Missing Permissions")
    )
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 5)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    # Raw exception must not be leaked to the user
    assert "Missing Permissions" not in call_kwargs.args[0]


@pytest.mark.asyncio
async def test_clear_http_exception_does_not_leak_raw_error(mock_bot, mock_interaction):
    mock_interaction.channel.purge = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(), "internal error details")
    )
    cog = General(mock_bot)
    await cog.clear.callback(cog, mock_interaction, 5)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    # Raw exception message must not be forwarded to Discord
    assert "internal error details" not in call_kwargs.args[0]
