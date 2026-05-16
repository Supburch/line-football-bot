import pytest
from app.utils.helpers import extract_command, safe_url
from app.utils.constants import BOT_PREFIX, DEFAULT_LOGO

def test_extract_command():
    text = f"{BOT_PREFIX} ตาราง"
    assert extract_command(text) == "ตาราง"
    
def test_safe_url():
    assert safe_url("http://example.com") == "https://example.com"
    assert safe_url("https://example.com") == "https://example.com"
    assert safe_url("ftp://example.com") == DEFAULT_LOGO
