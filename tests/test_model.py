import numpy as np
import pandas as pd
import pytest
from model import train_model, evaluate_chronological_model

def test_model_training_output():
    """Test that train_model returns the expected model and metadata encoders."""
    dummy_df = pd.DataFrame({
        "HomeTeam": ["Arsenal", "Chelsea", "Arsenal", "Liverpool"],
        "AwayTeam": ["Chelsea", "Arsenal", "Liverpool", "Chelsea"],
        "FTR": ["H", "D", "A", "H"],
        "FTHG": [2, 1, 0, 3],
        "FTAG": [1, 1, 1, 0],
        "season": ["2023-2024"] * 4,
        "weight": [1.0, 1.0, 1.0, 1.0],
        "date": ["2023-08-12", "2023-08-13", "2023-08-14", "2023-08-15"]
    })
    rf, target_enc, label_enc, team_hist, feat_cols = train_model(dummy_df)
    
    assert rf is not None
    assert hasattr(target_enc, "classes_")
    assert len(target_enc.classes_) == 3
    assert len(feat_cols) > 0

def test_chronological_evaluation_pipeline():
    """Test that evaluate_chronological_model executes safely with valid dataset structure."""
    dummy_df = pd.DataFrame({
        "HomeTeam": ["Arsenal", "Chelsea", "Liverpool", "Arsenal", "Man City", "Tottenham"],
        "AwayTeam": ["Chelsea", "Arsenal", "Chelsea", "Liverpool", "Tottenham", "Man City"],
        "FTR": ["H", "D", "A", "H", "A", "D"],
        "FTHG": [2, 1, 0, 3, 0, 1],
        "FTAG": [1, 1, 1, 0, 2, 1],
        "season": ["2022-2023", "2022-2023", "2022-2023", "2023-2024", "2023-2024", "2023-2024"],
        "weight": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "date": ["2022-09-01", "2022-09-02", "2022-09-03", "2023-09-01", "2023-09-02", "2023-09-03"]
    })
    
    evaluate_chronological_model(dummy_df)
    assert True