from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from app.handlers.network import speed_command

@pytest.fixture
def update():
    """Fixture for a mock Telegram Update."""
    update_mock = MagicMock()
    update_mock.effective_user.id = 123

    # The message and its edit_text method need to be async
    message_mock = MagicMock()
    message_mock.edit_text = AsyncMock()

    update_mock.message.reply_text = AsyncMock(return_value=message_mock)
    return update_mock

@pytest.fixture
def context():
    """Fixture for a mock Telegram Context."""
    context_mock = MagicMock()
    context_mock.bot_data = {
        "settings": MagicMock(admin_ids={123})
    }
    return context_mock

@patch("app.handlers.network.run_cmd")
async def test_speed_command_success(run_cmd_mock, update, context):
    """Test the speed_command success flow."""
    # Mock the return value of speedtest-cli
    run_cmd_mock.return_value = MagicMock(
        stdout="Ping: 10.0 ms\nDownload: 100.0 Mbit/s\nUpload: 50.0 Mbit/s",
        returncode=0
    )

    await speed_command(update, context)

    # 1. Verify initial message
    update.message.reply_text.assert_called_once_with("Oke, mulai tes kecepatan... 💨")

    # 2. Verify message edits
    pending_message = await update.message.reply_text()
    expected_calls = [
        call("Menguji kecepatan unduh... 📥"),
        call("Menguji kecepatan unggah... 📤"),
        call(
            'Beres! ✅ Ringkasan: Taraa! 🚀 Ini dia hasilnya:\n\n'
            '&lt;b&gt;Ping:&lt;/b&gt; 10.0 ms\n'
            '&lt;b&gt;Download:&lt;/b&gt; 100.0 Mbit/s\n'
            '&lt;b&gt;Upload:&lt;/b&gt; 50.0 Mbit/s'
        )
    ]
    pending_message.edit_text.assert_has_calls(expected_calls, any_order=False)

@patch("app.handlers.network.run_cmd")
async def test_speed_command_failure(run_cmd_mock, update, context):
    """Test the speed_command failure flow."""
    # Mock a failure
    run_cmd_mock.side_effect = Exception("Speedtest failed")

    await speed_command(update, context)

    # 1. Verify initial message
    update.message.reply_text.assert_called_once_with("Oke, mulai tes kecepatan... 💨")

    # 2. Verify error message edit
    pending_message = await update.message.reply_text()

    # Check that the last call was the error message
    final_call_args = pending_message.edit_text.call_args[0][0]
    assert "Waduh, sepertinya ada masalah" in final_call_args
    assert "Speedtest failed" in final_call_args
