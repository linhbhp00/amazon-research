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
# LOCAL HEADER PROTECTION
# =========================================================

EXPECTED_KEYWORD_COLUMNS = [
    "Search Term",
    "Search Frequency Rank",
    "Reporting Date",
]


def is_valid_keyword_header(columns):
    cols = [str(c).strip() for c in columns]
    score = sum([1 for c in EXPECTED_KEYWORD_COLUMNS if c in cols])
    return score >= 2


# =========================================================
# AUTO HEADER FIX (UNCHANGED)
# =========================================================

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
# 🔥 FIX MULTI-FILE SEARCH TERM NORMALIZATION (NEW)
# =========================================================

def normalize_search_term(x):
    if pd.isna(x):
        return ""

    x = str(x)
    x = x.replace("[", "").replace("]", "")
    x = x.replace('"', "").replace("'", "")
    return x.strip().lower()


# =========================================================
# CLEAN TEXT (UNCHANGED)
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
# SEARCH LINK
# =========================================================

def make_search_link(text):
    if pd.isna(text):
        return text

    return f'''
    <a href="https://www.amazon.com/s?k={quote_plus(str(text))}" target="_blank">
    {text}
    </a>
    '''


# =========================================================
# ASIN LINK
# =========================================================

def make_asin_link(asin):
    if pd.isna(asin):
        return asin

    return f'''
    <a href="https://www.amazon.com/dp/{asin}" target="_blank">
    {asin}
    </a>
    '''


# =========================================================
# NGRAM ENGINE (UNCHANGED)
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
# CLUSTER ENGINE (UNCHANGED - KEEP LOGIC)
# =========================================================

def generate_cluster_insights(trigram_df):

    cluster_definitions = {

        "Pet Memorial": {
            "keywords": ["dog", "cat", "pet", "rainbow bridge"],
            "emotion": "Pet Grief",
            "products": "Plaques, Frames, Wind Chimes",
        },

        "Family Loss": {
            "keywords": ["dad", "mom", "father", "mother", "loss"],
            "emotion": "Grief/Nostalgia",
            "products": "Lanterns, Blankets, Jewelry",
        },

        "Outdoor Memorial Decor": {
            "keywords": ["garden", "stone", "wind chime", "plaque"],
            "emotion": "Remembrance",
            "products": "Garden Decor, Solar Plaques",
        },

        "Funeral Service": {
            "keywords": ["funeral", "guest book", "cards"],
            "emotion": "Sympathy",
            "products": "Guest Books, Signs",
        },

        "Personalized Memorial": {
            "keywords": ["personalized", "custom", "engraved"],
            "emotion": "Memory",
            "products": "Custom Acrylic, Plaques",
        },
    }

    rows = []

    for cluster_name, config in cluster_definitions.items():

        total_freq = 0
        matched_phrases = []

        for _, row in trigram_df.iterrows():

            phrase = str(row["Phrase"]).lower()

            for keyword in config["keywords"]:
                if keyword in phrase:
                    total_freq += int(row["Frequency"])
                    matched_phrases.append(row["Phrase"])

        if total_freq > 0:

            competition = (
                "High" if total_freq >= 15 else
                "Medium" if total_freq >= 7 else
                "Low"
            )

            opportunity_score = min(100, int(total_freq * 8))

            action = (
                "Launch Aggressively" if opportunity_score >= 90 else
                "Scale" if opportunity_score >= 75 else
                "High Potential" if opportunity_score >= 60 else
                "Research Further"
            )

            rows.append({
                "Cluster": cluster_name,
                "Main Signals": ", ".join(list(set(matched_phrases))[:5]),
                "Emotion": config["emotion"],
                "Product Opportunities": config["products"],
                "Competition": competition,
                "Opportunity Score": opportunity_score,
                "Action": action
            })

    return pd.DataFrame(rows)


# =========================================================
# MAIN ENGINE (PATCHED ONLY)
# =========================================================

