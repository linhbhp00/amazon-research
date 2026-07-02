import streamlit as st
import pandas as pd
import numpy as np
import re

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
    "ASIN Sales",
    "ASIN Revenue",
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

    # already correct
    if is_valid_header(df.columns):
        return df

    # first row
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

    # second row
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
# CLEAN NUMBERS
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
# AMAZON ASIN LINK
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):
        return ""

    asin = str(asin).strip()

    return f"""
    <a href="https://www.amazon.com/dp/{asin}"
    target="_blank">
    {asin}
    </a>
    """


# =========================================================
# IMAGE HTML
# =========================================================

def make_image_html(url):

    if pd.isna(url):
        return ""

    url = str(url)

    return f"""
    <img src="{url}"
    style="
        width:70px;
        height:70px;
        object-fit:contain;
        border-radius:8px;
    ">
    """


# =========================================================
# AGE GROUP
# =========================================================

def classify_seller_group(months):

    if months <= 12:
        return "New Seller"

    elif months <= 36:
        return "Mid Seller"

    return "Old Seller"


def classify_listing_group(months):

    if months <= 6:
        return "New Listing"

    elif months <= 24:
        return "Mid Listing"

    return "Old Listing"


# =========================================================
# SALES GROUP
# =========================================================

def classify_sales_group(sales):

    if sales == 0:
        return "No Sale"

    elif sales < 500:
        return "Low Sales"

    elif sales <= 1000:
        return "Stable Sales"

    return "High Sales"


# =========================================================
# STRATEGY ENGINE
# =========================================================

