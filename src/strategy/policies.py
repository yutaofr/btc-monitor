"""Central policy definitions for strategy layers."""

STRATEGIC_FACTORS = (
    "MVRV_Proxy",
    "Puell_Multiple",
    "200WMA",
    "Cycle_Pos",
    "Net_Liquidity",
    "Yields",
)

TACTICAL_FACTORS = (
    "RSI_Div",
    "FearGreed",
)

RESEARCH_FACTORS = (
    "Production_Cost",
    "Options_Wall",
    "ETF_Flow",
)

REQUIRED_STRATEGIC_FACTORS = STRATEGIC_FACTORS

MIN_STRATEGIC_VALID_RATIO = 0.7

STRATEGIC_WEIGHTS = {
    "MVRV_Proxy": 1.5,
    "Puell_Multiple": 1.2,
    "200WMA": 1.0,
    "Cycle_Pos": 1.0,
    "Net_Liquidity": 1.0,
    "Yields": 1.0,
}

TACTICAL_WEIGHTS = {
    "RSI_Div": 1.0,
    "FearGreed": 1.0,
}

RESEARCH_WEIGHT = 1.0

COMBINED_LAYER_WEIGHTS = {
    "strategic": 0.7,
    "tactical": 0.3,
}


def classify_factor(name, *, research_only=False):
    if research_only or name in RESEARCH_FACTORS:
        return "research"
    if name in STRATEGIC_FACTORS:
        return "strategic"
    if name in TACTICAL_FACTORS:
        return "tactical"
    return "unknown"


def is_research_factor(name, *, research_only=False):
    return classify_factor(name, research_only=research_only) == "research"
