import pandas as pd
import os

def generate_report(pos_csv, cash_csv, report_path):
    pos_df = pd.read_csv(pos_csv) if os.path.exists(pos_csv) else None
    cash_df = pd.read_csv(cash_csv) if os.path.exists(cash_csv) else None
    
    with open(report_path, "w") as f:
        f.write("# BTC Monitor Dual-Decision Backtest Report\n")
        f.write(f"**Generated:** {pd.Timestamp.now()}\n\n")
        
        if pos_df is not None:
            f.write("## 1. Position Advisory Performance\n")
            _write_branch_metrics(f, pos_df, ["ADD", "REDUCE"])
            
        if cash_df is not None:
            f.write("\n## 2. Incremental Cash Advisory Performance\n")
            _write_branch_metrics(f, cash_df, ["BUY_NOW", "STAGGER_BUY"])
            
            f.write("\n### 2.1 Benchmark-Aware Timing vs DCA\n")
            _write_cash_timing_metrics(f, cash_df, "BUY_NOW", ">", "BUY_NOW beats DCA")
            _write_cash_timing_metrics(f, cash_df, "STAGGER_BUY", "<", "DCA beats immediate buy")

def _write_branch_metrics(f, df, actions):
    f.write("| Action | Count | 28d Precision | 84d Precision | 182d Precision |\n")
    f.write("|--------|-------|---------------|---------------|----------------|\n")
    for act in actions:
        subset = df[df["action"] == act]
        count = len(subset)
        p28 = _calc_prec(subset, "precision_28")
        p84 = _calc_prec(subset, "precision_84")
        p182 = _calc_prec(subset, "precision_182")
        f.write(f"| {act} | {count} | {p28} | {p84} | {p182} |\n")

def _calc_prec(subset, col):
    if col not in subset.columns: return "N/A"
    # CSV serialization may store booleans as strings ("True"/"False") or numerics
    raw = subset[col].dropna().astype(str).str.strip().str.lower()
    vals = raw.map({"true": 1.0, "false": 0.0, "1.0": 1.0, "0.0": 0.0, "1": 1.0, "0": 0.0})
    vals = vals.dropna()
    n = len(vals)
    if n == 0: return "N/A"
    if n < 5: return f"{vals.mean():.1%} (N={n}) ⚠️"
    return f"{vals.mean():.1%} (N={n})"


def _write_cash_timing_metrics(f, df, action, direction_symbol, success_label):
    subset = df[df["action"] == action]
    f.write(f"\n#### {action} ({success_label})\n")
    if subset.empty:
        f.write("No samples found.\n")
        return

    f.write("| Window | Avg Rel Perf (%) | N | Success Rate |\n")
    f.write("|--------|------------------|---|--------------|\n")
    for win in [28, 84]:
        perf_col = f"rel_dca_perf_{win}"
        success_col = f"timing_success_{win}"
        if perf_col not in subset.columns:
            continue

        vals = subset[perf_col].dropna()
        if vals.empty:
            continue

        avg = vals.mean()
        n = len(vals)

        if success_col in subset.columns:
            success_vals = subset[success_col].dropna().astype(bool)
            success = success_vals.mean() if not success_vals.empty else float("nan")
            success_str = "N/A" if pd.isna(success) else f"{success:.1%}"
        else:
            success = (vals > 0).mean() if direction_symbol == ">" else (vals < 0).mean()
            success_str = f"{success:.1%}"

        f.write(f"| {win}d | {avg:.2f}% | {n} | {success_str} |\n")


if __name__ == "__main__":
    generate_report(
        "data/backtest/position/results.csv",
        "data/backtest/cash/results.csv",
        "data/backtest/dual_performance_report.md"
    )
