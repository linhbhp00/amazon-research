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
# HEADER FIX
# =========================================================

EXPECTED_KEYWORD_COLUMNS = [
    "Search Term",
    "Search Frequency Rank",
    "Reporting Date",
]


def is_valid_keyword_header(columns):
    cols = [str(c).strip() for c in columns]
    return sum(c in cols for c in EXPECTED_KEYWORD_COLUMNS) >= 2


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
# MULTI-FILE NORMALIZER (CRITICAL FIX)
# =========================================================

def normalize_multi_file(df):
    df = df.copy()

    if "Search Term" not in df.columns:
        return df

    def normalize(x):
        if pd.isna(x):
            return ""

        x = str(x)
        x = x.replace("[", "").replace("]", "")
        x = x.replace('"', "").replace("'", "")
        return x.strip().lower()

    df["Search Term"] = df["Search Term"].apply(normalize)

    return df


# =========================================================
# NICHE ENGINE
# =========================================================

def assign_niche(df):
    df = df.copy()

    if "Search Term" not in df.columns:
        return df

    def infer(text):
        text = str(text).lower()
        tokens = re.findall(r"[a-zA-Z]+", text)

        if not tokens:
            return "unknown"

        return tokens[0]

    df["Niche"] = df["Search Term"].apply(infer)

    return df


# =========================================================
# QUARTER
# =========================================================

def convert_quarter(month):
    if pd.isna(month):
        return None
    return f"Q{((int(month) - 1) // 3) + 1}"


# =========================================================
# TEXT CLEAN
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
    <a href="https://www.amazon.com/s?k={quote_plus(str(text))}" target="_blank">{text}</a>
    """


def make_asin_link(asin):
    if pd.isna(asin):
        return asin

    return f"""
    <a href="https://www.amazon.com/dp/{asin}" target="_blank">{asin}</a>
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
# INSIGHT CARDS (REPLACES CLUSTER)
# =========================================================

def build_insight_cards(df):

    insights = []

    for niche in df["Niche"].dropna().unique():

        niche_df = df[df["Niche"] == niche]
        volume = len(niche_df)

        opportunity = (
            "High Market Opportunity" if volume > 200 else
            "Medium Market Opportunity" if volume > 80 else
            "Emerging Opportunity"
        )

        competition = (
            "High Competition" if volume > 150 else
            "Medium Competition" if volume > 60 else
            "Low Competition"
        )

        insights.append({
            "niche": niche,
            "opportunity": opportunity,
            "competition": competition,
            "products": "Memorial plaques | Frames | Garden stones",
            "actions": [
                "Validate demand",
                "Expand keywords",
                "Test listings",
                "Scale ads"
            ]
        })

    return insights


def render_cards(insights):

    for i in insights:

        st.markdown(f"""
        <div style="
            padding:16px;
            margin-bottom:12px;
            border-radius:14px;
            background:linear-gradient(135deg,#0f172a,#111827);
            border:1px solid #1f2937;
        ">

        <h3 style="color:#e5e7eb">{i['niche']}</h3>

        <p><b>Opportunity:</b> {i['opportunity']}</p>
        <p><b>Competition:</b> {i['competition']}</p>

        <p><b>Products:</b> {i['products']}</p>

        <p><b>Actions:</b> {" | ".join(i['actions'])}</p>

        </div>
        """, unsafe_allow_html=True)


# =========================================================
# MAIN ENGINE
# =========================================================

def render_keyword_engine(final_df):

    st.markdown("# Keyword Intelligence")

    if final_df is None or final_df.empty:
        st.info("Upload keyword CSV files")
        return

    # =====================================================
    # PIPELINE FIX ORDER (CRITICAL)
    # =====================================================

    final_df = auto_fix_keyword_headers(final_df)
    final_df = normalize_multi_file(final_df)
    final_df = assign_niche(final_df)

    # =====================================================
    # QUARTER
    # =====================================================

    if "Reporting Date" in final_df.columns:
        final_df["Reporting Date"] = pd.to_datetime(final_df["Reporting Date"], errors="coerce")
        final_df["Month"] = final_df["Reporting Date"].dt.month
        final_df["Quarter"] = final_df["Month"].apply(convert_quarter)

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:
        niche_filter = st.multiselect("Niche", final_df["Niche"].dropna().unique())

    with c2:
        quarter_filter = st.multiselect("Quarter", final_df["Quarter"].dropna().unique())

    with c3:
        year_filter = st.multiselect("Year", final_df.get("Year", []))

    filtered_df = final_df.copy()

    if niche_filter:
        filtered_df = filtered_df[filtered_df["Niche"].isin(niche_filter)]

    if quarter_filter:
        filtered_df = filtered_df[filtered_df["Quarter"].isin(quarter_filter)]

    if year_filter and "Year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Year"].isin(year_filter)]

    # =====================================================
    # AGGRID AUTO FIT FIX
    # =====================================================

    display_df = filtered_df.copy()

    gb = GridOptionsBuilder.from_dataframe(display_df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True
    )

    gridOptions = gb.build()

    gridOptions["onFirstDataRendered"] = JsCode("""
    function(params) {
        params.api.sizeColumnsToFit();

        setTimeout(() => {
            let allColumnIds = [];
            params.columnApi.getAllColumns().forEach(col => {
                allColumnIds.push(col.getId());
            });
            params.columnApi.autoSizeColumns(allColumnIds, false);
        }, 150);
    }
    """)

    AgGrid(
        display_df,
        gridOptions=gridOptions,
        theme="alpine-dark",
        height=720,
        allow_unsafe_jscode=True
    )

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3 = st.columns(3)
    m1.metric("Rows", len(filtered_df))
    m2.metric("Columns", len(filtered_df.columns))
    m3.metric("Niches", filtered_df["Niche"].nunique())

    # =====================================================
    # NLP
    # =====================================================

    st.markdown("# NLP Intelligence")

    col = next((c for c in ["Search Term", "Keyword"] if c in filtered_df.columns), None)

    if col is None:
        st.warning("No NLP column")
        return

    corpus = filtered_df[col].astype(str).apply(clean_text).tolist()

    single = extract_ngrams(corpus, (1, 1))
    bigram = extract_ngrams(corpus, (2, 2))
    trigram = extract_ngrams(corpus, (3, 3))

    # =====================================================
    # INSIGHT CARDS
    # =====================================================

    st.markdown("# Market Intelligence")

    insights = build_insight_cards(filtered_df)
    render_cards(insights)

    # =====================================================
    # RESEARCH UX (FINAL)
    # =====================================================

    st.markdown("## Research Recommendations")

    recs = [
        "Expand high-intent niches (pet memorial, family loss)",
        "Identify low competition keywords",
        "Test POD personalization products",
        "Scale winning ASINs",
        "Optimize seasonal demand"
    ]

    for r in recs:
        st.markdown(f"""
        <div style="
            padding:12px;
            margin-bottom:8px;
            border-radius:10px;
            background:#0b1220;
            border:1px solid #1f2937;
        ">
        {r}
        </div>
        """, unsafe_allow_html=True)
