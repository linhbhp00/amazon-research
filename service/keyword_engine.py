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
# LINK HELPERS
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return text

    text = str(text)

    return (
        f'<a href="https://www.amazon.com/s?k='
        f'{quote_plus(text)}" target="_blank">{text}</a>'
    )


def make_asin_link(asin):

    if pd.isna(asin):
        return asin

    asin = str(asin)

    return (
        f'<a href="https://www.amazon.com/dp/'
        f'{asin}" target="_blank">{asin}</a>'
    )


# =========================================================
# CLEAN TEXT
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
# NGRAM ENGINE
# =========================================================

@st.cache_data
def extract_ngrams(
    corpus,
    ngram_range=(1, 1),
    min_freq=2,
    top_n=30
):

    try:

        vectorizer = CountVectorizer(
            ngram_range=ngram_range,
            stop_words="english",
            min_df=min_freq
        )

        X = vectorizer.fit_transform(corpus)

        sums = np.array(
            X.sum(axis=0)
        ).flatten()

        words_freq = [

            (word, sums[idx])

            for word, idx
            in vectorizer.vocabulary_.items()
        ]

        words_freq = sorted(
            words_freq,
            key=lambda x: x[1],
            reverse=True
        )

        result_df = pd.DataFrame(
            words_freq[:top_n],
            columns=["Phrase", "Frequency"]
        )

        return result_df

    except:

        return pd.DataFrame(
            columns=["Phrase", "Frequency"]
        )


# =========================================================
# DETECT KEYWORDS
# =========================================================

def detect_keywords(df, keywords, label):

    rows = []

    for _, row in df.iterrows():

        phrase = str(row["Phrase"]).lower()

        for keyword in keywords:

            if keyword in phrase:

                rows.append({

                    "Phrase": row["Phrase"],
                    "Frequency": row["Frequency"],
                    "Signal": keyword,
                    "Category": label
                })

    return pd.DataFrame(rows)


# =========================================================
# MAIN ENGINE
# =========================================================

