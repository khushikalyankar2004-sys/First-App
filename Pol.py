streamlit
feedparser
requests
pandas
plotly
import streamlit as st
import pandas as pd
import plotly.express as px
import feedparser
import requests
from requests.exceptions import RequestException

st.set_page_config(page_title="Bihar Election 2025 — Live News", layout="wide")
st.title("Bihar Legislative Assembly Election 2025 — Live Google News")

st.markdown(
    "This app fetches **live Google News RSS** for `Bihar Election 2025`. "
    "If RSS fetching fails, the app shows diagnostics to help identify the issue."
)

RSS_URL = "https://news.google.com/rss/search?q=Bihar+Election+2025&hl=en-IN&gl=IN&ceid=IN:en"

@st.cache_data(ttl=60)  # cache for 60 seconds
def fetch_rss_with_feedparser(url: str):
    """
    Try to parse RSS directly with feedparser first. If entries are empty,
    return None so caller can try the requests fallback.
    """
    try:
        parsed = feedparser.parse(url)
        # feedparser may return a feed even on an HTTP error; check entries
        if parsed.bozo:
            # bozo indicates a parsing problem; return parsed and let caller inspect
            return parsed
        return parsed
    except Exception as e:
        return e  # return exception to show diagnostics

@st.cache_data(ttl=60)
def fetch_rss_with_requests(url: str):
    """
    Fallback: use requests with a common browser User-Agent and parse the content with feedparser.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        # feedparser can parse raw bytes too
        parsed = feedparser.parse(resp.content)
        return parsed
    except RequestException as e:
        return e

def get_news_dataframe(parsed_feed):
    """
    Convert parsed feed to a pandas DataFrame. If parsed_feed is an exception, raise it.
    """
    if isinstance(parsed_feed, Exception):
        raise parsed_feed

    entries = getattr(parsed_feed, "entries", None)
    if not entries:
        return pd.DataFrame()

    rows = []
    for e in entries:
        title = e.get("title", "")
        link = e.get("link", "")
        published = e.get("published", e.get("updated", ""))
        summary = e.get("summary", "")
        rows.append({"Title": title, "Link": link, "Published": published, "Summary": summary})
    return pd.DataFrame(rows)

col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("**Diagnostics**")
    st.markdown("- Cached for 60s")
    st.markdown("- If it fails, check app logs in Streamlit Cloud (Menu → Logs)")

with col1:
    st.subheader("📰 Live Google News (RSS) — Bihar Election 2025")

# 1) Try feedparser direct
parsed = fetch_rss_with_feedparser(RSS_URL)

# If feedparser returned an exception object, show diagnostics and try fallback
if isinstance(parsed, Exception):
    st.error("Error while parsing RSS with feedparser directly.")
    st.exception(parsed)
    st.info("Trying fallback (requests -> feedparser)...")
    parsed = fetch_rss_with_requests(RSS_URL)

# If parsed has no entries, try requests fallback (in case of redirect or user-agent blocking)
if not getattr(parsed, "entries", None):
    st.warning("No entries found with direct feedparser. Trying fallback (requests) if not already tried.")
    parsed_fallback = fetch_rss_with_requests(RSS_URL)
    # If fallback returns Exception, display error; else use it
    if isinstance(parsed_fallback, Exception):
        st.error("Fallback also failed.")
        st.exception(parsed_fallback)
        parsed = parsed_fallback  # keep for diagnostics below
    else:
        parsed = parsed_fallback

# Build DataFrame (or show friendly error)
news_df = pd.DataFrame()
try:
    news_df = get_news_dataframe(parsed)
except Exception as exc:
    st.error("Unable to build news dataframe from parsed feed.")
    st.exception(exc)

# Display news (if available)
if not news_df.empty:
    for idx, row in news_df.iterrows():
        st.markdown(f"### 🔹 [{row['Title']}]({row['Link']})")
        if row["Published"]:
            st.markdown(f"*Published: {row['Published']}*")
        if row["Summary"]:
            st.write(row["Summary"])
        st.markdown("---")
else:
    st.info("No news items available right now from Google News RSS.")
    st.write("Possible reasons:")
    st.write("- Temporary Google News RSS unavailability")
    st.write("- Network egress blocked from the host (check Streamlit Cloud logs)")
    st.write("- Remote endpoint changed or rate limited")

# -------------------------
# Sample static election data (keeps the app useful even when RSS fails)
# -------------------------
st.subheader("📊 Sample Constituency Data (Demo — editable in code)")

sample_data = {
    "Constituency": ["Patna Sahib", "Raghopur", "Nalanda", "Gaya Town"],
    "Party": ["BJP", "RJD", "JD(U)", "INC"],
    "Votes": [55000, 63000, 58000, 47000]
}
df = pd.DataFrame(sample_data)
st.dataframe(df)

fig = px.bar(df, x="Constituency", y="Votes", color="Party", title="Vote Comparison (Demo)")
st.plotly_chart(fig)

st.markdown("---")
st.markdown("If the live news doesn't load on Streamlit Cloud, open **Logs** from the Streamlit app dashboard — it shows network errors and missing dependency problems.")
