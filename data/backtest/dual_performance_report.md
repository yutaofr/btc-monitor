# BTC Monitor Dual-Decision Backtest Report
**Generated:** 2026-03-27 10:40:58.656346

## 1. Position Advisory Performance
| Action | Count | 28d Precision | 84d Precision | 182d Precision |
|--------|-------|---------------|---------------|----------------|
| ADD | 8 | 100.0% (N=8) | 100.0% (N=8) | 100.0% (N=8) |
| REDUCE | 1 | 100.0% (N=1) ⚠️ | 100.0% (N=1) ⚠️ | 100.0% (N=1) ⚠️ |

### 1.1 Sliding Window Analysis (Strategy Drift Monitoring)
| Action | LTM Count | LTM Precision (28d) | Full History Precision (28d) | Drift Status |
|--------|-----------|--------------------|-----------------------------|--------------|
| ADD | 0.0 | 0.0% | 100.0% | ✅ STABLE |
| REDUCE | 0.0 | 0.0% | 100.0% | ✅ STABLE |

**LTM Macro Correlation:** DXY: `0.01`, Yields: `0.11`

## 2. Incremental Cash Advisory Performance
| Action | Count | 28d Precision | 84d Precision | 182d Precision |
|--------|-------|---------------|---------------|----------------|
| BUY_NOW | 0 | N/A | N/A | N/A |
| STAGGER_BUY | 8 | N/A | N/A | N/A |

### 2.1 Benchmark-Aware Timing vs DCA

#### BUY_NOW (BUY_NOW beats DCA)
No samples found.

#### STAGGER_BUY (DCA beats immediate buy)
| Window | Avg Rel Perf (%) | N | Success Rate |
|--------|------------------|---|--------------|
| 28d | 13.73% | 8 | 0.0% |
| 84d | 32.41% | 8 | 0.0% |
