from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.handlers.system import run_command

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
    return context_mock

@patch("app.handlers.system.run_cmd")
async def test_run_command_authorized(run_cmd_mock, update, context):
    """Test that an authorized user can run a command."""
    context.bot_data["settings"].is_admin.return_value = True
    run_cmd_mock.return_value = MagicMock(returncode=0, stdout="test output", stderr="")
    context.args = ["ls", "-l"]

    await run_command(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "test output" in call_args
    assert "✅" in call_args

@patch("app.handlers.system.run_cmd")
async def test_run_command_unauthorized(run_cmd_mock, update, context):
    """Test that an unauthorized user is denied access."""
    context.bot_data["settings"].is_admin.return_value = False

    await run_command(update, context)

    update.message.reply_text.assert_called_once_with("You are not authorized to use this command.")
    run_cmd_mock.assert_not_called()

@patch("app.handlers.system.run_cmd")
async def test_run_command_no_args(run_cmd_mock, update, context):
    """Test that the command requires arguments."""
    context.args = []

    await run_command(update, context)

    update.message.reply_text.assert_called_once_with("Usage: /run <command>")
    run_cmd_mock.assert_not_called()

@patch("app.handlers.system.run_cmd")
async def test_run_command_failure(run_cmd_mock, update, context):
    """Test that a failing command returns an error."""
    run_cmd_mock.return_value = MagicMock(returncode=1, stdout="", stderr="test error")
    context.args = ["invalid-command"]

    await run_command(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "test error" in call_args
    assert "❌" in call_args
