# BTC Monitor 深度演进备忘录：从规则过滤到概率定价 (First Principles)

## 1. 核心矛盾：非对称收益与对称风控的错位
- **现象**：系统回测准确率高，但跑输 Buy & Hold。
- **根本原因**：系统将“错误买入”的惩罚设置得过高，而忽略了“错过底部”的致命性。
- **演进方向**：引入 **“非对称损失函数 (Asymmetric Loss Function)”**。在评估逻辑中，给“踏空风险”赋予比“套牢风险”更高的权重。

## 2. 状态感知的动态信息论 (Dynamic Information Entropy)
- **原理**：不同市场阶段，信息的有效性（信噪比）不同。
- **实现路径**：
    - **Capitulation Phase (投降期)**：提升 `On-chain Valuation` (MVRV, Puell) 权重至 70%。此时价格极度脱离价值，它是唯一的真相。
    - **Expansion Phase (扩张期)**：提升 `Net Liquidity` 权重。此时 BTC 是法币溢价的容器。
    - **Euphoria Phase (狂热期)**：提升 `Market Structure` (衍生品、溢价、乖离率) 权重。此时链上持有者已开始离场，价格完全由杠杆驱动。

## 3. 分母重构：法币本位向流动性本位迁移
- **逻辑**：BTC 的价格 $P_{BTC}$ 是 $Supply/Demand$ 的结果，但法币 $USD$ 本身在快速贬值。
- **动作**：
    - 引入 `Global_M2_Adjusted_Price`。
    - 所有的估值指标（如 200WMA）应考虑法币膨胀后的“实际支撑位”。

## 4. 概率化决策树 (Probabilistic Decision Tree)
- **重构逻辑**：
    - **旧逻辑**：`If (Evidence A missing) -> STOP`
    - **新逻辑**：`If (Evidence A missing) -> P(Success) drops by X% -> Reduce Allocation by Y%`
- **目的**：确保系统在任何时候都能给出一个“最优持仓建议”，即使数据是不完美的。

---
*撰写人：资深量化策略师 (Gemini CLI)*
*日期：2026-03-27*
