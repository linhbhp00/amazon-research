# service/keyword_engine.py

import re
import html
import numpy as np
import pandas as pd
import streamlit as st

from urllib.parse import quote_plus
from sklearn.feature_extraction.text import CountVectorizer

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# AMAZON LINK HELPERS
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return ""

    text = str(text).strip()

    if text == "":
        return ""

    safe_text = html.escape(text)

    return f'''
    <a href="https://www.amazon.com/s?k={quote_plus(text)}"
       target="_blank"
       style="color:#60a5fa;text-decoration:none;">
       {safe_text}
    </a>
    '''


def make_asin_link(asin):

    if pd.isna(asin):
        return ""

    asin = str(asin).strip()

    if asin == "":
        return ""

    safe_asin = html.escape(asin)

    return f'''
    <a href="https://www.amazon.com/dp/{asin}"
       target="_blank"
       style="color:#fbbf24;text-decoration:none;">
       {safe_asin}
    </a>
    '''

# =========================================================
# TEXT CLEANER
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
# EXTRACT NGRAMS
# =========================================================

@st.cache_data(show_spinner=False)
def extract_ngrams(
    corpus,
    ngram_range=(1, 1),
    min_freq=2,
    top_n=50
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

        return pd.DataFrame(
            words_freq[:top_n],
            columns=["Phrase", "Frequency"]
        )

    except:

        return pd.DataFrame(
            columns=["Phrase", "Frequency"]
        )

# =========================================================
# SMART CLUSTER ENGINE
# =========================================================

def generate_market_clusters(trigram_df):

    cluster_patterns = {

        "Pet Memorial": [
            "dog memorial",
            "cat memorial",
            "pet memorial",
            "rainbow bridge",
            "pet loss",
        ],

        "Personalized Memorial": [
            "custom memorial",
            "personalized memorial",
            "engraved",
            "photo plaque",
        ],

        "Outdoor Memorial Decor": [
            "garden stone",
            "wind chime",
            "memorial plaque",
            "solar lantern",
        ],

        "Sympathy Gifts": [
            "sympathy gift",
            "loss gift",
            "bereavement",
            "funeral gift",
        ],

        "Family Remembrance": [
            "loss mom",
            "loss dad",
            "father memorial",
            "mother memorial",
        ],
    }

    rows = []

    for cluster_name, patterns in cluster_patterns.items():

        matched_phrases = []
        total_frequency = 0

        for _, row in trigram_df.iterrows():

            phrase = str(row["Phrase"]).lower()

            for pattern in patterns:

                if pattern in phrase:

                    matched_phrases.append(
                        row["Phrase"]
                    )

                    total_frequency += int(
                        row["Frequency"]
                    )

        if total_frequency > 0:

            # =====================================
            # COMPETITION SCORE
            # =====================================

            if total_frequency >= 80:
                competition = "High"

            elif total_frequency >= 30:
                competition = "Medium"

            else:
                competition = "Low"

            # =====================================
            # OPPORTUNITY SCORE
            # =====================================

            opportunity_score = min(
                100,
                int(total_frequency * 1.8)
            )

            # =====================================
            # ACTION
            # =====================================

            if opportunity_score >= 90:
                action = "Launch Aggressively"

            elif opportunity_score >= 75:
                action = "Scale"

            elif opportunity_score >= 55:
                action = "High Potential"

            else:
                action = "Research Further"

            rows.append({

                "Cluster": cluster_name,

                "Main Signals": ", ".join(
                    list(set(matched_phrases))[:5]
                ),

                "Competition": competition,

                "Opportunity Score": opportunity_score,

                "Action": action
            })

    cluster_df = pd.DataFrame(rows)

    if not cluster_df.empty:

        cluster_df = cluster_df.sort_values(
            by="Opportunity Score",
            ascending=False
        )

    return cluster_df

# =========================================================
# RECOMMENDATION ENGINE
# =========================================================

def generate_recommendations(cluster_df):

    recommendations = []

    for _, row in cluster_df.iterrows():

        cluster = row["Cluster"]

        if cluster == "Pet Memorial":

            recommendations.append({
                "Opportunity":
                    "Expand into dog sympathy gifts",
                "Priority":
                    "High"
            })

            recommendations.append({
                "Opportunity":
                    "Research memorial lantern demand",
                "Priority":
                    "High"
            })

        elif cluster == "Outdoor Memorial Decor":

            recommendations.append({
                "Opportunity":
                    "Launch personalized garden decor",
                "Priority":
                    "Medium"
            })

        elif cluster == "Personalized Memorial":

            recommendations.append({
                "Opportunity":
                    "Scale engraved acrylic products",
                "Priority":
                    "High"
            })

    return pd.DataFrame(recommendations)

# =========================================================
# MAIN RENDER
# =========================================================

def render_keyword_engine(final_df):

    # =====================================================
    # SAFE CHECK
    # =====================================================

    if final_df is None or final_df.empty:

        st.info("No keyword dataset loaded.")
        return

    # =====================================================
    # REMOVE DUPLICATE COLUMNS
    # =====================================================

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ].copy()

    # =====================================================
    # REPORTING DATE -> QUARTER
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = pd.to_datetime(
            final_df["Reporting Date"],
            errors="coerce"
        )

        final_df["Month"] = (
            final_df["Reporting Date"]
            .dt.month
        )

        def detect_quarter(month):

            if pd.isna(month):
                return ""

            month = int(month)

            if month in [1, 2, 3]:
                return "Q1"

            elif month in [4, 5, 6]:
                return "Q2"

            elif month in [7, 8, 9]:
                return "Q3"

            else:
                return "Q4"

        final_df["Quarter"] = (
            final_df["Month"]
            .apply(detect_quarter)
        )

    # =====================================================
    # BACKLINKS
    # =====================================================

    for col in final_df.columns:

        col_lower = col.lower()

        try:

            if (
                "search term" in col_lower
                or "keyword" in col_lower
                or "query" in col_lower
                or "brand" in col_lower
                or "category" in col_lower
            ):

                final_df[col] = final_df[col].apply(
                    make_search_link
                )

            elif "asin" in col_lower:

                final_df[col] = final_df[col].apply(
                    make_asin_link
                )

        except:
            pass

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("## Keyword Intelligence")

    col1, col2, col3 = st.columns(3)

    with col1:

        niche_filter = st.multiselect(
            "Niche",
            sorted(
                final_df["Niche"]
                .dropna()
                .astype(str)
                .unique()
            )
            if "Niche" in final_df.columns
            else []
        )

    with col2:

        quarter_filter = st.multiselect(
            "Quarter",
            sorted(
                final_df["Quarter"]
                .dropna()
                .astype(str)
                .unique()
            )
            if "Quarter" in final_df.columns
            else []
        )

    with col3:

        year_filter = st.multiselect(
            "Year",
            sorted(
                final_df["Year"]
                .dropna()
                .astype(str)
                .unique()
            )
            if "Year" in final_df.columns
            else []
        )

    # =====================================================
    # FILTER DATAFRAME
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter:

        filtered_df = filtered_df[
            filtered_df["Niche"]
            .astype(str)
            .isin(niche_filter)
        ]

    if quarter_filter:

        filtered_df = filtered_df[
            filtered_df["Quarter"]
            .astype(str)
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
        placeholder="Search keyword..."
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
        if "Niche" in filtered_df.columns
        else 0
    )

    # =====================================================
    # GRID
    # =====================================================

    st.markdown("## Keyword Dataset")

    try:

        gb = GridOptionsBuilder.from_dataframe(
            filtered_df
        )

        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True,
            editable=False,
            floatingFilter=True,
            minWidth=140,
        )

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

        for col in filtered_df.columns:

            gb.configure_column(
                col,
                cellRenderer=cell_renderer,
            )

        grid_options = gb.build()

        AgGrid(
            filtered_df,
            gridOptions=grid_options,
            theme="alpine-dark",
            height=720,
            fit_columns_on_grid_load=True,
            update_mode=GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            reload_data=False,
        )

    except:

        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=720
        )

    # =====================================================
    # NLP ENGINE
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence")

    candidate_columns = [

        "Search Term",
        "Keyword",
        "Keywords",
        "Query",
        "Product Title",
        "Title",
    ]

    nlp_column = None

    for col in candidate_columns:

        if col in filtered_df.columns:

            nlp_column = col
            break

    if nlp_column is None:

        st.warning(
            "No NLP-compatible column found."
        )

        return

    corpus = (

        filtered_df[nlp_column]
        .astype(str)
        .apply(clean_text)
        .tolist()
    )

    # =====================================================
    # SETTINGS
    # =====================================================

    with st.expander(
        "NLP Settings",
        expanded=False
    ):

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
    # NGRAMS
    # =====================================================

    single_df = extract_ngrams(
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
    # CLUSTER ENGINE
    # =====================================================

    cluster_df = generate_market_clusters(
        trigram_df
    )

    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    recommendation_df = generate_recommendations(
        cluster_df
    )

    # =====================================================
    # INSIGHT METRICS
    # =====================================================

    st.markdown(
        "## Strategic Market Intelligence"
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Single Words",
        len(single_df)
    )

    m2.metric(
        "Bigram",
        len(bigram_df)
    )

    m3.metric(
        "Trigram",
        len(trigram_df)
    )

    m4.metric(
        "Clusters",
        len(cluster_df)
    )

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Demand Clusters",
        "Research Recommendation"
    ])

    # =====================================================
    # SINGLE
    # =====================================================

    with tab1:

        st.dataframe(
            single_df,
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
    # CLUSTER
    # =====================================================

    with tab4:

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=500
        )

    # =====================================================
    # RECOMMENDATION
    # =====================================================

    with tab5:

        st.dataframe(
            recommendation_df,
            use_container_width=True,
            height=500
        )
