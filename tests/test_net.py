from unittest.mock import MagicMock

import pytest
from app.services.net import ip_info

@pytest.fixture
def mock_psutil(mocker):
    return mocker.patch("app.services.net.psutil")

async def test_ip_info(mock_psutil):
    mock_psutil.net_if_addrs.return_value = {
        "lo": [
            MagicMock(family=17, address=""),
            MagicMock(family=2, address="127.0.0.1"),
            MagicMock(family=10, address="::1"),
        ],
        "eth0": [
            MagicMock(family=2, address="192.168.1.100"),
        ],
    }
    interfaces = await ip_info()
    assert len(interfaces) == 2
    assert interfaces[0].name == "lo"
    assert "127.0.0.1" in interfaces[0].addresses
    assert "::1" in interfaces[0].addresses
    assert interfaces[1].name == "eth0"
    assert "192.168.1.100" in interfaces[1].addresses
