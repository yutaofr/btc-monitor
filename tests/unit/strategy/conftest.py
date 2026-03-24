"""Shared test fixtures for strategy unit tests."""
import pytest
from datetime import datetime
from src.strategy.factor_models import FactorObservation


@pytest.fixture
def make_obs():
    """Factory fixture for creating FactorObservation objects in tests."""
    def _make(name: str, score: float, is_valid: bool = True) -> FactorObservation:
        return FactorObservation(
            name=name,
            score=score,
            is_valid=is_valid,
            details={},
            description="",
            timestamp=datetime.now(),
            freshness_ok=True,
            confidence_penalty=0.0,
            blocked_reason=""
        )
    return _make
