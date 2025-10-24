from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.handlers.docker import (
    CONTAINER_NAME_LOGS,
    CONTAINER_NAME_RESTART,
    CONTAINER_NAME_STOP,
    cancel,
    docker_menu,
    list_containers,
    logs_container,
    logs_container_start,
    restart_container,
    restart_container_start,
    stop_container,
    stop_container_start,
)
from app.menus import DOCKER_MENU
from telegram.ext import ConversationHandler

@pytest.fixture
def update():
    """Fixture for a mock Telegram Update."""
    update_mock = MagicMock()
    update_mock.effective_user.id = 123
    update_mock.message.reply_text = AsyncMock()
    return update_mock

@pytest.fixture
def context():
    """Fixture for a mock Telegram Context."""
    context_mock = MagicMock()
    context_mock.bot_data = {
        "settings": MagicMock(admin_ids={123})
    }
    context_mock.bot_data["settings"].is_admin.return_value = True
    return context_mock

async def test_docker_menu(update, context):
    """Test that the docker menu is displayed."""
    await docker_menu(update, context)
    update.message.reply_text.assert_called_once_with(
        "Ini dia menu buat ngatur para 'paus' di server kamu! 🐳\n"
        "Mau diapain nih, kapten?",
        reply_markup=DOCKER_MENU
    )

@patch("app.handlers.docker.run_cmd")
async def test_list_containers_authorized(run_cmd_mock, update, context):
    """Test that an authorized user can list containers."""
    run_cmd_mock.return_value = MagicMock(returncode=0, stdout="test output", stderr="")
    await list_containers(update, context)
    assert update.message.reply_text.call_count == 2


async def test_list_containers_unauthorized(update, context):
    """Test that an unauthorized user is denied access."""
    context.bot_data["settings"].is_admin.return_value = False
    await list_containers(update, context)
    update.message.reply_text.assert_called_with("Waduh, menu ini khusus buat admin. Kamu belum terdaftar, nih. 😅")


async def test_stop_container_start(update, context):
    """Test starting the stop container conversation."""
    result = await stop_container_start(update, context)
    update.message.reply_text.assert_called_once_with("Kontainer mana yang mau diberhentiin? Kasih tau nama atau ID-nya ya.")
    assert result == CONTAINER_NAME_STOP

@patch("app.handlers.docker.run_cmd")
async def test_stop_container(run_cmd_mock, update, context):
    """Test stopping a container."""
    run_cmd_mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
    update.message.text = "test_container"
    result = await stop_container(update, context)
    assert update.message.reply_text.call_count == 2
    assert result == ConversationHandler.END

async def test_restart_container_start(update, context):
    """Test starting the restart container conversation."""
    result = await restart_container_start(update, context)
    update.message.reply_text.assert_called_once_with("Siapa yang mau di-restart biar seger lagi? Kasih tau nama atau ID-nya.")
    assert result == CONTAINER_NAME_RESTART

@patch("app.handlers.docker.run_cmd")
async def test_restart_container(run_cmd_mock, update, context):
    """Test restarting a container."""
    run_cmd_mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
    update.message.text = "test_container"
    result = await restart_container(update, context)
    assert update.message.reply_text.call_count == 2
    assert result == ConversationHandler.END

async def test_logs_container_start(update, context):
    """Test starting the logs container conversation."""
    result = await logs_container_start(update, context)
    update.message.reply_text.assert_called_once_with("Mau lihat catatan harian (log) dari kontainer mana nih?")
    assert result == CONTAINER_NAME_LOGS

@patch("app.handlers.docker.run_cmd")
async def test_logs_container(run_cmd_mock, update, context):
    """Test getting container logs."""
    run_cmd_mock.return_value = MagicMock(returncode=0, stdout="test logs", stderr="")
    update.message.text = "test_container"
    result = await logs_container(update, context)
    assert update.message.reply_text.call_count == 2
    assert result == ConversationHandler.END

async def test_cancel(update, context):
    """Test cancelling the conversation."""
    result = await cancel(update, context)
    update.message.reply_text.assert_called_once_with("Oke, batal. Kita balik lagi ke menu Docker ya.", reply_markup=DOCKER_MENU)
    assert result == ConversationHandler.END
