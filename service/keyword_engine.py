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

    score = 0

    for expected in EXPECTED_KEYWORD_COLUMNS:

        if expected in cols:
            score += 1

    return score >= 2


# =========================================================
# AUTO HEADER FIX
# =========================================================

def auto_fix_keyword_headers(df):

    if df is None or df.empty:
        return df

    # ==========================================
    # CASE 1
    # HEADER ALREADY CORRECT
    # ==========================================

    if is_valid_keyword_header(df.columns):
        return df

    # ==========================================
    # CASE 2
    # HEADER IN FIRST ROW
    # ==========================================

    first_row = (
        df.iloc[0]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if is_valid_keyword_header(first_row):

        fixed_df = df.copy()

        fixed_df.columns = first_row

        fixed_df = fixed_df.iloc[1:].reset_index(drop=True)

        return fixed_df

    # ==========================================
    # CASE 3
    # HEADER IN SECOND ROW
    # ==========================================

    if len(df) > 1:

        second_row = (
            df.iloc[1]
            .fillna("")
            .astype(str)
            .tolist()
        )

        if is_valid_keyword_header(second_row):

            fixed_df = df.copy()

            fixed_df.columns = second_row

            fixed_df = fixed_df.iloc[2:].reset_index(drop=True)

            return fixed_df

    return df


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
# SEARCH LINK
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return text

    original_text = str(text)

    return f"""
    <a href="https://www.amazon.com/s?k={quote_plus(original_text)}"
    target="_blank"
    style="color:#60a5fa;text-decoration:none;font-weight:500;">
    {original_text}
    </a>
    """


# =========================================================
# ASIN LINK
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):
        return asin

    asin = str(asin)

    return f"""
    <a href="https://www.amazon.com/dp/{asin}"
    target="_blank"
    style="color:#60a5fa;text-decoration:none;font-weight:500;">
    {asin}
    </a>
    """


# =========================================================
# EXTRACT NGRAMS
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
# SMART NICHE FILTER
# =========================================================

def build_smart_niche_options(single_word_df):

    if single_word_df.empty:
        return []

    blacklist = {

        "gift",
        "gifts",
        "best",
        "new",
        "home",
        "decor",
        "set",
        "custom",
        "personalized",
        "amazon",
        "product",
        "products",
        "for",
        "and",
        "the",
        "with",
    }

    niche_words = []

    for _, row in single_word_df.iterrows():

        word = str(row["Phrase"]).lower()

        freq = int(row["Frequency"])

        if word in blacklist:
            continue

        if freq < 2:
            continue

        if len(word) <= 2:
            continue

        niche_words.append(word)

    return sorted(list(set(niche_words)))


# =========================================================
# MARKET INSIGHTS ENGINE
# =========================================================

def generate_market_insights(trigram_df):

    rows = []

    for _, row in trigram_df.iterrows():

        phrase = str(row["Phrase"])

        freq = int(row["Frequency"])

        # =====================================
        # COMPETITION
        # =====================================

        if freq >= 15:
            competition = "High"

        elif freq >= 7:
            competition = "Medium"

        else:
            competition = "Low"

        # =====================================
        # SCORE
        # =====================================

        opportunity_score = min(
            100,
            int(freq * 8)
        )

        # =====================================
        # DEMAND
        # =====================================

        if opportunity_score >= 85:

            demand = "Strong Market Demand"

            growth = (
                "Scale aggressively with bundles, variants, and personalization."
            )

            action = (
                "Launch expanded product line and dominate search volume."
            )

        elif opportunity_score >= 65:

            demand = "Growing Demand"

            growth = (
                "Expand keyword coverage and test adjacent products."
            )

            action = (
                "Validate profitable ASIN opportunities."
            )

        else:

            demand = "Emerging Opportunity"

            growth = (
                "Research niche depth and seasonal behavior."
            )

            action = (
                "Test low-competition listings before scaling."
            )

        rows.append({

            "Main Signals": phrase,

            "Emotion": demand,

            "Product Opportunities": growth,

            "Competition": competition,

            "Opportunity Score": opportunity_score,

            "Action": action
        })

    return pd.DataFrame(rows)


# =========================================================
# MAIN ENGINE
# =========================================================

