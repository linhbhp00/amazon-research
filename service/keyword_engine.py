import streamlit as st
import pandas as pd
import numpy as np
import re

from urllib.parse import quote_plus
from sklearn.feature_extraction.text import CountVectorizer

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# HEADER VALIDATION
# =========================================================

EXPECTED_KEYWORD_COLUMNS = [
    "Search Term",
    "Search Frequency Rank",
    "Reporting Date",
]


def is_valid_keyword_header(columns):
    cols = [str(c).strip() for c in columns]
    score = 0

    for expected in EXPECTED_KEYWORD_COLUMNS:
        if expected in cols:
            score += 1

    return score >= 2


def auto_fix_keyword_headers(df):
    if df is None or df.empty:
        return df

    if is_valid_keyword_header(df.columns):
        return df

    first_row = df.iloc[0].fillna("").astype(str).tolist()

    if is_valid_keyword_header(first_row):
        df = df.copy()
        df.columns = first_row
        return df.iloc[1:].reset_index(drop=True)

    if len(df) > 1:
        second_row = df.iloc[1].fillna("").astype(str).tolist()

        if is_valid_keyword_header(second_row):
            df = df.copy()
            df.columns = second_row
            return df.iloc[2:].reset_index(drop=True)

    return df


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# LINKS
# =========================================================

def make_search_link(text):
    if pd.isna(text):
        return text

    return f"""
    <a href="https://www.amazon.com/s?k={quote_plus(str(text))}" target="_blank">
        {text}
    </a>
    """


def make_asin_link(asin):
    if pd.isna(asin):
        return asin

    return f"""
    <a href="https://www.amazon.com/dp/{asin}" target="_blank">
        {asin}
    </a>
    """


# =========================================================
# NGRAM ENGINE
# =========================================================

@st.cache_data
def extract_ngrams(corpus, ngram_range=(1, 1), min_freq=2, top_n=30):

    try:
        vectorizer = CountVectorizer(
            ngram_range=ngram_range,
            stop_words="english",
            min_df=min_freq
        )

        X = vectorizer.fit_transform(corpus)

        sums = np.array(X.sum(axis=0)).flatten()

        words_freq = [
            (word, sums[idx])
            for word, idx in vectorizer.vocabulary_.items()
        ]

        words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)

        return pd.DataFrame(words_freq[:top_n], columns=["Phrase", "Frequency"])

    except:
        return pd.DataFrame(columns=["Phrase", "Frequency"])


# =========================================================
# NICHES (MULTI FILE SAFE)
# =========================================================

def assign_niche(df):
    df = df.copy()

    if "Search Term" not in df.columns:
        return df

    def infer(text):
        text = str(text).lower()

        if "dog" in text or "cat" in text or "pet" in text:
            return "pet memorial"

        if "dad" in text or "mom" in text or "father" in text:
            return "family loss"

        if "funeral" in text:
            return "funeral service"

        if "garden" in text or "stone" in text:
            return "outdoor memorial"

        return "general"

    df["Niche"] = df["Search Term"].apply(infer)
    return df


# =========================================================
# QUARTER FIX
# =========================================================

def convert_quarter(month):
    if pd.isna(month):
        return None
    return f"Q{((int(month) - 1) // 3) + 1}"


# =========================================================
# INSIGHT ENGINE (REPLACES CLUSTER)
# =========================================================

def build_insight_cards(df):

    insights = []

    if "Niche" not in df.columns:
        return insights

    for niche in df["Niche"].dropna().unique():

        niche_df = df[df["Niche"] == niche]
        volume = len(niche_df)

        if volume > 200:
            opportunity = "High Market Opportunity"
        elif volume > 80:
            opportunity = "Medium Market Opportunity"
        else:
            opportunity = "Emerging Opportunity"

        if volume > 150:
            competition = "High Competition"
        elif volume > 60:
            competition = "Medium Competition"
        else:
            competition = "Low Competition"

        insights.append({
            "niche": niche,
            "opportunity": opportunity,
            "competition": competition,
            "recommended_products": "Memorial plaques | Custom frames | Garden stones | Wind chimes",
            "next_actions": [
                "Validate demand signals",
                "Expand keyword set",
                "Test product listings",
                "Scale top ASIN ads"
            ]
        })

    return insights


