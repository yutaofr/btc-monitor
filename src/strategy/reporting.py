import os
import tempfile
import requests
import logging
import json
from typing import List, Optional, Dict, Any
from dataclasses import asdict
from src.strategy.factor_models import Recommendation
from src.strategy.tadr_engine import TADRInternalState

# 配置日志
logger = logging.getLogger("TADRReporter")

class TADRReporter:
    """
    TADR Phase 2 Final: Production-grade Reporting & Resilience.
    Includes backward compatibility anchors for V2.x tests.
    """

    def generate_report_markdown(self, recommendation: Recommendation, state: TADRInternalState) -> str:
        lines = []
        if state.is_circuit_breaker_active:
            lines.append("# 🚨 SYSTEM GATE LOCKED (CRITICAL CIRCUIT BREAKER)")
            lines.append(f"**Action:** `{recommendation.action}`")
            lines.append("> **WARNING**: The perception system has been DISCONNECTED due to critical data loss.")
            lines.append("---")
            
            # 1. 表格化 RCA 诊断 [指令 4.3.2]
            lines.append("## 🔍 Root Cause Analysis (RCA)")
            lines.append("| Factor | Status | Raw Score | Last Observed | Multiplier |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            
            for f, metadata in state.gate_status.items():
                is_active = metadata.get("is_active", False)
                status = "❌ MISSING" if is_active else "✅ OK"
                score = state.raw_scores_map.get(f, "N/A")
                last_obs = metadata.get("last_observed", "N/A")
                m = state.redundancy_multipliers.get(f, 1.0)
                # 高亮显示被压制的因子 [指令 5.1.1]
                m_str = f"**{m:.4f}**" if m < 0.99 else f"{m:.4f}"
                lines.append(f"| {f} | {status} | {score} | {last_obs} | {m_str} |")
            
            lines.append("\n**Diagnosis**: System grounded to prevent hallucinated signals.")
            lines.append("---")
        else:
            lines.append(f"# BTC Monitor TADR V3 Advisory: **{recommendation.action}**")
            lines.append(f"**Action:** `{recommendation.action}`")

        # 2. 核心指标表格 (含旧版断言点 [指令 4.3])
        lines.append("## 📊 Strategic Metrics")
        lines.append(f"**Summary:** {recommendation.summary}") # 新增
        lines.append(f"**Confidence:** `{int(state.confidence * 100)}`")
        lines.append(f"**Regime:** `{recommendation.strategic_regime}`")
        lines.append(f"**Strategic Regime:** `{recommendation.strategic_regime}`")
        lines.append(f"**Tactical State:** `{recommendation.tactical_state}`")
        
        lines.append("\n| Metric | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| **Target Allocation** | **{state.target_allocation:.1%}** |")
        lines.append(f"| **Confidence Level** | `{state.confidence:.2f}` |")
        lines.append(f"| **Market Regime** | `{', '.join(state.regime_labels)}` |")
        lines.append(f"| **Strategic Score** | `{state.strategic_score:.8f}` |")
        
        # 3. 因子详情表格 (无论是否熔断都展示)
        lines.append("\n## 🔍 Factor Evidence Details")
        lines.append("| Factor | Status | Raw Score | Multiplier |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for f in state.raw_scores_map.keys():
            is_missing = state.gate_status.get(f, {}).get("is_active", False)
            status = "❌ MISSING" if is_missing else "✅ OK"
            score = state.raw_scores_map.get(f, 0.0)
            m = state.redundancy_multipliers.get(f, 1.0)
            m_str = f"**{m:.4f}**" if m < 0.99 else f"{m:.4f}"
            lines.append(f"| {f} | {status} | {score:.4f} | {m_str} |")

        lines.append("\n---")
        if recommendation.supporting_factors:
            lines.append(f"**Supporting Factors:** {', '.join(recommendation.supporting_factors)}")
        if recommendation.blocked_reasons:
            lines.append(f"**Blocked Reasons:** {', '.join(recommendation.blocked_reasons)}")
        if recommendation.missing_required_blocks:
            lines.append(f"**Missing Blocks:** {', '.join(recommendation.missing_required_blocks)}")
        
        lines.append("### 🧪 Engineering Metadata (Shadow Parity)")
        lines.append(f"- **Computation ID (NS)**: `{state.computation_timestamp_ns}`")
        return "\n".join(lines)

    def generate_text_summary(self, state: TADRInternalState) -> str:
        status = "🔴 LOCKED" if state.is_circuit_breaker_active else "🟢 ACTIVE"
        regime = "/".join(state.regime_labels)
        return (f"BTC Monitor V3 [{status}]\n"
                f"Target Alloc: {state.target_allocation:.1%}\n"
                f"Confidence: {state.confidence:.2f}\n"
                f"Regime: {regime}")

    def save_report_atomically(self, file_path: str, content: str, state: Optional[TADRInternalState] = None, emergency_webhook: Optional[str] = None):
        """
        指令 [4.3.1]: 原子化写入。
        指令 [5.2]: 紧急 Webhook 包含 INTERNAL_STATE_DUMP。
        """
        dir_name = os.path.dirname(file_path) or "."
        temp_file = None
        try:
            fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
            temp_file = temp_path
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            os.replace(temp_path, file_path)
            logger.info(f"Report successfully persisted to {file_path}")
        except Exception as e:
            error_msg = f"CRITICAL: Failed to persist report to {file_path}. Reason: {e}"
            logger.critical(error_msg)
            
            if emergency_webhook:
                dump = asdict(state) if state else {"msg": "No state context available"}
                payload = {
                    "text": f"🚨 EMERGENCY: File Persistence Failure\n{error_msg}",
                    "internal_state_dump": dump
                }
                self.push_to_webhook(emergency_webhook, payload)
            
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def push_to_webhook(self, url: str, payload: Dict[str, Any], timeout: int = 5) -> bool:
        try:
            data = json.dumps(payload, default=str)
            response = requests.post(url, data=data, headers={'Content-Type': 'application/json'}, timeout=timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Webhook delivery failed: {e}")
            return False

# --- Global Access Functions (Backward Compatibility) ---
# 指令 [4.3]：将旧版报告函数桥接到新版 TADRReporter。

_default_reporter = TADRReporter()

def build_advisory_report(recommendation: Recommendation, state: Optional[TADRInternalState] = None, current_price: float = 0.0) -> str:
    # 注入价格信息（如果提供）
    if state is None:
        # 为旧代码提供 Mock State
        state = TADRInternalState(
            computation_timestamp_ns=0, raw_scores_map={}, weighted_scores_map={},
            redundancy_multipliers={}, correlation_matrix_snapshot={}, gate_status={},
            strategic_score=0.0, confidence=recommendation.confidence/100.0, 
            target_allocation=0.0, regime_labels=[recommendation.strategic_regime],
            is_circuit_breaker_active=False
        )
    md = _default_reporter.generate_report_markdown(recommendation, state)
    if current_price > 0:
        md = f"**CURRENT PRICE**: ${current_price:,.2f}\n\n" + md
    return md

def build_dual_advisory_report(pos_rec: Recommendation, cash_rec: Recommendation, current_price: float = 0.0) -> str:
    """Legacy support for dual reports."""
    return f"--- DUAL ADVISORY (LEGACY WRAPPER) ---\n\nPRICE: ${current_price:,.2f}\n\n[POSITION]: {pos_rec.action} ({pos_rec.confidence}%)\n[CASH]: {cash_rec.action} ({cash_rec.confidence}%)\n\nSUMMARY: {pos_rec.summary}"

def build_report_summary(state: TADRInternalState) -> str:
    return _default_reporter.generate_text_summary(state)
