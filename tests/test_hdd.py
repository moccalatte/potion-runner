from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.config import Settings
from app.services.hdd import hdd_status, is_mounted

@pytest.fixture
def mock_psutil(mocker):
    return mocker.patch("app.services.hdd.psutil")

def test_is_mounted(mock_psutil):
    mock_psutil.disk_partitions.return_value = [
        MagicMock(mountpoint="/"),
        MagicMock(mountpoint="/boot"),
    ]
    assert is_mounted(Path("/"))
    assert not is_mounted(Path("/data"))

def test_hdd_status(mock_psutil):
    settings = Settings(
        bot_token="fake",
        admin_ids={123},
        env_file=Path(".env"),
        data_dir=Path("."),
        log_dir=Path("."),
        backup_dir=Path("."),
        manifests_dir=Path("."),
        snapshots_dir=Path("."),
        hdd_mount=Path("/mnt/potion-data"),
        services_whitelist=[],
        self_service="",
        runtime_log=Path("."),
        actions_log=Path("."),
        health_file=Path("."),
    )
    mock_psutil.disk_usage.return_value = MagicMock(
        total=100, used=50, percent=50.0
    )
    mock_psutil.disk_partitions.return_value = [
        MagicMock(mountpoint=str(settings.hdd_mount))
    ]
    status = hdd_status(settings)
    assert status["mounted"] == "yes"
    assert status["total"] == "100.0 B"
    assert status["used"] == "50.0 B"
    assert status["percent"] == "50.0%"
