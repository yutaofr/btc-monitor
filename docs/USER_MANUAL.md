# BTC Monitor V3.0 (TADR) 用户手册

欢迎使用 **BTC Monitor V3.0**。本项目是专为比特币长期投资者设计的量化决策系统。本手册将指导您如何运行系统、解读 V3.0 (TADR) 报告以及执行历史审计。

---

## 1. 核心概念

### 1.1 TADR 架构
TADR 代表 **Target Allocation & Decision Resilience (目标仓位与决策韧性)**。与旧版本输出离散信号（如仅有 ADD/REDUCE）不同，V3.0 通过以下方式进行管理：
- **目标仓位 (%)**: 系统实时建议的 BTC 持仓比例（通常在 20% 底仓到 80% 重仓之间）。
- **置信度 (Confidence)**: 评估当前信号的强度。如果核心数据缺失，系统会通过熔断机制将置信度归零并锁定决策。
- **动态权重**: 系统自动识别 BTC 与宏观资产的相关性。例如，在 DXY 走强时，系统会自动调高宏观因子的权重。

---

## 2. 快速开始 (运行评估)

### 2.1 实时行情评估
每周运行一次系统以获取最新的仓位建议。

```bash
# 构建并运行评估
docker compose build
docker compose run --rm app
```

### 2.2 评估输出解读
系统会生成一个 Markdown 格式的报告（如 `data/reports/`），主要包含以下核心区块：

| 区块 | 说明 |
| :--- | :--- |
| **Action** | 建议的操作方向 (`ADD`, `REDUCE`, 或 `HOLD`)。 |
| **Target Allocation** | **关键指标**。建议的持仓比例，指导您的实盘操作。 |
| **Confidence** | 信号可信度。高于 70% 为强信号，低于 40% 建议保持观望。 |
| **Strategic Metrics** | 展示当前的市场环境（Regime）以及综合计分。 |
| **Factor Evidence** | 罗列所有生产因子的得分情况及权重缩放系数（Multiplier）。 |

---

## 3. 历史审计 (Acceptance Audit)

在您做出重大投资决策前，建议使用审计工具对当前逻辑进行历史回归，确认系统在类似历史环境下的表现。

### 运行审计
```bash
# 执行 V3.0 历史回测审计工具
export PYTHONPATH=$PYTHONPATH:. && python3 tests/acceptance/verify_tadr_v3.py
```

审计结果将保存在 `data/acceptance/v3_tadr_audit_results.csv`。通过观察系统在 2018、2021、2022 等历史阶段的表现，您可以更好地评估当前建议的稳健性。

---

## 4. 故障诊断与应急处理 (Fail-Closed)

### 4.1 熔断状态 (SYSTEM_GATE_LOCKED)
如果报告中出现 `🚨 SYSTEM_GATE_LOCKED` 警告，意味着系统检测到**核心数据缺失**（如宏观 FRED API 失效或估值数据无法获取）。

- **系统行为**: 自动将 `Action` 降级为 `HOLD`，并将目标仓位锁定在底仓水平。
- **处置方案**:
    1. 检查 `.env` 中的 `FRED_API_KEY` 是否有效。
    2. 核对 `requirements.txt` 中的依赖是否已全量安装。
    3. 运行全量测试 (`docker compose run --rm tests`) 定位缺失模块。

### 4.2 策略漂移 (Drift Warning)
如果系统报告中显示 `⚠️ DRIFT DETECTED`，代表最近 12 个月的策略表现与历史长期水平相比下降了 15% 以上。

- **处置方案**: 这通常代表市场范式发生了重大偏移，建议联系量化策略分析师或重新评估因子权重（`src/strategy/factor_registry.py`）。

---

## 5. 开发者与自定义

- **因子定义**: 若需调整因子权重或新增指标，请查阅 `src/strategy/factor_registry.py`。
- **仓位解析**: 目标仓位的解析逻辑位于 `src/strategy/allocation_resolver.py`。

---

## 免责声明
本项目仅用于技术研究与实验，不构成任何投资建议。加密资产波动极高，请独立判断并自担风险。
