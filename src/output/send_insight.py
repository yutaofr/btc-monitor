import argparse
import os
import sys
import json
import urllib.request
from datetime import datetime


DISCORD_MAX_CONTENT_BYTES = 1900


def byte_len(text):
    return len(text.encode("utf-8"))


def hard_split_text(text, max_bytes):
    chunks = []
    current = []
    current_bytes = 0
    for char in text:
        char_bytes = byte_len(char)
        if current and current_bytes + char_bytes > max_bytes:
            chunks.append("".join(current))
            current = []
            current_bytes = 0
        current.append(char)
        current_bytes += char_bytes
    if current:
        chunks.append("".join(current))
    return chunks


def split_discord_messages(content, max_bytes=DISCORD_MAX_CONTENT_BYTES):
    if byte_len(content) <= max_bytes:
        return [content]

    chunks = []
    current = ""
    blocks = content.split("\n\n")

    for index, block in enumerate(blocks):
        piece = block if index == 0 else "\n\n" + block
        if byte_len(piece) > max_bytes:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(hard_split_text(piece.lstrip("\n"), max_bytes))
            continue

        if current and byte_len(current + piece) > max_bytes:
            chunks.append(current)
            current = block
        else:
            current += piece

    if current:
        chunks.append(current)
    return chunks


def add_chunk_headers(chunks, title="BTC Monitor AI Report", max_bytes=DISCORD_MAX_CONTENT_BYTES):
    if len(chunks) == 1:
        return chunks

    payloads = []
    total = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        header = f"**{title} ({index}/{total})**\n"
        budget = max_bytes - byte_len(header)
        if byte_len(chunk) > budget:
            split_chunks = hard_split_text(chunk, budget)
            return add_chunk_headers(
                chunks[: index - 1] + split_chunks + chunks[index:],
                title=title,
                max_bytes=max_bytes,
            )
        payloads.append(header + chunk)
    return payloads


def post_to_discord(webhook_url, content, username="BTC Monitor AI"):
    """Sends a raw text/markdown message to Discord via webhook."""
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
            code = res.getcode()
            body = res.read().decode('utf-8')
            print(f"[INFO] Discord responded with code: {code}, body: {body}")
            return code
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Discord HTTP Error: {e.code} - {e.reason}")
        print(f"[ERROR] Response body: {e.read().decode('utf-8')}")
        return e.code
    except Exception as e:
        print(f"[ERROR] Discord post failed: {e}")
        return None


def send_content_to_discord(webhook_url, content, max_bytes=DISCORD_MAX_CONTENT_BYTES):
    chunks = split_discord_messages(content, max_bytes=max_bytes)
    payloads = add_chunk_headers(chunks, max_bytes=max_bytes)

    for index, payload in enumerate(payloads, start=1):
        code = post_to_discord(webhook_url, payload)
        if code is None or code >= 300:
            print(f"[ERROR] Discord chunk {index}/{len(payloads)} failed with code: {code}")
            return 1
    return 0


def generate_raw_digest(json_path):
    """Generates a high-fidelity markdown summary from the sanitized JSON."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        v3 = data.get("v3_recommendation", {})
        state = data.get("v3_state", {})
        legacy = data.get("legacy", {})
        
        action = v3.get("action", "N/A")
        confidence = v3.get("confidence", 0)
        allocation = state.get("target_allocation", 0)
        regime = v3.get("strategic_regime", "N/A")
        
        status_emoji = "📈" if action == "ADD" else "📉" if action == "REDUCE" else "🛡️"
        
        # Build Factor Summary (top 5)
        factors = v3.get("supporting_factors", [])
        factor_str = ", ".join([f"`{f}`" for f in factors[:5]]) if factors else "None"
        
        digest = (
            f"## {status_emoji} BTC Monitor V3 Signal: **{action}**\n"
            f"**Summary**: {v3.get('summary', 'N/A')}\n\n"
            f"**📊 Key Metrics**:\n"
            f"- **Target Allocation**: `{allocation:.1%}`\n"
            f"- **System Confidence**: `{confidence}%`\n"
            f"- **Market Regime**: `{regime}`\n"
            f"- **Tactical State**: `{v3.get('tactical_state', 'N/A')}`\n\n"
            f"**✅ Supporting Factors**: {factor_str}\n\n"
            f"**🔄 Legacy Sync**:\n"
            f"- Position: `{legacy.get('pos', {}).get('action', 'N/A')}`\n"
            f"- Cash: `{legacy.get('cash', {}).get('action', 'N/A')}`\n\n"
            f"---\n"
            f"*Note: AI interpretation skipped due to background environment. Using Raw Data fallback.*"
        )
        return digest
    except Exception as e:
        return f"⚠️ **BTC Monitor**: Error generating raw digest from JSON: {e}"

def main(argv=None):
    parser = argparse.ArgumentParser(description="Discord Insight Dispatcher")
    parser.add_argument("--mode", choices=["insight", "fallback_error"], required=True)
    parser.add_argument("--input", help="Path to gemini_insight.md (for insight mode)")
    parser.add_argument("--stage", help="Failing stage (for fallback_error mode)")
    parser.add_argument("--validated-json", help="Path to sanitized JSON (for fallback_error mode)")
    parser.add_argument("--message", help="Custom error message")
    
    args = parser.parse_args(argv)
    
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
        exit_code = send_content_to_discord(webhook_url, content)
        sys.exit(exit_code)
        
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
        exit_code = send_content_to_discord(webhook_url, error_msg)
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