def render_keyword_engine(final_df):

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if final_df is None or final_df.empty:

        st.info("Upload keyword CSV files to begin.")
        return

    # =====================================================
    # AUTO DETECT YEAR
    # =====================================================

    if "Year" not in final_df.columns:

        possible_year_cols = [

            col for col in final_df.columns

            if "year" in str(col).lower()
        ]

        if possible_year_cols:

            final_df["Year"] = final_df[
                possible_year_cols[0]
            ]

        else:

            final_df["Year"] = ""


    # =====================================================
    # AUTO DETECT QUARTER
    # =====================================================

    if "Quarter" not in final_df.columns:

        reporting_col = None

        for col in final_df.columns:

            if "reporting date" in str(col).lower():

                reporting_col = col
                break

        if reporting_col:

            final_df[reporting_col] = pd.to_datetime(
                final_df[reporting_col],
                errors="coerce"
            )

            final_df["Quarter"] = (
                final_df[reporting_col]
                .dt.quarter
                .apply(
                    lambda x:
                    f"Q{x}"
                    if pd.notna(x)
                    else ""
                )
            )

        else:

            final_df["Quarter"] = ""

    # =====================================================
    # HEADER
    # =====================================================

    st.markdown("# Keyword Intelligence")

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        niche_filter = st.multiselect(
            "Niche",
            options=sorted(
                final_df["Niche"]
                .dropna()
                .astype(str)
                .unique()
            )
            if "Niche" in final_df.columns
            else []
        )

    with c2:

        quarter_filter = st.multiselect(
            "Quarter",
            options=sorted(
                final_df["Quarter"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    with c3:

        year_filter = st.multiselect(
            "Year",
            options=sorted(
                final_df["Year"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    # =====================================================
    # FILTER DF
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter and "Niche" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Niche"].astype(str).isin(niche_filter)
        ]

    if quarter_filter:

        filtered_df = filtered_df[
            filtered_df["Quarter"].astype(str).isin(quarter_filter)
        ]

    if year_filter:

        filtered_df = filtered_df[
            filtered_df["Year"].astype(str).isin(year_filter)
        ]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search anything..."
    )

    if search_value:

        filtered_df = filtered_df[

            filtered_df.astype(str)

            .apply(

                lambda row:

                row.str.contains(
                    search_value,
                    case=False,
                    na=False
                ).any(),

                axis=1
            )
        ]

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Rows",
        f"{len(filtered_df):,}"
    )

    m2.metric(
        "Columns",
        len(filtered_df.columns)
    )

    m3.metric(
        "Unique Niches",
        filtered_df["Niche"].nunique()
        if "Niche" in filtered_df.columns
        else 0
    )

    m4.metric(
        "Unique Search Terms",
        filtered_df["Search Term"].nunique()
        if "Search Term" in filtered_df.columns
        else 0
    )

    # =====================================================
    # BACKLINKS
    # =====================================================

    link_columns = [

        "Search Term",

        "Top Clicked Brand #1",
        "Top Clicked Brand #2",
        "Top Clicked Brand #3",

        "Top Clicked Category #1",
        "Top Clicked Category #2",
        "Top Clicked Category #3",
    ]

    asin_columns = [

        "Top Clicked Product #1: ASIN",
        "Top Clicked Product #2: ASIN",
        "Top Clicked Product #3: ASIN",
    ]

    for col in link_columns:

        if col in filtered_df.columns:

            filtered_df[col] = filtered_df[col].apply(
                make_search_link
            )

    for col in asin_columns:

        if col in filtered_df.columns:

            filtered_df[col] = filtered_df[col].apply(
                make_asin_link
            )

    # =====================================================
    # DATA TABLE
    # =====================================================

    st.markdown("## Amazon Research Data")

    gb = GridOptionsBuilder.from_dataframe(filtered_df)

    gb.configure_default_column(

        sortable=True,
        filter=True,
        resizable=True,
        editable=False,

        floatingFilter=True,

        wrapText=False,
        autoHeight=False,

        minWidth=140,
        flex=1,
    )

    # =====================================================
    # FREEZE FIRST COLUMN
    # =====================================================

    if len(filtered_df.columns) > 0:

        gb.configure_column(
            filtered_df.columns[0],
            pinned="left",
            width=180
        )

    # =====================================================
    # AUTO WIDTH
    # =====================================================

    for col in filtered_df.columns:

        width = 160

        col_lower = str(col).lower()

        if "title" in col_lower:
            width = 520

        elif "search term" in col_lower:
            width = 280

        elif "brand" in col_lower:
            width = 220

        elif "category" in col_lower:
            width = 220

        elif "asin" in col_lower:
            width = 140

        elif "date" in col_lower:
            width = 160

        gb.configure_column(
            col,
            width=width
        )

    # =====================================================
    # HTML RENDERER
    # =====================================================

    cell_renderer = JsCode("""
    class UrlCellRenderer {

        init(params) {

            this.eGui = document.createElement('div');
            this.eGui.innerHTML = params.value || "";
        }

        getGui() {

            return this.eGui;
        }
    }
    """)

    for col in link_columns + asin_columns:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                cellRenderer=cell_renderer
            )

    # =====================================================
    # GRID OPTIONS
    # =====================================================

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    grid_options["animateRows"] = True

    grid_options["rowHeight"] = 42

    grid_options["suppressColumnVirtualisation"] = True

    # =====================================================
    # GRID
    # =====================================================

    try:

        AgGrid(

            filtered_df,

            gridOptions=grid_options,

            theme="alpine-dark",

            height=720,

            allow_unsafe_jscode=True,

            enable_enterprise_modules=False,

            update_mode=GridUpdateMode.NO_UPDATE,

            reload_data=False,
        )

    except Exception as e:

        st.warning(f"Grid render warning: {e}")

        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=720
        )

    # =====================================================
    # NLP ENGINE
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence Engine")

    # =====================================================
    # NLP SOURCE COLUMN
    # =====================================================

    candidate_columns = [

        "Search Term",
        "Keyword",
        "Keywords",
        "Product Title",
        "Title",
        "Query",
    ]

    nlp_source_column = None

    for col in candidate_columns:

        if col in filtered_df.columns:

            nlp_source_column = col
            break

    if nlp_source_column is None:

        st.warning("No NLP text column found.")
        return

    # =====================================================
    # SETTINGS
    # =====================================================

    with st.expander("NLP Settings", expanded=False):

        s1, s2 = st.columns(2)

        with s1:

            min_freq = st.slider(
                "Minimum Frequency",
                1,
                20,
                2
            )

        with s2:

            top_n = st.slider(
                "Top Results",
                10,
                100,
                30
            )

    # =====================================================
    # CORPUS
    # =====================================================

    nlp_series = (

        filtered_df[nlp_source_column]

        .astype(str)

        .apply(clean_text)
    )

    corpus = nlp_series.tolist()

    # =====================================================
    # NGRAM TABLES
    # =====================================================

    single_word_df = extract_ngrams(
        corpus,
        (1, 1),
        min_freq,
        top_n
    )

    bigram_df = extract_ngrams(
        corpus,
        (2, 2),
        min_freq,
        top_n
    )

    trigram_df = extract_ngrams(
        corpus,
        (3, 3),
        min_freq,
        top_n
    )

    # =====================================================
    # SIGNALS
    # =====================================================

    emotional_keywords = [

        "loss",
        "love",
        "memory",
        "sympathy",
        "funeral",
        "grief",
        "memorial",
        "rainbow bridge",
    ]

    commercial_keywords = [

        "gift",
        "buy",
        "best",
        "premium",
        "personalized",
        "custom",
        "decor",
    ]

    product_keywords = [

        "wind chime",
        "blanket",
        "frame",
        "stone",
        "garden",
        "lantern",
        "jewelry",
        "plaque",
    ]

    emotional_df = detect_keywords(
        trigram_df,
        emotional_keywords,
        "Emotion"
    )

    commercial_df = detect_keywords(
        trigram_df,
        commercial_keywords,
        "Commercial"
    )

    product_df = detect_keywords(
        trigram_df,
        product_keywords,
        "Product"
    )

    # =====================================================
    # CLUSTERS
    # =====================================================

    cluster_definitions = {

        "Pet Memorial": [
            "pet",
            "dog",
            "cat",
            "rainbow bridge",
        ],

        "Personalized": [
            "custom",
            "personalized",
            "engraved",
        ],

        "Outdoor Decor": [
            "garden",
            "stone",
            "wind chime",
            "plaque",
        ],
    }

    cluster_rows = []

    for cluster_name, keywords in cluster_definitions.items():

        total_freq = 0
        matched_phrases = []

        for _, row in trigram_df.iterrows():

            phrase = str(row["Phrase"]).lower()

            for keyword in keywords:

                if keyword in phrase:

                    total_freq += int(row["Frequency"])

                    matched_phrases.append(
                        row["Phrase"]
                    )

        if total_freq > 0:

            cluster_rows.append({

                "Cluster": cluster_name,

                "Signals": ", ".join(
                    list(set(matched_phrases))[:5]
                ),

                "Frequency": total_freq,

                "Opportunity Score": min(
                    100,
                    total_freq * 8
                )
            })

    cluster_df = pd.DataFrame(cluster_rows)

    # =====================================================
    # NLP METRICS
    # =====================================================

    st.markdown("## Strategic Market Intelligence")

    mm1, mm2, mm3, mm4 = st.columns(4)

    mm1.metric(
        "Single Words",
        len(single_word_df)
    )

    mm2.metric(
        "Bigram",
        len(bigram_df)
    )

    mm3.metric(
        "Trigram",
        len(trigram_df)
    )

    mm4.metric(
        "Keyword Clusters",
        len(cluster_df)
    )

    # =====================================================
    # NLP TABS
    # =====================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Keyword Clusters",
        "Market Insights"
    ])

    # =====================================================
    # SINGLE
    # =====================================================

    with tab1:

        st.dataframe(
            single_word_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # BIGRAM
    # =====================================================

    with tab2:

        st.dataframe(
            bigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # TRIGRAM
    # =====================================================

    with tab3:

        st.dataframe(
            trigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # CLUSTERS
    # =====================================================

    with tab4:

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=600
        )

    # =====================================================
    # INSIGHTS
    # =====================================================

    with tab5:

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("### Emotional Signals")

            st.dataframe(
                emotional_df,
                use_container_width=True,
                height=350
            )

            st.markdown("### Product Signals")

            st.dataframe(
                product_df,
                use_container_width=True,
                height=350
            )

        with c2:

            st.markdown("### Commercial Signals")

            st.dataframe(
                commercial_df,
                use_container_width=True,
                height=350
            )