def render_keyword_engine(final_df):

    st.markdown("# Keyword Intelligence")

    if final_df is None or final_df.empty:
        st.info("Upload keyword CSV files to begin.")
        return

    # =====================================================
    # HEADER FIX
    # =====================================================

    final_df = auto_fix_keyword_headers(final_df)
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]

    # =====================================================
    # 🔥 MULTI-FILE FIX (IMPORTANT PATCH)
    # =====================================================

    if "Search Term" in final_df.columns:
        final_df["Search Term"] = final_df["Search Term"].apply(normalize_search_term)

    # =====================================================
    # QUARTER FIX (UX IMPROVEMENT)
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = pd.to_datetime(
            final_df["Reporting Date"], errors="coerce"
        )

        final_df["Month"] = final_df["Reporting Date"].dt.month

        final_df["Quarter"] = final_df["Month"].apply(
            lambda x: f"Q{((x - 1)//3)+1}" if pd.notna(x) else None
        )

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:
        niche_filter = st.multiselect(
            "Niche",
            final_df["Niche"].dropna().unique()
            if "Niche" in final_df.columns else []
        )

    with col2:
        quarter_filter = st.multiselect(
            "Quarter",
            final_df["Quarter"].dropna().unique()
            if "Quarter" in final_df.columns else []
        )

    with col3:
        year_filter = st.multiselect(
            "Year",
            final_df["Year"].dropna().unique()
            if "Year" in final_df.columns else []
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter and "Niche" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Niche"].isin(niche_filter)]

    if quarter_filter and "Quarter" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Quarter"].isin(quarter_filter)]

    if year_filter and "Year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Year"].isin(year_filter)]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input("Quick Search", "")

    if search_value:
        filtered_df = filtered_df[
            filtered_df.astype(str).apply(
                lambda row: row.str.contains(search_value, case=False, na=False).any(),
                axis=1
            )
        ]

    # =====================================================
    # DISPLAY DF
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

    c1, c2, c3 = st.columns(3)

    c1.metric("Rows", len(filtered_df))
    c2.metric("Columns", len(filtered_df.columns))
    c3.metric("Unique Niches", filtered_df["Niche"].nunique() if "Niche" in filtered_df.columns else 0)

    # =====================================================
    # TABLE (AUTO-FIT FIXED)
    # =====================================================

    st.markdown("## Keyword Dataset")

    gb = GridOptionsBuilder.from_dataframe(display_df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
    )

    grid_options = gb.build()

    grid_options["onFirstDataRendered"] = JsCode("""
    function(params) {
        params.api.sizeColumnsToFit();

        setTimeout(() => {
            let allColumnIds = [];
            params.columnApi.getAllColumns().forEach(col => {
                allColumnIds.push(col.getId());
            });
            params.columnApi.autoSizeColumns(allColumnIds, false);
        }, 120);
    }
    """)

    AgGrid(
        display_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        allow_unsafe_jscode=True,
    )

    # =====================================================
    # NLP + CLUSTER (UNCHANGED)
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence")

    nlp_col = next((c for c in ["Search Term", "Keyword"] if c in filtered_df.columns), None)

    if nlp_col is None:
        st.warning("No NLP-compatible column found.")
        return

    corpus = filtered_df[nlp_col].astype(str).apply(clean_text).tolist()

    single = extract_ngrams(corpus, (1, 1))
    bigram = extract_ngrams(corpus, (2, 2))
    trigram = extract_ngrams(corpus, (3, 3))

    cluster_df = generate_cluster_insights(trigram)

    # =====================================================
    # TABS (UNCHANGED)
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "Single Word",
        "Bigram",
        "Trigram",
        "Cluster Intelligence"
    ])

    with tab1:
        st.dataframe(single, use_container_width=True, height=700)

    with tab2:
        st.dataframe(bigram, use_container_width=True, height=700)

    with tab3:
        st.dataframe(trigram, use_container_width=True, height=700)

    with tab4:

        st.dataframe(cluster_df, use_container_width=True, height=700)

        # =====================================================
        # 🔥 ONLY UX UPGRADE (RESEARCH RECOMMENDATIONS)
        # =====================================================

        st.markdown("## Research Recommendations")

        recs = [
            "Expand high-intent niches (pet memorial, family loss)",
            "Identify low competition keyword clusters",
            "Test POD personalization products",
            "Scale winning ASINs",
            "Optimize seasonal demand"
        ]

        for r in recs:
            st.markdown(f"""
            <div style="
                padding:10px;
                margin-bottom:6px;
                border-radius:10px;
                background:#0b1220;
                border:1px solid #1f2937;
            ">
            {r}
            </div>
            """, unsafe_allow_html=True)
