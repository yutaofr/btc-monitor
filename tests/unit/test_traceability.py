"""
SRT Traceability Matrix for BTC Monitor High-Confidence Advisory Architecture

| SRT Requirement                                              | Test Function Coverage                                                                                      |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1. Factor Registry Single Source of Truth                    | `test_factor_registry_completeness` (test_factor_registry.py)                                               |
| 2. Stateless Core Engine Evaluation                          | `test_engine_stateless_determinism` (test_advisory_engine.py)                                               |
| 3. Explicit ADD/REDUCE Action Gates                          | `test_evaluate_bullish_action`, `test_evaluate_blocked_action` (test_advisory_engine.py)                    |
| 4. Fail-Closed on Insufficient Strategic Data                | `test_get_strategic_regime_missing_blocks` (test_strategic_engine.py)                                       |
| 5. Confidence Score Monotonicity and Caps                    | `test_confidence_calculation_logic` (test_advisory_engine.py)                                               |
| 6. Isolation of Research-Only Factors (Zero Production Bias) | `test_research_factors_cannot_affect_advisory_actions` (test_advisory_engine.py)                            |
| 7. Backtest Artifact Schema Parity                           | `test_backtest_output_schema` (test_artifact_schema.py), `test_calculate_forward_returns` (test_advisory_metrics.py) |
"""

import ast
import os

def test_traceability_matrix_integrity():
    """Dynamically parses all test files to ensure the mapped traceability functions actually exist."""
    
    required_functions = [
        "test_registry_completeness",
        "test_advisory_deterministic_output",
        "test_one_factor_bullish_cannot_return_add",
        "test_mixed_evidence_returns_hold",
        "test_missing_blocks_returns_insufficient_data",
        "test_confidence_monotonicity",
        "test_research_factors_cannot_affect_advisory_actions",
        "test_backtest_output_schema",
        "test_calculate_forward_returns"
    ]
    
    found_functions = set()
    base_dir = os.path.join(os.path.dirname(__file__))
    
    for root, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename.startswith("test_") and filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    node = ast.parse(f.read(), filename=filepath)
                    for element in node.body:
                        if isinstance(element, ast.FunctionDef):
                            found_functions.add(element.name)
                            
    missing = [f for f in required_functions if f not in found_functions]
    assert not missing, f"Traceability Enforcement Failed. Missing required test implementations: {missing}"