def generate_strategy(row):

    seller = row["Seller Group"]
    listing = row["Listing Group"]
    sales = row["Sales Group"]

    # =============================================
    # TREND
    # =============================================

    if (
        seller == "New Seller"
        and listing == "New Listing"
        and sales == "High Sales"
    ):

        return (
            "Trending product. "
            "Monitor closely and validate demand quickly."
        )

    # =============================================
    # STRONG MOAT
    # =============================================

    if (
        seller == "Old Seller"
        and listing == "Old Listing"
        and sales == "High Sales"
    ):

        return (
            "Strong moat competitor. "
            "Avoid direct competition."
        )

    # =============================================
    # BIG SELLER TESTING
    # =============================================

    if (
        seller == "Old Seller"
        and listing == "New Listing"
        and sales == "High Sales"
    ):

        return (
            "Large seller testing niche. "
            "Track growth carefully."
        )

    # =============================================
    # STABLE
    # =============================================

    if (
        seller == "Mid Seller"
        and listing == "Mid Listing"
    ):

        return (
            "Stable market pattern. "
            "Learn and follow."
        )

    # =============================================
    # DEAD DEMAND
    # =============================================

    if sales == "Low Sales":

        return (
            "Weak demand signal. "
            "Research carefully before entering."
        )

    # =============================================
    # NO SALE
    # =============================================

    if sales == "No Sale":

        return (
            "No sales traction detected."
        )

    return (
        "Potential opportunity. "
        "Continue monitoring."
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

        st.info("Upload ASIN CSV files.")

        return

    # =====================================================
    # HEADER FIX
    # =====================================================

    final_df = auto_fix_headers(final_df)

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # CLEAN DATA
    # =====================================================

    numeric_cols = [
        "ASIN Sales",
        "ASIN Revenue",
        "Revenue",
        "Sales",
    ]

    for col in numeric_cols:

        if col in final_df.columns:

            final_df[col] = (
                final_df[col]
                .apply(clean_numeric)
            )

    # =====================================================
    # ASIN SALES
    # =====================================================

    if "ASIN Sales" not in final_df.columns:

        if "Sales" in final_df.columns:

            final_df["ASIN Sales"] = (
                final_df["Sales"]
            )

        else:

            final_df["ASIN Sales"] = 0

    # =====================================================
    # ASIN REVENUE
    # =====================================================

    if "ASIN Revenue" not in final_df.columns:

        if "Revenue" in final_df.columns:

            final_df["ASIN Revenue"] = (
                final_df["Revenue"]
            )

        else:

            final_df["ASIN Revenue"] = 0

    # =====================================================
    # AGE
    # =====================================================

    current_date = pd.Timestamp.now()

    possible_creation_cols = [
        "Creation Date",
        "Created Date",
        "Date Created",
    ]

    creation_col = None

    for col in possible_creation_cols:

        if col in final_df.columns:

            creation_col = col
            break

    if creation_col:

        final_df[creation_col] = pd.to_datetime(
            final_df[creation_col],
            errors="coerce"
        )

        final_df["Listing Age (mo)"] = (
            (
                current_date -
                final_df[creation_col]
            )
            .dt.days
            .fillna(0)
            .astype(int)
            / 30
        ).astype(int)

    else:

        final_df["Listing Age (mo)"] = 0

    # =====================================================
    # SELLER AGE
    # =====================================================

    possible_seller_cols = [
        "Seller Age (mo)",
        "Seller Age Months",
        "Seller Age",
    ]

    seller_col = None

    for col in possible_seller_cols:

        if col in final_df.columns:

            seller_col = col
            break

    if seller_col:

        final_df["Seller Age (mo)"] = (
            final_df[seller_col]
            .apply(clean_numeric)
            .astype(int)
        )

    else:

        final_df["Seller Age (mo)"] = 0

    # =====================================================
    # GROUPS
    # =====================================================

    final_df["Seller Group"] = (
        final_df["Seller Age (mo)"]
        .apply(classify_seller_group)
    )

    final_df["Listing Group"] = (
        final_df["Listing Age (mo)"]
        .apply(classify_listing_group)
    )

    final_df["Sales Group"] = (
        final_df["ASIN Sales"]
        .apply(classify_sales_group)
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

    # =====================================================
    # STRATEGY
    # =====================================================

    final_df["Strategy"] = (
        final_df
        .apply(generate_strategy, axis=1)
    )

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        seller_filter = st.multiselect(
            "Seller Group",
            sorted(
                final_df["Seller Group"]
                .dropna()
                .unique()
            )
        )

    with c2:

        listing_filter = st.multiselect(
            "Listing Group",
            sorted(
                final_df["Listing Group"]
                .dropna()
                .unique()
            )
        )

    with c3:

        sales_filter = st.multiselect(
            "Sales Group",
            sorted(
                final_df["Sales Group"]
                .dropna()
                .unique()
            )
        )

    with c4:

        action_filter = st.multiselect(
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

    if action_filter:

        filtered_df = filtered_df[
            filtered_df["Strategy"]
            .isin(action_filter)
        ]

    # =====================================================
    # IMAGE
    # =====================================================

    image_col = None

    for col in final_df.columns:

        if "image" in col.lower():

            image_col = col
            break

    if image_col:

        filtered_df["Image"] = (
            filtered_df[image_col]
            .apply(make_image_html)
        )

    # =====================================================
    # ASIN LINK
    # =====================================================

    if "ASIN" in filtered_df.columns:

        filtered_df["ASIN"] = (
            filtered_df["ASIN"]
            .apply(make_asin_link)
        )

    # =====================================================
    # COLUMN ORDER
    # =====================================================

    preferred_order = [

        "ASIN",
        "Image",
        "ASIN Sales",
        "ASIN Revenue",

        "KW Search",

        "Seller Age (mo)",
        "Seller Group",

        "Listing Age (mo)",
        "Listing Group",

        "Sales Group",

        "Group Before Sales",
        "Competitor Group",

        "Strategy",
    ]

    existing_cols = [
        col for col in preferred_order
        if col in filtered_df.columns
    ]

    remaining_cols = [
        col for col in filtered_df.columns
        if col not in existing_cols
    ]

    filtered_df = filtered_df[
        existing_cols + remaining_cols
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

    # freeze
    pinned_cols = [
        "ASIN",
        "Image",
        "ASIN Sales",
        "ASIN Revenue",
    ]

    for col in pinned_cols:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                pinned="left"
            )

    # image
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

    # link
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
            width=90
        )

    if "ASIN" in filtered_df.columns:

        gb.configure_column(
            "ASIN",
            cellRenderer=link_renderer,
            width=140
        )

    # auto fit
    gb.configure_grid_options(
        domLayout='normal'
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

    st.markdown("---")
    st.markdown("## Competitor Revenue Distribution")

    revenue_chart = (

        filtered_df
        .groupby("Group Before Sales")[
            "ASIN Revenue"
        ]
        .sum()
        .sort_values(ascending=False)

    )

    st.bar_chart(revenue_chart)

    # =====================================================
    # CATEGORY MARKET SHARE
    # =====================================================

    st.markdown("### Category Market Share by Group")

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
            filtered_df["Group Before Sales"]
            .dropna()
            .unique()
        )

        selected_group = st.selectbox(
            "Select Group Before Sales",
            options=group_options
        )

        category_df = filtered_df[
            filtered_df["Group Before Sales"]
            == selected_group
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

            st.bar_chart(chart_df)

    # =====================================================
    # COMPETITOR SUMMARY
    # =====================================================

    st.markdown("---")
    st.markdown("## Competitor Opportunity Intelligence")

    competitor_summary = (

        filtered_df
        .groupby("Group Before Sales")
        .agg({

            "ASIN": "count",

            "ASIN Revenue": "sum",

            "ASIN Sales": "sum",

            "Strategy": lambda x:
            x.mode().iloc[0]
            if not x.mode().empty
            else "Research"

        })
        .reset_index()

    )

    competitor_summary.columns = [

        "Competitor Group",

        "Total ASINs",

        "Total Revenue",

        "Total Sales",

        "Strategy"

    ]

    st.dataframe(
        competitor_summary,
        use_container_width=True,
        height=420
    )

    # =====================================================
    # STRATEGY CARDS
    # =====================================================

    st.markdown("### Market Strategy Signals")

    for _, row in competitor_summary.iterrows():

        group_name = row["Competitor Group"]

        total_asins = row["Total ASINs"]

        strategy = row["Strategy"]

        revenue = int(row["Total Revenue"])

        sales = int(row["Total Sales"])

        st.markdown(
            f"""
            <div style="
                padding:18px;
                margin-bottom:14px;
                border-radius:14px;
                background:#0f172a;
                border-left:6px solid #3b82f6;
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

                <b>{total_asins}</b> ASINs detected
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
