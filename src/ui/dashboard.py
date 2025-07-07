"""
Simple Streamlit Dashboard for IT Newsfeed System

This dashboard provides a clean interface to view filtered IT news items
ranked by relevance and recency.
"""

import time
from datetime import datetime
from typing import Any, Dict, List

import requests
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000"
RETRIEVE_ENDPOINT = f"{API_BASE_URL}/api/v1/retrieve"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

def check_api_health() -> bool:
    """Check if the API is running and healthy."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_news_items() -> List[Dict[str, Any]]:
    """Fetch news items from the API."""
    try:
        response = requests.get(RETRIEVE_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API returns {"items": [...]} structure
            return data.get("items", [])
        else:
            st.error(f"API Error: {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return timestamp_str


def display_news_item(item: Dict[str, Any]):
    """Display a single news item in a card format."""
    # Ensure item is a dictionary
    if not isinstance(item, dict):
        st.error(f"Invalid item format: {type(item)}")
        return

    with st.container():
        # Create a card-like container
        st.markdown("---")

        # Header with title and relevance score
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {item.get('title', 'No Title')}")
        with col2:
            if 'relevance_score' in item:
                score = item['relevance_score']
                color = "🔴" if score > 0.7 else "🟡" if score > 0.4 else "🟢"
                st.markdown(f"{color} **{score:.2f}**")

        # Source and timestamp
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**Source:** {item.get('source', 'Unknown')}")
        with col2:
            st.markdown(f"**Published:** {format_timestamp(item.get('published_at', ''))}")

        # Body content
        if item.get('body'):
            st.markdown(f"**Summary:** {item.get('body', '')}")

        # Relevance breakdown (if available)
        if 'relevance_breakdown' in item:
            breakdown = item['relevance_breakdown']
            st.markdown("**Relevance Breakdown:**")
            for factor, score in breakdown.items():
                st.markdown(f"- {factor}: {score:.3f}")

def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="IT Newsfeed Dashboard",
        page_icon="📰",
        layout="wide"
    )

    st.title("📰 IT Newsfeed Dashboard")
    st.markdown("Real-time IT news filtered for relevance to IT managers")

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=True)

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()

        # API status
        st.header("System Status")
        if check_api_health():
            st.success("✅ API Healthy")
        else:
            st.error("❌ API Unavailable")
            st.info("Make sure the API is running on localhost:8000")

        # Instructions
        st.header("Instructions")
        st.markdown("""
        This dashboard shows IT news items filtered for relevance to IT managers.

        **Relevance Score:**
        - 🔴 High (>0.7): Critical IT issues
        - 🟡 Medium (0.4-0.7): Important updates
        - 🟢 Low (<0.4): General tech news

        **Sources:** RSS feeds from Tom's Hardware and Ars Technica
        """)

    # Main content area
    if not check_api_health():
        st.error("⚠️ Cannot connect to the API. Please ensure the newsfeed system is running.")
        st.info("Start the API with: `python -m src.api.main`")
        return

    # Fetch and display news
    with st.spinner("Fetching latest news..."):
        news_items = fetch_news_items()

    if not news_items:
        st.info("📭 No news items available. The system may be filtering out all current items.")
        st.info("Try ingesting some test data via the API to see results.")
        return

    # Display news count
    st.success(f"📊 Found {len(news_items)} relevant news items")

    # Display each news item
    for item in news_items:
        display_news_item(item)

    # Footer
    st.markdown("---")
    st.markdown("*Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*")

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
