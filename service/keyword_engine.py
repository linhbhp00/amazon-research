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

    # =====================================================
    # HEADER ALREADY CORRECT
    # =====================================================

    if is_valid_keyword_header(df.columns):
        return df

    # =====================================================
    # FIRST ROW
    # =====================================================

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

    # =====================================================
    # SECOND ROW
    # =====================================================

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
# NORMALIZE SEARCH TERM
# =========================================================

def normalize_search_term(x):

    if pd.isna(x):
        return ""

    x = str(x)

    x = x.replace("[", "")
    x = x.replace("]", "")
    x = x.replace('"', "")
    x = x.replace("'", "")

    return x.strip().lower()


# =========================================================
# ASSIGN NICHE
# =========================================================

def assign_niche(df):

    if "Search Term" not in df.columns:
        return df

    df = df.copy()

    unique_terms = (
        df["Search Term"]
        .dropna()
        .astype(str)
        .unique()
    )

    if len(unique_terms) == 1:

        niche_value = unique_terms[0]

        df["Niche"] = niche_value

    else:

        df["Niche"] = (
            df["Search Term"]
            .astype(str)
            .apply(
                lambda x:
                x.split(" ")[0]
                if x.strip()
                else "unknown"
            )
        )

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

        return {
            "text": "",
            "url": "#"
        }

    text = str(text)

    return {
        "text": text,
        "url": f"https://www.amazon.com/s?k={quote_plus(text)}"
    }


