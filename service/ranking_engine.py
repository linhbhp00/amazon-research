# =========================================================
# service/ranking_engine.py
# =========================================================

import re
import streamlit as st
import pandas as pd
import numpy as np

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# CLEAN NUMERIC
# =========================================================

def clean_numeric(value):

    try:

        if pd.isna(value):
            return 0

        value = str(value)

        value = (
            value
            .replace(",", "")
            .replace("$", "")
            .replace("%", "")
            .strip()
        )

        return float(value)

    except:

        return 0


# =========================================================
# CLASSIFY KEYWORD
# =========================================================

def classify_keyword(row):

    try:

        search_volume = float(
            row.get("Search Volume", 0)
        )

        iq_score = float(
            row.get("Cerebro IQ Score", 0)
        )

        cpc = float(
            row.get("H10 PPC Sugg. Bid", 0)
        )

        competing = float(
            row.get("Competing Products", 0)
        )

        trend = float(
            row.get("Search Volume Trend", 0)
        )

        # =================================================
        # EASY WIN
        # =================================================

        if (
            search_volume >= 3000
            and iq_score >= 1000
            and cpc <= 1.5
            and competing <= 5000
        ):

            return "Easy Win"

        # =================================================
        # BUILD RANK
        # =================================================

        elif (
            search_volume >= 5000
            and trend > 0
            and iq_score >= 700
        ):

            return "Build Rank"

        # =================================================
        # HIGH COMPETITION
        # =================================================

        elif (
            competing >= 20000
            or cpc >= 3
        ):

            return "High Competition"

        # =================================================
        # TRENDING
        # =================================================

        elif trend >= 15:

            return "Trending"

        return "Mid Opportunity"

    except:

        return "Unknown"


# =========================================================
# SCORE KEYWORD
# =========================================================

def score_keyword(row):

    try:

        sv = float(
            row.get("Search Volume", 0)
        )

        iq = float(
            row.get("Cerebro IQ Score", 0)
        )

        cpc = float(
            row.get("H10 PPC Sugg. Bid", 0)
        )

        comp = float(
            row.get("Competing Products", 0)
        )

        trend = float(
            row.get("Search Volume Trend", 0)
        )

        score = (
            (sv * 0.30)
            + (iq * 0.35)
            + (trend * 0.20)
            - (cpc * 200)
            - (comp * 0.01)
        )

        return round(score, 2)

    except:

        return 0


# =========================================================
# NORMALIZE KEYWORD
# =========================================================

def normalize_keyword(keyword):

    keyword = str(keyword).lower()

    keyword = re.sub(
        r"[^a-z0-9\s]",
        " ",
        keyword
    )

    keyword = re.sub(
        r"\s+",
        " ",
        keyword
    )

    return keyword.strip()


# =========================================================
# KEYWORD CLUSTER ENGINE
# =========================================================

def detect_cluster(keyword):

    keyword = normalize_keyword(keyword)

    # =====================================================
    # CLUSTER RULES
    # =====================================================

    cluster_rules = {

        # =================================================
        # DOG COLLAR
        # =================================================

        "Dog Collar": [

            "dog collar",
            "puppy collar",
            "pet collar",
            "martingale collar",
            "leather dog collar",
            "personalized dog collar",
            "gps dog collar",
            "shock collar",

        ],

        # =================================================
        # DOG LEASH
        # =================================================

        "Dog Leash": [

            "dog leash",
            "pet leash",
            "retractable leash",
            "puppy leash",
            "training leash",

        ],

        # =================================================
        # DOG DNA
        # =================================================

        "Dog DNA Testing": [

            "dog dna",
            "dna test",
            "dog breed identification",
            "breed identification",
            "dog breed test",
            "dna kit",
            "dog ancestry",

        ],

        # =================================================
        # PET MEMORIAL
        # =================================================

        "Pet Memorial": [

            "pet memorial",
            "dog memorial",
            "cat memorial",
            "pet loss",
            "sympathy gift",
            "rainbow bridge",

        ],

        # =================================================
        # PET TOY
        # =================================================

        "Pet Toys": [

            "dog toy",
            "cat toy",
            "pet toy",
            "chew toy",
            "squeaky toy",

        ],

        # =================================================
        # PET BED
        # =================================================

        "Pet Bed": [

            "dog bed",
            "cat bed",
            "pet bed",

        ],

        # =================================================
        # PET FEEDING
        # =================================================

        "Pet Feeding": [

            "dog bowl",
            "cat bowl",
            "food bowl",
            "pet feeder",
            "slow feeder",

        ],

        # =================================================
        # BABY REGISTRY
        # =================================================

        "Baby Registry": [

            "baby registry",
            "baby shower registry",
            "newborn registry",

        ],

        # =================================================
        # GIFT CARD
        # =================================================

        "Gift Card": [

            "gift card",
            "amazon card",
            "visa gift card",

        ],

        # =================================================
        # BLANKET
        # =================================================

        "Blanket": [

            "blanket",
            "throw blanket",
            "weighted blanket",
            "baby blanket",

        ],

        # =================================================
        # MUG
        # =================================================

        "Mug": [

            "mug",
            "coffee mug",
            "tea mug",

        ],

        # =================================================
        # SHIRT
        # =================================================

        "Shirt": [

            "shirt",
            "hoodie",
            "sweatshirt",
            "tshirt",

        ],

        # =================================================
        # JEWELRY
        # =================================================

        "Jewelry": [

            "necklace",
            "bracelet",
            "ring",
            "earring",

        ],

        # =================================================
        # HOME DECOR
        # =================================================

        "Home Decor": [

            "home decor",
            "wall art",
            "canvas",
            "wood sign",

        ],
    }

    # =====================================================
    # MATCH
    # =====================================================

    for cluster, phrases in cluster_rules.items():

        for phrase in phrases:

            if phrase in keyword:

                return cluster

    # =====================================================
    # SMART FALLBACK
    # =====================================================

    words = keyword.split()

    if len(words) >= 3:

        return " ".join(
            word.capitalize()
            for word in words[:3]
        )

    if len(words) >= 2:

        return " ".join(
            word.capitalize()
            for word in words[:2]
        )

    return "General"


