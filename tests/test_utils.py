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
def test_match_state_manager_ttl():
    import time
    from app.services.match_state_manager import MatchStateManager
    
    mgr = MatchStateManager()
    
    # 1. Add some active state
    mgr.commit_memory("match1", 1, 0, scorer="Salah", minute="45")
    mgr.register_event_failure("event1", is_fatal=False)
    
    # Verify they exist
    assert mgr.get_score("match1") == (1, 0)
    assert mgr.can_retry_event("event1") is False  # Because it just failed and has backoff
    
    # 2. Run cleanup with a very long threshold (e.g. 10 seconds). Nothing should be evicted.
    mgr.cleanup_expired_states(max_age_seconds=10.0)
    assert mgr.get_score("match1") == (1, 0)
    assert "event1" in mgr._failed_events
    
    # 3. Sleep a bit and run cleanup with 0.01 threshold
    time.sleep(0.05)
    mgr.cleanup_expired_states(max_age_seconds=0.01)
    
    # Verify everything got evicted/purged!
    assert mgr.get_score("match1") is None
    assert mgr.get_last_scorer("match1") == ""
    assert "event1" not in mgr._failed_events
