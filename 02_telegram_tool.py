"""02_telegram_tool.py — Resilient Telegram Notification Sender using BotFather Token.

Features:
- Handles long messages by splitting into chunks (Telegram limit is 4096 chars).
- Safe HTML / plain text fallback if Markdown parsing contains unclosed entity tags.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def send_telegram_message(message: str, bot_token: str = None, chat_id: str = None) -> str:
    """Send a formatted news digest message to Telegram channel or user."""
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not cid:
        print("\n⚠️ [Telegram Mock Mode] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured in .env.")
        print("📢 [Simulated Telegram Message Send]:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        return "MOCK_SUCCESS: Telegram token not configured, message printed to console."

    try:
        from telegram import Bot
        bot = Bot(token=token)

        # Telegram maximum message length is 4096 chars. Split if larger.
        chunks = []
        max_chunk = 3800
        lines = message.split("\n")
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_chunk:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk.strip():
            chunks.append(current_chunk)

        for chunk in chunks:
            try:
                # Try Markdown first
                await bot.send_message(chat_id=cid, text=chunk, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as parse_err:
                # Fallback to plain text if Markdown parsing fails
                print(f"Notice: Markdown entity issue ({parse_err}). Sending as clean text.")
                plain_text = chunk.replace("*", "").replace("`", "")
                await bot.send_message(chat_id=cid, text=plain_text, disable_web_page_preview=True)

        print("✅ Telegram notification sent successfully!")
        return "SUCCESS: Notification sent to Telegram."
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return f"ERROR: {e}"

if __name__ == "__main__":
    test_msg = "📰 *Daily Tech & Industry Digest*\n\n1. *Sample Headline*\nDetails about the event..."
    asyncio.run(send_telegram_message(test_msg))
