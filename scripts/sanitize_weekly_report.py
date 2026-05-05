import json
import argparse
import os
import sys

def sanitize(data):
    """
    Strict allowlist-based sanitization for weekly reports.
    Removes all sensitive data (secrets, paths, identifiers) before passing to Gemini.
    """
    sanitized = {
        "timestamp": data.get("timestamp"),
        "v3_recommendation": None,
        "v3_state": None,
        "legacy": None,
        "raw_results_summary": []
    }
    
    # 1. Sanitize V3 Recommendation
    if data.get("v3_recommendation"):
        rec = data["v3_recommendation"]
        sanitized["v3_recommendation"] = {
            "action": rec.get("action"),
            "confidence": rec.get("confidence"),
            "strategic_regime": rec.get("strategic_regime"),
            "tactical_state": rec.get("tactical_state"),
            "supporting_factors": rec.get("supporting_factors", []),
            "conflicting_factors": rec.get("conflicting_factors", []),
            "summary": rec.get("summary")
        }
    
    # 2. Sanitize V3 Internal State (Crucial for Interpretabilty)
    if data.get("v3_state"):
        state = data["v3_state"]
        sanitized["v3_state"] = {
            "strategic_score": state.get("strategic_score"),
            "confidence": state.get("confidence"),
            "target_allocation": state.get("target_allocation"),
            "regime_labels": state.get("regime_labels", []),
            "gate_status_summary": {
                name: {"is_active": status.get("is_active")}
                for name, status in state.get("gate_status", {}).items()
            }
        }
        
    # 3. Sanitize Legacy Recommendations
    if data.get("legacy"):
        sanitized["legacy"] = {
            "pos": {
                "action": data["legacy"]["pos"].get("action"),
                "confidence": data["legacy"]["pos"].get("confidence")
            },
            "cash": {
                "action": data["legacy"]["cash"].get("action"),
                "confidence": data["legacy"]["cash"].get("confidence")
            }
        }
        
    # 4. Summary of raw results (Only name and score)
    if data.get("raw_results"):
        for res in data["raw_results"]:
            sanitized["raw_results_summary"].append({
                "name": res.get("name"),
                "score": res.get("score"),
                "is_valid": res.get("is_valid")
            })
            
    return sanitized

def main():
    parser = argparse.ArgumentParser(description="Sanitize weekly reports for AI interpretation")
    parser.add_argument("--input", required=True, help="Path to raw weekly_report.json")
    parser.add_argument("--output", required=True, help="Path to save sanitized JSON")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        sys.exit(1)
        
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
            
        sanitized_data = sanitize(data)
        
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(sanitized_data, f, indent=2)
            
        print(f"Sanitization complete. Clean data saved to {args.output}")
    except Exception as e:
        print(f"Error during sanitization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
