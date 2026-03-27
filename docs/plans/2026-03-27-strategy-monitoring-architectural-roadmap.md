# BTC Monitor V3.0 功能性架构方案：目标仓位与动态状态切换 (TADR)

## 1. 核心设计哲学
从 **“方向性建议 (Directional Advice)”** 进化为 **“战略目标配置 (Strategic Allocation)”**。系统不再仅告诉用户“买或卖”，而是基于证据强度计算出当前环境下的**最优目标仓位百分比 (Target Allocation %)**。

---

## 2. 模块化架构组件

### 2.1 动态证据聚合器 (Dynamic Evidence Aggregator)
**功能：** 根据市场状态动态调整因子权重，而非使用固定权重。
- **关联度感知 (Correlation Aware)**：引入 `src/monitoring/correlation_engine.py`。计算 BTC 与各区块（Macro, Equities, Gold）的 90 天滚动相关性。
- **权重自适应 (Adaptive Weighting)**：
    - 若 $Corr(BTC, DXY)$ 极高 -> 自动提升 `macro_liquidity` 区块权重。
    - 若 $Corr(BTC, S&P500)$ 极高 -> 引入 Beta 风险对冲系数。
    - 若处于“脱钩期” -> 权重回归 `valuation` 链上基本面。

### 2.2 概率置信度引擎 (Probabilistic Confidence Scorer)
**功能：** 取代现有的二元门禁（Binary Gating），采用连续分布评分。
- **证据衰减模型 (Evidence Decay)**：核心因子缺失时，评分不再归零，而是按其权重的倒数进行置信度扣减。
- **一致性得分 (Confluence Score)**：计算不同证据区块之间的向量夹角。若“估值看多”但“宏观看空”，一致性得分下降，直接压制最终仓位上限。

### 2.3 目标仓位解析器 (Target Allocation Resolver)
**功能：** 将综合得分映射为具体的持仓比例。
- **映射函数**：$Target\% = Sigmoid(StrategicScore \times Confidence) \times MarketCap$。
- **阶梯约束 (Tiered Constraints)**：
    - **底层基础仓位 (Floor)**：长期周期的持有底仓（如 20%）。
    - **战术浮动仓位 (Tactical Sleeve)**：受战术指标驱动的波动部分（如 0-30%）。
    - **硬上限 (Cap)**：当 `FearGreed > 85` 或 `Stretch > 3.0` 时，强制将 Target% 限制在 60% 以下。

### 2.4 风险调整执行逻辑 (Risk-Adjusted Execution)
**功能：** 解决“如何到达目标仓位”的问题。
- **强度建议 (Action Intensity)**：
    - 若 $Current\% < Target\%$ -> 输出 `ADD` 并附带 `Intensity` (0.0-1.0)。
    - $Intensity = \frac{Target\% - Current\%}{Volatility}$。波动率越高，到达目标的步长越小（防针尖追高）。

---

## 3. 核心算法流程 (The TADR Flow)

1.  **观察观测 (Observations)**：获取所有因子 Observation 对象。
2.  **相关性校准 (Correlation Sync)**：获取当前 BTC 宏观属性状态。
3.  **区块加权评分 (Block Scoring)**：应用动态权重，生成各区块分数。
4.  **计算目标持仓 (Compute Target %)**：
    - 基础模型：`Regime Score` (-10 到 +10) 线性映射到 0% - 100%。
    - 风险扣减：减去战术背离产生的“不确定性溢价”。
5.  **输出建议 (Final Recommendation)**：
    - `Target Allocation: 45%`
    - `Current Estimate: 20% (User-input or historical)`
    - `Action: ADD to reach target`
    - `Strategy: Vol-weighted staging (3 weeks execution)`

---

## 4. 关键代码接口变更预想

```python
# src/strategy/allocation_engine.py

class AllocationEngine:
    def resolve_target(self, observations: List[FactorObservation]) -> float:
        # 1. 获取动态权重
        weights = self.correlation_engine.get_weights()
        
        # 2. 证据聚合
        strategic_score = self.aggregator.sum_weighted(observations, weights)
        
        # 3. 计算置信度 (非二元)
        confidence = self.calibrator.compute_probabilistic_confidence(observations)
        
        # 4. 映射到仓位 (0.0 - 1.0)
        base_alloc = self.mapping_func(strategic_score)
        
        # 5. 战术约束
        final_alloc = self.apply_tactical_constraints(base_alloc, observations)
        
        return final_alloc
```

---

## 5. 路线图落实建议 (Implementation Plan)

1.  **Phase 1: 监控层增强**。实现滚动相关性计算，不改变决策，仅在报告中展示。
2.  **Phase 2: 影子评分**。在 V2.0 运行的同时，输出 V3.0 的影子目标仓位，进行 3 个月的回测对齐。
3.  **Phase 3: 全面切换**。废弃 `ADD/REDUCE` 的二元逻辑，全面转为“仓位缺口管理”。

---
*设计者：资深量化策略师 (Gemini CLI)*
*日期：2026-03-27*
