# =========================================================
# service/ranking_engine.py
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
)

from utils.csv_utils import read_csv_safe


# =========================================================
# MAIN FUNCTION
# =========================================================

def render_ranking_engine():

    st.markdown("# Ranking Opportunity Engine")

    # =====================================================
    # SESSION STATE
    # =====================================================

    if "ranking_df" not in st.session_state:
        st.session_state.ranking_df = None

    if "ranking_file_names" not in st.session_state:
        st.session_state.ranking_file_names = []

    # =====================================================
    # UPLOADER
    # =====================================================

    uploaded_files = st.file_uploader(
        "Upload Ranking CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="ranking_uploader"
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
                    st.warning(f"Cannot read file: {uploaded_file.name}")
                    continue

                # =================================================
                # FIX HEADER
                # =================================================

                df.columns = [
                    str(col).strip()
                    for col in df.columns
                ]

                # =================================================
                # CLEAN NUMERIC COLUMNS
                # =================================================

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

                        df[col] = (
                            df[col]
                            .astype(str)
                            .str.replace(",", "", regex=False)
                            .str.replace("%", "", regex=False)
                        )

                        df[col] = pd.to_numeric(
                            df[col],
                            errors="coerce"
                        )

                # =================================================
                # PRODUCT TYPE DETECTION
                # =================================================

                def detect_product_type(keyword):

                    keyword = str(keyword).lower()

                    mapping = {
                        "blanket": "Blanket",
                        "mug": "Mug",
                        "pillow": "Pillow",
                        "shirt": "Shirt",
                        "hoodie": "Hoodie",
                        "canvas": "Canvas",
                        "poster": "Poster",
                        "necklace": "Jewelry",
                        "bracelet": "Jewelry",
                        "plaque": "Plaque",
                        "frame": "Frame",
                        "ornament": "Ornament",
                        "tumbler": "Tumbler",
                        "ring": "Jewelry",
                        "keychain": "Keychain",
                        "wind chime": "Wind Chime",
                    }

                    for key, value in mapping.items():

                        if key in keyword:
                            return value

                    return "Other"

                # =================================================
                # DEMAND LEVEL
                # =================================================

                def classify_demand(volume):

                    if pd.isna(volume):
                        return "Low"

                    if volume >= 50000:
                        return "Extreme"

                    elif volume >= 20000:
                        return "High"

                    elif volume >= 5000:
                        return "Medium"

                    return "Low"

                # =================================================
                # COMPETITION LEVEL
                # =================================================

                def classify_competition(row):

                    comp = row.get(
                        "Competing Products",
                        0
                    )

                    title_density = row.get(
                        "Title Density",
                        0
                    )

                    if comp >= 100000 or title_density >= 50:
                        return "Extreme"

                    elif comp >= 30000 or title_density >= 20:
                        return "High"

                    elif comp >= 10000:
                        return "Medium"

                    return "Low"

                # =================================================
                # OPPORTUNITY SCORE
                # =================================================

                def calculate_opportunity(row):

                    score = 0

                    sv = row.get("Search Volume", 0)
                    iq = row.get("Cerebro IQ Score", 0)
                    trend = row.get("Search Volume Trend", 0)
                    cpr = row.get("CPR", 999)
                    comp = row.get("Competing Products", 999999)

                    # Demand
                    if sv >= 50000:
                        score += 35
                    elif sv >= 20000:
                        score += 25
                    elif sv >= 5000:
                        score += 15

                    # IQ
                    if iq >= 1000:
                        score += 25
                    elif iq >= 500:
                        score += 15

                    # Trend
                    if trend >= 20:
                        score += 15
                    elif trend >= 10:
                        score += 10

                    # CPR
                    if cpr <= 10:
                        score += 15
                    elif cpr <= 30:
                        score += 10

                    # Competition
                    if comp <= 10000:
                        score += 15
                    elif comp <= 50000:
                        score += 8

                    return min(score, 100)

                # =================================================
                # APPLY ENGINE
                # =================================================

                if "Keyword Phrase" in df.columns:

                    df["Product Type"] = df[
                        "Keyword Phrase"
                    ].apply(detect_product_type)

                else:

                    df["Product Type"] = "Other"

                df["Demand Level"] = df[
                    "Search Volume"
                ].apply(classify_demand)

                df["Competition Level"] = df.apply(
                    classify_competition,
                    axis=1
                )

                df["Opportunity Score"] = df.apply(
                    calculate_opportunity,
                    axis=1
                )

                # =================================================
                # BUILD RANK DECISION
                # =================================================

                def build_rank_decision(row):

                    score = row["Opportunity Score"]

                    if score >= 75:
                        return "Build Rank Aggressively"

                    elif score >= 55:
                        return "Good Ranking Opportunity"

                    elif score >= 35:
                        return "Moderate Competition"

                    return "Hard To Rank"

                df["Ranking Decision"] = df.apply(
                    build_rank_decision,
                    axis=1
                )

                # =================================================
                # PRIORITY COLOR
                # =================================================

                def priority_color(score):

                    if score >= 75:
                        return "🟢"

                    elif score >= 55:
                        return "🟡"

                    return "🔴"

                df["Priority"] = df[
                    "Opportunity Score"
                ].apply(priority_color)

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {e}"
                )

        # =====================================================
        # SAVE SESSION
        # =====================================================

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.ranking_df = final_df

            st.session_state.ranking_file_names = [
                f.name for f in uploaded_files
            ]

    # =====================================================
    # ACTIVE DATA
    # =====================================================

    final_df = st.session_state.ranking_df

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.ranking_file_names:

        st.success("Ranking Dataset Loaded")

        for file_name in st.session_state.ranking_file_names:
            st.caption(f"• {file_name}")

        if st.button(
            "Clear Ranking Dataset",
            key="clear_ranking"
        ):

            st.session_state.ranking_df = None
            st.session_state.ranking_file_names = []

            st.rerun()

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if final_df is None or final_df.empty:

        st.info("Upload ranking CSV to begin.")
        return

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        demand_filter = st.multiselect(
            "Demand Level",
            sorted(
                final_df["Demand Level"]
                .dropna()
                .unique()
            )
        )

    with c2:

        competition_filter = st.multiselect(
            "Competition Level",
            sorted(
                final_df["Competition Level"]
                .dropna()
                .unique()
            )
        )

    with c3:

        product_filter = st.multiselect(
            "Product Type",
            sorted(
                final_df["Product Type"]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if demand_filter:

        filtered_df = filtered_df[
            filtered_df["Demand Level"].isin(
                demand_filter
            )
        ]

    if competition_filter:

        filtered_df = filtered_df[
            filtered_df["Competition Level"].isin(
                competition_filter
            )
        ]

    if product_filter:

        filtered_df = filtered_df[
            filtered_df["Product Type"].isin(
                product_filter
            )
        ]

    # =====================================================
    # SEARCH
    # =====================================================

    search = st.text_input(
        "Search Keyword",
        placeholder="Search keyword..."
    )

    if search and "Keyword Phrase" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["Keyword Phrase"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Keywords",
        len(filtered_df)
    )

    m2.metric(
        "Avg Search Volume",
        f"{int(filtered_df['Search Volume'].mean()):,}"
        if "Search Volume" in filtered_df.columns
        else 0
    )

    m3.metric(
        "Avg IQ Score",
        f"{int(filtered_df['Cerebro IQ Score'].mean())}"
        if "Cerebro IQ Score" in filtered_df.columns
        else 0
    )

    m4.metric(
        "High Opportunity KW",
        len(
            filtered_df[
                filtered_df["Opportunity Score"] >= 75
            ]
        )
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("## Ranking Insights")

    high_opportunity = filtered_df[
        filtered_df["Opportunity Score"] >= 75
    ]

    hard_keywords = filtered_df[
        filtered_df["Opportunity Score"] < 35
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🟢 Best Keywords To Rank")

        if not high_opportunity.empty:

            display_cols = [
                col for col in [
                    "Keyword Phrase",
                    "Search Volume",
                    "Cerebro IQ Score",
                    "Competing Products",
                    "Opportunity Score",
                    "Ranking Decision"
                ]
                if col in high_opportunity.columns
            ]

            st.dataframe(
                high_opportunity[
                    display_cols
                ].sort_values(
                    by="Opportunity Score",
                    ascending=False
                ),
                use_container_width=True,
                height=400
            )

    with col2:

        st.markdown("### 🔴 Hard Keywords")

        if not hard_keywords.empty:

            display_cols = [
                col for col in [
                    "Keyword Phrase",
                    "Search Volume",
                    "Competing Products",
                    "Title Density",
                    "Opportunity Score",
                    "Ranking Decision"
                ]
                if col in hard_keywords.columns
            ]

            st.dataframe(
                hard_keywords[
                    display_cols
                ].sort_values(
                    by="Competing Products",
                    ascending=False
                ),
                use_container_width=True,
                height=400
            )

    # =====================================================
    # FULL DATA
    # =====================================================

    st.markdown("## Full Ranking Dataset")

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        minWidth=120
    )

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=700,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        enable_enterprise_modules=True,
    )
