# BTC Monitor: 比特币长线分层定投与仓位管理系统

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-39%20passed-success.svg)](/tests/unit)

**BTC Monitor** 是一个面向比特币长期投资者的量化决策支持工具。系统采用了“无状态高确信度建议引擎 (Stateless Advisory Engine)”架构，不再直接接管预算与执行，而是通过严谨的证据分块、回退限制与置信度打分，来输出最高质量的长期分批建仓与减仓建议：

1. 当前战略周期是否支持建仓（或减仓）
2. 战术级别是否确认了相应的时机
3. 通过严格的操作门槛（Action Gates）给出最终建议：`ADD`、`REDUCE` 或 `HOLD`

> **核心约束**
> 本项目禁止使用任何付费 API、付费数据源、试用后收费数据接口或商业终端数据。生产决策仅依赖免费公开数据。

> **运行方式**
> 项目已移除内部常驻调度，需要由外部调度系统触发，推荐每周运行一次。

---

## 核心架构

### 1. 战略层 Strategic

战略层决定长期配置方向，只使用慢变量和高解释力因子：

- `MVRV_Proxy`
- `Puell_Multiple`
- `200WMA`
- `Cycle_Pos`
- `Net_Liquidity`
- `Yields`

输出战略状态：

- `AGGRESSIVE_ACCUMULATE`
- `NORMAL_ACCUMULATE`
- `DEFENSIVE_HOLD`
- `RISK_REDUCE`

### 2. 战术层 Tactical

战术层只负责执行时机确认，不负责决定长期方向：

- `RSI_Div`
- `FearGreed`

输出时机状态：

- `BUY_NOW`
- `STAGGER_BUY`
- `WAIT`

### 3. 建议层 (Advisory Layer)

建议层（`AdvisoryEngine`）严格无状态，评估战略与战术的并发确认情况，输出确信度（Confidence Score, 0-100）与最终动作建议：

- `ADD`: 明确的增配信号（需战略与战术双确认满足最低阈值）
- `REDUCE`: 明确的减配信号
- `HOLD`: 不满足操作条件，持币观望
- `INSUFFICIENT_DATA`: 核心数据缺失，采取保守回退（Fail-Closed）

系统通过独立的评价机制阻拦由于单方面异常引发的伪动作。

---

## 因子分层与状态

### 生产核心因子

这些因子会进入生产评分：

- `MVRV_Proxy`
- `Puell_Multiple`
- `200WMA`
- `Cycle_Pos`
- `Net_Liquidity`
- `Yields`
- `RSI_Div`
- `FearGreed`

### 研究因子

这些因子仍会显示在报告中，但已经冻结为 `research-only`，**不再参与生产评分**：

- `Production_Cost`
- `Options_Wall`
- `ETF_Flow`

冻结原因：

- 免费历史数据不可回放
- 数据源稳定性不足
- 当前实现仍属于研究代理，不适合作为生产决策依据

---

## 数据源策略

### 允许的免费数据源

- BTC 行情：`Binance public`, `Yahoo Finance`, `CoinGecko`, `CryptoCompare`
- 宏观数据：`FRED`
- 链上免费数据：`Blockchain.com`, `Mempool.space`
- 情绪数据：`Alternative.me Fear & Greed`

### 明确禁止

- 任何付费 API
- 任何需要 billing setup 的数据接口
- 只有实时免费、历史收费的核心生产信号
- 无法稳定回测复现的主评分数据源

---

## 决策逻辑

当前系统由 `factor_registry.py` 驱动因子树与评价：

- 战略层分数主导长期方向 (Regime)
- 战术层确认入场/减仓时机 (Tactical State)
- 动作门槛（Action Gates）严格校验：例如 `ADD` 必须具备至少 N 个有效的基本面独立块证据，且战术面不得存在严重背离。
- 若战略或战术数据严重受损缺失，则默认回退（Fail-Closed）输出 `HOLD`，同时降低确信度。

执行动作示例：

- `BULLISH` (战略) + `CONFIRMED_UP` (战术) -> 强置信度的 `ADD`
- 缺失核心区块证据 -> 建议动作降级为 `HOLD`，并在报告中显式说明 `Blocked Reasons`

---

## 项目结构

```text
btc-monitor/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── fetchers/
│   ├── indicators/
│   ├── strategy/
│   │   ├── advisory_engine.py
│   │   ├── factor_models.py
│   │   ├── factor_registry.py
│   │   ├── strategic_engine.py
│   │   ├── tactical_engine.py
│   │   └── reporting.py
│   ├── state/
│   └── backtest/
├── tests/unit/
├── data/
├── docs/plans/
├── Dockerfile
└── docker-compose.yml
```

---

## 快速开始

### 1. 环境准备

建议使用 Docker 运行。宿主机本地开发则使用 Python 3.12。

### 2. 配置

1. 复制环境变量模板：`cp .env.example .env`
2. 配置 `FRED_API_KEY`
3. Telegram 通知为可选项

### 3. 运行评估

```bash
docker build -t btc-monitor .
docker run --rm --env-file .env -v $(pwd)/data:/app/data btc-monitor
```

### 4. 运行单元测试

```bash
docker run --rm --env-file .env btc-monitor pytest tests/unit
```

### 5. 运行回测

```bash
docker run --rm --env-file .env btc-monitor python -m src.backtest.btc_backtest
```

### 6. 使用 docker compose

```bash
docker compose build
docker compose run --rm app
docker compose run --rm tests
```

---

## 报告输出

当前报告会展示：

- `Final Score`
- `Strategic Score`
- `Tactical Score`
- `Regime`
- `Timing`
- `Strategic Coverage`
- `Missing Required Core Factors`
- `Excluded Research Factors`

示例：

```text
# BTC Monitor Advisory Report
**Action:** `ADD`
**Confidence:** `90` / 100
**Regime:** `BULLISH`
**Tactical State:** `CONFIRMED_UP`
**Price:** $65,000.00

**Summary:** Strong conviction standard allocation.

## Confluence Analysis
**Supporting Factors:** MVRV_Proxy, 200WMA, Puell_Multiple, RSI_Div
```

---

## 回测说明

回测现在已对齐 live 评分框架：

- 使用同一套分层合成规则
- 使用免费历史链上估值数据
- 研究因子保持 `research-only`
- 新增了 live/backtest parity 测试，避免线上线下评分逻辑再次漂移

需要注意：

- `FearGreed`、`Options_Wall`、`ETF_Flow` 缺乏稳定免费历史回放，回测中不进入生产评分
- 当前回测已经比旧版本更接近 live，但仍是策略验证工具，不是交易仿真系统

---

## 当前状态

本仓库当前已完成：

- 研究因子冻结
- 分层评分架构
- 执行决策引擎
- 时区感知状态管理
- 报告覆盖率诊断
- live/backtest parity 校验

当前单元测试状态：`39 passed`

---

## 免责声明

本项目仅用于技术研究与策略实验，不构成任何投资建议。加密资产波动极高，请独立判断并自担风险。
