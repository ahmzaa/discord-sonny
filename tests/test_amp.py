"""Unit tests for cogs/amp.py."""

import os
import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("NETWORKADMIN_ROLE_ID", "111")
os.environ.setdefault("AMP_URL", "http://localhost:8080")
os.environ.setdefault("AMP_USER", "admin")
os.environ.setdefault("AMP_PASS", "password")

from ampapi import AMPInstanceState, AMPInstance, AMPMinecraftInstance
from ampapi.modules import Players, Player

from cogs.amp import (
    _state_label,
    _find_instance,
    _RUNNING_STATES,
    _STOPPED_STATES,
    _HIDDEN_STATES,
    _STATE_COLOUR,
    AMP,
)
from tests.conftest import make_mock_instance


# ------------------------------------------------------------------ #
#  _state_label                                                        #
# ------------------------------------------------------------------ #


def test_state_label_ready():
    instance = make_mock_instance(app_state=AMPInstanceState.ready)
    assert _state_label(instance) == "Ready"


def test_state_label_stopped():
    instance = make_mock_instance(app_state=AMPInstanceState.stopped)
    assert _state_label(instance) == "Stopped"


@pytest.mark.parametrize("state", list(AMPInstanceState))
def test_state_label_all_states(state):
    instance = make_mock_instance(app_state=state)
    label = _state_label(instance)
    assert isinstance(label, str)
    assert len(label) > 0
    assert label[0].isupper()


# ------------------------------------------------------------------ #
#  _find_instance                                                      #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_find_instance_by_friendly_name():
    inst = make_mock_instance(friendly_name="MyServer", instance_name="myserver01")
    with patch("cogs.amp._get_all_instances", AsyncMock(return_value=[inst])):
        result = await _find_instance("MyServer", MagicMock())
    assert result is inst


@pytest.mark.asyncio
async def test_find_instance_by_instance_name():
    inst = make_mock_instance(friendly_name="MyServer", instance_name="myserver01")
    with patch("cogs.amp._get_all_instances", AsyncMock(return_value=[inst])):
        result = await _find_instance("myserver01", MagicMock())
    assert result is inst


