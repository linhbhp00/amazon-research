# =========================================================
# service/keyword_engine.py
# HEADER PROTECTION LOCAL + AUTO HEADER FIX
# =========================================================

import re
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
# LOCAL HEADER PROTECTION
# =========================================================

EXPECTED_HEADERS = [

    "Search Frequency Rank",
    "Search Term",

    "Top Clicked Brand #1",
    "Top Clicked Brands #2",
    "Top Clicked Brands #3",

    "Top Clicked Category #1",
    "Top Clicked Category #2",
    "Top Clicked Category #3",

    "Top Clicked Product #1: ASIN",
    "Top Clicked Product #1: Product Title",
    "Top Clicked Product #1: Click Share",
    "Top Clicked Product #1: Conversion Share",

    "Top Clicked Product #2: ASIN",
    "Top Clicked Product #2: Product Title",
    "Top Clicked Product #2: Click Share",
    "Top Clicked Product #2: Conversion Share",

    "Top Clicked Product #3: ASIN",
    "Top Clicked Product #3: Product Title",
    "Top Clicked Product #3: Click Share",
    "Top Clicked Product #3: Conversion Share",

    "Reporting Date"
]

# =========================================================
# AUTO HEADER FIX
# =========================================================

def auto_fix_headers(df):

    """
    LOCAL HEADER FIX ONLY
    Không ảnh hưởng app.py / asin_engine / ranking_engine
    """

    if df is None or df.empty:
        return df

    df = df.copy()

    # -----------------------------------------------------
    # REMOVE FULL EMPTY ROWS
    # -----------------------------------------------------

    df = df.dropna(
        how="all"
    ).reset_index(drop=True)

    if df.empty:
        return df

    # -----------------------------------------------------
    # DETECT HEADER ROW
    # -----------------------------------------------------

    detected_header_index = None

    for idx in range(min(10, len(df))):

        row_values = (
            df.iloc[idx]
            .fillna("")
            .astype(str)
            .tolist()
        )

        score = 0

        for value in row_values:

            value_lower = value.lower()

            if (
                "search term" in value_lower
                or "asin" in value_lower
                or "reporting date" in value_lower
                or "clicked" in value_lower
            ):
                score += 1

        if score >= 3:

            detected_header_index = idx
            break

    # -----------------------------------------------------
    # FALLBACK HEADER
    # -----------------------------------------------------

    if detected_header_index is None:

        detected_header_index = 1

    # -----------------------------------------------------
    # APPLY HEADER
    # -----------------------------------------------------

    headers = (

        df.iloc[detected_header_index]
        .fillna("")
        .astype(str)
        .tolist()
    )

    # -----------------------------------------------------
    # CLEAN HEADERS
    # -----------------------------------------------------

    clean_headers = []

    used_headers = {}

    for i, header in enumerate(headers):

        header = str(header).strip()

        # fallback if empty
        if header == "" or header.lower() == "nan":

            if i < len(EXPECTED_HEADERS):
                header = EXPECTED_HEADERS[i]
            else:
                header = f"Column_{i}"

        # deduplicate
        if header in used_headers:

            used_headers[header] += 1

            header = (
                f"{header}_{used_headers[header]}"
            )

        else:

            used_headers[header] = 0

        clean_headers.append(header)

    # -----------------------------------------------------
    # APPLY DATA
    # -----------------------------------------------------

    data_df = (
        df.iloc[detected_header_index + 1:]
        .copy()
        .reset_index(drop=True)
    )

    data_df.columns = clean_headers

    # -----------------------------------------------------
    # REMOVE INVALID ROWS
    # -----------------------------------------------------

    if "Search Term" in data_df.columns:

        data_df = data_df[
            data_df["Search Term"]
            .astype(str)
            .str.strip()
            != ""
        ]

    # -----------------------------------------------------
    # FORCE REQUIRED COLUMNS
    # -----------------------------------------------------

    for col in EXPECTED_HEADERS:

        if col not in data_df.columns:

            data_df[col] = ""

    return data_df


# =========================================================
# LINK HELPERS
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return ""

    text = str(text).strip()

    if text == "":
        return ""

    url = (
        "https://www.amazon.com/s?k="
        f"{quote_plus(text)}"
    )

    return (
        f'<a href="{url}" '
        f'target="_blank">{text}</a>'
    )


def make_asin_link(asin):

    if pd.isna(asin):
        return ""

    asin = str(asin).strip()

    if asin == "":
        return ""

    url = (
        f"https://www.amazon.com/dp/{asin}"
    )

    return (
        f'<a href="{url}" '
        f'target="_blank">{asin}</a>'
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

    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

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

            stop_words="english",

            ngram_range=ngram_range,

            min_df=min_freq
        )

        X = vectorizer.fit_transform(corpus)

        sums = np.array(
            X.sum(axis=0)
        ).flatten()

        words_freq = [

            (
                word,
                int(sums[idx])
            )

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

            columns=[
                "Phrase",
                "Frequency"
            ]
        )

    except:

        return pd.DataFrame(
            columns=[
                "Phrase",
                "Frequency"
            ]
        )


# =========================================================
# SMART CLUSTER ENGINE
# =========================================================

