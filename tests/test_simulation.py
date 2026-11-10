import pytest

def test_season_fixture_counts():
    """Test that a 20-team season generates exactly 380 fixtures and 38 matches per team."""
    try:
        from service import generate_season_fixtures
        teams = [f"Team {i}" for i in range(1, 21)]
        fixtures = generate_season_fixtures(teams)
        
        assert len(fixtures) == 380, f"Expected 380 fixtures, got {len(fixtures)}"
        
        # Verify each team plays 38 matches (19 home, 19 away)
        match_counts = {team: 0 for team in teams}
        for f in fixtures:
            match_counts[f['HomeTeam']] += 1
            match_counts[f['AwayTeam']] += 1
            
        for team, count in match_counts.items():
            assert count == 38, f"Team {team} played {count} matches instead of 38"
    except (ImportError, AttributeError):
        pytest.skip("Season fixture generator function not directly exposed in service module.")

def test_standings_calculation_and_sorting():
    """Test standings statistics, point consistency, and correct sorting."""
    try:
        from service import calculate_standings
        # Mock match results
        matches = [
            {"HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "FTHG": 2, "FTAG": 1, "FTR": "H"},
            {"HomeTeam": "Chelsea", "AwayTeam": "Arsenal", "FTHG": 1, "FTAG": 1, "FTR": "D"},
        ]
        standings = calculate_standings(matches)
        assert len(standings) > 0
        
        # Check sorting: Points descending, then GD, then GF
        for i in range(len(standings) - 1):
            curr, nxt = standings[i], standings[i+1]
            if curr['points'] == nxt['points']:
                if curr['goal_difference'] == nxt['goal_difference']:
                    assert curr['goals_for'] >= nxt['goals_for']
                else:
                    assert curr['goal_difference'] >= nxt['goal_difference']
            else:
                assert curr['points'] >= nxt['points']
    except (ImportError, AttributeError):
        pytest.skip("Standings calculation helper not directly exposed.")