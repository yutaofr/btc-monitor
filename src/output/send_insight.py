import argparse
import os
import sys
import json
from src.output.discord_notifier import send_discord_signal

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
            content = f.read()
            
        # For MVP, we'll just print it or send a simplified notification
        # In a real impl, we'd use discord_notifier to send a rich embed with the MD content
        print(f"Sending Insight to Discord: {args.input}")
        # Placeholder for real discord call (since send_discord_signal expects Recommendation object)
        # We might need to extend discord_notifier.py to handle raw Markdown.
        
    elif args.mode == "fallback_error":
        print(f"Sending Fallback Error to Discord: Stage={args.stage}, Message={args.message}")
        # In a real impl, we'd extract a digest from validated-json and send it.

if __name__ == "__main__":
    main()
