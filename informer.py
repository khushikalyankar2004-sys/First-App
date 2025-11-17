# pod_informer_app.py
import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import requests
from PIL import Image
import io
import os
import time

st.set_page_config(page_title="POD Informer — Trademark / Keyword / Niche Checker", layout="wide")

# ---------------- Helper / Config ----------------
st.title("POD Informer — Trademark, Copyright & Niche Checker")
st.markdown(
    """
    Use this tool for **initial research** on keywords, trademarks, and image copyright signals.
    **Important:** For definitive trademark/copyright status always check official registries (USPTO, EUIPO, WIPO) or consult a lawyer.
    """
)

with st.expander("🔧 API Keys (optional — improves accuracy)"):
    serpapi_key = st.text_input("SerpAPI key (for Google search counts / results)", value="", type="password",
                               help="Optional but highly recommended. Get from https://serpapi.com/")
    tineye_api_username = st.text_input("TinEye API username (optional)", value="", type="password")
    tineye_api_key = st.text_input("TinEye API key (optional)", value="", type="password")
    use_google_vision = st.checkbox("Use Google Vision webDetection for image (requires GOOGLE_APPLICATION_CREDENTIALS env var)", value=False)
    st.write("If you don't have keys, the app will still run with limited functionality (pytrends-based suggestions).")

# ---------------- Layout: Left column inputs, right column results ----------------
left, right = st.columns([1, 1.4])

# --------- Left: Input Controls ---------
with left:
    st.subheader("1) Check type")
    check_type = st.selectbox("Select type to check", ["Text (title/keyword)", "Image (upload)"])

    st.markdown("### 2) Keyword / Title search")
    title_input = st.text_input("Enter text to check (e.g., 'Hey Cutie')", value="Hey Cutie")

    st.markdown("### 3) Title search style")
    search_style = st.selectbox("Search style", ["Evergreen", "Trending"], index=0,
                                help="Evergreen = long-term keywords; Trending = currently rising topics")

    st.markdown("### 4) Niche & Sub-niche helper")
    niche_input = st.text_input("Enter your niche (e.g., 'hiking', 'pet lovers')", value="hiking")
    subn_count = st.slider("How many sub-niche suggestions?", min_value=5, max_value=30, value=10)

    st.markdown("### 5) Image upload (if Image selected)")
    uploaded_image = st.file_uploader("Upload image (PNG/JPG) — used only if 'Image' selected", type=["png", "jpg", "jpeg"])

    st.markdown("### 6) Run checks")
    run_btn = st.button("Run Research")

# --------- Utilities ---------
def serpapi_search_count(query, serpapi_key):
    """
    Use SerpAPI to get the approximate number of results for a query (Google).
    Returns integer count or None.
    """
    if not serpapi_key:
        return None
    try:
        params = {"engine": "google", "q": query, "api_key": serpapi_key}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        data = resp.json()
        if "search_information" in data and "total_results" in data["search_information"]:
            return int(data["search_information"]["total_results"])
        # fallback: try organic_results length
        if "organic_results" in data:
            return len(data["organic_results"])
    except Exception as e:
        st.warning(f"SerpAPI error: {e}")
    return None

def tineye_reverse_search(image_bytes, username, api_key):
    """
    Call TinEye API: https://services.tineye.com/ (requires account)
    Returns match_count or None
    """
    if not (username and api_key):
        return None
    try:
        files = {"image_upload": ("upload.jpg", image_bytes)}
        auth = (username, api_key)
        resp = requests.post("https://api.tineye.com/rest/search/", files=files, auth=auth, timeout=20)
        data = resp.json()
        # the exact JSON structure depends on account; try to fetch results
        if "results" in data:
            return len(data["results"])
    except Exception as e:
        st.warning(f"Tineye error: {e}")
    return None

def google_vision_web_detection(image_bytes):
    """
    Uses google-cloud-vision library if env put and selected.
    Returns dict with 'best_guess_labels' and 'web_entities' etc.
    """
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.web_detection(image=image, timeout=20)
        web = response.web_detection
        result = {"best_guess_labels": [], "web_entities": [], "full_matching_images": []}
        if web.best_guess_labels:
            result["best_guess_labels"] = [bg.label for bg in web.best_guess_labels]
        if web.web_entities:
            result["web_entities"] = [{"description": e.description, "score": e.score} for e in web.web_entities if e.description]
        if web.full_matching_images:
            result["full_matching_images"] = [f.url for f in web.full_matching_images]
        return result
    except Exception as e:
        st.warning(f"Google Vision error: {e}")
        return None

