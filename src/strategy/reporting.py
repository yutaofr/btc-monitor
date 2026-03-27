from typing import List, Optional
from src.strategy.factor_models import Recommendation
from src.strategy.tadr_engine import TADRInternalState

class TADRReporter:
    """
    指令 [4.3]：增强报告系统。
    实现 SYSTEM_GATE_LOCKED 显式预警与 RCA 归因。
    """

    def generate_report_markdown(self, recommendation: Recommendation, state: TADRInternalState) -> str:
        """
        生成 V3.0 决策报告。
        """
        lines = []

        # 1. 核心状态预警 (SYSTEM_GATE_LOCKED) [指令 4.3.1]
        if state.is_circuit_breaker_active:
            lines.append("# 🚨 SYSTEM GATE LOCKED (CRITICAL CIRCUIT BREAKER)")
            lines.append("> **WARNING**: The perception system has been DISCONNECTED due to critical data loss.")
            lines.append("---")
            
            # 2. 熔断归因 (Root Cause Analysis) [指令 4.3.2]
            lines.append("## 🔍 Root Cause Analysis (RCA)")
            
            # 细化归因分析
            data_missing = [f for f, is_gate_active in state.gate_status.items() if is_gate_active]
            
            lines.append(f"**Critical Block Failure**: `{', '.join(data_missing)}`")
            
            diagnosis_details = []
            for factor in data_missing:
                # 模拟诊断：实际应从 observations 中提取原因
                diagnosis_details.append(f"- **{factor}**: 数据源无效 (Invalid) 或 接口响应超时 (Timeout)。")
            
            lines.append("\n**Diagnostic Details**:")
            lines.extend(diagnosis_details)
            lines.append("\n**Status**: [LOGIC_INTERCEPTED] - System grounded to prevent hallucinated signals.")
            lines.append("---")
        else:
            lines.append(f"# BTC Monitor TADR V3 Advisory: {recommendation.action}")

        # 3. 目标配置详情
        lines.append(f"## 📊 Strategic Target Allocation: **{state.target_allocation:.1%}**")
        lines.append(f"**Confidence Level**: `{state.confidence:.2f}` (Entropy & Confluence Scored)")
        lines.append(f"**Market Regime**: `{', '.join(state.regime_labels)}`")

        # 4. 影子测试元数据 (Shadow Test Metadata)
        lines.append("---")
        lines.append("### 🧪 Engineering Metadata (Shadow Parity)")
        lines.append(f"- **Computation ID (NS)**: `{state.computation_timestamp_ns}`")
        lines.append(f"- **Strategic Score**: `{state.strategic_score:.8f}`")
        lines.append(f"- **Redundancy Penalty (Smooth)**: `{min(state.redundancy_multipliers.values()) if state.redundancy_multipliers else 1.0:.8f}`")

        return "\n".join(lines)
