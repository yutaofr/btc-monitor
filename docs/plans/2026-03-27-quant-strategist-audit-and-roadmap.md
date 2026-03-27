# BTC Monitor 量化审计报告与演进路线图 (2026-03-27)

## 1. 审计摘要 (Executive Summary)

**审计对象：** BTC Monitor Stateless Advisory Engine (v2.0)
**核心结论：** 系统展现了极高的决策确定性（胜率 100%），但存在严重的**幸存者偏差**与**决策迟滞**。目前的架构是一个优秀的“极值抄底器”，但在常规牛熊转换中的覆盖率（Recall）不足以支撑全周期的资产管理需求。

---

## 2. 策略表现审计 (Backtest Performance Audit)

基于 2017-2026 年回测数据：

### 2.1 仓位分支 (Position Branch)
- **ADD 信号 (N=8)**：集中于 2019 年底及 2020 年 COVID 暴跌。28d/84d/182d 准确率均为 100%。
- **REDUCE 信号 (N=1)**：仅在 2021 年 12 月触发。虽然避开了随后的深跌，但在顶部 6.9 万回落 17% 后才发出信号，时效性较差。
- **评价**：系统为了追求“不亏损”的绝对确信度，牺牲了 90% 以上的可交易机会。

### 2.2 现金分支 (Incremental Cash Branch)
- **Alpha 亏损**：回测显示 `STAGGER_BUY` 对标简单 DCA 的成功率为 **0.0%**。在系统建议“分批”时，市场通常已处于加速上涨阶段，等待导致了更高的入场成本。
- **BUY_NOW 真空**：全历史 0 次触发。决策门槛过于追求“完美共振”，在现实金融数据中属于“过拟合于安全性”。

---

## 3. 逻辑漏洞与缺陷分析 (Logical Deficits)

1.  **战术否决过度 (Tactical Over-Veto)**：系统在战略看多时，常因 FearGreed 处于 70-80 区间或短期价格略微偏离 EMA 而否决 `ADD` 或 `BUY_NOW`。在强趋势中，这会导致严重的踏空。
2.  **数据新鲜度降级陷阱 (Freshness Trap)**：由于 FRED 等宏观数据源更新延迟，系统频繁报出 `Yields is stale` 警告，进而进入 `Fail-Closed` 模式将信号回退至 `HOLD`。这在实操中会导致在关键时刻（如联储会议周）失去决策能力。
3.  **REDUCE 滞后性**：过度依赖 `EMA21_Weekly` 作为趋势破位确认。对于长线持仓，21 周均线的距离往往对应 20% 以上的回撤，风险暴露过大。

---

## 4. 系统演进路线图 (Evolution Roadmap)

### 短期改进 (Short-term Fixes) - 优先级：高
- **[STRAT-01] 宏观 TTL 修正**：将 `factor_registry.py` 中宏观因子的 `freshness_ttl_hours` 从 168 小时（1周）提升至 240 小时（10天），以容忍 FRED 接口的常规发布延迟。
- **[STRAT-02] 战术否决权降权**：在战略评分极强（如 `Strategic Score > 7.0`）时，强制忽略 `FearGreed` 等情绪因子的 `is_wait_veto` 属性，允许在强趋势中“顺势而为”。

### 中期优化 (Medium-term Research) - 优先级：中
- **[STRAT-03] 引入“减盈” (TAKE_PROFIT) 状态**：在 `REDUCE` 之前增加一个低确信度的利润兑现信号，当 MVRV 或 Puell 进入前 5% 分位且价格偏离均线过远时触发，不依赖趋势破位。
- **[STRAT-04] 重构现金策略基准**：废弃 `STAGGER_BUY` 这种不确定的模糊表述，改为“加速 DCA” (Aggressive DCA) 与“防御 DCA” (Defensive DCA)，将建议量化为具体的执行强度比率。

### 长期演进 (Long-term Vision) - 优先级：低
- **[STRAT-05] 波动率门控 (Vol-Gating)**：引入价格波幅作为战术确认的依据。在低波上涨中放宽入场门槛，在高波剧震中收紧逻辑。

---

## 5. 知识库记录

- **策略哲学**：防御优先，宁可踏空不可深套。
- **统计有效性**：MVRV-Proxy 与 Net_Liquidity 的双重门禁是本系统最稳健的利润护城河。
- **警告**：禁止在 LTM Precision（最近 12 个月准确率）下降超过 15% 时手动干预策略逻辑，应优先检查数据源漂移。

---
*报告撰写人：资深量化策略师 (Gemini CLI)*
*日期：2026-03-27*
