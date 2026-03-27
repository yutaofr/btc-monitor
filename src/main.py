import argparse
from datetime import datetime, timezone
from src.strategy.advisory_evaluator import AdvisoryEvaluator
from src.strategy.position_advisory_engine import PositionAdvisoryEngine
from src.strategy.incremental_buy_engine import IncrementalBuyEngine
from src.strategy.reporting import build_dual_advisory_report

def run_evaluation():
    """Trigger a full evaluation cycle and print/notify result."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Market Evaluation Snapshot...")
    
    # Use AdvisoryEvaluator directly to fetch the raw IndicatorResult list
    # mapped to FactorObservations for the new AdvisoryEngine
    fetch_engine = AdvisoryEvaluator()
    raw_results = fetch_engine.evaluate_all()
    
    from src.strategy.factor_models import FactorObservation
    from src.strategy.factor_registry import get_factor
    from src.strategy.factor_utils import check_freshness
    
    observations = []
    for res in raw_results:
        try:
            definition = get_factor(res.name)
            ttl = definition.freshness_ttl_hours
            
            # IndicatorResult may have None. Fallback explicitly to now()
            obs_ts = res.timestamp if res.timestamp is not None else datetime.now(timezone.utc)
            is_fresh = check_freshness(obs_ts, ttl)
        except KeyError:
            is_fresh = True # Fallback for unknown factors
            obs_ts = res.timestamp if res.timestamp is not None else datetime.now(timezone.utc)
            
        observations.append(
            FactorObservation(
                name=res.name,
                score=res.score,
                is_valid=res.is_valid,
                confidence_penalty=10 if not res.is_valid else 0,
                details=getattr(res, "details", {}),
                description=getattr(res, "description", ""),
                timestamp=obs_ts,
                freshness_ok=is_fresh,
                blocked_reason=""
            )
        )
    
    pos_engine = PositionAdvisoryEngine()
    cash_engine = IncrementalBuyEngine()
    
    pos_recommendation = pos_engine.evaluate(observations)
    cash_recommendation = cash_engine.evaluate(observations)
    
    curr_price = fetch_engine.get_current_price() or 0
    report = build_dual_advisory_report(pos_recommendation, cash_recommendation, current_price=curr_price)
    
    print("-" * 30)
    print(report)
    print("-" * 30)
    
    print(f"[{datetime.now(timezone.utc).isoformat()}] Cycle Complete. Decisions: Pos={pos_recommendation.action}, Cash={cash_recommendation.action}")

def main():
    parser = argparse.ArgumentParser(description="BTC Monitor DCA & Position Management (Run-Once Tool)")
    parser.add_argument("--now", action="store_true", help="(Deprecated) Kept for backward compatibility. The tool always runs immediately now.")
    args = parser.parse_args()

    # The tool is now a pure CLI utility. Scheduling should be done externally (e.g., via Cron).
    run_evaluation()

if __name__ == "__main__":
    main()

