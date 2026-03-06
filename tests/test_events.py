"""Unit tests for cogs/events.py."""

import os
import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("WELCOME_CHANNEL_ID", "222")
os.environ.setdefault("INITIAL_MEMBER_ROLE_ID", "333")
os.environ.setdefault("GENERAL_CHANNEL_ID", "444")
os.environ.setdefault("SUPPORT_CHANNEL_ID", "555")
os.environ.setdefault("VC_TEXT_CHANNEL_ID", "666")
os.environ.setdefault("DCADMIN_ROLE_ID", "777")
os.environ.setdefault("NETWORKADMIN_ROLE_ID", "111")

from cogs.events import Events


def _make_member(name: str = "TestUser") -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.mention = f"<@{name}>"
    member.name = name
    member.guild = MagicMock()
    member.guild.get_role = MagicMock(return_value=MagicMock(spec=discord.Role))
    member.add_roles = AsyncMock()
    return member


# ------------------------------------------------------------------ #
#  create_welcome_embed                                                #
# ------------------------------------------------------------------ #


def test_welcome_embed_contains_mention(mock_bot):
    cog = Events(mock_bot)
    member = _make_member("Alice")
    embed = cog.create_welcome_embed(member)
    assert member.mention in embed.description


def test_welcome_embed_no_missing_space(mock_bot):
    """Ensure there is no 'a<@&' pattern — the bug that was fixed."""
    cog = Events(mock_bot)
    member = _make_member("Alice")
    embed = cog.create_welcome_embed(member)
    assert "a<@&" not in embed.description


def test_welcome_embed_utc_timestamp(mock_bot):
    """embed.timestamp must be timezone-aware (UTC)."""
    cog = Events(mock_bot)
    member = _make_member("Alice")
    embed = cog.create_welcome_embed(member)
    assert embed.timestamp is not None
    assert embed.timestamp.tzinfo is not None


def test_welcome_embed_colour(mock_bot):
    cog = Events(mock_bot)
    member = _make_member("Alice")
    embed = cog.create_welcome_embed(member)
    assert embed.color == discord.Color.from_rgb(0, 176, 244)


# ------------------------------------------------------------------ #
#  on_member_join                                                      #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_on_member_join_assigns_role(mock_bot):
    cog = Events(mock_bot)
    cog.initial_member_role_id = 333
    cog.welcome_channel_id = 222

    member = _make_member()
    role = MagicMock(spec=discord.Role)
    member.guild.get_role = MagicMock(return_value=role)

    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    mock_bot.get_channel = MagicMock(return_value=channel)

    await cog.on_member_join(member)
    member.add_roles.assert_called_once_with(role)


@pytest.mark.asyncio
async def test_on_member_join_no_role_found(mock_bot):
    """No exception when get_role returns None."""
    cog = Events(mock_bot)
    cog.initial_member_role_id = 333
    cog.welcome_channel_id = 222

    member = _make_member()
    member.guild.get_role = MagicMock(return_value=None)

    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    mock_bot.get_channel = MagicMock(return_value=channel)

    await cog.on_member_join(member)
    member.add_roles.assert_not_called()


@pytest.mark.asyncio
async def test_on_member_join_forbidden_role(mock_bot, capsys):
    """discord.Forbidden on add_roles prints error and does not raise."""
    cog = Events(mock_bot)
    cog.initial_member_role_id = 333
    cog.welcome_channel_id = 222

    member = _make_member()
    role = MagicMock(spec=discord.Role)
    member.guild.get_role = MagicMock(return_value=role)
    member.add_roles = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "Missing Permissions")
    )

    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    mock_bot.get_channel = MagicMock(return_value=channel)

    await cog.on_member_join(member)
    captured = capsys.readouterr()
    assert "permission" in captured.out.lower() or "error" in captured.out.lower()


@pytest.mark.asyncio
async def test_on_member_join_sends_welcome(mock_bot):
    cog = Events(mock_bot)
    cog.initial_member_role_id = 333
    cog.welcome_channel_id = 222

    member = _make_member()
    member.guild.get_role = MagicMock(return_value=None)

    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    mock_bot.get_channel = MagicMock(return_value=channel)

    await cog.on_member_join(member)
    channel.send.assert_called_once()
    _, kwargs = channel.send.call_args
    assert isinstance(kwargs.get("embed"), discord.Embed)


@pytest.mark.asyncio
async def test_on_member_join_wrong_channel_type(mock_bot):
    """channel.send not called if channel is not a TextChannel."""
    cog = Events(mock_bot)
    cog.initial_member_role_id = 333
    cog.welcome_channel_id = 222

    member = _make_member()
    member.guild.get_role = MagicMock(return_value=None)

    # Return a VoiceChannel (not a TextChannel)
    channel = MagicMock(spec=discord.VoiceChannel)
    channel.send = AsyncMock()
    mock_bot.get_channel = MagicMock(return_value=channel)

    await cog.on_member_join(member)
    channel.send.assert_not_called()


# ------------------------------------------------------------------ #
#  /testwelcome                                                        #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_testwelcome_sends_ephemeral(mock_bot, mock_interaction):
    cog = Events(mock_bot)
    await cog.test_welcome.callback(cog, mock_interaction)
    call_kwargs = mock_interaction.response.send_message.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert isinstance(call_kwargs.kwargs.get("embed"), discord.Embed)
