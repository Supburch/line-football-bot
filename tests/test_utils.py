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
    
    # Test UK country name mapping
    assert safe_url(None, "Scotland") == "https://flagcdn.com/w160/gb-sct.png"
    assert safe_url(None, "England") == "https://flagcdn.com/w160/gb-eng.png"
    assert safe_url(None, "Wales") == "https://flagcdn.com/w160/gb-wls.png"
    assert safe_url(None, "Northern Ireland") == "https://flagcdn.com/w160/gb-nir.png"
    
    # Test UK country URL mapping (Area IDs)
    assert safe_url("https://crests.thefootball-data.org/2000.svg") == "https://flagcdn.com/w160/gb-sct.png"
    assert safe_url("https://crests.thefootball-data.org/2000.png") == "https://flagcdn.com/w160/gb-sct.png"
    assert safe_url("https://crests.thefootball-data.org/2072.svg") == "https://flagcdn.com/w160/gb-eng.png"
    assert safe_url("https://crests.thefootball-data.org/2264.svg") == "https://flagcdn.com/w160/gb-wls.png"
    assert safe_url("https://crests.thefootball-data.org/2163.svg") == "https://flagcdn.com/w160/gb-nir.png"
    
    # Test SVG conversion via images.weserv.nl with URL encoding (':' becomes '%3A', '/' remains '/')
    assert safe_url("https://example.com/logo.svg") == "https://images.weserv.nl/?url=https://example.com/logo.svg&format=png"
    
    # Test collision prevention (Germany team ID 759 should NOT map to Scotland)
    assert safe_url("https://crests.thefootball-data.org/759.svg") == "https://images.weserv.nl/?url=https://crests.thefootball-data.org/759.svg&format=png"
    assert safe_url("https://crests.thefootball-data.org/759.svg", "Germany") == "https://images.weserv.nl/?url=https://crests.thefootball-data.org/759.svg&format=png"



