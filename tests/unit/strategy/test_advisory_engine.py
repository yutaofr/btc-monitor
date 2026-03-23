import pytest
import sys
from datetime import datetime
from src.strategy.factor_models import FactorObservation, Recommendation
from src.strategy.advisory_engine import AdvisoryEngine

def test_advisory_engine_isolation():
    """Ensure advisory engine constructor accepts only stateless inputs."""
    engine = AdvisoryEngine()
    
    # Must accept only explicit factor observations
    observations = [
        FactorObservation(
            name="MVRV_Proxy",
            score=8.0,
            is_valid=True,
            details={},
            description="Bullish",
            timestamp=datetime.now(),
            freshness_ok=True,
            confidence_penalty=0.0,
            blocked_reason=""
        )
    ]
    
    rec = engine.evaluate(observations)
    assert isinstance(rec, Recommendation)
    assert rec.action in ["ADD", "REDUCE", "HOLD", "INSUFFICIENT_DATA"]

def test_advisory_import_boundary():
    """Ensure the advisory engine does NOT import StateTracker or execution paths."""
    # If it imports StateTracker, this test will fail after tracking imports
    for module_name in sys.modules:
        if module_name.startswith("src.strategy.advisory_engine"):
            import ast
            import inspect
            import src.strategy.advisory_engine as adv_module
            
            source = inspect.getsource(adv_module)
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "state" not in alias.name.lower()
                        assert "execution" not in alias.name.lower()
                elif isinstance(node, ast.ImportFrom):
                    assert node.module is not None
                    assert "state" not in node.module.lower()
                    assert "execution" not in node.module.lower()

def test_advisory_deterministic_output():
    """Ensure identical inputs produce exactly the same recommendation."""
    engine = AdvisoryEngine()
    obs = [
        FactorObservation("MVRV_Proxy", 8.0, True, {}, "", datetime.now(), True, 0.0, "")
    ]
    
    rec1 = engine.evaluate(obs)
    rec2 = engine.evaluate(obs)
    
    assert rec1.action == rec2.action
    assert rec1.confidence == rec2.confidence
    assert rec1.summary == rec2.summary

def test_one_factor_bullish_cannot_return_add():
    engine = AdvisoryEngine()
    obs = [
        FactorObservation("MVRV_Proxy", 10.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("200WMA", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("Net_Liquidity", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
    ]
    rec = engine.evaluate(obs)
    assert rec.action != "ADD"

def test_one_factor_overheated_cannot_return_reduce():
    engine = AdvisoryEngine()
    obs = [
        FactorObservation("MVRV_Proxy", -10.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("200WMA", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("Net_Liquidity", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
    ]
    rec = engine.evaluate(obs)
    assert rec.action != "REDUCE"

def test_missing_required_blocks_returns_insufficient_data():
    engine = AdvisoryEngine()
    obs = [
        FactorObservation("MVRV_Proxy", 10.0, True, {}, "", datetime.now(), True, 0.0, "")
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "INSUFFICIENT_DATA"

def test_mixed_evidence_returns_hold():
    engine = AdvisoryEngine()
    obs = [
        FactorObservation("MVRV_Proxy", 5.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("200WMA", -5.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("Net_Liquidity", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "HOLD"

def test_research_factors_cannot_affect_advisory_actions():
    engine = AdvisoryEngine()
    
    # Base observations that would normally return HOLD (mixed evidence)
    base_obs = [
        FactorObservation("MVRV_Proxy", 5.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("200WMA", -5.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("Net_Liquidity", 0.0, True, {}, "", datetime.now(), True, 0.0, ""),
    ]
    base_rec = engine.evaluate(base_obs)
    
    # Add strong bullish research-factors which should be entirely ignored
    research_obs = base_obs + [
        FactorObservation("Options_Wall", 10.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("ETF_Flow", 10.0, True, {}, "", datetime.now(), True, 0.0, ""),
        FactorObservation("Production_Cost", 10.0, True, {}, "", datetime.now(), True, 0.0, "")
    ]
    research_rec = engine.evaluate(research_obs)
    
    assert base_rec.action == research_rec.action
    assert base_rec.confidence == research_rec.confidence
    # The research factors should be silently discarded or reported contextually but not affect score.
