# BTC Monitor: 比特币长线共振定投与仓位管理系统

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-22%20passed-success.svg)](/tests/unit)

**BTC Monitor** 是一款专为比特币长线投资者设计的量化决策支持系统。系统通过每周一次（巴黎时间周一晚9点）的深度市场扫描，结合9大核心维度的共振信号，自动判定当月定投的最佳时机，并提供牛市顶部的止盈/转配建议。

---

## 🎯 核心逻辑与原则

### 1. 九大因子共振系统 (Multi-Factor Confluence)
系统不仅监控价格，更通过以下层级进行归一化打分：
*   **技术面 (Technical)**: 200WMA 偏离度、Pi Cycle 周期顶部、周线 RSI 底背离。
*   **宏观与流动性 (Macro)**: 全球美元净流动性 (WALCL - TGA - RRP) 变化、10年美债收益率趋向。
*   **情绪与周期 (Sentiment)**: 恐慌贪婪指数、距历史高点的回撤深度 (Drawdown)。
*   **资金面 (Options/ETF)**: BITO 期权 Put Wall 支撑位、现货 ETF (IBIT) 资金流向与价格的背离分析。

### 2. 量化工程原则
*   **动态归一化得分**: 针对免费 API 不稳定的现状，采用动态分母计算。若某个 API 挂掉，系统自动剔除该权重并重新归一化得分，确保决策不中断。
*   **额度结转机制**: 本月若无买入信号，定投额度自动累加至下月，最高支持 3.0x 累计。
*   **安全至上**: 严禁代码硬编码 Key，全隔离 Docker 环境运行。

---

## 📂 项目结构

```text
btc-monitor/
├── src/
│   ├── main.py          # 主入口与调度器 (周一晚9点)
│   ├── config.py        # 环境变量与阈值配置
│   ├── indicators/      # 因子计算逻辑 (Technical, Macro, ETF等)
│   ├── strategy/        # 归一化打分与决策引擎
│   └── state/           # 状态持久化 (state.json)
├── tests/               # 完整的单元测试套件 (22+ cases)
├── data/                # 本地存储 (state.json, logs)
├── .env.example         # 环境变量模板
├── Dockerfile           # 运行环境
└── docker-compose.yml   # 容器定义
```

---

## 🚀 快速开始

### 1. 环境准备
确保您的机器已安装 **Docker** 和 **Docker Compose**。

### 2. 配置 API Key
1. 复制模板文件：`cp .env.example .env`
2. 获取 [FRED API Key](https://fred.stlouisfed.org/docs/api/api_key.html) 并填入 `.env`。
3. (可选) 配置 Telegram 通知 Token。

### 3. 一键运行与测试

**执行即时诊断 (Dry-run):**
```bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt && PYTHONPATH=. python src/main.py --now"
```

**运行所有单元测试:**
```bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt && PYTHONPATH=. pytest tests/unit"
```

**后台持续运行 (生产模式):**
```bash
docker-compose up -d app
```

---

## 📊 报告示例

系统每次运行会生成如下格式的诊断报告：
> **Final Score:** `78.5` / 100
> **Decision: [BUY]** - Execute DCA with 1.0x budget.
> 
> **Breakdown:**
> - ✅ **200WMA**: 9.5 (Price below 200WMA)
> - ✅ **ETF_Flow**: 8.0 (Price Down, IBIT Inflow Divergence)
> - ❌ **FearGreed**: -2.0 (Neutral Sentiment)
> ...

---

## ⚖️ 免责声明
本软件仅供技术研究分享，不构成任何投资建议。虚拟货币投资具有极高风险，请投资者根据自身风险承受能力独立决策。
