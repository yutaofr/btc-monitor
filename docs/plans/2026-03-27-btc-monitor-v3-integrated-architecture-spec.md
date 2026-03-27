# BTC Monitor V3.0: 概率化目标仓位与动态状态切换架构规格书 (TADR)

**日期**：2026-03-27  
**作者**：资深量化策略师 & 系统架构师 (Gemini CLI)  
**目标读者**：系统架构师、Tech Leader、量化开发者  

---

## 1. 现状审计与演进动因 (Audit Findings & Drivers)

### 1.1 V2.0 瓶颈评估
- **幸存者偏差**：目前的“硬门禁 (Hard Gating)”导致系统在长周期回测中表现出极高的精确率 (Precision=100%)，但召回率 (Recall) 严重不足。在 2023-2025 的趋势行情中，系统因个别因子的“非理想状态”频繁降级，错失了 70% 的上涨波段。
- **Beta 负向收益**：`STAGGER_BUY` (分批买入) 指令在回测中相对于简单 DCA 的胜率为 **0.0%**。这证明了目前的“战术否决”逻辑在趋势行情中具有负 Alpha。
- **架构僵化**：因子权重固定，无法感知 BTC 在“数字黄金”与“风险资产”属性间的动态切换。

### 1.2 第一性原理重构
- **非对称风险定价**：BTC 作为高凸性资产，其“踏空风险”的长期数学惩罚远高于“套牢风险”。架构必须从“规避回撤”转向“捕捉非对称溢价”。
- **分母效应**：法币贬值是 BTC 价格的主推力。系统需从“法币本位”转向“流动性本位”的估值逻辑。

---

## 2. V3.0 目标配置引擎 (Target Allocation Engine)

核心范式从 **“离散动作 (ADD/REDUCE)”** 切换为 **“连续目标仓位 (Target Allocation %)”**。

### 2.1 架构组件 (Modular Architecture)

#### A. 动态证据聚合器 (Dynamic Evidence Aggregator)
- **相关性自适应 (Correlation Adaptive)**：
    - 引入 `CorrelationEngine`：实时计算 BTC 与 Macro (DXY, Yields)、Equities (SPX) 的滚动相关性。
    - **权重漂移 (Weight Drift)**：根据相关性动态调整 `StrategicBlock` 的权重权重分配。
- **信息熵权 (Entropy Weighting)**：根据因子当前所处的百分位（如 MVRV 进入极端低估区），自动提升该区块的信噪比权重。

#### B. 概率置信度评分器 (Probabilistic Confidence Scorer)
- **非二元门控 (Non-Binary Gating)**：废弃“因子缺失即降级”逻辑。
- **证据衰减 (Evidence Decay)**：若核心因子（如 Puell Multiple）缺失，系统通过计算“信息残缺熵”，按比例下调该区块的置信度，而非直接归零。
- **非对称损失校准 (Asymmetric Loss Calibration)**：在计算置信度时，对“底部信号”给予更高的容错空间。

#### C. 目标仓位解析器 (Target Allocation Resolver)
- **映射模型**：$Target\% = Sigmoid(\sum Score_{Block} \times Confidence) \times Allocation_{Cap}$。
- **仓位层级 (Allocation Tiers)**：
    - **基础层 (20%)**：战略牛市周期的核心底仓。
    - **溢价层 (0-80%)**：受流动性与估值驱动的动态增量。
- **波动率步长 (Vol-Step Execution)**：根据当前市场 ATR (真实波幅) 建议到达目标仓位的执行周期（如 3 周或 8 周）。

---

## 3. 核心算法流程 (The TADR Execution Flow)

1.  **数据层**：Fetch 因子观测，同步获取相关性矩阵。
2.  **战略层 (Strategic Engine)**：
    - 确定当前市场 Regime (Capitulation / Expansion / Overheated)。
    - 根据 Regime 和相关性分配 Block Weights。
3.  **置信度层 (Calibration)**：
    - 计算证据一致性。
    - 处理缺失数据或 Stale 数据的权重衰减。
4.  **决策层 (Allocation Engine)**：
    - 计算 `Current_Target_Allocation`。
    - 与用户当前持仓进行 Diff，输出 `Action Intensity`。

---

## 4. 技术实施路线图 (Implementation Roadmap)

### Phase 1: 监控与影子系统 (Shadow Mode)
- 实现 `CorrelationEngine` 和 `LTM Strategy Drift` 监控。
- 在报告中增加 `Target Allocation (Experimental)` 指标。

### Phase 2: 逻辑解耦 (Decoupling)
- 将 `PositionAdvisoryEngine` 与 `IncrementalBuyEngine` 逻辑统一为单一的 `AllocationResolver`。
- 实现概率置信度算法，替换现有的 Hard-Gate 校验函数。

### Phase 3: 全面切换 (Full Migration)
- 废弃 `ADD/REDUCE/HOLD` 命令，转向 `Target-based Execution`。
- 对齐 Live 与 Backtest 的动态权重模型。

---

## 5. 设计约束 (Constraints)
- **Fail-Closed**：当宏观流动性数据（如 FRED）不可用且相关性处于高位时，Target Allocation 必须强制锚定在基础底仓水平。
- **Data Policy**：动态相关性计算必须仅依赖 `CCXT` 和 `FRED` 的免费接口，禁止引入付费数据依赖。

---
*签署人：系统架构设计委员会 (Gemini CLI)*
*日期：2026-03-27*