# =========================================================
# ASIN LINK
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):

        return {
            "text": "",
            "url": "#"
        }

    asin = str(asin)

    return {
        "text": asin,
        "url": f"https://www.amazon.com/dp/{asin}"
    }


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

        dynamic_min_df = max(
            1,
            min(
                min_freq,
                int(len(corpus) * 0.01)
            )
        )

        vectorizer = CountVectorizer(
            ngram_range=ngram_range,
            stop_words="english",
            min_df=dynamic_min_df
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
# CLUSTER ENGINE
# =========================================================

def generate_cluster_insights(trigram_df):

    cluster_definitions = {

        "Pet Memorial": {
            "keywords": [
                "dog",
                "cat",
                "pet",
                "rainbow bridge",
            ],
            "emotion": "Pet Grief",
            "products": "Plaques, Frames, Wind Chimes",
        },

        "Family Loss": {
            "keywords": [
                "dad",
                "mom",
                "father",
                "mother",
                "loss",
            ],
            "emotion": "Grief/Nostalgia",
            "products": "Lanterns, Blankets, Jewelry",
        },

        "Outdoor Memorial Decor": {
            "keywords": [
                "garden",
                "stone",
                "wind chime",
                "plaque",
            ],
            "emotion": "Remembrance",
            "products": "Garden Decor, Solar Plaques",
        },

        "Funeral Service": {
            "keywords": [
                "funeral",
                "guest book",
                "cards",
            ],
            "emotion": "Sympathy",
            "products": "Guest Books, Signs",
        },

        "Personalized Memorial": {
            "keywords": [
                "personalized",
                "custom",
                "engraved",
            ],
            "emotion": "Memory",
            "products": "Custom Acrylic, Plaques",
        },
    }

    rows = []

    for _, config in cluster_definitions.items():

        total_freq = 0

        matched_phrases = []

        for _, row in trigram_df.iterrows():

            phrase = str(
                row["Phrase"]
            ).lower()

            for keyword in config["keywords"]:

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

            confidence = (
                "High Confidence"
                if total_freq >= 20
                else "Medium Confidence"
                if total_freq >= 8
                else "Low Confidence"
            )

            if opportunity_score >= 90:

                action = "Launch Aggressively"

            elif opportunity_score >= 75:

                action = "Scale Existing Products"

            elif opportunity_score >= 60:

                action = "Validate Market"

            else:

                action = "Research Further"

            rows.append({

                "Main Signals": ", ".join(
                    list(set(matched_phrases))[:5]
                ),

                "Emotion": config["emotion"],

                "Product Opportunities":
                config["products"],

                "Competition": competition,

                "Opportunity Score":
                opportunity_score,

                "Recommended Action":
                action,

                "Confidence":
                confidence
            })

    return pd.DataFrame(rows)


# =========================================================
# MARKET RECOMMENDATIONS
# =========================================================

def generate_market_recommendations(cluster_df):

    recommendations = []

    if cluster_df.empty:
        return recommendations

    for _, row in cluster_df.iterrows():

        score = row["Opportunity Score"]

        emotion = row["Emotion"]

        signals = row["Main Signals"]

        products = row["Product Opportunities"]

        competition = row["Competition"]

        confidence = row["Confidence"]

        # =================================================
        # HIGH DEMAND
        # =================================================

        if score >= 85:

            title = "High Demand Expansion"

            detail = (
                f"Strong demand detected around "
                f"{signals}. "
                f"Recommended products: {products}."
            )

            next_step = (
                "Scale product line and validate"
                " winning ASIN opportunities."
            )

        # =================================================
        # MID DEMAND
        # =================================================

        elif score >= 60:

            title = "Growth Opportunity"

            detail = (
                f"Moderate growth potential in "
                f"{emotion.lower()} niche."
            )

            next_step = (
                "Test low competition keyword variations"
                " and personalized bundles."
            )

        # =================================================
        # LOW DEMAND
        # =================================================

        else:

            title = "Emerging Demand"

            detail = (
                f"Early signals detected for "
                f"{signals}."
            )

            next_step = (
                "Monitor trend growth before scaling."
            )

        recommendations.append({

            "title": title,

            "detail": detail,

            "competition": competition,

            "next_step": next_step,

            "confidence": confidence
        })

    return recommendations


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

    # =====================================================
    # REMOVE DUPLICATE COLUMNS
    # =====================================================

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # SEARCH TERM NORMALIZE
    # =====================================================

    if "Search Term" in final_df.columns:

        final_df["Search Term"] = (
            final_df["Search Term"]
            .apply(normalize_search_term)
        )

    # =====================================================
    # NICHE FIX
    # =====================================================

    final_df = assign_niche(final_df)

    # =====================================================
    # DATE FIX
    # =====================================================

    if "Reporting Date" in final_df.columns:

        final_df["Reporting Date"] = (
            pd.to_datetime(
                final_df["Reporting Date"],
                errors="coerce"
            )
        )

        final_df["Year"] = (
            final_df["Reporting Date"]
            .dt.year
        )

        final_df["Month"] = (
            final_df["Reporting Date"]
            .dt.month
        )

        final_df["Quarter"] = (
            final_df["Month"]
            .apply(
                lambda x:
                f"Q{((x - 1)//3)+1}"
                if pd.notna(x)
                else None
            )
        )

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
            if "Niche" in final_df.columns
            else []
        )

    with col2:

        quarter_filter = st.multiselect(
            "Quarter",
            options=["Q1", "Q2", "Q3", "Q4"]
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

    if niche_filter and "Niche" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Niche"]
            .astype(str)
            .isin(niche_filter)
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
    # DISPLAY DATAFRAME
    # =====================================================

    display_df = filtered_df.copy()

    # =====================================================
    # SEARCH TERM LINKS
    # =====================================================

    if "Search Term" in display_df.columns:

        display_df["Search Term"] = (
            display_df["Search Term"]
            .apply(make_search_link)
        )

    # =====================================================
    # BRAND/CATEGORY LINKS
    # =====================================================

    for col in display_df.columns:

        col_lower = col.lower()

        if (
            "brand" in col_lower
            or "category" in col_lower
        ):

            display_df[col] = (
                display_df[col]
                .apply(make_search_link)
            )

    # =====================================================
    # ASIN LINKS
    # =====================================================

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
        "Unique Niches",
        filtered_df["Niche"].nunique()
        if "Niche" in filtered_df.columns
        else 0
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
    )

    # =====================================================
    # URL RENDERER
    # =====================================================

    cell_renderer = JsCode("""
    class UrlCellRenderer {

        init(params) {

            this.eGui = document.createElement('a');

            this.eGui.innerText = params.value?.text || '';

            this.eGui.setAttribute(
                'href',
                params.value?.url || '#'
            );

            this.eGui.setAttribute(
                'target',
                '_blank'
            );

            this.eGui.style.color = '#60a5fa';

            this.eGui.style.textDecoration = 'none';
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

    # =====================================================
    # AUTO FIT
    # =====================================================

    grid_options["onFirstDataRendered"] = JsCode("""
    function(params) {

        params.api.sizeColumnsToFit();

        setTimeout(() => {

            let allColumnIds = [];

            params.columnApi.getAllColumns().forEach(function(col) {
                allColumnIds.push(col.getId());
            });

            params.columnApi.autoSizeColumns(
                allColumnIds,
                false
            );

        }, 120);
    }
    """)

    AgGrid(
        display_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
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

    cluster_df = generate_cluster_insights(
        trigram_df
    )

    # =====================================================
    # CONFIDENCE CHECK
    # =====================================================

    if cluster_df.empty:

        st.warning(
            "Dataset too small or weak for strategic insights."
        )

    # =====================================================
    # METRICS
    # =====================================================

    st.markdown(
        "## Strategic Market Intelligence"
    )

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
        "Market Signals",
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

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        st.markdown("## Research Recommendations")

        recommendations = (
            generate_market_recommendations(
                cluster_df
            )
        )

        if not recommendations:

            st.info(
                "No strong market opportunities detected yet."
            )

        for r in recommendations:

            st.markdown(f"""
            <div style="
                padding:16px;
                margin-bottom:12px;
                border-radius:12px;
                background:#0b1220;
                border:1px solid #1f2937;
            ">

            <div style="
                font-size:18px;
                font-weight:700;
                margin-bottom:8px;
                color:#f8fafc;
            ">
            {r['title']}
            </div>

            <div style="
                color:#cbd5e1;
                margin-bottom:10px;
                line-height:1.6;
            ">
            {r['detail']}
            </div>

            <div style="
                margin-bottom:8px;
                color:#93c5fd;
                font-size:14px;
            ">
            Opportunity Level: {r['competition']}
            </div>

            <div style="
                margin-bottom:8px;
                color:#86efac;
                font-size:14px;
            ">
            Recommended Next Step:
            {r['next_step']}
            </div>

            <div style="
                color:#facc15;
                font-size:13px;
            ">
            Insight Confidence:
            {r['confidence']}
            </div>

            </div>
            """, unsafe_allow_html=True)