def pytrends_related_keywords(keyword, timeframe="today 12-m", top_n=10):
    """
    Use pytrends to get related queries. Returns list of related query strings.
    timeframe examples: 'today 12-m', 'now 7-d'
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        kw_list = [keyword]
        pytrends.build_payload(kw_list, timeframe=timeframe)
        related = pytrends.related_queries()
        if keyword in related and related[keyword]['top'] is not None:
            top = related[keyword]['top']['query'].tolist()[:top_n]
            return top
        # fallback: related_topics
        related_topics = pytrends.related_topics()
        if keyword in related_topics and related_topics[keyword]['rising'] is not None:
            top = related_topics[keyword]['rising']['topic_title'].tolist()[:top_n]
            return top
    except Exception as e:
        st.info("pytrends could not fetch related queries (network or rate limit).")
    return []

def pytrends_interest_score(keyword, timeframe="today 12-m"):
    """
    Returns an interest score (0-100) average for the keyword over timeframe.
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.get_interest_over_time(keyword, timeframe=timeframe)
        if df.empty:
            return None
        # average interest
        avg = int(df[keyword].mean())
        return avg
    except Exception as e:
        return None

# ---------- Main Execution ----------
if run_btn:
    with st.spinner("Running research... this may take 10–30 seconds depending on APIs..."):
        # 1) Trademark/Text check
        st.header("A) Trademark / Copyright Quick Check")
        if check_type.startswith("Text"):
            st.subheader("Text analysis")
            st.write(f"**Query:** `{title_input}`")
            # 1a: do pytrends interest to sense if phrase is trending
            trend_timeframe = "now 7-d" if search_style == "Trending" else "today 12-m"
            interest = pytrends_interest_score(title_input, timeframe=trend_timeframe)
            if interest is not None:
                st.write(f"Google Trends interest (avg, timeframe={trend_timeframe}): **{interest}/100**")
            else:
                st.write("Google Trends: no data (phrase may be too short or low volume).")

            # 1b: SerpAPI quick trademark hint
            serp_count = serpapi_search_count(f"{title_input} trademark", serpapi_key) if serpapi_key else None
            if serp_count is not None:
                st.write(f"Google search hits for '{title_input} trademark': **{serp_count:,}** results")
                if serp_count > 2000:
                    st.info("Many results. Likely used / discussed widely — manual search on official registries recommended.")
            else:
                st.write("Google search counts not available (SerpAPI key not provided).")

            # 1c: quick heuristic: look for exact-match registered trademark pages (if SerpAPI)
            trademark_hits = []
            if serpapi_key:
                try:
                    # search for official trademark registries mentions
                    q = f"{title_input} trademark registered OR registration OR 'registered trademark' site:gov OR site:trademarks.justia.com OR site:tmsearch.uspto.gov"
                    params = {"engine": "google", "q": q, "api_key": serpapi_key, "num": 10}
                    r = requests.get("https://serpapi.com/search.json", params=params, timeout=15).json()
                    for orr in r.get("organic_results", []):
                        title = orr.get("title", "")
                        snippet = orr.get("snippet", "")
                        link = orr.get("link", "")
                        trademark_hits.append({"title": title, "snippet": snippet, "link": link})
                except Exception as e:
                    st.warning("SerpAPI trademark search failed.")
            if trademark_hits:
                st.write("Potential trademark/registration pages found (manual review required):")
                for h in trademark_hits:
                    st.write(f"- [{h['title']}]({h['link']}) — {h['snippet']}")
                st.warning("These are search hits — open the links and check official registries for real status.")
            else:
                st.success("No obvious registered-trademark pages found via quick search (not definitive).")
                st.caption("Manual check on USPTO / EUIPO / WIPO recommended for final confirmation.")

        # 2) Image check
        if check_type.startswith("Image"):
            st.subheader("Image analysis")
            if not uploaded_image:
                st.error("Please upload an image to analyze.")
            else:
                img_bytes = uploaded_image.read()
                img_preview = Image.open(io.BytesIO(img_bytes))
                st.image(img_preview, caption="Uploaded image", use_column_width=True)

                # TinEye reverse image
                tineye_matches = None
                if tineye_api_username and tineye_api_key:
                    tineye_matches = tineye_reverse_search(img_bytes, tineye_api_username, tineye_api_key)
                    if tineye_matches is not None:
                        st.write(f"TinEye reported **{tineye_matches}** matching image(s) (open TinEye dashboard for details).")
                # Google Vision web detection
                gv = None
                if use_google_vision:
                    gv = google_vision_web_detection(img_bytes)
                    if gv:
                        st.write("Google Vision web detection results (best guess labels):")
                        st.write(gv.get("best_guess_labels", []))
                        if gv.get("web_entities"):
                            st.write("Top web entities detected (may indicate the image exists elsewhere):")
                            st.write(pd.DataFrame(gv["web_entities"])[:10])
                        if gv.get("full_matching_images"):
                            st.write("Full matching image URLs (open links to verify):")
                            for u in gv["full_matching_images"][:10]:
                                st.write(u)
                if not (tineye_matches or gv):
                    st.info("No reverse-image API used / keys not provided. You should manually run a reverse-image search (TinEye or Google Images) to verify copyright ownership.")

        # -------- B) Keyword / Niche Analysis ----------
        st.header("B) Keyword / Niche Insights (for POD sellers)")
        st.write("Using Google Trends (pytrends) + web search counts (SerpAPI if provided) to generate sub-niche suggestions and a safety score.")

        # 1) Label evergreen vs trending
        timeframe = "today 12-m" if search_style == "Evergreen" else "now 7-d"
        st.write(f"Labeling using timeframe: **{timeframe}**")
        main_interest = pytrends_interest_score(niche_input, timeframe=timeframe)
        st.write(f"Main niche average interest: **{main_interest if main_interest is not None else 'N/A'}/100**")

        # 2) Get related keywords / sub-niches
        related = pytrends_related_keywords(niche_input, timeframe=timeframe, top_n=subn_count)
        if not related:
            st.info("pytrends could not return related queries; showing simple heuristics.")
            # basic fallback: split niche into words + small variations
            related = [f"{niche_input} {w}" for w in ["design", "shirt", "gift", "lover", "illustration"]][:subn_count]
        st.write(f"Found {len(related)} related sub-niche keywords.")

        # 3) For each related sub-niche compute heuristic 'safety' score:
        rows = []
        for kw in related:
            # interest score (0-100)
            interest_score = pytrends_interest_score(kw, timeframe=timeframe)
            # web competition estimate via SerpAPI (total_results)
            results_count = serpapi_search_count(kw, serpapi_key) if serpapi_key else None
            # Heuristic: safe if interest moderate-high and low result_count
            safe = None
            if interest_score is None:
                # fallback: if results_count small => safe
                if results_count is None:
                    safe = "Unknown"
                else:
                    safe = "✅" if results_count < 200000 else "❌"
            else:
                # high interest and low competition -> safe
                if interest_score >= 40 and (results_count is None or results_count < 200000):
                    safe = "✅"
                elif interest_score >= 20 and (results_count is not None and results_count < 100000):
                    safe = "✅"
                else:
                    safe = "❌"
            rows.append({"sub_niche": kw, "interest": interest_score if interest_score is not None else "N/A",
                         "search_results": f"{results_count:,}" if results_count is not None else "N/A",
                         "safe": safe})
            time.sleep(0.2)  # polite pacing

        df = pd.DataFrame(rows)
        # show as table with emoji / ticks
        def icon(s):
            if s == "✅": return "✅ Less competition / Good demand"
            if s == "❌": return "❌ High competition / Risky"
            return "❓ Unknown"
        df_display = df.rename(columns={"sub_niche": "Sub-niche", "interest": "Interest (0-100)", "search_results": "Google hits", "safe": "Status"})
        st.dataframe(df_display, height=300)
        st.markdown("**Legend:** ✅ = suggested (lower competition with decent demand). ❌ = crowded/high competition. ❓ = insufficient data.")

        # Quick CSV export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download sub-niche table (CSV)", data=csv, file_name="subniche_table.csv", mime="text/csv")

        # Final recommendation block
        st.header("C) Quick Recommendations for New POD Sellers")
        st.write("""
        - Use this tool for **initial filtering** — always manually check trademark registries for any phrase you plan to print.
        - For **images**, always use original/licensed art or create your own. Reverse-image checks (TinEye / Google) help find identical images already used.
        - Target **sub-niches** marked ✅: lower competition but decent demand — good for new sellers.
        - Avoid ❌ niches unless you have a unique angle or superior marketing.
        - If you plan to sell globally, check **multiple** trademark registries (USPTO, EUIPO, WIPO).
        """)
        st.success("Research run complete. Use the CSV export to keep a record.")

# ---------------- Footer / Notes ----------------
st.markdown("---")
st.caption(
    "This app provides research signals — NOT legal clearance. For trademark clearance or copyright disputes consult a qualified attorney or official national registry."
)