# =========================================================
# ACTION
# =========================================================

def get_action(classification):

    classification = str(classification)

    if classification == "Easy Win":
        return "Scale"

    if classification == "Build Rank":
        return "Launch"

    if classification == "Trending":
        return "Monitor"

    if classification == "High Competition":
        return "Avoid"

    if classification == "Mid Opportunity":
        return "Research"

    return "Analyze"


# =========================================================
# STRATEGY
# =========================================================

def get_strategy(action):

    action = str(action)

    if action == "Scale":

        return (
            "High opportunity keyword. "
            "Scale aggressively."
        )

    if action == "Launch":

        return (
            "Strong ranking potential. "
            "Build ranking campaign."
        )

    if action == "Monitor":

        return (
            "Trend detected. "
            "Monitor search growth."
        )

    if action == "Avoid":

        return (
            "Competition too high."
        )

    if action == "Research":

        return (
            "Requires deeper validation."
        )

    return (
        "Analyze manually."
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def render_ranking_engine(final_df):

    st.markdown("# Ranking Intelligence")

    # =====================================================
    # EMPTY
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload Ranking CSV files."
        )

        return

    # =====================================================
    # CLEAN COLUMNS
    # =====================================================

    final_df.columns = [

        str(col).strip()
        for col in final_df.columns

    ]

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # NUMERIC CLEAN
    # =====================================================

    numeric_cols = [

        "Search Volume",
        "Search Volume Trend",
        "Cerebro IQ Score",
        "H10 PPC Sugg. Bid",
        "Competing Products",
        "CPR",
        "Title Density",
        "Keyword Sales",
        "Organic Rank",
        "Sponsored Rank",

    ]

    for col in numeric_cols:

        if col in final_df.columns:

            final_df[col] = (
                final_df[col]
                .apply(clean_numeric)
            )

    # =====================================================
    # CLUSTER
    # =====================================================

    if "Keyword Phrase" in final_df.columns:

        final_df["Cluster"] = (
            final_df["Keyword Phrase"]
            .apply(detect_cluster)
        )

    else:

        final_df["Cluster"] = "General"

    # =====================================================
    # SCORE
    # =====================================================

    final_df["Opportunity Score"] = (
        final_df.apply(
            score_keyword,
            axis=1
        )
    )

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    final_df["Keyword Classification"] = (
        final_df.apply(
            classify_keyword,
            axis=1
        )
    )

    # =====================================================
    # ACTION
    # =====================================================

    final_df["Action"] = (
        final_df[
            "Keyword Classification"
        ]
        .apply(get_action)
    )

    # =====================================================
    # STRATEGY
    # =====================================================

    final_df["Strategy"] = (
        final_df["Action"]
        .apply(get_strategy)
    )

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        classification_filter = st.multiselect(
            "Keyword Classification",
            options=sorted(
                final_df[
                    "Keyword Classification"
                ]
                .dropna()
                .unique()
            )
        )

    with c2:

        cluster_filter = st.multiselect(
            "Cluster",
            options=sorted(
                final_df[
                    "Cluster"
                ]
                .dropna()
                .unique()
            )
        )

    with c3:

        action_filter = st.multiselect(
            "Action",
            options=sorted(
                final_df[
                    "Action"
                ]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search keyword..."
    )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if classification_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Keyword Classification"
            ]
            .isin(classification_filter)
        ]

    if cluster_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Cluster"
            ]
            .isin(cluster_filter)
        ]

    if action_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Action"
            ]
            .isin(action_filter)
        ]

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
        "Keywords",
        f"{len(filtered_df):,}"
    )

    m2.metric(
        "Easy Win",
        len(
            filtered_df[
                filtered_df[
                    "Keyword Classification"
                ] == "Easy Win"
            ]
        )
    )

    m3.metric(
        "Build Rank",
        len(
            filtered_df[
                filtered_df[
                    "Keyword Classification"
                ] == "Build Rank"
            ]
        )
    )

    m4.metric(
        "Trending",
        len(
            filtered_df[
                filtered_df[
                    "Keyword Classification"
                ] == "Trending"
            ]
        )
    )

    # =====================================================
    # DATASET
    # =====================================================

    st.markdown(
        "## Ranking Intelligence Dataset"
    )

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        wrapText=False,
        autoHeight=False,
    )

    gb.configure_grid_options(
        domLayout="normal"
    )

    for col in filtered_df.columns:

        gb.configure_column(
            col,
            flex=1,
            minWidth=140,
        )

    # =====================================================
    # FREEZE KEYWORD
    # =====================================================

    if "Keyword Phrase" in filtered_df.columns:

        gb.configure_column(
            "Keyword Phrase",
            pinned="left",
            minWidth=320,
            flex=2,
        )

    # =====================================================
    # COLOR STYLES
    # =====================================================

    classification_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {};
        }

        if (params.value == 'Easy Win') {
            return {
                backgroundColor: '#14532d',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'Build Rank') {
            return {
                backgroundColor: '#1d4ed8',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'Trending') {
            return {
                backgroundColor: '#7c3aed',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'High Competition') {
            return {
                backgroundColor: '#7f1d1d',
                color: 'white',
                fontWeight: '700'
            };
        }

        return {
            backgroundColor: '#374151',
            color: 'white',
            fontWeight: '700'
        };
    }
    """)

    action_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {};
        }

        if (params.value == 'Scale') {
            return {
                backgroundColor: '#15803d',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'Launch') {
            return {
                backgroundColor: '#1d4ed8',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'Monitor') {
            return {
                backgroundColor: '#7c3aed',
                color: 'white',
                fontWeight: '700'
            };
        }

        if (params.value == 'Avoid') {
            return {
                backgroundColor: '#7f1d1d',
                color: 'white',
                fontWeight: '700'
            };
        }

        return {
            backgroundColor: '#374151',
            color: 'white',
            fontWeight: '700'
        };
    }
    """)

    gb.configure_column(
        "Keyword Classification",
        cellStyle=classification_style,
        minWidth=190,
    )

    gb.configure_column(
        "Action",
        cellStyle=action_style,
        minWidth=140,
    )

    # =====================================================
    # GRID
    # =====================================================

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=760,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        reload_data=False,
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown(
        "## Keyword Opportunity Intelligence"
    )

    insight_df = (
        filtered_df
        .groupby(
            [
                "Keyword Classification",
                "Cluster",
            ]
        )
        .agg({

            "Keyword Phrase": "count",
            "Opportunity Score": "mean",
            "Search Volume": "mean",
            "H10 PPC Sugg. Bid": "mean",

        })
        .reset_index()
    )

    insight_df.columns = [

        "Classification",
        "Cluster",
        "Keyword Count",
        "Avg Opportunity Score",
        "Avg Search Volume",
        "Avg CPC",

    ]

    insight_df = insight_df.sort_values(
        by="Keyword Count",
        ascending=False
    )

    st.dataframe(
        insight_df,
        use_container_width=True,
        height=420
    )

    # =====================================================
    # TOP KEYWORDS
    # =====================================================

    st.markdown(
        "## Top Opportunity Keywords"
    )

    top_keywords = (
        filtered_df
        .sort_values(
            by="Opportunity Score",
            ascending=False
        )
        .head(50)
    )

    display_cols = [

        "Keyword Phrase",
        "Cluster",
        "Keyword Classification",
        "Search Volume",
        "Cerebro IQ Score",
        "H10 PPC Sugg. Bid",
        "Competing Products",
        "Opportunity Score",
        "Action",

    ]

    display_cols = [
        col for col in display_cols
        if col in top_keywords.columns
    ]

    st.dataframe(
        top_keywords[
            display_cols
        ],
        use_container_width=True,
        height=420
    )
