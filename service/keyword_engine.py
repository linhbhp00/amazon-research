# service/keyword_engine.py

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

    return f'''
    <a href="https://www.amazon.com/s?k={quote_plus(text)}"
       target="_blank">
       {text}
    </a>
    '''


def make_asin_link(asin):

    if pd.isna(asin):
        return asin

    asin = str(asin)

    return f'''
    <a href="https://www.amazon.com/dp/{asin}"
       target="_blank">
       {asin}
    </a>
    '''


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
# NGRAM EXTRACTOR
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
    # EMPTY
    # =====================================================

    if final_df is None or final_df.empty:

        st.info("Upload keyword CSV files to begin.")
        return

    # =====================================================
    # TITLE
    # =====================================================

    st.markdown("# Keyword Intelligence")

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        niche_filter = st.multiselect(
            "Niche",
            options=sorted(
                final_df["Niche"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    with col2:

        quarter_filter = st.multiselect(
            "Quarter",
            options=sorted(
                final_df["Quarter"]
                .dropna()
                .unique()
            )
        )

    with col3:

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
    # FILTER DATAFRAME
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter:

        filtered_df = filtered_df[
            filtered_df["Niche"]
            .isin(niche_filter)
        ]

    if quarter_filter:

        filtered_df = filtered_df[
            filtered_df["Quarter"]
            .isin(quarter_filter)
        ]

    if year_filter:

        filtered_df = filtered_df[
            filtered_df["Year"]
            .astype(str)
            .isin(year_filter)
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

            filtered_df[col] = (
                filtered_df[col]
                .apply(make_search_link)
            )

    for col in asin_columns:

        if col in filtered_df.columns:

            filtered_df[col] = (
                filtered_df[col]
                .apply(make_asin_link)
            )

    # =====================================================
    # METRICS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Rows",
        f"{len(filtered_df):,}"
    )

    c2.metric(
        "Columns",
        len(filtered_df.columns)
    )

    c3.metric(
        "Unique Niches",
        filtered_df["Niche"].nunique()
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
        minWidth=140,
    )

    first_col = filtered_df.columns[0]

    gb.configure_column(
        first_col,
        pinned="left",
        width=180
    )

    for col in filtered_df.columns:

        width = 160

        col_lower = col.lower()

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

        elif "month" in col_lower:
            width = 120

        elif "quarter" in col_lower:
            width = 120

        elif "year" in col_lower:
            width = 120

        elif "date" in col_lower:
            width = 160

        gb.configure_column(
            col,
            width=width,
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

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    grid_options["animateRows"] = True

    grid_options["rowHeight"] = 42

    # =====================================================
    # AGGRID SAFE RENDER
    # =====================================================

    try:

        AgGrid(
            filtered_df,

            gridOptions=grid_options,

            theme="alpine-dark",

            height=720,

            update_mode=GridUpdateMode.NO_UPDATE,

            allow_unsafe_jscode=True,

            enable_enterprise_modules=False,

            reload_data=False,
        )

    except Exception:

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
    # DETECT NLP COLUMN
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

    # fallback
    if nlp_source_column is None:

        text_scores = {}

        for col in filtered_df.columns:

            try:

                avg_length = (
                    filtered_df[col]
                    .astype(str)
                    .str.len()
                    .mean()
                )

                text_scores[col] = avg_length

            except:
                pass

        if text_scores:

            nlp_source_column = max(
                text_scores,
                key=text_scores.get
            )

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
    # GENERATE TABLES
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
        "remembrance",
        "sympathy",
        "funeral",
        "grief",
        "memorial",
        "rainbow bridge",
    ]

    commercial_keywords = [

        "gift",
        "gifts",
        "buy",
        "best",
        "premium",
        "personalized",
        "custom",
        "plaque",
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
        "card",
    ]

    # =====================================================
    # DETECT SIGNALS
    # =====================================================

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
    # SEARCH INTENT
    # =====================================================

    intent_map = {

        "gift": "Commercial",
        "buy": "Transactional",
        "best": "Commercial",
        "cheap": "Budget",
        "review": "Research",
        "how": "Informational",
        "personalized": "Customization",
        "custom": "Customization",
    }

    intent_rows = []

    for _, row in trigram_df.iterrows():

        phrase = str(row["Phrase"]).lower()

        for keyword, intent in intent_map.items():

            if keyword in phrase:

                intent_rows.append({

                    "Phrase": row["Phrase"],
                    "Intent": intent,
                    "Frequency": row["Frequency"]
                })

    intent_df = pd.DataFrame(intent_rows)

    # =====================================================
    # CLUSTER ENGINE
    # =====================================================

    cluster_definitions = {

        "Pet Memorial": [
            "pet",
            "dog",
            "cat",
            "rainbow bridge",
        ],

        "Personalized Memorial": [
            "personalized",
            "custom",
            "engraved",
        ],

        "Outdoor Memorial Decor": [
            "garden",
            "stone",
            "wind chime",
            "plaque",
        ],

        "Funeral Service": [
            "funeral",
            "guest book",
            "cards",
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

            if total_freq >= 15:
                competition = "High"

            elif total_freq >= 7:
                competition = "Medium"

            else:
                competition = "Low"

            opportunity_score = min(
                100,
                int(total_freq * 8)
            )

            cluster_rows.append({

                "Cluster": cluster_name,

                "Signals": ", ".join(
                    list(set(matched_phrases))[:5]
                ),

                "Frequency": total_freq,

                "Competition": competition,

                "Opportunity Score": opportunity_score
            })

    cluster_df = pd.DataFrame(cluster_rows)

    if not cluster_df.empty:

        cluster_df = cluster_df.sort_values(
            by="Opportunity Score",
            ascending=False
        )

    # =====================================================
    # STRATEGIC INSIGHTS
    # =====================================================

    st.markdown("## Strategic Market Intelligence")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Single Words",
        len(single_word_df)
    )

    metric2.metric(
        "Bigram",
        len(bigram_df)
    )

    metric3.metric(
        "Trigram",
        len(trigram_df)
    )

    metric4.metric(
        "Keyword Clusters",
        len(cluster_df)
    )

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Keyword Clusters",
        "Market Insights"
    ])

    # =====================================================
    # SINGLE WORD
    # =====================================================

    with tab1:

        st.markdown(
            "### Keyword Frequency Analysis"
        )

        st.dataframe(
            single_word_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # BIGRAM
    # =====================================================

    with tab2:

        st.markdown("### Bigram Analysis")

        st.dataframe(
            bigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # TRIGRAM
    # =====================================================

    with tab3:

        st.markdown("### Trigram Analysis")

        st.dataframe(
            trigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # CLUSTERS
    # =====================================================

    with tab4:

        st.markdown(
            "### Keyword Clustering"
        )

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=600
        )

    # =====================================================
    # MARKET INSIGHTS
    # =====================================================

    with tab5:

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                "### Emotional Signals"
            )

            st.dataframe(
                emotional_df,
                use_container_width=True,
                height=350
            )

            st.markdown(
                "### Product Signals"
            )

            st.dataframe(
                product_df,
                use_container_width=True,
                height=350
            )

        with c2:

            st.markdown(
                "### Commercial Signals"
            )

            st.dataframe(
                commercial_df,
                use_container_width=True,
                height=350
            )

            st.markdown(
                "### Search Intent"
            )

            st.dataframe(
                intent_df,
                use_container_width=True,
                height=350
            )
