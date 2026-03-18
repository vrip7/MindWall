"""
MindWall — Example Phishing Email Test Runner

Submits all example emails to the MindWall API and displays analysis results.
Requires: pip install httpx  (already installed if running from the API venv)

Usage:
    python examples/test_examples.py
    python examples/test_examples.py --file examples/ceo_fraud.json
    python examples/test_examples.py --url http://localhost:5297 --key YOUR_KEY
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required. Install with: pip install httpx")
    sys.exit(1)

DEFAULTS = {
    "url": "http://localhost:5297",
    "key": "CD080A0539991A69FC414E46CC3E7434",
}

SEVERITY_COLORS = {
    "low": "\033[92m",       # green
    "medium": "\033[93m",    # yellow
    "high": "\033[91m",      # red
    "critical": "\033[95m",  # magenta
}
RESET = "\033[0m"
BOLD = "\033[1m"


def analyze(client: httpx.Client, base_url: str, api_key: str, payload: dict) -> dict:
    """Submit a single email for analysis."""
    resp = client.post(
        f"{base_url}/api/analyze",
        json=payload,
        headers={"X-MindWall-Key": api_key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def print_result(filename: str, payload: dict, result: dict):
    """Pretty-print an analysis result."""
    severity = result.get("severity", "unknown")
    color = SEVERITY_COLORS.get(severity, "")
    score = result.get("manipulation_score", 0)
    action = result.get("recommended_action", "unknown")

    print(f"\n{'='*70}")
    print(f"{BOLD}File:{RESET}     {filename}")
    print(f"{BOLD}Subject:{RESET}  {payload.get('subject', 'N/A')}")
    print(f"{BOLD}From:{RESET}     {payload.get('sender_display_name', '')} <{payload.get('sender_email', '')}>")
    print(f"{BOLD}Score:{RESET}    {color}{score:.1f}/100{RESET}")
    print(f"{BOLD}Severity:{RESET} {color}{severity.upper()}{RESET}")
    print(f"{BOLD}Action:{RESET}   {action}")
    print(f"{BOLD}Time:{RESET}     {result.get('processing_time_ms', 0)}ms")

    dims = result.get("dimension_scores", {})
    if dims:
        # Show top 3 triggered dimensions
        top = sorted(dims.items(), key=lambda x: x[1], reverse=True)[:3]
        triggered = [(k, v) for k, v in top if v > 0]
        if triggered:
            print(f"{BOLD}Top dimensions:{RESET}")
            for dim, val in triggered:
                bar = "█" * int(val / 5) + "░" * (20 - int(val / 5))
                print(f"  {dim:<35} {bar} {val:.0f}")

    explanation = result.get("explanation", "")
    if explanation:
        # Truncate long explanations
        if len(explanation) > 200:
            explanation = explanation[:200] + "..."
        print(f"{BOLD}Explanation:{RESET} {explanation}")


def main():
    parser = argparse.ArgumentParser(description="Test MindWall with example phishing emails")
    parser.add_argument("--url", default=DEFAULTS["url"], help="MindWall API base URL")
    parser.add_argument("--key", default=DEFAULTS["key"], help="API secret key")
    parser.add_argument("--file", help="Test a single JSON file instead of all examples")
    args = parser.parse_args()

    examples_dir = Path(__file__).parent

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(examples_dir.glob("*.json"))

    if not files:
        print("No example JSON files found.")
        sys.exit(1)

    print(f"{BOLD}MindWall — Phishing Detection Test{RESET}")
    print(f"API: {args.url}")
    print(f"Examples: {len(files)} file(s)")

    passed = 0
    failed = 0

    with httpx.Client() as client:
        for filepath in files:
            try:
                payload = json.loads(filepath.read_text(encoding="utf-8"))
                # Ensure unique message_uid per run to avoid DB conflicts
                payload["message_uid"] = f"{payload['message_uid']}-{uuid.uuid4().hex[:8]}"
            except (json.JSONDecodeError, OSError) as e:
                print(f"\n[ERROR] Failed to read {filepath.name}: {e}")
                failed += 1
                continue

            try:
                start = time.perf_counter()
                result = analyze(client, args.url, args.key, payload)
                elapsed = (time.perf_counter() - start) * 1000

                print_result(filepath.name, payload, result)
                passed += 1
            except httpx.HTTPStatusError as e:
                print(f"\n[ERROR] {filepath.name}: HTTP {e.response.status_code} — {e.response.text[:200]}")
                failed += 1
            except httpx.ConnectError:
                print(f"\n[ERROR] Cannot connect to {args.url}. Is MindWall running?")
                sys.exit(1)
            except Exception as e:
                print(f"\n[ERROR] {filepath.name}: {e}")
                failed += 1

    print(f"\n{'='*70}")
    print(f"{BOLD}Results: {passed} passed, {failed} failed out of {len(files)} examples{RESET}")


if __name__ == "__main__":
    main()