def build_clusters(trigram_df):

    cluster_rules = {

        "Pet Memorial": [
            "dog memorial",
            "cat memorial",
            "pet memorial",
            "rainbow bridge",
        ],

        "Memorial Gifts": [
            "memorial gifts",
            "sympathy gifts",
            "loss gifts",
        ],

        "Outdoor Memorial": [
            "garden",
            "wind chime",
            "stone",
            "solar",
        ],

        "Personalized Memorial": [
            "personalized",
            "custom",
            "engraved",
        ],

        "Funeral Service": [
            "funeral",
            "guest book",
            "sympathy",
        ]
    }

    rows = []

    for cluster_name, keywords in cluster_rules.items():

        total_freq = 0

        matched_phrases = []

        for _, row in trigram_df.iterrows():

            phrase = str(
                row["Phrase"]
            ).lower()

            freq = int(
                row["Frequency"]
            )

            for keyword in keywords:

                if keyword in phrase:

                    total_freq += freq

                    matched_phrases.append(
                        row["Phrase"]
                    )

                    break

        if total_freq > 0:

            if total_freq >= 50:
                competition = "High"

            elif total_freq >= 20:
                competition = "Medium"

            else:
                competition = "Low"

            opportunity = min(
                100,
                int(total_freq * 1.8)
            )

            if opportunity >= 90:
                action = "Launch Aggressively"

            elif opportunity >= 70:
                action = "High Potential"

            else:
                action = "Research Further"

            rows.append({

                "Cluster": cluster_name,

                "Main Signals": ", ".join(
                    list(set(matched_phrases))[:5]
                ),

                "Competition": competition,

                "Opportunity Score": opportunity,

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
# MAIN ENGINE
# =========================================================

def render_keyword_engine(final_df):

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload keyword CSV files to begin."
        )

        return

    # =====================================================
    # LOCAL HEADER FIX
    # =====================================================

    final_df = auto_fix_headers(final_df)

    # =====================================================
    # YEAR / QUARTER FIX
    # =====================================================

    if "Year" not in final_df.columns:

        final_df["Year"] = ""

    if "Quarter" not in final_df.columns:

        final_df["Quarter"] = ""

    # =====================================================
    # REPORTING DATE → QUARTER
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = pd.to_datetime(
            final_df["Reporting Date"],
            errors="coerce"
        )

        month_series = (
            final_df["Reporting Date"]
            .dt.month
        )

        final_df["Quarter"] = np.select(

            [
                month_series.isin([1,2,3]),
                month_series.isin([4,5,6]),
                month_series.isin([7,8,9]),
                month_series.isin([10,11,12]),
            ],

            [
                "Q1",
                "Q2",
                "Q3",
                "Q4",
            ],

            default=""
        )

    # =====================================================
    # BACKLINKS
    # =====================================================

    for col in final_df.columns:

        col_lower = col.lower()

        try:

            if "asin" in col_lower:

                final_df[col] = final_df[col].apply(
                    make_asin_link
                )

            elif (

                "search term" in col_lower
                or "brand" in col_lower
                or "category" in col_lower
            ):

                final_df[col] = final_df[col].apply(
                    make_search_link
                )

        except:
            pass

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("# Keyword Intelligence")

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
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter:

        filtered_df = filtered_df[
            filtered_df["Niche"].isin(
                niche_filter
            )
        ]

    if quarter_filter:

        filtered_df = filtered_df[
            filtered_df["Quarter"].isin(
                quarter_filter
            )
        ]

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
    # GRID
    # =====================================================

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

    # =====================================================
    # LINK RENDERER
    # =====================================================

    cell_renderer = JsCode("""

    class UrlCellRenderer {

      init(params) {

        this.eGui =
            document.createElement('div');

        this.eGui.innerHTML =
            params.value || "";
      }

      getGui() {

        return this.eGui;
      }
    }

    """)

    for col in filtered_df.columns:

        col_lower = col.lower()

        if (

            "asin" in col_lower
            or "search term" in col_lower
            or "brand" in col_lower
            or "category" in col_lower
        ):

            gb.configure_column(

                col,

                cellRenderer=cell_renderer
            )

    grid_options = gb.build()

    AgGrid(

        filtered_df,

        gridOptions=grid_options,

        theme="streamlit",

        height=720,

        allow_unsafe_jscode=True,

        update_mode=GridUpdateMode.NO_UPDATE,

        enable_enterprise_modules=False,

        reload_data=False,
    )

    # =====================================================
    # NLP SOURCE
    # =====================================================

    nlp_column = None

    candidate_columns = [

        "Search Term",
        "Keyword",
        "Keywords",
        "Title",
    ]

    for col in candidate_columns:

        if col in filtered_df.columns:

            nlp_column = col

            break

    if nlp_column is None:

        st.warning(
            "No NLP-compatible column found."
        )

        return

    # =====================================================
    # NLP SECTION
    # =====================================================

    st.markdown("---")

    st.markdown(
        "# NLP Market Intelligence"
    )

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

    corpus = (

        filtered_df[nlp_column]
        .astype(str)
        .apply(clean_text)
        .tolist()
    )

    single_word_df = extract_ngrams(
        corpus,
        (1,1),
        min_freq,
        top_n
    )

    bigram_df = extract_ngrams(
        corpus,
        (2,2),
        min_freq,
        top_n
    )

    trigram_df = extract_ngrams(
        corpus,
        (3,3),
        min_freq,
        top_n
    )

    cluster_df = build_clusters(
        trigram_df
    )

    # =====================================================
    # TABS
    # =====================================================

    t1, t2, t3, t4 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Cluster Intelligence"
    ])

    with t1:

        st.dataframe(
            single_word_df,
            use_container_width=True,
            height=600
        )

    with t2:

        st.dataframe(
            bigram_df,
            use_container_width=True,
            height=600
        )

    with t3:

        st.dataframe(
            trigram_df,
            use_container_width=True,
            height=600
        )

    with t4:

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=600
        )
