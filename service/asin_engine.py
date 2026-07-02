import streamlit as st
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import CountVectorizer
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
)

# =========================================================
# RANKING ENGINE
# =========================================================

def render_ranking_engine():

    st.markdown("# Ranking Engine")

    # =====================================================
    # SESSION
    # =====================================================

    if "ranking_df" not in st.session_state:
        st.session_state.ranking_df = None

    if "ranking_files" not in st.session_state:
        st.session_state.ranking_files = []

    # =====================================================
    # CSV READER
    # =====================================================

    @st.cache_data(show_spinner=False)
    def read_csv_safe(uploaded_file):

        encodings = [
            "utf-8",
            "utf-8-sig",
            "latin1",
            "cp1252"
        ]

        separators = [
            ",",
            ";",
            "\t"
        ]

        for enc in encodings:

            for sep in separators:

                try:

                    uploaded_file.seek(0)

                    df = pd.read_csv(
                        uploaded_file,
                        encoding=enc,
                        sep=sep,
                        engine="python",
                        on_bad_lines="skip"
                    )

                    if len(df.columns) > 5:
                        return df

                except:
                    continue

        return None

    # =====================================================
    # SIDEBAR UPLOAD
    # =====================================================

    with st.sidebar:

        st.markdown("---")
        st.markdown("## Ranking Engine")

        uploaded_files = st.file_uploader(
            "Upload Ranking CSV",
            type=["csv"],
            accept_multiple_files=True,
            key="ranking_upload"
        )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    if uploaded_files:

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:
                    continue

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {e}"
                )

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.ranking_df = final_df

            st.session_state.ranking_files = [
                f.name for f in uploaded_files
            ]

    # =====================================================
    # ACTIVE DATA
    # =====================================================

    df = st.session_state.ranking_df

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if df is None or df.empty:

        st.info("Upload Ranking CSV to begin.")
        return

    # =====================================================
    # FILE STATUS
    # =====================================================

    st.success(
        f"{len(st.session_state.ranking_files)} file(s) loaded"
    )

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    numeric_cols = [
        "ABA Total Click Share",
        "ABA Total Conv. Share",
        "Keyword Sales",
        "Cerebro IQ Score",
        "Search Volume",
        "Search Volume Trend",
        "H10 PPC Sugg. Bid",
        "H10 PPC Sugg. Min Bid",
        "H10 PPC Sugg. Max Bid",
        "Competing Products",
        "CPR",
        "Title Density",
        "Organic Rank",
        "Sponsored Rank",
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # =====================================================
    # CLEAN KEYWORD
    # =====================================================

    keyword_col = "Keyword Phrase"

    if keyword_col not in df.columns:

        st.error("Missing column: Keyword Phrase")
        return

    df[keyword_col] = (
        df[keyword_col]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("## Ranking Filters")

    c1, c2, c3 = st.columns(3)

    with c1:

        min_search = st.number_input(
            "Min Search Volume",
            value=1000
        )

    with c2:

        max_comp = st.number_input(
            "Max Competing Products",
            value=500000
        )

    with c3:

        min_iq = st.number_input(
            "Min IQ Score",
            value=100
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = df.copy()

    if "Search Volume" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Search Volume"] >= min_search
        ]

    if "Competing Products" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Competing Products"] <= max_comp
        ]

    if "Cerebro IQ Score" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Cerebro IQ Score"] >= min_iq
        ]

    # =====================================================
    # PRODUCT TYPE DETECTION
    # =====================================================

    product_keywords = [
        "blanket",
        "pillow",
        "shirt",
        "mug",
        "tumbler",
        "plaque",
        "frame",
        "wind chime",
        "stone",
        "lantern",
        "necklace",
        "bracelet",
        "sign",
        "poster",
        "canvas",
        "ornament",
        "keychain",
    ]

    def detect_product_type(keyword):

        keyword = str(keyword).lower()

        for item in product_keywords:

            if item in keyword:
                return item

        return "other"

    filtered_df["Product Type"] = (
        filtered_df[keyword_col]
        .apply(detect_product_type)
    )

    # =====================================================
    # DEMAND SCORE
    # =====================================================

    def calculate_demand_score(row):

        score = 0

        try:

            score += (
                row.get("Search Volume", 0) / 1000
            )

            score += (
                row.get("Cerebro IQ Score", 0) / 50
            )

            score += (
                row.get("Search Volume Trend", 0) / 10
            )

            score += (
                row.get("ABA Total Click Share", 0)
            )

            score += (
                row.get("ABA Total Conv. Share", 0)
            )

        except:
            pass

        return round(score, 2)

    filtered_df["Demand Score"] = (
        filtered_df.apply(
            calculate_demand_score,
            axis=1
        )
    )

    # =====================================================
    # COMPETITION SCORE
    # =====================================================

    def calculate_competition_score(row):

        score = 0

        try:

            score += (
                row.get("Competing Products", 0) / 100000
            )

            score += (
                row.get("CPR", 0) / 10
            )

            score += (
                row.get("Title Density", 0)
            )

            score += (
                row.get("H10 PPC Sugg. Bid", 0) * 2
            )

        except:
            pass

        return round(score, 2)

    filtered_df["Competition Score"] = (
        filtered_df.apply(
            calculate_competition_score,
            axis=1
        )
    )

    # =====================================================
    # OPPORTUNITY SCORE
    # =====================================================

    filtered_df["Opportunity Score"] = (
        filtered_df["Demand Score"]
        -
        filtered_df["Competition Score"]
    )

    # =====================================================
    # RANKING RECOMMENDATION
    # =====================================================

    def classify_keyword(row):

        opp = row["Opportunity Score"]

        if opp >= 40:
            return "Build Rank Aggressively"

        elif opp >= 20:
            return "Good Opportunity"

        elif opp >= 10:
            return "Moderate"

        return "Highly Competitive"

    filtered_df["Recommendation"] = (
        filtered_df.apply(
            classify_keyword,
            axis=1
        )
    )

    # =====================================================
    # METRICS
    # =====================================================

    st.markdown("## Ranking Intelligence")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Keywords",
        len(filtered_df)
    )

    m2.metric(
        "Avg Search Volume",
        f"{int(filtered_df['Search Volume'].mean()):,}"
        if "Search Volume" in filtered_df.columns
        else "-"
    )

    m3.metric(
        "Avg IQ Score",
        round(
            filtered_df["Cerebro IQ Score"].mean(),
            1
        )
        if "Cerebro IQ Score" in filtered_df.columns
        else "-"
    )

    m4.metric(
        "Avg Opportunity",
        round(
            filtered_df["Opportunity Score"].mean(),
            1
        )
    )

    # =====================================================
    # PRODUCT TYPE INSIGHTS
    # =====================================================

    st.markdown("## Product Type Demand")

    product_summary = (
        filtered_df.groupby("Product Type")
        .agg({
            "Keyword Phrase": "count",
            "Search Volume": "mean",
            "Opportunity Score": "mean",
        })
        .reset_index()
    )

    product_summary.columns = [
        "Product Type",
        "Keyword Count",
        "Avg Search Volume",
        "Avg Opportunity Score",
    ]

    product_summary = product_summary.sort_values(
        by="Avg Opportunity Score",
        ascending=False
    )

    st.dataframe(
        product_summary,
        use_container_width=True,
        height=320
    )

    # =====================================================
    # BEST KEYWORDS
    # =====================================================

    best_keywords = filtered_df.sort_values(
        by="Opportunity Score",
        ascending=False
    ).head(100)

    # =====================================================
    # HARD KEYWORDS
    # =====================================================

    hard_keywords = filtered_df.sort_values(
        by="Competition Score",
        ascending=False
    ).head(100)

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3 = st.tabs([
        "Best Keywords",
        "Competitive Keywords",
        "All Keywords"
    ])

    # =====================================================
    # BEST KW
    # =====================================================

    with tab1:

        st.markdown(
            "### Keywords Recommended To Build Rank"
        )

        st.dataframe(
            best_keywords[[
                "Keyword Phrase",
                "Product Type",
                "Search Volume",
                "Cerebro IQ Score",
                "Competition Score",
                "Opportunity Score",
                "Recommendation"
            ]],
            use_container_width=True,
            height=700
        )

    # =====================================================
    # HARD KW
    # =====================================================

    with tab2:

        st.markdown(
            "### Hard / Expensive Keywords"
        )

        st.dataframe(
            hard_keywords[[
                "Keyword Phrase",
                "Product Type",
                "Search Volume",
                "Competing Products",
                "H10 PPC Sugg. Bid",
                "Competition Score",
                "Recommendation"
            ]],
            use_container_width=True,
            height=700
        )

    # =====================================================
    # ALL KW
    # =====================================================

    with tab3:

        gb = GridOptionsBuilder.from_dataframe(
            filtered_df
        )

        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True,
            floatingFilter=True,
        )

        grid_options = gb.build()

        AgGrid(
            filtered_df,
            gridOptions=grid_options,
            theme="streamlit",
            height=800,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            reload_data=False,
        )

    # =====================================================
    # STRATEGIC INSIGHTS
    # =====================================================

    st.markdown("## Strategic Insights")

    top_build = (
        filtered_df[
            filtered_df["Recommendation"]
            ==
            "Build Rank Aggressively"
        ]
        .head(10)
    )

    if not top_build.empty:

        st.success(
            f"""
            High-opportunity keywords detected:
            {len(top_build)} keywords should be prioritized
            for ranking campaigns.
            """
        )

    high_comp = (
        filtered_df[
            filtered_df["Recommendation"]
            ==
            "Highly Competitive"
        ]
    )

    if not high_comp.empty:

        st.warning(
            f"""
            {len(high_comp)} keywords are highly competitive.
            Avoid aggressive PPC unless conversion rate is high.
            """
        )
