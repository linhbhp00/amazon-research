from utils.csv_utils import read_csv_safe
import streamlit as st
import pandas as pd
import numpy as np
import re

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# HELPERS
# =========================================================

def safe_numeric(series):

    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "")
        .str.replace("$", "")
        .str.replace("%", "")
        .str.strip(),
        errors="coerce"
    )

# =========================================================
# CLEAN TEXT
# =========================================================

def clean_keyword(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================================================
# DEMAND CLASSIFIER
# =========================================================

def classify_demand(search_volume):

    if pd.isna(search_volume):
        return "Unknown"

    if search_volume >= 50000:
        return "Massive Demand"

    elif search_volume >= 20000:
        return "High Demand"

    elif search_volume >= 5000:
        return "Medium Demand"

    return "Low Demand"

# =========================================================
# COMPETITION CLASSIFIER
# =========================================================

def classify_competition(competing_products):

    if pd.isna(competing_products):
        return "Unknown"

    if competing_products >= 50000:
        return "Extreme"

    elif competing_products >= 20000:
        return "High"

    elif competing_products >= 5000:
        return "Medium"

    return "Low"

# =========================================================
# OPPORTUNITY SCORE
# =========================================================

def calculate_opportunity(row):

    iq_score = row.get("Cerebro IQ Score", 0)
    search_volume = row.get("Search Volume", 0)
    competing_products = row.get("Competing Products", 0)
    title_density = row.get("Title Density", 0)
    cpr = row.get("CPR", 0)

    if pd.isna(iq_score):
        iq_score = 0

    if pd.isna(search_volume):
        search_volume = 0

    if pd.isna(competing_products):
        competing_products = 0

    if pd.isna(title_density):
        title_density = 0

    if pd.isna(cpr):
        cpr = 0

    # =====================================================
    # FORMULA
    # =====================================================

    score = (
        (iq_score * 0.4)
        + (search_volume / 1000 * 0.3)
        - (competing_products / 10000 * 0.2)
        - (title_density * 0.5)
        - (cpr * 0.1)
    )

    return round(score, 2)

# =========================================================
# RANKING DECISION
# =========================================================

def ranking_decision(row):

    score = row["Opportunity Score"]

    competition = row["Competition Level"]

    if score >= 40 and competition in ["Low", "Medium"]:

        return "Aggressive Rank"

    elif score >= 20:

        return "Good Opportunity"

    elif competition == "Extreme":

        return "Hard Competition"

    return "Avoid"

# =========================================================
# PRODUCT TYPE DETECTOR
# =========================================================

def detect_product_type(keyword):

    keyword = str(keyword).lower()

    mapping = {

        # memorial
        "wind chime": "Outdoor Decor",
        "garden stone": "Outdoor Decor",
        "plaque": "Outdoor Decor",
        "lantern": "Decor",

        # gifts
        "gift": "Gift",
        "blanket": "Blanket",
        "jewelry": "Jewelry",

        # pet
        "dog": "Pet Memorial",
        "cat": "Pet Memorial",
        "pet": "Pet Memorial",

        # personalized
        "personalized": "Personalized",
        "custom": "Personalized",
        "engraved": "Personalized",
    }

    for key, value in mapping.items():

        if key in keyword:
            return value

    return "General"

# =========================================================
# DEMAND INTENT DETECTOR
# =========================================================

def detect_intent(keyword):

    keyword = str(keyword).lower()

    if "best" in keyword:
        return "Commercial"

    if "buy" in keyword:
        return "Transactional"

    if "how" in keyword:
        return "Informational"

    if "review" in keyword:
        return "Research"

    if "cheap" in keyword:
        return "Budget"

    if "gift" in keyword:
        return "Gift Intent"

    return "General"

# =========================================================
# ENGINE
# =========================================================

def render_ranking_engine():

    st.markdown("## Keyword Ranking Intelligence")

    uploaded_file = st.file_uploader(
        "Upload Keyword Ranking CSV",
        type=["csv"],
        key="ranking_engine"
    )

    if uploaded_file is None:

        st.info("Upload ranking keyword CSV.")
        return

    # =====================================================
    # LOAD CSV
    # =====================================================

    try:

        df = pd.read_csv(uploaded_file)

    except:

        uploaded_file.seek(0)

        df = pd.read_csv(
            uploaded_file,
            encoding="latin1"
        )

    # =====================================================
    # CLEAN COLUMNS
    # =====================================================

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    required_columns = [
        "Keyword Phrase",
        "Cerebro IQ Score",
        "Search Volume",
        "Search Volume Trend",
        "H10 PPC Sugg. Bid",
        "Competing Products",
        "CPR",
        "Title Density",
        "Organic Rank",
    ]

    missing_cols = [
        col for col in required_columns
        if col not in df.columns
    ]

    if len(missing_cols) > 0:

        st.error(
            f"Missing columns: {missing_cols}"
        )

        return

    # =====================================================
    # CLEAN NUMERIC
    # =====================================================

    numeric_cols = [
        "Cerebro IQ Score",
        "Search Volume",
        "Search Volume Trend",
        "H10 PPC Sugg. Bid",
        "Competing Products",
        "CPR",
        "Title Density",
        "Organic Rank",
        "Sponsored Rank",
        "Keyword Sales",
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = safe_numeric(
                df[col]
            )

    # =====================================================
    # CLEAN KW
    # =====================================================

    df["Keyword Clean"] = df[
        "Keyword Phrase"
    ].apply(clean_keyword)

    # =====================================================
    # DEMAND
    # =====================================================

    df["Demand Level"] = df[
        "Search Volume"
    ].apply(classify_demand)

    # =====================================================
    # COMPETITION
    # =====================================================

    df["Competition Level"] = df[
        "Competing Products"
    ].apply(classify_competition)

    # =====================================================
    # PRODUCT TYPE
    # =====================================================

    df["Product Type"] = df[
        "Keyword Phrase"
    ].apply(detect_product_type)

    # =====================================================
    # SEARCH INTENT
    # =====================================================

    df["Search Intent"] = df[
        "Keyword Phrase"
    ].apply(detect_intent)

    # =====================================================
    # OPPORTUNITY SCORE
    # =====================================================

    df["Opportunity Score"] = df.apply(
        calculate_opportunity,
        axis=1
    )

    # =====================================================
    # RANKING ACTION
    # =====================================================

    df["Ranking Strategy"] = df.apply(
        ranking_decision,
        axis=1
    )

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        demand_filter = st.multiselect(
            "Demand Level",
            options=sorted(
                df["Demand Level"]
                .dropna()
                .unique()
            )
        )

    with col2:

        competition_filter = st.multiselect(
            "Competition Level",
            options=sorted(
                df["Competition Level"]
                .dropna()
                .unique()
            )
        )

    with col3:

        strategy_filter = st.multiselect(
            "Ranking Strategy",
            options=sorted(
                df["Ranking Strategy"]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # FILTERED DF
    # =====================================================

    filtered_df = df.copy()

    if demand_filter:

        filtered_df = filtered_df[
            filtered_df["Demand Level"]
            .isin(demand_filter)
        ]

    if competition_filter:

        filtered_df = filtered_df[
            filtered_df["Competition Level"]
            .isin(competition_filter)
        ]

    if strategy_filter:

        filtered_df = filtered_df[
            filtered_df["Ranking Strategy"]
            .isin(strategy_filter)
        ]

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total Keywords",
        len(filtered_df)
    )

    m2.metric(
        "Avg IQ Score",
        round(
            filtered_df["Cerebro IQ Score"]
            .mean(),
            0
        )
    )

    m3.metric(
        "Aggressive Rank",
        len(
            filtered_df[
                filtered_df["Ranking Strategy"]
                == "Aggressive Rank"
            ]
        )
    )

    m4.metric(
        "Hard Competition",
        len(
            filtered_df[
                filtered_df["Ranking Strategy"]
                == "Hard Competition"
            ]
        )
    )

    # =====================================================
    # STYLE JS
    # =====================================================

    ranking_style = JsCode("""
    function(params) {

        if (params.value == 'Aggressive Rank') {
            return {
                'backgroundColor': '#22c55e',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Good Opportunity') {
            return {
                'backgroundColor': '#facc15',
                'color': 'black',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Hard Competition') {
            return {
                'backgroundColor': '#ef4444',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Avoid') {
            return {
                'backgroundColor': '#7f1d1d',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }
    }
    """)

    # =====================================================
    # GRID
    # =====================================================

    display_cols = [
        "Keyword Phrase",
        "Product Type",
        "Search Intent",
        "Demand Level",
        "Competition Level",
        "Cerebro IQ Score",
        "Search Volume",
        "Search Volume Trend",
        "Competing Products",
        "CPR",
        "Title Density",
        "H10 PPC Sugg. Bid",
        "Organic Rank",
        "Opportunity Score",
        "Ranking Strategy",
    ]

    grid_df = filtered_df[
        display_cols
    ].copy()

    gb = GridOptionsBuilder.from_dataframe(
        grid_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
    )

    gb.configure_column(
        "Ranking Strategy",
        cellStyle=ranking_style
    )

    gb.configure_column(
        "Keyword Phrase",
        pinned="left",
        width=320
    )

    gb.configure_column(
        "Opportunity Score",
        width=140
    )

    grid_options = gb.build()

    grid_options["rowHeight"] = 42

    # =====================================================
    # TABLE
    # =====================================================

    st.markdown("## Ranking Intelligence Dashboard")

    AgGrid(
        grid_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=850,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("---")
    st.markdown("## Strategic Keyword Insights")

    # =====================================================
    # TOP KW
    # =====================================================

    aggressive_df = filtered_df[
        filtered_df["Ranking Strategy"]
        == "Aggressive Rank"
    ].sort_values(
        by="Opportunity Score",
        ascending=False
    )

    st.markdown("### Top Keywords To Rank")

    st.dataframe(
        aggressive_df[
            [
                "Keyword Phrase",
                "Product Type",
                "Demand Level",
                "Competition Level",
                "Opportunity Score",
            ]
        ].head(20),
        use_container_width=True,
        height=400
    )

    # =====================================================
    # HARD KW
    # =====================================================

    hard_df = filtered_df[
        filtered_df["Ranking Strategy"]
        == "Hard Competition"
    ].sort_values(
        by="Competing Products",
        ascending=False
    )

    st.markdown("### Difficult Keywords")

    st.dataframe(
        hard_df[
            [
                "Keyword Phrase",
                "Search Volume",
                "Competing Products",
                "Title Density",
                "Competition Level",
            ]
        ].head(20),
        use_container_width=True,
        height=400
    )

    # =====================================================
    # CLUSTER INSIGHTS
    # =====================================================

    st.markdown("## Product Type Insights")

    cluster_df = (
        filtered_df.groupby("Product Type")
        .agg({
            "Search Volume": "mean",
            "Opportunity Score": "mean",
            "Keyword Phrase": "count",
        })
        .reset_index()
    )

    cluster_df.columns = [
        "Product Type",
        "Avg Search Volume",
        "Avg Opportunity",
        "Keyword Count",
    ]

    cluster_df = cluster_df.sort_values(
        by="Avg Opportunity",
        ascending=False
    )

    st.dataframe(
        cluster_df,
        use_container_width=True,
        height=400
    )

    # =====================================================
    # AUTOMATED INSIGHTS
    # =====================================================

    st.markdown("## AI Ranking Insights")

    top_cluster = cluster_df.iloc[0]

    st.markdown(f"""
    ### Best Product Cluster

    **{top_cluster['Product Type']}**

    - Average Opportunity Score: {round(top_cluster['Avg Opportunity'],1)}
    - Average Search Volume: {round(top_cluster['Avg Search Volume'],0)}
    - Keyword Count: {top_cluster['Keyword Count']}

    Insight:
    Đây là nhóm keyword có:
    - demand mạnh
    - competition hợp lý
    - khả năng rank cao

    Recommendation:
    - build SEO cluster
    - optimize listing title
    - push PPC ranking
    - create long-tail supporting keywords
    """)

    # =====================================================
    # TRENDING KEYWORDS
    # =====================================================

    trending_df = filtered_df.sort_values(
        by="Search Volume Trend",
        ascending=False
    ).head(15)

    st.markdown("## Trending Keywords")

    st.dataframe(
        trending_df[
            [
                "Keyword Phrase",
                "Search Volume Trend",
                "Search Volume",
                "Opportunity Score",
                "Ranking Strategy",
            ]
        ],
        use_container_width=True,
        height=350
    )

    # =====================================================
    # FINAL STRATEGY
    # =====================================================

    st.markdown("## Final Strategy Layer")

    st.markdown("""
    ### Aggressive Rank
    - high IQ score
    - low competition
    - low title density
    - scalable PPC

    ### Good Opportunity
    - medium competition
    - suitable long-tail SEO
    - lower CPC

    ### Hard Competition
    - large competitors
    - high CPR
    - expensive PPC

    ### Avoid
    - low demand
    - low conversion potential
    - saturated keywords
    """)
