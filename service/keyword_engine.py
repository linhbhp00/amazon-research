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

            for word, idx in vectorizer.vocabulary_.items()
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
# SIGNAL DETECTOR
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

def render_keyword_engine(df):

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if df is None or df.empty:

        st.warning("No keyword dataset loaded.")

        return

    # =====================================================
    # TITLE
    # =====================================================

    st.markdown("# Keyword Intelligence")

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("## Dataset Filters")

    col1, col2, col3 = st.columns(3)

    filtered_df = df.copy()

    # -----------------------------------------------------
    # NICHE
    # -----------------------------------------------------

    with col1:

        if "Niche" in filtered_df.columns:

            niche_filter = st.multiselect(

                "Niche",

                options=sorted(
                    filtered_df["Niche"]
                    .dropna()
                    .astype(str)
                    .unique()
                )
            )

            if niche_filter:

                filtered_df = filtered_df[
                    filtered_df["Niche"].isin(
                        niche_filter
                    )
                ]

    # -----------------------------------------------------
    # QUARTER
    # -----------------------------------------------------

    with col2:

        if "Quarter" in filtered_df.columns:

            quarter_filter = st.multiselect(

                "Quarter",

                options=sorted(
                    filtered_df["Quarter"]
                    .dropna()
                    .unique()
                )
            )

            if quarter_filter:

                filtered_df = filtered_df[
                    filtered_df["Quarter"].isin(
                        quarter_filter
                    )
                ]

    # -----------------------------------------------------
    # YEAR
    # -----------------------------------------------------

    with col3:

        if "Year" in filtered_df.columns:

            year_filter = st.multiselect(

                "Year",

                options=sorted(
                    filtered_df["Year"]
                    .dropna()
                    .astype(str)
                    .unique()
                )
            )

            if year_filter:

                filtered_df = filtered_df[
                    filtered_df["Year"].isin(
                        year_filter
                    )
                ]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(

        "Quick Search",

        placeholder="Search keyword, ASIN, category..."
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

    c1, c2, c3, c4 = st.columns(4)

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

    c4.metric(
        "Unique Search Terms",
        filtered_df["Search Term"].nunique()
        if "Search Term" in filtered_df.columns
        else 0
    )

    # =====================================================
    # DISPLAY DATA
    # =====================================================

    st.markdown("## Amazon Research Data")

    display_df = filtered_df.copy()

    # -----------------------------------------------------
    # BACKLINKS
    # -----------------------------------------------------

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

        if col in display_df.columns:

            display_df[col] = display_df[col].apply(
                make_search_link
            )

    for col in asin_columns:

        if col in display_df.columns:

            display_df[col] = display_df[col].apply(
                make_asin_link
            )

    # =====================================================
    # GRID
    # =====================================================

    gb = GridOptionsBuilder.from_dataframe(display_df)

    gb.configure_default_column(

        sortable=True,
        filter=True,
        resizable=True,
        editable=False,
        floatingFilter=True,

        minWidth=140,
        flex=1,
    )

    first_col = display_df.columns[0]

    gb.configure_column(

        first_col,

        pinned="left",
        width=180
    )

    # -----------------------------------------------------
    # WIDTH
    # -----------------------------------------------------

    for col in display_df.columns:

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
            width = 160

        elif "date" in col_lower:
            width = 160

        gb.configure_column(
            col,
            width=width
        )

    # -----------------------------------------------------
    # HTML RENDERER
    # -----------------------------------------------------

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

        if col in display_df.columns:

            gb.configure_column(

                col,

                cellRenderer=cell_renderer
            )

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    grid_options["animateRows"] = True

    grid_options["rowHeight"] = 42

    # =====================================================
    # RENDER GRID
    # =====================================================

    try:

        AgGrid(

            display_df,

            gridOptions=grid_options,

            theme="alpine-dark",

            height=700,

            fit_columns_on_grid_load=False,

            update_mode=GridUpdateMode.NO_UPDATE,

            allow_unsafe_jscode=True,

            enable_enterprise_modules=False,

            reload_data=False,
        )

    except Exception as e:

        st.error(f"AgGrid Error: {e}")

        st.dataframe(
            display_df,
            use_container_width=True
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

    if nlp_source_column is None:

        st.warning("No NLP column detected.")

        return

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
    # CORPUS
    # =====================================================

    nlp_series = (

        filtered_df[nlp_source_column]

        .astype(str)

        .apply(clean_text)
    )

    corpus = nlp_series.tolist()

    # =====================================================
    # NGRAMS
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
    ]

    commercial_keywords = [

        "gift",
        "buy",
        "best",
        "premium",
        "personalized",
        "custom",
    ]

    product_keywords = [

        "wind chime",
        "blanket",
        "frame",
        "stone",
        "garden",
        "lantern",
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
    }

    cluster_rows = []

    for cluster_name, keywords in cluster_definitions.items():

        total_freq = 0

        matched_phrases = []

        for _, row in trigram_df.iterrows():

            phrase = str(
                row["Phrase"]
            ).lower()

            for keyword in keywords:

                if keyword in phrase:

                    total_freq += int(
                        row["Frequency"]
                    )

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
                    list(
                        set(matched_phrases)
                    )[:5]
                ),

                "Frequency": total_freq,

                "Competition": competition,

                "Opportunity Score": opportunity_score
            })

    cluster_df = pd.DataFrame(cluster_rows)

    # =====================================================
    # METRICS
    # =====================================================

    st.markdown("## Strategic Market Intelligence")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Single Words",
        len(single_word_df)
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

            st.markdown(
                "### Emotional Signals"
            )

            st.dataframe(
                emotional_df,
                use_container_width=True,
                height=300
            )

            st.markdown(
                "### Product Signals"
            )

            st.dataframe(
                product_df,
                use_container_width=True,
                height=300
            )

        with c2:

            st.markdown(
                "### Commercial Signals"
            )

            st.dataframe(
                commercial_df,
                use_container_width=True,
                height=300
            )
