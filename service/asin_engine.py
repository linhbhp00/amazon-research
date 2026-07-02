import streamlit as st
import pandas as pd
import numpy as np
import re

from datetime import datetime
from urllib.parse import quote_plus

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# HEADER FIX
# =========================================================

EXPECTED_COLUMNS = [
    "ASIN",
    "Image URL",
    "Creation Date",
]

def is_valid_header(columns):

    cols = [str(c).strip() for c in columns]

    score = 0

    for expected in EXPECTED_COLUMNS:

        if expected in cols:
            score += 1

    return score >= 2


def auto_fix_headers(df):

    if df is None or df.empty:
        return df

    # ==========================================
    # HEADER OK
    # ==========================================

    if is_valid_header(df.columns):
        return df

    # ==========================================
    # FIRST ROW
    # ==========================================

    first_row = (
        df.iloc[0]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if is_valid_header(first_row):

        fixed_df = df.copy()

        fixed_df.columns = first_row

        fixed_df = fixed_df.iloc[1:].reset_index(drop=True)

        return fixed_df

    # ==========================================
    # SECOND ROW
    # ==========================================

    if len(df) > 1:

        second_row = (
            df.iloc[1]
            .fillna("")
            .astype(str)
            .tolist()
        )

        if is_valid_header(second_row):

            fixed_df = df.copy()

            fixed_df.columns = second_row

            fixed_df = fixed_df.iloc[2:].reset_index(drop=True)

            return fixed_df

    return df


# =========================================================
# NUMBER CLEANER
# =========================================================

def clean_numeric(value):

    if pd.isna(value):
        return 0

    value = str(value)

    value = value.replace(",", "")
    value = value.replace("$", "")
    value = value.strip()

    try:
        return float(value)
    except:
        return 0


# =========================================================
# AMAZON LINK
# =========================================================

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
# IMAGE RENDER
# =========================================================

def make_image_html(url):

    if pd.isna(url):
        return ""

    url = str(url)

    return f"""
    <img src="{url}"
    style="
        width:70px;
        border-radius:8px;
    ">
    """


# =========================================================
# AGE CALCULATOR
# =========================================================

def calculate_age_months(date_value):

    try:

        date_value = pd.to_datetime(
            date_value,
            errors="coerce"
        )

        if pd.isna(date_value):
            return 0

        today = pd.Timestamp.now()

        months = (
            (today.year - date_value.year) * 12
            + (today.month - date_value.month)
        )

        return max(months, 0)

    except:

        return 0


# =========================================================
# SELLER GROUP
# =========================================================

def get_seller_group(months):

    if months <= 12:
        return "New Seller"

    elif months <= 36:
        return "Mid Seller"

    return "Old Seller"


# =========================================================
# LISTING GROUP
# =========================================================

def get_listing_group(months):

    if months <= 6:
        return "New Listing"

    elif months <= 24:
        return "Mid Listing"

    return "Old Listing"


# =========================================================
# SALES GROUP
# =========================================================

def get_sales_group(sales):

    if sales == 0:
        return "No Sale"

    elif sales < 500:
        return "Low Sales"

    elif sales <= 1000:
        return "Stable Sales"

    return "High Sales"


# =========================================================
# STRATEGY
# =========================================================

def get_strategy(group):

    if "Old Seller" in group and "Old Listing" in group:

        return (
            "Strong moat competitor. "
            "Avoid direct competition."
        )

    if "Old Seller" in group and "New Listing" in group:

        return (
            "Large seller testing niche. "
            "Monitor closely."
        )

    if "Mid Seller" in group and "Mid Listing" in group:

        return (
            "Stable competitor. "
            "Learn and follow patterns."
        )

    if "New Seller" in group and "New Listing" in group:

        return (
            "Trending opportunity. "
            "Research and scale quickly."
        )

    return (
        "Analyze deeper before entering."
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def render_asin_engine(final_df):

    st.markdown("# ASIN Intelligence")

    # =====================================================
    # EMPTY
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload ASIN CSV files to begin."
        )

        return

    # =====================================================
    # FIX HEADERS
    # =====================================================

    final_df = auto_fix_headers(
        final_df
    )

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # IMAGE COLUMN
    # =====================================================

    if "Image URL" in final_df.columns:

        final_df["Image"] = (
            final_df["Image URL"]
            .apply(make_image_html)
        )

    # =====================================================
    # ASIN LINK
    # =====================================================

    if "ASIN" in final_df.columns:

        final_df["ASIN"] = (
            final_df["ASIN"]
            .apply(make_asin_link)
        )

    # =====================================================
    # SALES / REVENUE
    # =====================================================

    sales_cols = [
        "ASIN Sales",
        "Sales",
    ]

    revenue_cols = [
        "ASIN Revenue",
        "Revenue",
    ]

    sales_col = None
    revenue_col = None

    for col in sales_cols:

        if col in final_df.columns:
            sales_col = col
            break

    for col in revenue_cols:

        if col in final_df.columns:
            revenue_col = col
            break

    if sales_col:

        final_df["ASIN Sales"] = (
            final_df[sales_col]
            .apply(clean_numeric)
            .astype(int)
        )

    else:

        final_df["ASIN Sales"] = 0

    if revenue_col:

        final_df["ASIN Revenue"] = (
            final_df[revenue_col]
            .apply(clean_numeric)
        )

    else:

        final_df["ASIN Revenue"] = 0

    # =====================================================
    # AGE
    # =====================================================

    creation_cols = [
        "Creation Date",
        "Created Date",
        "Date Created",
    ]

    creation_col = None

    for col in creation_cols:

        if col in final_df.columns:

            creation_col = col
            break

    if creation_col:

        final_df["Listing Age (mo)"] = (
            final_df[creation_col]
            .apply(calculate_age_months)
        )

    else:

        final_df["Listing Age (mo)"] = 0

    final_df["Seller Age (mo)"] = (
        final_df["Listing Age (mo)"]
    )

    # =====================================================
    # GROUPS
    # =====================================================

    final_df["Seller Group"] = (
        final_df["Seller Age (mo)"]
        .apply(get_seller_group)
    )

    final_df["Listing Group"] = (
        final_df["Listing Age (mo)"]
        .apply(get_listing_group)
    )

    final_df["Sales Group"] = (
        final_df["ASIN Sales"]
        .apply(get_sales_group)
    )

    final_df["Group Before Sales"] = (
        final_df["Seller Group"]
        + " + "
        + final_df["Listing Group"]
    )

    final_df["Competitor Group"] = (
        final_df["Group Before Sales"]
        + " + "
        + final_df["Sales Group"]
    )

    final_df["Strategy"] = (
        final_df["Competitor Group"]
        .apply(get_strategy)
    )

    # =====================================================
    # FILTERS
    # =====================================================

    f1, f2, f3, f4 = st.columns(4)

    with f1:

        seller_filter = st.multiselect(
            "Seller Group",
            sorted(
                final_df["Seller Group"]
                .dropna()
                .unique()
            )
        )

    with f2:

        listing_filter = st.multiselect(
            "Listing Group",
            sorted(
                final_df["Listing Group"]
                .dropna()
                .unique()
            )
        )

    with f3:

        sales_filter = st.multiselect(
            "Sales Group",
            sorted(
                final_df["Sales Group"]
                .dropna()
                .unique()
            )
        )

    with f4:

        strategy_filter = st.multiselect(
            "Strategy",
            sorted(
                final_df["Strategy"]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if seller_filter:

        filtered_df = filtered_df[
            filtered_df["Seller Group"]
            .isin(seller_filter)
        ]

    if listing_filter:

        filtered_df = filtered_df[
            filtered_df["Listing Group"]
            .isin(listing_filter)
        ]

    if sales_filter:

        filtered_df = filtered_df[
            filtered_df["Sales Group"]
            .isin(sales_filter)
        ]

    if strategy_filter:

        filtered_df = filtered_df[
            filtered_df["Strategy"]
            .isin(strategy_filter)
        ]

    # =====================================================
    # DATASET
    # =====================================================

    st.markdown("## ASIN Dataset")

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        wrapText=True,
        autoHeight=True,
    )

    # =====================================================
    # FREEZE
    # =====================================================

    freeze_cols = [
        "ASIN",
        "Image",
        "ASIN Sales",
        "ASIN Revenue",
    ]

    for col in freeze_cols:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                pinned="left"
            )

    # =====================================================
    # IMAGE RENDERER
    # =====================================================

    image_renderer = JsCode("""
    class ImgCellRenderer {
      init(params) {
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = params.value || '';
      }

      getGui() {
        return this.eGui;
      }
    }
    """)

    link_renderer = JsCode("""
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

    if "Image" in filtered_df.columns:

        gb.configure_column(
            "Image",
            cellRenderer=image_renderer,
            width=90,
            autoHeight=True
        )

    if "ASIN" in filtered_df.columns:

        gb.configure_column(
            "ASIN",
            cellRenderer=link_renderer
        )

    # =====================================================
    # COLOR STYLE
    # =====================================================

    color_js = JsCode("""
    function(params) {

        if (params.value == null) {
            return {};
        }

        const value = params.value.toString();

        if (value.includes("Old")) {

            return {
                backgroundColor: "#7f1d1d",
                color: "white",
                fontWeight: "700"
            };
        }

        if (value.includes("Mid")) {

            return {
                backgroundColor: "#1d4ed8",
                color: "white",
                fontWeight: "700"
            };
        }

        if (value.includes("New")) {

            return {
                backgroundColor: "#15803d",
                color: "white",
                fontWeight: "700"
            };
        }

        return {};
    }
    """)

    for col in [

        "Seller Group",
        "Listing Group",
        "Sales Group",
        "Group Before Sales",
        "Competitor Group",

    ]:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                cellStyle=color_js
            )

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=760,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        reload_data=False,
    )

    # =====================================================
    # REVENUE DISTRIBUTION
    # =====================================================

    st.markdown(
        "## Competitor Revenue Distribution"
    )

    revenue_chart = (
        filtered_df
        .groupby("Group Before Sales")[
            "ASIN Revenue"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    st.bar_chart(
        revenue_chart
    )

    # =====================================================
    # CATEGORY MARKET SHARE
    # =====================================================

    st.markdown(
        "## Category Market Share by Group"
    )

    possible_category_cols = [

        "Category",
        "Categories",
        "Main Category",
        "Product Category",

    ]

    category_col = None

    for col in possible_category_cols:

        if col in filtered_df.columns:

            category_col = col
            break

    if category_col:

        group_options = sorted(
            filtered_df[
                "Group Before Sales"
            ]
            .dropna()
            .unique()
        )

        selected_group = st.selectbox(
            "Select Group Before Sales",
            options=group_options
        )

        category_df = filtered_df[
            filtered_df[
                "Group Before Sales"
            ] == selected_group
        ]

        if not category_df.empty:

            category_share = (
                category_df[category_col]
                .fillna("Unknown")
                .astype(str)
                .value_counts(normalize=True)
                .mul(100)
                .round(1)
                .reset_index()
            )

            category_share.columns = [
                "Category",
                "Market Share %"
            ]

            st.dataframe(
                category_share,
                use_container_width=True,
                height=320
            )

            chart_df = (
                category_share
                .set_index("Category")
            )

            st.bar_chart(
                chart_df
            )

    # =====================================================
    # COMPETITOR SUMMARY
    # =====================================================

    st.markdown(
        "## Competitor Opportunity Intelligence"
    )

    competitor_summary = (
        filtered_df
        .groupby("Group Before Sales")
        .agg({

            "ASIN": "count",
            "ASIN Revenue": "sum",
            "ASIN Sales": "sum",

        })
        .reset_index()
    )

    competitor_summary.columns = [

        "Competitor Group",
        "Total ASINs",
        "Total Revenue",
        "Total Sales",

    ]

    competitor_summary["Strategy"] = (
        competitor_summary[
            "Competitor Group"
        ]
        .apply(get_strategy)
    )

    # =====================================================
    # CARDS
    # =====================================================

    for _, row in competitor_summary.iterrows():

        group_name = row["Competitor Group"]

        total_asins = row["Total ASINs"]

        revenue = int(
            row["Total Revenue"]
        )

        sales = int(
            row["Total Sales"]
        )

        strategy = row["Strategy"]

        strategy_lower = strategy.lower()

        # ============================================
        # COLORS
        # ============================================

        if "avoid" in strategy_lower:

            border = "#ef4444"
            bg = "#450a0a"

        elif (
            "follow" in strategy_lower
            or "learn" in strategy_lower
        ):

            border = "#3b82f6"
            bg = "#0f172a"

        else:

            border = "#22c55e"
            bg = "#052e16"

        st.markdown(
            f"""
            <div style="
                padding:18px;
                margin-bottom:16px;
                border-radius:14px;
                background:{bg};
                border-left:6px solid {border};
            ">

            <div style="
                font-size:20px;
                font-weight:700;
                color:white;
                margin-bottom:10px;
            ">
                {group_name}
            </div>

            <div style="
                color:#cbd5e1;
                line-height:1.8;
                font-size:15px;
            ">

                <b>{total_asins}</b>
                ASINs detected

                <br>

                Total Revenue:
                <b>${revenue:,}</b>

                <br>

                Total Sales:
                <b>{sales:,}</b>

                <br><br>

                <b>Strategy:</b>
                {strategy}

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )
