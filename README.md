# Daily News Agent 🗞️ (LangChain + LangGraph + FastMCP + Telegram Bot + Memory Chat)

Complete implementation of the **Daily 10:45 AM Telegram News Agent** based on the class requirements.

---

## 🎯 Architecture & Components

| Component | Technology | Role |
|---|---|---|
| **MCP Server** | `FastMCP` (`01_news_mcp_server.py`) | Provides news fetching across **The Guardian**, **MIT Technology Review**, **DeepLearning.AI / HackerNews**, and **TechCrunch AI**, deduplication checks, and memory query tools. |
| **Telegram Bot** | `python-telegram-bot` (`02_telegram_tool.py`) | Sends formatted news bulletins to user/group using BotFather credentials. |
| **LangGraph Agent** | `langgraph` + `langchain` (`03_langgraph_daily_agent.py`) | Orchestrates state machine: `fetch_node` ➔ `deduplicate_node` ➔ `summarize_node` ➔ `deliver_and_save_node`. |
| **Follow-up Chat UI** | `streamlit` (`04_chat_web_ui.py`) | Chat interface with **Memory Integration** to query details on past news (cyber attacks, funding, model releases). |
| **Daily 10:45 AM Scheduler** | `schedule` (`05_daily_scheduler.py`) | Automatically fires every day at **10:45 AM** (or custom time). |

---

## 📁 Project Structure

```
daily-news-agent/
├── 01_news_mcp_server.py      # Custom FastMCP Server with 4 sources + SQLite deduplication
├── 02_telegram_tool.py        # Telegram message dispatcher (BotFather integration)
├── 03_langgraph_daily_agent.py# LangGraph StateGraph Workflow (Fetch -> Deduplicate -> Summarize -> Deliver)
├── 04_chat_web_ui.py          # Streamlit Chat interface with Memory for follow-up questions
├── 05_daily_scheduler.py      # 10:45 AM daily automatic trigger runner
├── data/
│   └── news_history.db        # SQLite database for deduplication & memory queries
├── .env.example               # Environment variables template
├── .env                       # Active API tokens (Telegram, LLM)
└── README.md
```

---

## 🤖 1. Telegram Bot Setup (BotFather)

1. Open Telegram on your phone or computer.
2. Search for **`@BotFather`** and start the chat.
3. Send `/newbot` and give your bot a name and username (e.g. `MyDailyNewsBot`).
4. BotFather will provide an **HTTP API Token** like: `7123456789:ABCdefGhIJKlmNoP...`.
5. Open a chat with your new bot and click **Start** or send a message (e.g., `hello`).
6. Get your **Chat ID** by visiting:  
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`  
   *(or search `@userinfobot` on Telegram and click Start)*.
7. Add both to `daily-news-agent/.env`:
   ```env
   TELEGRAM_BOT_TOKEN="7123456789:ABCdefGhIJKlmNoP..."
   TELEGRAM_CHAT_ID="123456789"
   ```

---

## 🚀 2. How to Run & Test

First, navigate to the folder:
```bash
cd /Users/niveditabiswas/Downloads/AI-engineer-lecture-notes-master/daily-news-agent
```

### A. Test the MCP Server (4 Sources & Deduplication)
```bash
python3 01_news_mcp_server.py --test
```

### B. Run the Daily 10:45 AM Workflow (Instant Dispatch Test)
```bash
python3 05_daily_scheduler.py --now
```
*(Fetches from all 4 channels, eliminates duplicates, summarizes with LLM, sends to Telegram, and saves to history DB)*.

### C. Run the Daily 10:45 AM Continuous Background Scheduler
```bash
python3 05_daily_scheduler.py --time "10:45"
```

### D. Run the Interactive Follow-Up Chat Web UI (With Memory)
```bash
streamlit run 04_chat_web_ui.py
```
Open **[http://localhost:8501](http://localhost:8501)** to:
- View today's bulletin.
- Chat with the AI about past news stories using SQLite memory!
