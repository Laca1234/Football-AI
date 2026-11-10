import numpy as np
import pytest

def test_brier_score_calculation():
    """Test that multiclass Brier score calculation is mathematically sound."""
    probas = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]])
    y_test_arr = np.array([0, 1])
    num_classes = 3
    y_test_onehot = np.eye(num_classes)[y_test_arr]
    brier_score = np.mean(np.sum((probas - y_test_onehot) ** 2, axis=1))
    
    assert 0.0 <= brier_score <= 2.0
    assert np.isfinite(brier_score)