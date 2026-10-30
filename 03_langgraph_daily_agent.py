"""03_langgraph_daily_agent.py — LangGraph Workflow for Multi-Domain Tech News.

Covers:
- Big Tech (Nvidia, Microsoft, Google, Meta, Apple)
- Startups & Newly Established Companies
- Artificial Intelligence & Machine Learning
- Cyber Security & Vulnerabilities
- Blockchain & Web3
- Data Science & Automation
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import TypedDict, List, Dict, Optional
from dotenv import load_dotenv

HERE = Path(__file__).parent.resolve()
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

sys.path.insert(0, str(HERE))
import importlib
mcp_server = importlib.import_module("01_news_mcp_server")
telegram_tool = importlib.import_module("02_telegram_tool")

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage


# =============================================================
# 1. DEFINE LANGGRAPH STATE
# =============================================================

class DailyNewsState(TypedDict):
    category_filter: Optional[str]    # None for all, or 'ai', 'security', 'blockchain', 'startups', 'bigtech'
    raw_articles: List[Dict]          # Articles fetched from MCP server across all sources
    fresh_articles: List[Dict]        # Non-duplicate articles
    digest_summary: Optional[str]     # LLM generated bulletin
    delivery_status: Optional[str]    # Telegram delivery result


# =============================================================
# 2. DEFINE GRAPH NODES
# =============================================================

def fetch_node(state: DailyNewsState) -> dict:
    """Node 1: Fetch fresh news from MCP Server across BigTech, Startups, AI, Security, Crypto."""
    cat = state.get("category_filter")
    if cat and cat != "all":
        print(f"\n📡 [Node: fetch_node] Fetching category '{cat}' news from MCP Server...")
        news_json = mcp_server.fetch_news_by_category(cat)
    else:
        print("\n📡 [Node: fetch_node] Fetching comprehensive multi-domain tech news from MCP Server...")
        news_json = mcp_server.fetch_all_daily_news()

    try:
        articles = json.loads(news_json)
    except Exception:
        articles = []
        
    print(f"   ✅ Retrieved {len(articles)} total articles across all channels.")
    return {"raw_articles": articles}


def deduplicate_node(state: DailyNewsState) -> dict:
    """Node 2: Document history check (Prevents duplicate news)."""
    print("\n🔍 [Node: deduplicate_node] Checking Document History database to prevent duplication...")
    raw = state.get("raw_articles", [])
    fresh = []
    
    for item in raw:
        title = item.get("title", "")
        if not title:
            continue
        status = mcp_server.check_document_history(title)
        if "DUPLICATE" in status:
            print(f"   ⏭️ Skipping duplicate: {title[:40]}...")
        else:
            fresh.append(item)
            
    print(f"   🎯 Unique fresh articles found: {len(fresh)} (Filtered: {len(raw) - len(fresh)} duplicates).")
    return {"fresh_articles": fresh}


def summarize_node(state: DailyNewsState) -> dict:
    """Node 3: Group by industry domains and craft a categorized Telegram bulletin."""
    print("\n🤖 [Node: summarize_node] Categorizing and summarizing top stories...")
    fresh = state.get("fresh_articles", [])
    
    if not fresh:
        return {"digest_summary": "📰 *Daily Tech & Industry Digest*\n\nNo brand-new updates detected since last run. All current headlines are already delivered."}

    # Group fresh articles by category
    categories = {}
    for art in fresh:
        c = art.get("category", "tech")
        categories.setdefault(c, []).append(art)

    # Build prompt representation
    articles_context = ""
    for cat_name, arts in categories.items():
        articles_context += f"\n### CATEGORY: {cat_name.upper()}\n"
        for a in arts[:2]:
            articles_context += f"- Title: {a.get('title')}\n  Source: {a.get('source')}\n  Summary: {a.get('summary')}\n  Link: {a.get('link')}\n"

    llm = get_llm_model()
    prompt = f"""You are an elite Tech Journalist covering all industry domains:
