import streamlit as st
import pandas as pd
import numpy as np

from datetime import datetime
from urllib.parse import quote_plus

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
        .str.strip(),
        errors="coerce"
    )

# =========================================================
# AGE CLASSIFICATION
# =========================================================

def classify_seller_age(months):

    if pd.isna(months):
        return "Unknown"

    if months <= 12:
        return "New Seller"

    elif months <= 36:
        return "Mid Seller"

    return "Old Seller"

def classify_listing_age(months):

    if pd.isna(months):
        return "Unknown"

    if months <= 6:
        return "New Listing"

    elif months <= 24:
        return "Mid Listing"

    return "Old Listing"

# =========================================================
# COLOR MAP
# =========================================================

def row_color(group):

    colors = {
        "New Seller": "#22c55e",
        "Mid Seller": "#facc15",
        "Old Seller": "#ef4444",

        "New Listing": "#22c55e",
        "Mid Listing": "#facc15",
        "Old Listing": "#ef4444",
    }

    return colors.get(group, "#1f2937")

# =========================================================
# ENGINE
# =========================================================

def render_asin_engine():

    st.markdown("## ASIN Intelligence Engine")

    uploaded_file = st.file_uploader(
        "Upload ASIN Research CSV",
        type=["csv"],
        key="asin_engine"
    )

    if uploaded_file is None:

        st.info("Upload ASIN research CSV.")
        return

    # =====================================================
    # LOAD DATA
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
    # COLUMN CLEANING
    # =====================================================

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    required_columns = [
        "Keyword Search",
        "ASIN",
        "URL",
        "Image URL",
        "Brand",
        "Seller",
        "Creation Date",
        "Revenue",
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
    # CLEAN NUMBERS
    # =====================================================

    numeric_cols = [
        "Revenue",
        "Sales",
        "Review Count",
        "Rating",
        "Seller Country / Fees",
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = safe_numeric(
                df[col]
            )

    # =====================================================
    # DATE PARSE
    # =====================================================

    df["Creation Date"] = pd.to_datetime(
        df["Creation Date"],
        errors="coerce"
    )

    current_date = pd.Timestamp.now()

    df["Listing Age Months"] = (
        (
            current_date -
            df["Creation Date"]
        ).dt.days / 30
    ).round(0)

    # =====================================================
    # GROUPS
    # =====================================================

    df["Seller Group"] = df[
        "Listing Age Months"
    ].apply(classify_seller_age)

    df["Listing Group"] = df[
        "Listing Age Months"
    ].apply(classify_listing_age)

    # =====================================================
    # MARKET STATUS
    # =====================================================

    def market_status(row):

        age = row["Listing Age Months"]

        revenue = row.get("Revenue", 0)

        if pd.isna(age):
            return "Unknown"

        # ---------------------------------------------
        # NEW TREND
        # ---------------------------------------------

        if age <= 6 and revenue >= 10000:
            return "Trending Product"

        # ---------------------------------------------
        # STABLE WINNER
        # ---------------------------------------------

        elif age > 24 and revenue >= 20000:
            return "Stable Winner"

        # ---------------------------------------------
        # DEAD NICHE
        # ---------------------------------------------

        elif age > 24 and revenue < 3000:
            return "Weak Demand"

        # ---------------------------------------------
        # GROWTH
        # ---------------------------------------------

        elif age <= 12 and revenue >= 5000:
            return "Growth Potential"

        return "Normal"

    df["Market Status"] = df.apply(
        market_status,
        axis=1
    )

    # =====================================================
    # OPPORTUNITY SCORE
    # =====================================================

    def calculate_opportunity(row):

        revenue = row.get("Revenue", 0)
        reviews = row.get("Review Count", 0)
        age = row.get("Listing Age Months", 0)

        if pd.isna(revenue):
            revenue = 0

        if pd.isna(reviews):
            reviews = 0

        if pd.isna(age):
            age = 0

        score = (
            (revenue / 1000)
            + max(0, 40 - reviews)
            + max(0, 24 - age)
        )

        return round(score, 0)

    df["Opportunity Score"] = df.apply(
        calculate_opportunity,
        axis=1
    )

    # =====================================================
    # ASIN LINK
    # =====================================================

    def make_asin_link(row):

        asin = str(row["ASIN"])

        url = row["URL"]

        return f'<a href="{url}" target="_blank">{asin}</a>'

    df["ASIN Link"] = df.apply(
        make_asin_link,
        axis=1
    )

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        selected_market = st.multiselect(
            "Market Status",
            options=sorted(
                df["Market Status"]
                .dropna()
                .unique()
            )
        )

    with col2:

        selected_seller = st.multiselect(
            "Seller Group",
            options=sorted(
                df["Seller Group"]
                .dropna()
                .unique()
            )
        )

    with col3:

        selected_listing = st.multiselect(
            "Listing Group",
            options=sorted(
                df["Listing Group"]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # FILTER
    # =====================================================

    filtered_df = df.copy()

    if selected_market:

        filtered_df = filtered_df[
            filtered_df["Market Status"]
            .isin(selected_market)
        ]

    if selected_seller:

        filtered_df = filtered_df[
            filtered_df["Seller Group"]
            .isin(selected_seller)
        ]

    if selected_listing:

        filtered_df = filtered_df[
            filtered_df["Listing Group"]
            .isin(selected_listing)
        ]

    # =====================================================
    # METRICS
    # =====================================================

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total ASIN",
        len(filtered_df)
    )

    m2.metric(
        "Avg Revenue",
        f"${filtered_df['Revenue'].mean():,.0f}"
        if "Revenue" in filtered_df.columns
        else "-"
    )

    m3.metric(
        "Trending Products",
        len(
            filtered_df[
                filtered_df["Market Status"]
                == "Trending Product"
            ]
        )
    )

    m4.metric(
        "High Opportunity",
        len(
            filtered_df[
                filtered_df["Opportunity Score"] >= 60
            ]
        )
    )

    # =====================================================
    # IMAGE RENDERER
    # =====================================================

    image_renderer = JsCode("""
    class ImgCellRenderer {
        init(params) {
            this.eGui = document.createElement('img');
            this.eGui.setAttribute('src', params.value);
            this.eGui.setAttribute('width', '60');
        }

        getGui() {
            return this.eGui;
        }
    }
    """)

    # =====================================================
    # LINK RENDERER
    # =====================================================

    link_renderer = JsCode("""
    class UrlCellRenderer {
        init(params) {
            this.eGui = document.createElement('div');
            this.eGui.innerHTML = params.value;
        }

        getGui() {
            return this.eGui;
        }
    }
    """)

    # =====================================================
    # GRID
    # =====================================================

    display_columns = [
        "Keyword Search",
        "Image URL",
        "ASIN Link",
        "Brand",
        "Revenue",
        "Sales",
        "Review Count",
        "Rating",
        "Creation Date",
        "Listing Age Months",
        "Seller Group",
        "Listing Group",
        "Market Status",
        "Opportunity Score",
    ]

    available_columns = [
        col for col in display_columns
        if col in filtered_df.columns
    ]

    grid_df = filtered_df[
        available_columns
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

    # =====================================================
    # IMAGE COLUMN
    # =====================================================

    if "Image URL" in grid_df.columns:

        gb.configure_column(
            "Image URL",
            headerName="Product Image",
            cellRenderer=image_renderer,
            width=100
        )

    # =====================================================
    # ASIN LINK
    # =====================================================

    if "ASIN Link" in grid_df.columns:

        gb.configure_column(
            "ASIN Link",
            cellRenderer=link_renderer,
            width=140
        )

    # =====================================================
    # COLOR GROUPS
    # =====================================================

    seller_style = JsCode("""
    function(params) {

        if (params.value == 'New Seller') {
            return {
                'backgroundColor': '#22c55e',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Mid Seller') {
            return {
                'backgroundColor': '#facc15',
                'color': 'black',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Old Seller') {
            return {
                'backgroundColor': '#ef4444',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }
    }
    """)

    listing_style = JsCode("""
    function(params) {

        if (params.value == 'New Listing') {
            return {
                'backgroundColor': '#22c55e',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Mid Listing') {
            return {
                'backgroundColor': '#facc15',
                'color': 'black',
                'fontWeight': 'bold'
            }
        }

        if (params.value == 'Old Listing') {
            return {
                'backgroundColor': '#ef4444',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }
    }
    """)

    gb.configure_column(
        "Seller Group",
        cellStyle=seller_style
    )

    gb.configure_column(
        "Listing Group",
        cellStyle=listing_style
    )

    # =====================================================
    # BUILD
    # =====================================================

    grid_options = gb.build()

    grid_options["rowHeight"] = 90

    # =====================================================
    # TABLE
    # =====================================================

    st.markdown("## ASIN Intelligence Dashboard")

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
    st.markdown("## Market Insights")

    # =====================================================
    # TOP OPPORTUNITY
    # =====================================================

    top_opportunity = filtered_df.sort_values(
        by="Opportunity Score",
        ascending=False
    ).head(10)

    st.markdown("### Top Opportunity ASIN")

    st.dataframe(
        top_opportunity[
            [
                "Keyword Search",
                "ASIN",
                "Revenue",
                "Listing Age Months",
                "Market Status",
                "Opportunity Score",
            ]
        ],
        use_container_width=True,
        height=400
    )

    # =====================================================
    # INSIGHT TEXT
    # =====================================================

    trending_count = len(
        filtered_df[
            filtered_df["Market Status"]
            == "Trending Product"
        ]
    )

    stable_count = len(
        filtered_df[
            filtered_df["Market Status"]
            == "Stable Winner"
        ]
    )

    weak_count = len(
        filtered_df[
            filtered_df["Market Status"]
            == "Weak Demand"
        ]
    )

    st.markdown("## Strategic Insights")

    st.markdown(f"""
    ### Trending Products

    - {trending_count} ASIN đang thuộc nhóm trending
    - Listing mới nhưng doanh thu cao
    - Có khả năng niche đang tăng mạnh
    - Phù hợp launch nhanh

    ### Stable Winners

    - {stable_count} ASIN thuộc nhóm seller mạnh lâu năm
    - Đây là niche đã validate demand
    - Cần differentiation mạnh nếu muốn compete

    ### Weak Demand

    - {weak_count} ASIN thuộc nhóm demand thấp
    - Listing cũ nhưng revenue yếu
    - Không phù hợp để launch mới

    ### Market Signals

    - New Listing + High Revenue = trend signal
    - Old Listing + Stable Revenue = moat niche
    - Low Reviews + High Revenue = opportunity gap
    - High Opportunity Score = dễ rank + dễ scale
    """)