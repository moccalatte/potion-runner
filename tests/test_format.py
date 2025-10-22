from app.utils.format import human_bytes

def test_human_bytes():
    assert human_bytes(1024) == "1.0 KB"
    assert human_bytes(1) == "1.0 B"
    assert human_bytes(1024 * 1024 * 5) == "5.0 MB"
