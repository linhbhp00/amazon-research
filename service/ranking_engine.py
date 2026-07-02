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
    JsCode,
)

from utils.csv_utils import read_csv_safe

# =========================================================
# HELPERS
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

        # =============================================
        # EASY WIN
        # =============================================

        if (
            search_volume >= 3000
            and iq_score >= 1000
            and cpc <= 1.5
            and competing <= 5000
        ):

            return "Easy Win"

        # =============================================
        # BUILD RANK
        # =============================================

        elif (
            search_volume >= 5000
            and trend > 0
            and iq_score >= 700
        ):

            return "Build Rank"

        # =============================================
        # HIGH COMPETITION
        # =============================================

        elif (
            competing >= 20000
            or cpc >= 3
        ):

            return "High Competition"

        # =============================================
        # TRENDING
        # =============================================

        elif trend >= 15:

            return "Trending"

        return "Mid Opportunity"

    except:

        return "Unknown"


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


def detect_product_type(keyword):

    keyword = str(keyword).lower()

    product_map = {

        "Blanket": [
            "blanket"
        ],

        "Mug": [
            "mug",
            "cup",
        ],

        "Shirt": [
            "shirt",
            "hoodie",
            "sweatshirt",
        ],

        "Jewelry": [
            "necklace",
            "bracelet",
            "ring",
        ],

        "Memorial": [
            "memorial",
            "sympathy",
            "funeral",
        ],

        "Pet": [
            "dog",
            "cat",
            "pet",
        ]
    }

    for product, words in product_map.items():

        for word in words:

            if word in keyword:
                return product

    return "General"


# =========================================================
# MAIN ENGINE
# =========================================================

def render_ranking_engine():

    st.markdown("# Ranking Engine")

    # =====================================================
    # SESSION
    # =====================================================

    if "ranking_df" not in st.session_state:
        st.session_state.ranking_df = None

    if "ranking_file_names" not in st.session_state:
        st.session_state.ranking_file_names = []

    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Ranking Engine")

    uploaded_files = st.sidebar.file_uploader(
        "Upload Ranking CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="ranking_csv"
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

                    st.warning(
                        f"Cannot read {uploaded_file.name}"
                    )

                    continue

                # =========================================
                # FIX HEADER
                # =========================================

                if df.columns.tolist()[0] == 0:

                    header_row = df.iloc[0]

                    df = df[1:].copy()

                    df.columns = header_row

                df = df.reset_index(drop=True)

                # =========================================
                # CLEAN COLUMN NAMES
                # =========================================

                df.columns = [
                    str(col).strip()
                    for col in df.columns
                ]

                # =========================================
                # NUMERIC CONVERSION
                # =========================================

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

                    if col in df.columns:

                        df[col] = pd.to_numeric(
                            df[col]
                            .astype(str)
                            .str.replace(",", ""),
                            errors="coerce"
                        )

                # =========================================
                # PRODUCT TYPE
                # =========================================

                if "Keyword Phrase" in df.columns:

                    df["Product Type"] = (
                        df["Keyword Phrase"]
                        .apply(detect_product_type)
                    )

                else:

                    df["Product Type"] = "General"

                # =========================================
                # OPPORTUNITY SCORE
                # =========================================

                df["Opportunity Score"] = (
                    df.apply(
                        score_keyword,
                        axis=1
                    )
                )

                # =========================================
                # KEYWORD TYPE
                # =========================================

                df["Keyword Classification"] = (
                    df.apply(
                        classify_keyword,
                        axis=1
                    )
                )

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing "
                    f"{uploaded_file.name}: {e}"
                )

        # =============================================
        # SAVE SESSION
        # =============================================

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

        st.sidebar.success(
            "Ranking Dataset Loaded"
        )

        for file_name in (
            st.session_state
            .ranking_file_names
        ):

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear Ranking Dataset"
        ):

            st.session_state.ranking_df = None

            st.session_state.ranking_file_names = []

            st.rerun()

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload Ranking CSV files."
        )

        return

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

        product_filter = st.multiselect(
            "Product Type",
            options=sorted(
                final_df[
                    "Product Type"
                ]
                .dropna()
                .unique()
            )
        )

    with c3:

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

    if product_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Product Type"
            ]
            .isin(product_filter)
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
        "High Competition",
        len(
            filtered_df[
                filtered_df[
                    "Keyword Classification"
                ] == "High Competition"
            ]
        )
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown(
        "## Keyword Opportunity Insights"
    )

    insight_df = (
        filtered_df
        .groupby(
            [
                "Keyword Classification",
                "Product Type"
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
        "Product Type",
        "Keyword Count",
        "Avg Opportunity Score",
        "Avg Search Volume",
        "Avg CPC",
    ]

    st.dataframe(
        insight_df,
        use_container_width=True
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

    st.dataframe(
        top_keywords[
            [
                "Keyword Phrase",
                "Keyword Classification",
                "Product Type",
                "Search Volume",
                "Cerebro IQ Score",
                "H10 PPC Sugg. Bid",
                "Competing Products",
                "Opportunity Score",
            ]
        ],
        use_container_width=True,
        height=400
    )

    # =====================================================
    # AGGRID
    # =====================================================

    st.markdown(
        "## Ranking Intelligence Dashboard"
    )

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        minWidth=140
    )

    # =====================================================
    # COLOR RULES
    # =====================================================

    classification_style = JsCode("""
    function(params) {

        if (
            params.value == 'Easy Win'
        ) {

            return {
                'backgroundColor': '#14532d',
                'color': 'white'
            }
        }

        if (
            params.value == 'Build Rank'
        ) {

            return {
                'backgroundColor': '#1d4ed8',
                'color': 'white'
            }
        }

        if (
            params.value == 'Trending'
        ) {

            return {
                'backgroundColor': '#7c3aed',
                'color': 'white'
            }
        }

        if (
            params.value == 'High Competition'
        ) {

            return {
                'backgroundColor': '#7f1d1d',
                'color': 'white'
            }
        }

        return {
            'backgroundColor': '#374151',
            'color': 'white'
        }
    }
    """)

    gb.configure_column(
        "Keyword Classification",
        cellStyle=classification_style,
        width=180
    )

    gb.configure_column(
        "Keyword Phrase",
        pinned="left",
        width=320
    )

    gb.configure_column(
        "Opportunity Score",
        width=180
    )

    # =====================================================
    # BUILD GRID
    # =====================================================

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.NO_UPDATE
    )
