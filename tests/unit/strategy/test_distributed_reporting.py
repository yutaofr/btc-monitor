import pytest
import os
from unittest.mock import MagicMock, patch
from src.strategy.reporting import TADRReporter
from src.strategy.tadr_engine import TADRInternalState
from src.strategy.factor_models import Recommendation

def test_atomic_write_to_file(tmp_path):
    """验证原子化写入逻辑。"""
    reporter = TADRReporter()
    target_file = tmp_path / "final_report.md"
    
    # 模拟状态
    state = TADRInternalState(
        computation_timestamp_ns=123, raw_scores_map={}, weighted_scores_map={},
        redundancy_multipliers={}, correlation_matrix_snapshot={}, gate_status={},
        strategic_score=0.0, confidence=1.0, target_allocation=0.5,
        regime_labels=["Bull"], is_circuit_breaker_active=False
    )
    rec = Recommendation(action="ADD", confidence=100, strategic_regime="Bull", 
                         tactical_state="A", supporting_factors=[], conflicting_factors=[],
                         missing_required_blocks=[], missing_required_factors=[],
                         blocked_reasons=[], freshness_warnings=[], excluded_research_factors=[],
                         summary="Test")
    
    report_md = reporter.generate_report_markdown(rec, state)
    
    # 执行原子写入
    reporter.save_report_atomically(str(target_file), report_md)
    
    assert target_file.exists()
    with open(target_file, "r") as f:
        assert f.read() == report_md

def test_webhook_non_blocking_failure():
    """验证 Webhook 推送失败不阻塞主流程。"""
    reporter = TADRReporter()
    
    # 模拟 requests.post 抛出异常
    with patch("requests.post", side_effect=Exception("Network Down")):
        # 此调用不应抛出异常
        success = reporter.push_to_webhook("http://broken-url", {"text": "summary"})
        assert success is False

def test_slack_summary_format():
    """验证 Slack 摘要包含核心指标。"""
    reporter = TADRReporter()
    state = TADRInternalState(
        computation_timestamp_ns=123, raw_scores_map={}, weighted_scores_map={},
        redundancy_multipliers={}, correlation_matrix_snapshot={}, gate_status={},
        strategic_score=0.0, confidence=0.85, target_allocation=0.456,
        regime_labels=["Neutral"], is_circuit_breaker_active=False
    )
    
    summary = reporter.generate_text_summary(state)
    assert "45.6%" in summary
    assert "0.85" in summary
