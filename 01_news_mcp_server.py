"""01_news_mcp_server.py — Custom MCP Server for Comprehensive Tech Industry News.

Coverage:
1. Big Tech Giants (Nvidia, Microsoft, Google, Apple, Meta, OpenAI)
2. Emerging Startups & Newly Established Companies (YC, a16z, funding rounds)
3. Blockchain & Crypto (CoinTelegraph, Web3, DeFi, Exchanges)
4. Cyber Security (The Hacker News, CISA, Zero-Days, Vulnerabilities)
5. Artificial Intelligence & Automation Intelligence (LLMs, Agentic AI, Autonomous Workflows)
6. Machine Learning & Data Science (ArXiv AI, DeepLearning research)

Tools:
- `fetch_all_daily_news()`: Live aggregation across all industry verticals.
- `fetch_news_by_category(category)`: Filter news by topic (ai, startups, cyber, blockchain, bigtech).
- `check_document_history(title)`: Prevents repeated news using SQLite history.
- `save_news_document(title, summary, source, category, link)`: Saves sent stories.
- `query_news_memory(keyword)`: Lets user query past news in follow-up chat with memory!
"""

import os
import ssl
import json
import sqlite3
import urllib.request
from pathlib import Path
import certifi
import feedparser
from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).parent.resolve()
DB_FILE = HERE / "data" / "news_history.db"

# Initialize SQLite database with category and memory query support
def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            summary TEXT,
            source TEXT,
            category TEXT,
            link TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

mcp = FastMCP("comprehensive-tech-news-server")

NEWS_FEEDS = [
    # 1. Big Tech & General Tech Giants (Nvidia, Microsoft, Google, Meta, Apple)
    {
        "category": "bigtech",
        "name": "The Guardian Tech",
        "url": "https://www.theguardian.com/technology/rss"
    },
    {
        "category": "bigtech",
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/"
    },
    # 2. Startups & Newly Established Companies (Funding, YC, a16z, VC)
    {
        "category": "startups",
        "name": "TechCrunch Startups",
        "url": "https://techcrunch.com/category/startups/feed/"
    },
    # 3. AI, Automation Intelligence & Machine Learning
    {
        "category": "ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/"
    },
    {
        "category": "ai",
        "name": "HackerNews AI",
        "url": "https://hnrss.org/frontpage?q=AI"
    },
    {
        "category": "data_science",
        "name": "ArXiv Computer Science AI",
        "url": "https://rss.arxiv.org/rss/cs.AI"
    },
    # 4. Cyber Security
    {
        "category": "security",
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews"
    },
    # 5. Blockchain & Web3
    {
        "category": "blockchain",
        "name": "CoinTelegraph",
        "url": "https://cointelegraph.com/rss"
    }
]


def _parse_url_articles(url: str, source_label: str, category: str, limit: int = 3):
    articles = []
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            feed = feedparser.parse(resp.read())
            for entry in feed.entries[:limit]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags
                clean_summary = summary.replace("<p>", "").replace("</p>", "").replace("<br>", " ")
                clean_summary = clean_summary.replace("<b>", "").replace("</b>", "")[:280]
                link = entry.get("link", "")
                if title:
                    articles.append({
                        "title": title,
                        "summary": clean_summary,
                        "source": source_label,
                        "category": category,
                        "link": link,
                        "published": entry.get("published", "")
                    })
    except Exception as e:
        print(f"Error reading {source_label}: {e}")
    return articles


@mcp.tool()
def fetch_all_daily_news() -> str:
    """Fetch live news across Big Tech, Startups, AI, Cyber Security, Blockchain, and Data Science."""
    all_articles = []
    for info in NEWS_FEEDS:
        arts = _parse_url_articles(info["url"], info["name"], info["category"], limit=3)
        all_articles.extend(arts)
    return json.dumps(all_articles, indent=2)


@mcp.tool()
def fetch_news_by_category(category: str) -> str:
    """Fetch news for a specific domain: 'bigtech', 'startups', 'ai', 'security', 'blockchain'."""
    filtered_articles = []
    cat_lower = category.lower().strip()
    for info in NEWS_FEEDS:
        if cat_lower in info["category"] or info["category"] in cat_lower:
            arts = _parse_url_articles(info["url"], info["name"], info["category"], limit=4)
            filtered_articles.extend(arts)
    return json.dumps(filtered_articles, indent=2)


@mcp.tool()
def check_document_history(title: str) -> str:
    """Deduplication check: Return DUPLICATE if title exists in SQLite memory, else NEW."""
    conn = sqlite3.connect(str(DB_FILE))
    c = conn.cursor()
    c.execute("SELECT id, title, sent_at FROM news_history WHERE title = ?", (title.strip(),))
    row = c.fetchone()
    conn.close()
    if row:
        return f"DUPLICATE: Sent on {row[2]}"
    return "NEW"


@mcp.tool()
def save_news_document(title: str, summary: str, source: str, category: str = "tech", link: str = "") -> str:
    """Store sent news in SQLite database memory with category."""
    try:
        conn = sqlite3.connect(str(DB_FILE))
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO news_history (title, summary, source, category, link)
            VALUES (?, ?, ?, ?, ?)
        """, (title.strip(), summary.strip(), source.strip(), category.strip(), link.strip()))
        conn.commit()
        conn.close()
        return "SUCCESS"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def query_news_memory(keyword: str) -> str:
    """Query past news memory for user follow-up questions (companies, technologies, attacks)."""
    conn = sqlite3.connect(str(DB_FILE))
    c = conn.cursor()
    search = f"%{keyword.strip()}%"
    c.execute("""
        SELECT title, summary, source, category, link, sent_at
        FROM news_history
        WHERE title LIKE ? OR summary LIKE ? OR category LIKE ?
        ORDER BY id DESC LIMIT 6
    """, (search, search, search))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return f"No stored news found matching '{keyword}'."
        
    res = []
    for r in rows:
        res.append(f"• [{r[3].upper()}] {r[0]}\n  Source: {r[2]} ({r[5]})\n  Summary: {r[1]}\n  Link: {r[4]}")
    return "\n\n".join(res)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Domain Tech News MCP Server")
    parser.add_argument("--test", action="store_true", help="Test fetching across all verticals")
    args = parser.parse_args()

    if args.test:
        print("=== Fetching live multi-domain tech news ===")
        news = json.loads(fetch_all_daily_news())
        print(f"Total articles fetched: {len(news)}")
        for a in news[:6]:
            print(f"- [{a['category'].upper()}] [{a['source']}] {a['title']}")
        print("\n=== Testing Memory Deduplication ===")
        print("Check sample title:", check_document_history("Testing deduplication"))
    else:
        mcp.run()