Big Tech (Nvidia, Microsoft, Google, Meta, Apple), Startups & Newly Established Companies, AI & Machine Learning, Cyber Security, and Blockchain.

Create an engaging 'Daily Tech & Industry Digest' formatted in clean Telegram Markdown.
Group the top headlines into clear sections:
- 🏢 *Big Tech & Giants* (Microsoft, Nvidia, Google, Apple)
- 🚀 *Startups & Emerging Ventures* (New companies, VC funding)
- 🧠 *AI & Machine Learning*
- 🛡️ *Cyber Security & Vulnerabilities*
- ⛓️ *Blockchain & Web3*

For each headline include:
• *[Company/Topic] Headline*: 1-sentence insight. [Read More](link)

Conclude with:
💡 *Key Market Trend*: 1 sentence summarizing the biggest industry move today.

Articles to summarize:
{articles_context}
"""
    try:
        response = llm.invoke([
            SystemMessage(content="You are a professional tech news editor delivering structured Telegram updates."),
            HumanMessage(content=prompt)
        ])
        digest = response.content
    except Exception as e:
        print(f"LLM synthesis fallback: {e}")
        digest = "📰 *Daily Tech & Industry Digest*\n\n"
        for cat_name, arts in categories.items():
            digest += f"\n*{cat_name.upper()}*\n"
            for a in arts[:2]:
                digest += f"• *{a.get('title')}* ({a.get('source')})\n  {a.get('summary')}\n  [Link]({a.get('link')})\n"
        
    return {"digest_summary": digest}


def deliver_and_save_node(state: DailyNewsState) -> dict:
    """Node 4: Send via Telegram tool and record to SQLite database memory."""
    print("\n🚀 [Node: deliver_and_save_node] Delivering to Telegram & updating memory...")
    digest = state.get("digest_summary", "")
    
    # 1. Send via Telegram Bot
    status = asyncio.run(telegram_tool.send_telegram_message(digest))
    
    # 2. Save fresh articles to history database so they don't repeat tomorrow
    fresh = state.get("fresh_articles", [])
    for art in fresh[:8]:
        mcp_server.save_news_document(
            title=art.get("title", ""),
            summary=art.get("summary", ""),
            source=art.get("source", "RSS"),
            category=art.get("category", "tech"),
            link=art.get("link", "")
        )
    print("   💾 Successfully recorded fresh articles into SQLite history database.")
    
    return {"delivery_status": status}


# =============================================================
# Helper: LLM Provider
# =============================================================

def get_llm_model():
    groq_key = os.getenv("GROQ_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, temperature=0)

    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=google_key, temperature=0)

    from langchain_openai import ChatOpenAI
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    return ChatOpenAI(base_url=base_url, api_key="ollama", model=model_name, temperature=0)


# =============================================================
# 3. ASSEMBLE GRAPH
# =============================================================

def build_daily_news_graph():
    workflow = StateGraph(DailyNewsState)
    
    workflow.add_node("fetch", fetch_node)
    workflow.add_node("deduplicate", deduplicate_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("deliver_and_save", deliver_and_save_node)
    
    workflow.add_edge(START, "fetch")
    workflow.add_edge("fetch", "deduplicate")
    workflow.add_edge("deduplicate", "summarize")
    workflow.add_edge("summarize", "deliver_and_save")
    workflow.add_edge("deliver_and_save", END)
    
    return workflow.compile()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Domain Tech News Agent")
    parser.add_argument("--category", type=str, default="all", help="Category: all, ai, security, blockchain, startups, bigtech")
    args = parser.parse_args()

    print("🌟 Starting Comprehensive Tech Industry News Workflow...")
    app = build_daily_news_graph()
    result = app.invoke({"category_filter": args.category})
    
    print("\n" + "=" * 60)
    print("✨ Workflow Completed Successfully!")
    print(f"Status: {result.get('delivery_status')}")
    print("=" * 60)
