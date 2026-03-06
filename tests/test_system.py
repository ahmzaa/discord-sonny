"""Unit tests for cogs/system.py."""

import asyncio
import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch, call

from cogs.system import System


def _psutil_mocks():
    """Returns a dict of patch targets and their mock return values."""
    ram = MagicMock()
    ram.percent = 42.0
    ram.used = 1024**3  # 1 GB
    ram.total = 4 * 1024**3  # 4 GB

    disk = MagicMock()
    disk.percent = 55.0

    return {
        "psutil.virtual_memory": MagicMock(return_value=ram),
        "psutil.disk_usage": MagicMock(return_value=disk),
        "psutil.boot_time": MagicMock(return_value=0.0),
        "platform.system": MagicMock(return_value="Linux"),
        "platform.release": MagicMock(return_value="5.15.0"),
    }


@pytest.mark.asyncio
async def test_system_defers_first(mock_bot, mock_interaction):
    """response.defer() must be called before followup.send()."""
    mocks = _psutil_mocks()
    call_order = []

    mock_interaction.response.defer = AsyncMock(
        side_effect=lambda: call_order.append("defer")
    )
    mock_interaction.followup.send = AsyncMock(
        side_effect=lambda **kw: call_order.append("send")
    )

    with (
        patch("asyncio.get_event_loop") as mock_loop_fn,
        patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
        patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
        patch("psutil.boot_time", mocks["psutil.boot_time"]),
        patch("platform.system", mocks["platform.system"]),
        patch("platform.release", mocks["platform.release"]),
    ):
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value=25.0)
        mock_loop_fn.return_value = mock_loop
        cog = System(mock_bot)
        await cog.system_status.callback(cog, mock_interaction)

    assert call_order.index("defer") < call_order.index("send")


@pytest.mark.asyncio
async def test_system_embed_has_required_fields(mock_bot, mock_interaction):
    """Embed must contain CPU, RAM, Disk, OS, and uptime fields."""
    mocks = _psutil_mocks()

    with (
        patch("asyncio.get_event_loop") as mock_loop_fn,
        patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
        patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
        patch("psutil.boot_time", mocks["psutil.boot_time"]),
        patch("platform.system", mocks["platform.system"]),
        patch("platform.release", mocks["platform.release"]),
    ):
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value=25.0)
        mock_loop_fn.return_value = mock_loop
        cog = System(mock_bot)
        await cog.system_status.callback(cog, mock_interaction)

    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert embed is not None
    assert isinstance(embed, discord.Embed)
    field_names = [f.name for f in embed.fields]
    assert "CPU Usage" in field_names
    assert "RAM Usage" in field_names
    assert "Disk Space" in field_names
    assert "OS" in field_names
    assert "LXC Booted Since" in field_names


@pytest.mark.asyncio
async def test_system_uses_executor_for_cpu(mock_bot, mock_interaction):
    """cpu_percent must be run via run_in_executor, not called directly."""
    mocks = _psutil_mocks()

    with patch("asyncio.get_event_loop") as mock_loop_fn:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value=33.0)
        mock_loop_fn.return_value = mock_loop
        with (
            patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
            patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
            patch("psutil.boot_time", mocks["psutil.boot_time"]),
            patch("platform.system", mocks["platform.system"]),
            patch("platform.release", mocks["platform.release"]),
        ):
            cog = System(mock_bot)
            await cog.system_status.callback(cog, mock_interaction)

    mock_loop.run_in_executor.assert_called_once()


@pytest.mark.asyncio
async def test_system_utc_timestamp(mock_bot, mock_interaction):
    """Embed timestamp must be timezone-aware."""
    mocks = _psutil_mocks()

    with patch("asyncio.get_event_loop") as mock_loop_fn:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value=10.0)
        mock_loop_fn.return_value = mock_loop
        with (
            patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
            patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
            patch("psutil.boot_time", mocks["psutil.boot_time"]),
            patch("platform.system", mocks["platform.system"]),
            patch("platform.release", mocks["platform.release"]),
        ):
            cog = System(mock_bot)
            await cog.system_status.callback(cog, mock_interaction)

    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert embed.timestamp is not None
    assert embed.timestamp.tzinfo is not None
