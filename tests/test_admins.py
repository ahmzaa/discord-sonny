"""Unit tests for cogs/admins.py."""

import os
import pytest
import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("NETWORKADMIN_ROLE_ID", "111")

from cogs.admins import Admin


# ------------------------------------------------------------------ #
#  /reload                                                             #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_reload_success(mock_bot, mock_interaction):
    mock_bot.reload_extension = AsyncMock()
    cog = Admin(mock_bot)
    await cog.reload.callback(cog, mock_interaction, "amp")
    mock_bot.reload_extension.assert_called_once_with("cogs.amp")
    call_kwargs = mock_interaction.response.send_message.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "reloaded" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_reload_extension_error_logs_and_sends_safe_message(
    mock_bot, mock_interaction, capsys
):
    """ExtensionError: logs to stdout, sends sanitised message to Discord."""
    mock_bot.reload_extension = AsyncMock(side_effect=commands.ExtensionNotFound("amp"))
    cog = Admin(mock_bot)
    await cog.reload.callback(cog, mock_interaction, "amp")

    # Should have printed to stdout
    captured = capsys.readouterr()
    assert "amp" in captured.out.lower() or "extension" in captured.out.lower()

    # Discord message should not expose raw exception
    call_kwargs = mock_interaction.response.send_message.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    sent_msg = call_kwargs.args[0]
    assert "syntax error" not in sent_msg
    assert "logs" in sent_msg.lower() or "failed" in sent_msg.lower()


@pytest.mark.asyncio
async def test_reload_unexpected_error_logs_and_sends_safe_message(
    mock_bot, mock_interaction, capsys
):
    """Unexpected error: logs to stdout, sends sanitised message to Discord."""
    mock_bot.reload_extension = AsyncMock(
        side_effect=RuntimeError("/home/user/secrets/path_leaked")
    )
    cog = Admin(mock_bot)
    await cog.reload.callback(cog, mock_interaction, "amp")

    captured = capsys.readouterr()
    assert "unexpected" in captured.out.lower() or "error" in captured.out.lower()

    call_kwargs = mock_interaction.response.send_message.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    sent_msg = call_kwargs.args[0]
    # Internal path must not be leaked to the user
    assert "/home/user/secrets/path_leaked" not in sent_msg
