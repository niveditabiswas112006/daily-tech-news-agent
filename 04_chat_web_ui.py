"""04_chat_web_ui.py — Interactive Multi-Domain Tech News Chat & Memory UI.

Features:
- Live multi-category news feed (Big Tech, Startups, AI, Cybersecurity, Blockchain).
- Follow-up query chat with memory to inquire about:
  * Company acquisitions & funding rounds
  * Cyber attacks & zero-day vulnerabilities
  * AI models, autonomous agents, and benchmarks
  * Blockchain hacks, regulatory moves, and updates
"""

import sys
import sqlite3
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

HERE = Path(__file__).parent.resolve()
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

sys.path.insert(0, str(HERE))
import importlib
mcp_server = importlib.import_module("01_news_mcp_server")
daily_agent = importlib.import_module("03_langgraph_daily_agent")

st.set_page_config(page_title="TechPulse — AI Industry News & Memory Chat", page_icon="🌐", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0D47A1; margin-bottom: 0.2rem; }
    .sub-header { color: #555; margin-bottom: 1.5rem; font-size: 1.05rem; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-right: 6px; }
    .badge-bigtech { background: #E3F2FD; color: #1565C0; }
    .badge-startups { background: #E8F5E9; color: #2E7D32; }
    .badge-ai { background: #F3E5F5; color: #6A1B9A; }
    .badge-security { background: #FFEBEE; color: #C62828; }
    .badge-blockchain { background: #FFF8E1; color: #F57F17; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌐 TechPulse: Industry-Wide News & Memory Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Tracking: <b>Big Tech</b> (Nvidia, Microsoft, Google), <b>Startups</b>, <b>AI & Automation</b>, <b>Cyber Security</b>, <b>Blockchain</b></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ News Orchestrator")
    cat_choice = st.selectbox(
        "Select Domain to Dispatch:",
        ["All Industry Domains (Complete Digest)", "bigtech", "startups", "ai", "security", "blockchain"]
    )
    domain_arg = "all" if "All" in cat_choice else cat_choice

    if st.button("🚀 Fetch & Deliver to Telegram", type="primary"):
        with st.spinner("LangGraph agent running across all live feeds..."):
            app = daily_agent.build_daily_news_graph()
            res = app.invoke({"category_filter": domain_arg})
            st.success("Delivered to Telegram!")
            st.info(f"Delivery: {res.get('delivery_status')}")
            st.session_state["latest_digest"] = res.get("digest_summary")

    st.markdown("---")
    st.subheader("📡 Live Feed Sources")
    st.markdown("- 🏢 **Big Tech**: The Guardian, MIT Tech Review\n- 🚀 **Startups**: TechCrunch Startups, YC & a16z\n- 🧠 **AI**: TechCrunch AI, HackerNews AI, ArXiv\n- 🛡️ **Cyber Security**: The Hacker News\n- ⛓️ **Blockchain**: CoinTelegraph")

    st.markdown("---")
    conn = sqlite3.connect(str(mcp_server.DB_FILE))
    count = conn.execute("SELECT count(*) FROM news_history").fetchone()[0]
    conn.close()
    st.metric("Total Stories In Memory DB", count)

tab1, tab2, tab3 = st.tabs(["📋 Latest News Bulletin", "💬 Follow-Up Chat (With Memory)", "🗄️ Memory Database Explorer"])

with tab1:
    st.subheader("Curated Industry Bulletin")
    if "latest_digest" in st.session_state and st.session_state["latest_digest"]:
        st.markdown(st.session_state["latest_digest"])
    else:
        st.info("Click '**Fetch & Deliver to Telegram**' in the sidebar to generate today's comprehensive digest!")

with tab2:
    st.subheader("Ask Follow-Up Questions on Any Company or Tech News")
    st.caption("Ask about Nvidia chip updates, Microsoft-OpenAI revenues, Binance hack, CISA vulnerabilities, new startup investments, etc.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your Tech Industry Intelligence Assistant. Ask me anything about current Big Tech news, AI models, cyber attacks, startups, or blockchain developments."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_query := st.chat_input("e.g., Tell me details about the Binance hack, or which new startups got funded?"):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Querying MCP Memory Database & synthesizing answer..."):
                memory_context = mcp_server.query_news_memory(user_query)
                llm = daily_agent.get_llm_model()
                prompt = f"""You are an elite Tech Industry Analyst.
The user is asking a follow-up question. Use the stored historical news memory to answer in detail.

Memory Records from Database:
{memory_context}

User Question: {user_query}

Provide a comprehensive, factual, and well-structured answer citing companies, sources, and specifics."""
                try:
                    response = llm.invoke(prompt)
                    ans = response.content
                except Exception as e:
                    ans = f"Memory search results:\n\n{memory_context}"
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab3:
    st.subheader("Past Delivered Articles (SQLite Memory)")
    conn = sqlite3.connect(str(mcp_server.DB_FILE))
    c = conn.cursor()
    c.execute("SELECT id, sent_at, category, source, title, link FROM news_history ORDER BY id DESC LIMIT 25")
    rows = c.fetchall()
    conn.close()

    if rows:
        for r in rows:
            cat = r[2] or "tech"
            st.markdown(f"**[{cat.upper()}]** [{r[4]}]({r[5]}) — *{r[3]} ({r[1]})*")
    else:
        st.write("No stored articles yet.")
