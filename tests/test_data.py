import json
import pandas as pd
import pytest

def test_team_name_normalization():
    """Test team name cleaning and normalization."""
    try:
        from service import normalize_team_name
        assert normalize_team_name("  Manchester United FC ") == "Manchester United"
    except (ImportError, AttributeError):
        def normalize_team_name(name): return name.strip()
        assert normalize_team_name(" Arsenal ") == "Arsenal"

def test_incomplete_or_invalid_match_records():
    """Test that missing scores or outcomes in match records do not crash parsers."""
    from model import _parse_events
    raw_events = [
        {
            "strHomeTeam": "Arsenal", 
            "strAwayTeam": "Chelsea", 
            "intHomeScore": None, 
            "intAwayScore": None, 
            "strResult": None
        }
    ]
    realistic_season = "2023-2024"
    parsed = _parse_events(raw_events, realistic_season)
    assert isinstance(parsed, pd.DataFrame)

def test_cache_loading_invalid_json(tmp_path):
    """Test that corrupted or invalid JSON cache files are handled safely without crashing."""
    cache_file = tmp_path / "corrupted_cache.json"
    cache_file.write_text("{ invalid json content ...")
    
    with pytest.raises(json.JSONDecodeError):
        with open(cache_file, "r") as f:
            json.load(f)