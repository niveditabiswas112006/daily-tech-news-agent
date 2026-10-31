"""05_realtime_news_monitor.py — Continuous Real-Time Tech News Monitor & Telegram Dispatcher.

Features:
- Continuously polls live news feeds (The Guardian, MIT Tech, TechCrunch Startups & AI,
  The Hacker News, CoinTelegraph, ArXiv AI) every X minutes (default: every 15 minutes, or custom).
- Instant Delivery: As soon as ANY new article, breaking story, or development appears,
  it immediately formats and pushes it to your Telegram bot.
- Deduplication: Uses the local SQLite history DB (`news_history.db`) to ensure you NEVER
  receive the same article twice.
- No Wait: You don't have to wait for a fixed 9:00 AM or 10:45 AM slot. Whenever tech happens,
  you get it immediately!

Usage:
  python3 05_realtime_news_monitor.py --interval 15
  (Runs continuously, checking every 15 minutes)

  python3 05_realtime_news_monitor.py --now
  (Runs an immediate check right now and dispatches any new stories)
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

HERE = Path(__file__).parent.resolve()
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

sys.path.insert(0, str(HERE))
import importlib
daily_agent = importlib.import_module("03_langgraph_daily_agent")


def run_realtime_check():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⚡ [{now_str}] Checking live feeds for fresh breaking news...")
    try:
        app = daily_agent.build_daily_news_graph()
        # Category filter 'all' covers Big Tech, Startups, AI, Cybersecurity, Blockchain
        result = app.invoke({"category_filter": "all"})
        status = result.get("delivery_status", "UNKNOWN")
        print(f"✅ [{now_str}] Check completed. Status: {status}")
        return status
    except Exception as e:
        print(f"❌ [{now_str}] Error during live news check: {e}")
        return f"ERROR: {e}"


def main():
    parser = argparse.ArgumentParser(description="Real-Time Tech News Monitor")
    parser.add_argument("--now", action="store_true", help="Run once immediately to fetch latest breaking news")
    parser.add_argument("--interval", type=int, default=15, help="Minutes between live feed checks (default: 15 mins)")
    args = parser.parse_args()

    if args.now:
        print("🚀 Checking live feeds immediately for any new stories...")
        run_realtime_check()
        return

    interval_minutes = max(1, args.interval)
    print("=" * 65)
    print("📡 Real-Time Tech News Monitor is ACTIVE!")
    print(f"🔄 Polling live feeds every {interval_minutes} minute(s) for fresh news.")
    print("📲 As soon as any new article appears, it is dispatched to Telegram.")
    print("Press Ctrl+C to stop.")
    print("=" * 65)

    # Run initial check immediately on startup
    run_realtime_check()

    # Loop continuously
    while True:
        try:
            time.sleep(interval_minutes * 60)
            run_realtime_check()
        except KeyboardInterrupt:
            print("\n🛑 Real-time monitor stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Polling loop error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