@pytest.mark.asyncio
async def test_find_instance_not_found():
    inst = make_mock_instance(friendly_name="OtherServer", instance_name="other01")
    with patch("cogs.amp._get_all_instances", AsyncMock(return_value=[inst])):
        result = await _find_instance("nonexistent", MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_find_instance_empty_list():
    with patch("cogs.amp._get_all_instances", AsyncMock(return_value=[])):
        result = await _find_instance("anything", MagicMock())
    assert result is None


# ------------------------------------------------------------------ #
#  /amp status                                                         #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_status_not_found(mock_bot, mock_interaction):
    cog = AMP(mock_bot)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=None)):
        await cog.amp_status.callback(cog, mock_interaction, "ghost")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "not found" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_amp_status_found_sends_embed(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_status.callback(cog, mock_interaction, "TestInstance")
    call_kwargs = mock_interaction.followup.send.call_args
    embed = call_kwargs.kwargs.get("embed")
    assert embed is not None
    assert isinstance(embed, discord.Embed)
    assert embed.color == _STATE_COLOUR[AMPInstanceState.ready]


# ------------------------------------------------------------------ #
#  /amp start                                                          #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
@pytest.mark.parametrize("state", list(_RUNNING_STATES))
async def test_amp_start_already_running(mock_bot, mock_interaction, state):
    inst = make_mock_instance(app_state=state)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_start.callback(cog, mock_interaction, "TestInstance")
    inst.start_instance.assert_not_called()
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_amp_start_success(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.stopped)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_start.callback(cog, mock_interaction, "TestInstance")
    inst.start_instance.assert_called_once()
    assert mock_interaction.followup.send.called


@pytest.mark.asyncio
async def test_amp_start_connection_error(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.stopped)
    inst.start_instance = AsyncMock(side_effect=ConnectionError)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_start.callback(cog, mock_interaction, "TestInstance")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True


# ------------------------------------------------------------------ #
#  /amp stop                                                           #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
@pytest.mark.parametrize("state", list(_STOPPED_STATES))
async def test_amp_stop_already_stopped(mock_bot, mock_interaction, state):
    inst = make_mock_instance(app_state=state)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stop.callback(cog, mock_interaction, "TestInstance")
    inst.stop_instance.assert_not_called()
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_amp_stop_success(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stop.callback(cog, mock_interaction, "TestInstance")
    inst.stop_instance.assert_called_once()


@pytest.mark.asyncio
async def test_amp_stop_connection_error_message(mock_bot, mock_interaction):
    """ConnectionError should say 'not available', not 'already offline'."""
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    inst.stop_instance = AsyncMock(side_effect=ConnectionError)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stop.callback(cog, mock_interaction, "TestInstance")
    call_kwargs = mock_interaction.followup.send.call_args
    assert "not available" in call_kwargs.args[0].lower()
    assert "already offline" not in call_kwargs.args[0].lower()


# ------------------------------------------------------------------ #
#  /amp list                                                           #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_list_filters_failed_by_default(mock_bot, mock_interaction):
    running = make_mock_instance("RunningServer", app_state=AMPInstanceState.ready)
    failed = make_mock_instance("FailedServer", app_state=AMPInstanceState.failed)
    with patch(
        "cogs.amp._get_all_instances", AsyncMock(return_value=[running, failed])
    ):
        cog = AMP(mock_bot)
        await cog.amp_list.callback(cog, mock_interaction, show_all=False)
    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert "RunningServer" in embed.description
    assert "FailedServer" not in embed.description


@pytest.mark.asyncio
async def test_amp_list_shows_failed_when_show_all(mock_bot, mock_interaction):
    running = make_mock_instance("RunningServer", app_state=AMPInstanceState.ready)
    failed = make_mock_instance("FailedServer", app_state=AMPInstanceState.failed)
    with patch(
        "cogs.amp._get_all_instances", AsyncMock(return_value=[running, failed])
    ):
        cog = AMP(mock_bot)
        await cog.amp_list.callback(cog, mock_interaction, show_all=True)
    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert "RunningServer" in embed.description
    assert "FailedServer" in embed.description


@pytest.mark.asyncio
async def test_amp_list_empty(mock_bot, mock_interaction):
    stopped = make_mock_instance("StoppedServer", app_state=AMPInstanceState.stopped)
    with patch("cogs.amp._get_all_instances", AsyncMock(return_value=[stopped])):
        cog = AMP(mock_bot)
        await cog.amp_list.callback(cog, mock_interaction, show_all=False)
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "no" in call_kwargs.args[0].lower()


# ------------------------------------------------------------------ #
#  /amp players                                                        #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_players_not_running(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.stopped)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_players.callback(cog, mock_interaction, "TestInstance")
    inst.get_user_list.assert_not_called()
    assert mock_interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_amp_players_empty(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    mock_players = MagicMock(spec=Players)
    mock_players.sorted = []
    inst.get_user_list = AsyncMock(return_value=mock_players)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_players.callback(cog, mock_interaction, "TestInstance")
    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert "no players" in embed.description.lower()


@pytest.mark.asyncio
async def test_amp_players_with_players(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    mock_players = MagicMock(spec=Players)
    mock_players.sorted = [
        Player(uuid="aaa", name="Alice"),
        Player(uuid="bbb", name="Bob"),
    ]
    inst.get_user_list = AsyncMock(return_value=mock_players)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_players.callback(cog, mock_interaction, "TestInstance")
    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert "Alice" in embed.description
    assert "Bob" in embed.description


# ------------------------------------------------------------------ #
#  /amp console — backtick sanitisation                               #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_console_sanitises_backticks(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)

    entry = MagicMock()
    entry.source = "Server"
    entry.contents = "some output with ```backticks```"

    updates = MagicMock()
    updates.console_entries = [entry]
    inst.get_updates = AsyncMock(return_value=updates)

    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_console.callback(
            cog, mock_interaction, "TestInstance", "say hello"
        )

    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    output_field = next(f for f in embed.fields if f.name == "Recent output")
    assert "```backticks```" not in output_field.value
    assert "'''backticks'''" in output_field.value


# ------------------------------------------------------------------ #
#  /amp restart                                                        #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_restart_not_found(mock_bot, mock_interaction):
    with patch("cogs.amp._find_instance", AsyncMock(return_value=None)):
        cog = AMP(mock_bot)
        await cog.amp_restart.callback(cog, mock_interaction, "ghost")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "not found" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_amp_restart_success(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_restart.callback(cog, mock_interaction, "TestInstance")
    inst.restart_instance.assert_called_once()
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is None or not call_kwargs.kwargs.get(
        "ephemeral"
    )


@pytest.mark.asyncio
async def test_amp_restart_connection_error(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    inst.restart_instance = AsyncMock(side_effect=ConnectionError)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_restart.callback(cog, mock_interaction, "TestInstance")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "offline" in call_kwargs.args[0].lower()


# ------------------------------------------------------------------ #
#  /amp kill                                                           #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_kill_not_found(mock_bot, mock_interaction):
    with patch("cogs.amp._find_instance", AsyncMock(return_value=None)):
        cog = AMP(mock_bot)
        await cog.amp_kill.callback(cog, mock_interaction, "ghost")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "not found" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("state", list(_STOPPED_STATES))
async def test_amp_kill_already_stopped(mock_bot, mock_interaction, state):
    inst = make_mock_instance(app_state=state)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_kill.callback(cog, mock_interaction, "TestInstance")
    inst.kill_application.assert_not_called()
    assert mock_interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_amp_kill_success(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_kill.callback(cog, mock_interaction, "TestInstance")
    inst.kill_application.assert_called_once()
    call_kwargs = mock_interaction.followup.send.call_args
    assert "force-killed" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_amp_kill_connection_error(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    inst.kill_application = AsyncMock(side_effect=ConnectionError)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_kill.callback(cog, mock_interaction, "TestInstance")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "not available" in call_kwargs.args[0].lower()


# ------------------------------------------------------------------ #
#  /amp stats                                                          #
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_amp_stats_not_found(mock_bot, mock_interaction):
    with patch("cogs.amp._find_instance", AsyncMock(return_value=None)):
        cog = AMP(mock_bot)
        await cog.amp_stats.callback(cog, mock_interaction, "ghost")
    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "not found" in call_kwargs.args[0].lower()


@pytest.mark.asyncio
async def test_amp_stats_not_running(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.stopped)
    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stats.callback(cog, mock_interaction, "TestInstance")
    inst.get_status.assert_not_called()
    assert mock_interaction.followup.send.call_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_amp_stats_success_with_metrics(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)

    cpu = MagicMock()
    cpu.percent = 42
    cpu.raw_value = 42
    cpu.max_value = 100
    cpu.units = "%"

    mem = MagicMock()
    mem.percent = 60
    mem.raw_value = 2048
    mem.max_value = 4096
    mem.units = "MB"

    metrics = MagicMock()
    metrics.cpu_usage = cpu
    metrics.memory_usage = mem
    metrics.active_users = None

    status = MagicMock()
    status.metrics = metrics
    inst.get_status = AsyncMock(return_value=status)

    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stats.callback(cog, mock_interaction, "TestInstance")

    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert embed is not None
    field_names = [f.name for f in embed.fields]
    assert "CPU Usage" in field_names
    assert "Memory Usage" in field_names


@pytest.mark.asyncio
async def test_amp_stats_no_metrics(mock_bot, mock_interaction):
    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    status = MagicMock()
    status.metrics = None
    inst.get_status = AsyncMock(return_value=status)

    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stats.callback(cog, mock_interaction, "TestInstance")

    embed = mock_interaction.followup.send.call_args.kwargs.get("embed")
    assert "no metrics" in embed.description.lower()


@pytest.mark.asyncio
async def test_amp_stats_action_result_error(mock_bot, mock_interaction):
    from ampapi import ActionResultError

    inst = make_mock_instance(app_state=AMPInstanceState.ready)
    inst.get_status = AsyncMock(return_value=MagicMock(spec=ActionResultError))

    with patch("cogs.amp._find_instance", AsyncMock(return_value=inst)):
        cog = AMP(mock_bot)
        await cog.amp_stats.callback(cog, mock_interaction, "TestInstance")

    call_kwargs = mock_interaction.followup.send.call_args
    assert call_kwargs.kwargs.get("ephemeral") is True
    assert "could not retrieve" in call_kwargs.args[0].lower()
