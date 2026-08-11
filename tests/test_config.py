from __future__ import annotations

import pytest

from app.core.config import Settings


def test_vector_score_threshold_must_be_between_zero_and_one():
    for invalid in (-0.1, 1.1):
        with pytest.raises(ValueError, match="VECTOR_SCORE_THRESHOLD"):
            Settings(vector_score_threshold=invalid)
