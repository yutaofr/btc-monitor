import argparse
import os
import sys
import json
import urllib.request
from datetime import datetime

def post_to_discord(webhook_url, content, username="BTC Monitor AI"):
    """Sends a raw text/markdown message to Discord via webhook."""
    # Discord content limit is 2000 chars. We'll truncate if necessary.
    if len(content) > 1900:
        content = content[:1900] + "\n... (truncated)"
        
    payload = {
        "content": content,
        "username": username,
        "avatar_url": "https://bitcoin.org/img/icons/opengraph.png"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        webhook_url, 
        data=data, 
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            return res.getcode()
    except Exception as e:
        print(f"[ERROR] Discord post failed: {e}")
        return None

def generate_raw_digest(json_path):
    """Generates a human-readable markdown summary from the sanitized JSON."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        v3 = data.get("v3_recommendation", {})
        state = data.get("v3_state", {})
        
        action = v3.get("action", "N/A")
        confidence = v3.get("confidence", 0)
        allocation = state.get("target_allocation", 0)
        regime = v3.get("strategic_regime", "N/A")
        
        emoji = "📈" if action == "ADD" else "📉" if action == "REDUCE" else "🛡️"
        
        digest = (
            f"# {emoji} BTC Monitor Raw Signal: **{action}**\n"
            f"**Target Allocation**: `{allocation:.1%}`\n"
            f"**Confidence**: `{confidence}%`\n"
            f"**Market Regime**: `{regime}`\n\n"
            f"**Summary**: {v3.get('summary', 'N/A')}\n\n"
            f"--- \n"
            f"*AI interpretation skipped due to environment constraints.*"
        )
        return digest
    except Exception as e:
        return f"⚠️ **BTC Monitor**: Error generating raw digest from JSON: {e}"

def main():
    parser = argparse.ArgumentParser(description="Discord Insight Dispatcher")
    parser.add_argument("--mode", choices=["insight", "fallback_error"], required=True)
    parser.add_argument("--input", help="Path to gemini_insight.md (for insight mode)")
    parser.add_argument("--stage", help="Failing stage (for fallback_error mode)")
    parser.add_argument("--validated-json", help="Path to sanitized JSON (for fallback_error mode)")
    parser.add_argument("--message", help="Custom error message")
    
    args = parser.parse_args()
    
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not set.")
        sys.exit(1)
        
    if args.mode == "insight":
        if not args.input or not os.path.exists(args.input):
            print(f"Error: Insight file {args.input} not found.")
            sys.exit(1)
            
        with open(args.input, 'r') as f:
            content = f.read().strip()
            
        # Fallback to Raw Digest if insight is empty (e.g. Gemini failed in background)
        if not content:
            print(f"[{datetime.now().isoformat()}] Insight is empty. Falling back to Raw Digest.")
            if args.validated_json and os.path.exists(args.validated_json):
                content = generate_raw_digest(args.validated_json)
            else:
                content = "⚠️ **BTC Monitor Report**: AI interpretation unavailable and no sanitized data found."
            
        print(f"[{datetime.now().isoformat()}] Sending Insight to Discord...")
        post_to_discord(webhook_url, content)
        
    elif args.mode == "fallback_error":
        error_msg = f"## 🚨 BTC Monitor Service Alert\n**Stage**: {args.stage}\n**Error**: {args.message or 'Unknown error during execution.'}\n"
        
        # Try to append a summary if JSON exists
        if args.validated_json and os.path.exists(args.validated_json):
            try:
                with open(args.validated_json, 'r') as f:
                    data = json.load(f)
                    v3 = data.get("v3_recommendation", {})
                    error_msg += f"\n**Last Valid Recommendation**: {v3.get('action', 'N/A')} (Conf: {v3.get('confidence', '0')}%)"
            except:
                pass
                
        print(f"[{datetime.now().isoformat()}] Sending Fallback Error to Discord...")
        post_to_discord(webhook_url, error_msg)

if __name__ == "__main__":
    main()
