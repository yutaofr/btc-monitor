# 策略监控系统架构演进与知识库 (Architectural Roadmap)

**文档编号：** `ARCH-KB-2026-03-27`  
**关联需求：** `SRD-2026-03-27-MONITORING`  
**状态：** 存档 (用于指导未来迭代)

---

## 1. 架构回顾 (Post-Mortem)

在 `v1.2` 版本中，我们引入了基于 **滑动窗口 (Sliding Window)** 和 **滚动相关性 (Rolling Correlation)** 的监控体系。该架构成功实现了“分析层”与“建议层”的解耦，确保了在不增加生产环境复杂度的前提下，提升了系统的自诊断能力。

---

## 2. 核心架构建议与演进路径 (Future Improvements)

### 2.1 性能扩展与计算缓存 (Performance Scaling & Caching)
**当前现状：** `compute_rolling_correlation` 采用 Pandas 矢量化计算，在 10 年量级的数据表现良好。  
**潜在风险：** 随着回测历史扩展到 20 年（包含早期高频数据）或引入更多宏观因子，重复计算 Pearson 相关系数将产生非必要的 CPU 开销。  
**建议方案：**
- **持久化缓存 (Disk-based Caching)**：由于历史宏观数据（如 2015 年的 DXY）是静态的，建议引入 `joblib` 或简单的 JSON 缓存层。
- **增量更新 (Incremental Updates)**：仅对新增的一周数据进行相关性滑动计算，而非每次回测重新计算全量历史。

### 2.2 自适应漂移阈值 (Adaptive Drift Thresholds)
**当前现状：** 漂移预警阈值硬编码为 `15%`（即 LTM 精度低于 Full History 85% 时报警）。  
**潜在风险：** 固定阈值无法应对不同市场波动率（Volatility Regimes）下的精度扰动。在牛市末期，噪声增加可能导致频繁误报。  
**建议方案：**
- **配置化 (Externalized Config)**：将 `DRIFT_THRESHOLD` 移入 `src/config.py`。
- **统计学置信区间 (Z-Score Drift)**：未来演进为基于标准差的偏移检测。当 `LTM_Precision < (Full_Mean - 2 * Full_Std)` 时触发预警，而非固定百分比。

### 2.3 机构化相关性扩展 (Institutional Correlation Expansion)
**当前现状：** 目前仅追踪 DXY 和 Yields。  
**背景分析：** 随着 2024 年现货 ETF 的引入，BTC 的价格形成机制正在发生结构性变化。  
**建议方案：**
- **ETF Flow Correlation**：在 `metrics.py` 中增加对 ETF 净流入（Proxy data from Yahoo Finance）的相关性追踪。
- **高频宏观锚定**：增加对美股（NVDA/NDX）的相关性监控，识别 BTC 作为“高贝塔科技资产”的属性偏移。

---

## 3. 知识库记录 (Lessons Learned)

### 3.1 生产/回测一致性 (Parity Principle)
**核心教训：** 在早期的 `v1.1` 开发中，生产代码的 `IndicatorResult` 与回测脚本的得分计算曾出现微小漂移。  
**架构要求：** **“一致性之盾 (Parity Shield)”**（即 `test_parity_logic.py`）必须作为 CI 的强制环节。任何对 `AdvisoryEngine` 的修改，必须通过随机采样测试，证明回测逻辑与之 100% 对齐。

### 3.2 非侵入式设计 (Non-Invasive Analytics)
**设计共识：** 监控代码绝不能出现在 `src/strategy/advisory_engine.py` 中。保持决策路径的简洁（Clean Path）是系统高可用性的前提。监控元数据应通过 `Recommendation` 对象的 `metadata` 或 `reporting` 层的可选参数进行注入。

---
**架构师签核：**  
*2026-03-27 - Senior System Architect*