def render_cards(insights):

    for i in insights:

        st.markdown(
            f"""
            <div style="
                padding:16px;
                border-radius:12px;
                background:#111827;
                margin-bottom:12px;
            ">
                <h3>{i['niche']}</h3>

                <p><b>Market Opportunity:</b> {i['opportunity']}</p>

                <p><b>Competition:</b> {i['competition']}</p>

                <p><b>Recommended Products:</b><br>{i['recommended_products']}</p>

                <p><b>Next Actions:</b><br>{" | ".join(i['next_actions'])}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# MAIN ENGINE
# =========================================================

def render_keyword_engine(final_df):

    st.markdown("# Keyword Intelligence")

    if final_df is None or final_df.empty:
        st.info("Upload keyword CSV files to begin.")
        return

    # =====================================================
    # FIX HEADER + CLEAN
    # =====================================================

    final_df = auto_fix_keyword_headers(final_df)
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]

    # =====================================================
    # MULTI FILE NICHES
    # =====================================================

    final_df = assign_niche(final_df)

    # =====================================================
    # QUARTER ENGINE
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = pd.to_datetime(
            final_df["Reporting Date"],
            errors="coerce"
        )

        final_df["Month"] = final_df["Reporting Date"].dt.month
        final_df["Quarter"] = final_df["Month"].apply(convert_quarter)

    # =====================================================
    # FILTER UI
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:
        niche_filter = st.multiselect(
            "Niche",
            final_df["Niche"].dropna().unique()
            if "Niche" in final_df.columns else []
        )

    with c2:
        quarter_filter = st.multiselect(
            "Quarter",
            final_df["Quarter"].dropna().unique()
            if "Quarter" in final_df.columns else []
        )

    with c3:
        year_filter = st.multiselect(
            "Year",
            final_df["Year"].dropna().unique()
            if "Year" in final_df.columns else []
        )

    filtered_df = final_df.copy()

    if niche_filter:
        filtered_df = filtered_df[filtered_df["Niche"].isin(niche_filter)]

    if quarter_filter:
        filtered_df = filtered_df[filtered_df["Quarter"].isin(quarter_filter)]

    if year_filter and "Year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Year"].isin(year_filter)]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input("Quick Search")

    if search_value:
        filtered_df = filtered_df[
            filtered_df.astype(str).apply(
                lambda row: row.str.contains(search_value, case=False, na=False).any(),
                axis=1
            )
        ]

    # =====================================================
    # LINKS
    # =====================================================

    display_df = filtered_df.copy()

    if "Search Term" in display_df.columns:
        display_df["Search Term"] = display_df["Search Term"].apply(make_search_link)

    for col in display_df.columns:
        if "asin" in col.lower():
            display_df[col] = display_df[col].apply(make_asin_link)

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3 = st.columns(3)

    m1.metric("Rows", len(filtered_df))
    m2.metric("Columns", len(filtered_df.columns))
    m3.metric("Niches", filtered_df["Niche"].nunique())

    # =====================================================
    # AGGRID (AUTO FIT FIX)
    # =====================================================

    st.markdown("## Keyword Dataset")

    gb = GridOptionsBuilder.from_dataframe(display_df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True
    )

    gridOptions = gb.build()

    gridOptions["onGridReady"] = JsCode("""
    function(params) {
        params.api.sizeColumnsToFit();
    }
    """)

    AgGrid(
        display_df,
        gridOptions=gridOptions,
        theme="alpine-dark",
        height=720,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
    )

    # =====================================================
    # NLP ENGINE
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence")

    candidate_columns = [
        "Search Term",
        "Keyword",
        "Product Title",
        "Title",
        "Query",
    ]

    source_col = next(
        (c for c in candidate_columns if c in filtered_df.columns),
        None
    )

    if source_col is None:
        st.warning("No NLP-compatible column found.")
        return

    series = filtered_df[source_col].astype(str).apply(clean_text)
    corpus = series.tolist()

    single = extract_ngrams(corpus, (1, 1))
    bigram = extract_ngrams(corpus, (2, 2))
    trigram = extract_ngrams(corpus, (3, 3))

    # =====================================================
    # METRICS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    c1.metric("Single Words", len(single))
    c2.metric("Bigram", len(bigram))
    c3.metric("Trigram", len(trigram))

    # =====================================================
    # TABS
    # =====================================================

    t1, t2, t3, t4 = st.tabs([
        "Single Word",
        "Bigram",
        "Trigram",
        "Market Intelligence"
    ])

    with t1:
        st.dataframe(single, use_container_width=True)

    with t2:
        st.dataframe(bigram, use_container_width=True)

    with t3:
        st.dataframe(trigram, use_container_width=True)

    with t4:

        st.markdown("## Market Intelligence Cards")

        insights = build_insight_cards(filtered_df)
        render_cards(insights)