def render_keyword_engine(final_df):

    st.markdown("# Keyword Intelligence")

    # =====================================================
    # EMPTY
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload keyword CSV files to begin."
        )

        return

    # =====================================================
    # HEADER FIX
    # =====================================================

    final_df = auto_fix_keyword_headers(
        final_df
    )

    # remove duplicate columns
    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # DATE ENGINE
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = (
            pd.to_datetime(
                final_df["Reporting Date"],
                errors="coerce"
            )
        )

        final_df["Month"] = (
            final_df["Reporting Date"]
            .dt.month
        )

        final_df["Quarter"] = (
            final_df["Month"]
            .apply(
                lambda x:
                f"Q{int(((int(x)-1)//3)+1)}"
                if pd.notna(x)
                else None
            )
        )

        final_df["Year"] = (
            final_df["Reporting Date"]
            .dt.year
            .fillna(0)
            .astype(int)
            .astype(str)
        )

        final_df["Year"] = (
            final_df["Year"]
            .replace("0", np.nan)
        )

    # =====================================================
    # NLP SOURCE
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

        if col in final_df.columns:

            nlp_source_column = col

            break

    if nlp_source_column is None:

        st.warning(
            "No NLP-compatible column found."
        )

        return

    # =====================================================
    # NLP SETTINGS
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
        final_df[nlp_source_column]
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
    # MARKET INSIGHTS
    # =====================================================

    cluster_df = generate_market_insights(
        trigram_df
    )

    # =====================================================
    # SMART NICHE OPTIONS
    # =====================================================

    smart_niche_options = (
        build_smart_niche_options(
            single_word_df
        )
    )

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        niche_filter = st.multiselect(
            "Niche Intelligence",
            options=smart_niche_options
        )

    with col2:

        quarter_filter = st.multiselect(
            "Quarter",
            options=sorted(
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
            options=sorted(
                final_df["Year"]
                .dropna()
                .astype(str)
                .unique()
            )
            if "Year" in final_df.columns
            else []
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if niche_filter:

        pattern = "|".join(niche_filter)

        filtered_df = filtered_df[
            filtered_df["Search Term"]
            .astype(str)
            .str.contains(
                pattern,
                case=False,
                na=False
            )
        ]

    if quarter_filter and "Quarter" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Quarter"]
            .astype(str)
            .isin(quarter_filter)
        ]

    if year_filter and "Year" in filtered_df.columns:

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
    # AMAZON LINKS
    # =====================================================

    display_df = filtered_df.copy()

    if "Search Term" in display_df.columns:

        display_df["Search Term"] = (
            display_df["Search Term"]
            .apply(make_search_link)
        )

    for col in display_df.columns:

        col_lower = col.lower()

        if "brand" in col_lower:

            display_df[col] = (
                display_df[col]
                .apply(make_search_link)
            )

        if "category" in col_lower:

            display_df[col] = (
                display_df[col]
                .apply(make_search_link)
            )

    for col in display_df.columns:

        if "asin" in col.lower():

            display_df[col] = (
                display_df[col]
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
        "Market Signals",
        len(smart_niche_options)
    )

    # =====================================================
    # DATASET TABLE
    # =====================================================

    st.markdown("## Keyword Dataset")

    gb = GridOptionsBuilder.from_dataframe(
        display_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
    
        # auto fit
        flex=1,
        minWidth=120,
    
        # tránh xuống dòng
        wrapText=False,
        autoHeight=False,
    )
    
    cell_renderer = JsCode("""
    class UrlCellRenderer {
      init(params) {
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = params.value || '';
      }

      getGui() {
        return this.eGui;
      }
    }
    """)

    for col in display_df.columns:

        col_lower = col.lower()

        if (
            "search term" in col_lower
            or "brand" in col_lower
            or "category" in col_lower
            or "asin" in col_lower
        ):

            gb.configure_column(
                col,
                cellRenderer=cell_renderer
            )

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    AgGrid(
        display_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        columns_auto_size_mode="FIT_CONTENTS",
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
    )

    # =====================================================
    # NLP ENGINE
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence")

    # =====================================================
    # METRICS
    # =====================================================

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

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
        "Market Insights",
        len(cluster_df)
    )

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Market Intelligence"

    ])

    # =====================================================
    # SINGLE WORD
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
    # MARKET INTELLIGENCE
    # =====================================================

    with tab4:

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=700
        )

        # =====================================================
        # RESEARCH RECOMMENDATIONS
        # =====================================================

        st.markdown(
            "## Research Recommendations"
        )

        recommendations = [

            {
                "title": "High Demand Expansion",
                "desc": (
                    "Scale proven high-frequency keywords into adjacent products and bundles."
                )
            },

            {
                "title": "Low Competition Opportunities",
                "desc": (
                    "Target emerging long-tail phrases with lower seller saturation."
                )
            },

            {
                "title": "Personalization Strategy",
                "desc": (
                    "Test custom, engraved, and POD product variations to improve conversion."
                )
            },

            {
                "title": "ASIN Growth Potential",
                "desc": (
                    "Validate top-performing search intent with additional listing variations."
                )
            },

            {
                "title": "Seasonal Demand Intelligence",
                "desc": (
                    "Monitor quarter-based trends to identify scalable seasonal demand."
                )
            },
        ]

        for rec in recommendations:

            st.markdown(
                f"""
                <div style="
                    padding:18px;
                    margin-bottom:12px;
                    border-radius:14px;
                    background:#0b1220;
                    border:1px solid #1f2937;
                ">

                <div style="
                    font-size:18px;
                    font-weight:700;
                    color:#f8fafc;
                    margin-bottom:6px;
                ">
                    {rec['title']}
                </div>

                <div style="
                    font-size:14px;
                    color:#cbd5e1;
                    line-height:1.6;
                ">
                    {rec['desc']}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )
