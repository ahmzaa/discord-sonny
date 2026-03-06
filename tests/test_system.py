"""Unit tests for cogs/system.py."""

import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch

from cogs.system import System


def _make_mocks_and_loop():
    """Returns (mocks dict, mock_loop) for patching psutil and the event loop."""
    ram = MagicMock()
    ram.percent = 42.0
    ram.used = 1024**3  # 1 GB
    ram.total = 4 * 1024**3  # 4 GB

    disk = MagicMock()
    disk.percent = 55.0

    mocks = {
        "psutil.virtual_memory": MagicMock(return_value=ram),
        "psutil.disk_usage": MagicMock(return_value=disk),
        "psutil.boot_time": MagicMock(return_value=0.0),
        "platform.system": MagicMock(return_value="Linux"),
        "platform.release": MagicMock(return_value="5.15.0"),
    }

    mock_loop = MagicMock()
    # run_in_executor is called 4 times (cpu, ram, disk, boot_time)
    # Return values: cpu=25.0, ram mock, disk mock, boot_time=0.0
    mock_loop.run_in_executor = AsyncMock(side_effect=[25.0, ram, disk, 0.0])

    return mocks, mock_loop


@pytest.mark.asyncio
async def test_system_defers_first(mock_bot, mock_interaction):
    """response.defer() must be called before followup.send()."""
    mocks, mock_loop = _make_mocks_and_loop()
    call_order = []

    mock_interaction.response.defer = AsyncMock(
        side_effect=lambda: call_order.append("defer")
    )
    mock_interaction.followup.send = AsyncMock(
        side_effect=lambda **kw: call_order.append("send")
    )

    with (
        patch("asyncio.get_running_loop", return_value=mock_loop),
        patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
        patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
        patch("psutil.boot_time", mocks["psutil.boot_time"]),
        patch("platform.system", mocks["platform.system"]),
        patch("platform.release", mocks["platform.release"]),
    ):
        cog = System(mock_bot)
        await cog.system_status.callback(cog, mock_interaction)

    assert call_order.index("defer") < call_order.index("send")


@pytest.mark.asyncio
async def test_system_embed_has_required_fields(mock_bot, mock_interaction):
    """Embed must contain CPU, RAM, Disk, OS, and uptime fields."""
    mocks, mock_loop = _make_mocks_and_loop()

    with (
        patch("asyncio.get_running_loop", return_value=mock_loop),
        patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
        patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
        patch("psutil.boot_time", mocks["psutil.boot_time"]),
        patch("platform.system", mocks["platform.system"]),
        patch("platform.release", mocks["platform.release"]),
    ):
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
async def test_system_uses_executor_for_all_blocking_calls(mock_bot, mock_interaction):
    """All blocking psutil calls must go through run_in_executor."""
    mocks, mock_loop = _make_mocks_and_loop()

    with (
        patch("asyncio.get_running_loop", return_value=mock_loop),
        patch("psutil.virtual_memory", mocks["psutil.virtual_memory"]),
        patch("psutil.disk_usage", mocks["psutil.disk_usage"]),
        patch("psutil.boot_time", mocks["psutil.boot_time"]),
        patch("platform.system", mocks["platform.system"]),
        patch("platform.release", mocks["platform.release"]),
    ):
        cog = System(mock_bot)
        await cog.system_status.callback(cog, mock_interaction)

    # cpu_percent, virtual_memory, disk_usage, boot_time = 4 executor calls
    assert mock_loop.run_in_executor.call_count == 4


@pytest.mark.asyncio
async def test_system_utc_timestamp(mock_bot, mock_interaction):
    """Embed timestamp must be timezone-aware."""
    mocks, mock_loop = _make_mocks_and_loop()

    with (
        patch("asyncio.get_running_loop", return_value=mock_loop),
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
