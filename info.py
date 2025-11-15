import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px

st.title("Bihar Legislative Assembly Election 2025 – Live Google News Dashboard")

st.write("This dashboard fetches LIVE Bihar election 2025 updates directly from Google News RSS.")

# -----------------------------------------------------------------------
# 1. FETCH NEWS FROM GOOGLE NEWS RSS (LIVE DATA)
# -----------------------------------------------------------------------

RSS_URL = "https://news.google.com/rss/search?q=Bihar+Election+2025&hl=en-IN&gl=IN&ceid=IN:en"

feed = feedparser.parse(RSS_URL)

news_list = []
for entry in feed.entries:
    news_list.append({
        "Title": entry.title,
        "Link": entry.link,
        "Published": entry.published
    })

news_df = pd.DataFrame(news_list)

# -----------------------------------------------------------------------
# 2. SHOW LIVE NEWS
# -----------------------------------------------------------------------

st.subheader("📰 Latest Bihar Election 2025 News (Live from Google News)")

if not news_df.empty:
    for i, row in news_df.iterrows():
        st.markdown(f"### 🔹 [{row['Title']}]({row['Link']})")
        st.markdown(f"*Published: {row['Published']}*")
        st.markdown("---")
else:
    st.warning("No live news available right now.")

# -----------------------------------------------------------------------
# 3. SAMPLE ELECTION DATA (STATIC DEMO — EDITABLE)
# -----------------------------------------------------------------------

st.subheader("📊 Sample Constituency Data (Demo)")

data = {
    "Constituency": ["Patna Sahib", "Raghopur", "Nalanda", "Gaya Town"],
    "Party": ["BJP", "RJD", "JD(U)", "INC"],
    "Votes": [55000, 63000, 58000, 47000]
}

df = pd.DataFrame(data)

st.dataframe(df)

# Plot chart
fig = px.bar(df, x="Constituency", y="Votes", color="Party",
             title="Vote Comparison (Demo)")
st.plotly_chart(fig)

st.markdown("---")
st.markdown("⚡ App auto-fetches real-time Google News updates every time you refresh the page.")
