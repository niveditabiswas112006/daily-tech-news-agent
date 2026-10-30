"""05_daily_scheduler.py — Automated Scheduler for 10:45 AM Daily Telegram Delivery.

Teaching & Operational Goal:
Runs continuously and triggers the LangGraph workflow every day at 10:45 AM.
Also includes a `--now` option to test the exact 10:45 AM dispatch immediately.

Usage:
1. Run everyday in background at 10:45 AM:
   python3 05_daily_scheduler.py

2. Test immediate execution:
   python3 05_daily_scheduler.py --now
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
import schedule

HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE))
import importlib
daily_agent = importlib.import_module("03_langgraph_daily_agent")

def job_send_daily_news():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⏰ [{now_str}] Triggering 10:45 AM Daily News LangGraph Workflow...")
    try:
        app = daily_agent.build_daily_news_graph()
        result = app.invoke({"topic": "ai"})
        print(f"✅ [{now_str}] News Delivery Complete. Status: {result.get('delivery_status')}")
    except Exception as e:
        print(f"❌ [{now_str}] Error executing daily news job: {e}")

def main():
    parser = argparse.ArgumentParser(description="Daily 10:45 AM Telegram News Scheduler")
    parser.add_argument("--now", action="store_true", help="Run the daily news job immediately once")
    parser.add_argument("--time", type=str, default="10:45", help="Time of day to send news (HH:MM in 24hr format, default: 10:45)")
    args = parser.parse_args()

    if args.now:
        print("⚡ Executing immediate dispatch test...")
        job_send_daily_news()
        return

    target_time = args.time
    schedule.every().day.at(target_time).do(job_send_daily_news)
    
    print("=" * 60)
    print(f"⏰ Daily News Scheduler started!")
    print(f"📅 Scheduled to deliver news every day at: {target_time}")
    print(f"🤖 Connected to LangGraph Agent + MCP Server + Telegram Bot")
    print(f"Press Ctrl+C to stop.")
    print("=" * 60)

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()

