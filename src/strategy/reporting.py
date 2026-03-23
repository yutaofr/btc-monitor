from src.strategy.policies import (
    MIN_STRATEGIC_VALID_RATIO,
    REQUIRED_STRATEGIC_FACTORS,
    STRATEGIC_FACTORS,
    STRATEGIC_WEIGHTS,
    TACTICAL_FACTORS,
    TACTICAL_WEIGHTS,
    classify_factor,
)


def _coverage_ratio(results, factor_names, weight_map):
    total_weight = sum(weight_map.get(name, 1.0) for name in factor_names)
    if total_weight == 0:
        return 0.0

    valid_weight = 0.0
    for result in results:
        if result.name in factor_names and result.is_valid:
            valid_weight += weight_map.get(result.name, result.weight)

    return round((valid_weight / total_weight) * 100, 2)


def summarize_results(results, is_research_only):
    strategic_results = []
    tactical_results = []
    research_results = []
    unknown_results = []

    for result in results:
        research_only = is_research_only(result)
        layer = classify_factor(result.name, research_only=research_only)
        if layer == "strategic":
            strategic_results.append(result)
        elif layer == "tactical":
            tactical_results.append(result)
        elif layer == "research":
            research_results.append(result)
        else:
            unknown_results.append(result)

    valid_strategic_names = {
        result.name for result in strategic_results if result.is_valid
    }
    missing_required = [
        name for name in REQUIRED_STRATEGIC_FACTORS if name not in valid_strategic_names
    ]

    return {
        "strategic_results": strategic_results,
        "tactical_results": tactical_results,
        "research_results": research_results,
        "unknown_results": unknown_results,
        "strategic_coverage": _coverage_ratio(strategic_results, STRATEGIC_FACTORS, STRATEGIC_WEIGHTS),
        "tactical_coverage": _coverage_ratio(tactical_results, TACTICAL_FACTORS, TACTICAL_WEIGHTS),
        "missing_required": missing_required,
        "excluded_research": [result.name for result in research_results],
    }


def build_report(
    results,
    final_score,
    price,
    budget_multiplier,
    strategic_score,
    tactical_score,
    regime,
    timing,
    is_research_only,
):
    summary = summarize_results(results, is_research_only)

    lines = []
    lines.append(f"# BTC Monitor Report")
    lines.append(f"**Final Score:** `{final_score}` / 100")
    lines.append(f"**Strategic Score:** `{strategic_score}` / 100")
    lines.append(f"**Tactical Score:** `{tactical_score}` / 100")
    lines.append(f"**Regime:** `{regime}`")
    lines.append(f"**Timing:** `{timing}`")
    lines.append(f"**Price:** ${price:,.2f}")
    lines.append(f"**Budget Multiplier:** {budget_multiplier}x")
    lines.append(f"**Strategic Coverage:** `{summary['strategic_coverage']}`%")
    lines.append(f"**Tactical Coverage:** `{summary['tactical_coverage']}`%")
    lines.append(f"**Min Strategic Coverage Target:** `{round(MIN_STRATEGIC_VALID_RATIO * 100, 2)}`%")

    if summary["missing_required"]:
        lines.append("**Missing Required Core Factors:** " + ", ".join(summary["missing_required"]))
    else:
        lines.append("**Missing Required Core Factors:** none")

    if summary["excluded_research"]:
        lines.append("**Excluded Research Factors:** " + ", ".join(summary["excluded_research"]))
    else:
        lines.append("**Excluded Research Factors:** none")

    lines.append("\n## Multi-Factor Breakdown")

    for result in results:
        research_only = is_research_only(result)
        layer = classify_factor(result.name, research_only=research_only)
        if research_only:
            status_emoji = "🔒"
            label = " (research-only)"
        elif layer in ("strategic", "tactical"):
            status_emoji = "✅" if result.score > 0 else "❌" if result.score < 0 else "⚪"
            label = f" ({layer})"
        else:
            status_emoji = "⚪"
            label = " (excluded)"

        lines.append(f"- {status_emoji} **{result.name}**{label}: {result.score} (_{result.description}_)")

    return "\n".join(lines)

def build_advisory_report(rec, current_price: float = 0.0) -> str:
    """
    Builds a markdown report from a pure AdvisoryEngine Recommendation output.
    """
    lines = []
    lines.append("# BTC Monitor Advisory Report")
    lines.append(f"**Action:** `{rec.action}`")
    lines.append(f"**Confidence:** `{rec.confidence}` / 100")
    lines.append(f"**Regime:** `{rec.strategic_regime}`")
    lines.append(f"**Tactical State:** `{rec.tactical_state}`")
    
    if current_price > 0:
        lines.append(f"**Price:** ${current_price:,.2f}")
        
    lines.append(f"\n**Summary:** {rec.summary}")
    
    if rec.action in ("HOLD", "INSUFFICIENT_DATA") and rec.blocked_reasons:
        lines.append("\n## Blocked Reasons:")
        for reason in rec.blocked_reasons:
            lines.append(f"- {reason}")
            
    if rec.missing_required_blocks:
        lines.append(f"\n**Missing Blocks:** {', '.join(rec.missing_required_blocks)}")
        
    if rec.missing_required_factors:
        lines.append(f"**Missing Required Factors:** {', '.join(rec.missing_required_factors)}")
        
    lines.append("\n## Confluence Analysis")
    if rec.supporting_factors:
        lines.append(f"**Supporting Factors:** {', '.join(rec.supporting_factors)}")
    else:
        lines.append("**Supporting Factors:** none")
        
    if rec.conflicting_factors:
        lines.append(f"**Conflicting Factors:** {', '.join(rec.conflicting_factors)}")
        
    if rec.freshness_warnings:
        lines.append("\n## ⚠️ Freshness Warnings")
        for warning in rec.freshness_warnings:
            lines.append(f"- {warning}")
            
    if rec.excluded_research_factors:
        lines.append(f"\n**Excluded Research Factors:** {', '.join(rec.excluded_research_factors)}")
        
    return "\n".join(lines)
