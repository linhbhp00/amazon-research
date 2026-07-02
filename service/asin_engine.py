import streamlit as st
import pandas as pd

from urllib.parse import quote_plus

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# HEADER VALIDATION
# =========================================================

EXPECTED_ASIN_COLUMNS = [
    "ASIN",
    "Title",
]

CREATION_DATE_COLUMNS = [
    "Creation Date",
    "Created At",
    "Launch Date",
    "Date Created",
]

# =========================================================
# VALID HEADER
# =========================================================

def is_valid_asin_header(columns):

    cols = [str(c).strip() for c in columns]

    score = 0

    for expected in EXPECTED_ASIN_COLUMNS:

        if expected in cols:
            score += 1

    return score >= 1


# =========================================================
# AUTO HEADER FIX
# =========================================================

def auto_fix_asin_headers(df):

    if df is None or df.empty:
        return df

    if is_valid_asin_header(df.columns):
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

    if is_valid_asin_header(first_row):

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

        if is_valid_asin_header(second_row):

            fixed_df = df.copy()

            fixed_df.columns = second_row

            fixed_df = fixed_df.iloc[2:].reset_index(drop=True)

            return fixed_df

    return df


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
    style="
        color:#60a5fa;
        text-decoration:none;
        font-weight:700;
    ">
    {asin}
    </a>
    """


# =========================================================
# SEARCH LINK
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return text

    text = str(text)

    return f"""
    <a href="https://www.amazon.com/s?k={quote_plus(text)}"
    target="_blank"
    style="
        color:#60a5fa;
        text-decoration:none;
    ">
    {text}
    </a>
    """


# =========================================================
# SALES GROUP
# =========================================================

def classify_sales_level(value):

    try:
        value = int(float(value))
    except:
        return "No Sale"

    if value > 1000:
        return "High Sales"

    elif value >= 500:
        return "Stable Sales"

    elif value > 0:
        return "Low Sales"

    return "No Sale"


# =========================================================
# SELLER AGE GROUP
# =========================================================

def classify_seller_age(months):

    if pd.isna(months):
        return None

    if months <= 12:
        return "New Seller"

    elif months <= 36:
        return "Mid Seller"

    return "Old Seller"


# =========================================================
# LISTING AGE GROUP
# =========================================================

def classify_listing_age(months):

    if pd.isna(months):
        return None

    if months <= 6:
        return "New Listing"

    elif months <= 24:
        return "Mid Listing"

    return "Old Listing"


# =========================================================
# COMPETITOR GROUP
# =========================================================

def build_competitor_group(row):

    seller = row.get("Seller Group")
    listing = row.get("Listing Group")
    sales = row.get("Sales Group")

    if pd.isna(seller) or pd.isna(listing):
        return None

    return f"{seller} + {listing} + {sales}"


# =========================================================
# STRATEGY
# =========================================================

def build_strategy(group):

    strategies = {

        "Old Seller + Old Listing + High Sales":
        "Strong moat competitor. Avoid direct competition.",

        "Old Seller + New Listing + High Sales":
        "Large seller testing niche. Monitor closely.",

        "Mid Seller + Mid Listing + Stable Sales":
        "Stable seller. Learn and follow patterns.",

        "Mid Seller + Mid Listing + High Sales":
        "Market still open. Strong research opportunity.",

        "New Seller + New Listing + High Sales":
        "Trending product detected. Seller scaling aggressively.",

        "New Seller + Mid Listing + Low Sales":
        "Weak demand signal. Low priority niche.",
    }

    return strategies.get(
        group,
        "Further research required."
    )


# =========================================================
# ACTION
# =========================================================

def build_action(group):

    actions = {

        "Old Seller + Old Listing + High Sales":
        "Avoid Direct Competition",

        "Old Seller + New Listing + High Sales":
        "Monitor Closely",

        "Mid Seller + Mid Listing + Stable Sales":
        "Learn Pattern",

        "Mid Seller + Mid Listing + High Sales":
        "Deep Research",

        "New Seller + New Listing + High Sales":
        "Trend Opportunity",

        "New Seller + Mid Listing + Low Sales":
        "Avoid Market",
    }

    return actions.get(
        group,
        "Research"
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
    # FIX HEADER
    # =====================================================

    final_df = auto_fix_asin_headers(
        final_df
    )

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # CREATION DATE
    # =====================================================

    creation_col = None

    for col in CREATION_DATE_COLUMNS:

        if col in final_df.columns:

            creation_col = col
            break

    if creation_col:

        final_df[creation_col] = pd.to_datetime(
            final_df[creation_col],
            errors="coerce"
        )

        current_date = pd.Timestamp.now()

        final_df["Listing Age (mo)"] = (
            (
                current_date -
                final_df[creation_col]
            ).dt.days / 30
        ).round(0)

        final_df["Listing Age (mo)"] = (
            final_df["Listing Age (mo)"]
            .fillna(0)
            .astype(int)
        )

        final_df["Seller Age (mo)"] = (
            final_df["Listing Age (mo)"]
        )

        final_df["Seller Group"] = (
            final_df["Seller Age (mo)"]
            .apply(classify_seller_age)
        )

        final_df["Listing Group"] = (
            final_df["Listing Age (mo)"]
            .apply(classify_listing_age)
        )

    # =====================================================
    # SALES / REVENUE
    # =====================================================

    sales_col = None
    revenue_col = None

    possible_sales_cols = [
        "ASIN Sales",
        "Sales",
        "Monthly Sales",
    ]

    possible_revenue_cols = [
        "ASIN Revenue",
        "Revenue",
        "Monthly Revenue",
    ]

    for col in possible_sales_cols:

        if col in final_df.columns:

            sales_col = col
            break

    for col in possible_revenue_cols:

        if col in final_df.columns:

            revenue_col = col
            break

    if sales_col:

        final_df[sales_col] = pd.to_numeric(
            final_df[sales_col],
            errors="coerce"
        ).fillna(0).astype(int)

        final_df["Sales Group"] = (
            final_df[sales_col]
            .apply(classify_sales_level)
        )

    else:

        final_df["Sales Group"] = "No Sale"

    if revenue_col:

        final_df[revenue_col] = pd.to_numeric(
            final_df[revenue_col],
            errors="coerce"
        ).fillna(0)

    # =====================================================
    # COMPETITOR GROUP
    # =====================================================

    final_df["Competitor Group"] = (
        final_df.apply(
            build_competitor_group,
            axis=1
        )
    )

    final_df["Strategy"] = (
        final_df["Competitor Group"]
        .apply(build_strategy)
    )

    final_df["Action"] = (
        final_df["Competitor Group"]
        .apply(build_action)
    )

    # =====================================================
    # REMOVE IMAGE URL
    # =====================================================

    image_col = None

    possible_image_cols = [
        "Image URL",
        "Image",
        "Main Image",
    ]

    for col in possible_image_cols:

        if col in final_df.columns:

            image_col = col
            break

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search ASIN, keyword..."
    )

    filtered_df = final_df.copy()

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
    # DISPLAY DF
    # =====================================================

    display_df = filtered_df.copy()

    # =====================================================
    # HIDE IMAGE URL
    # =====================================================

    if image_col == "Image URL":

        pass

    # =====================================================
    # ASIN LINK
    # =====================================================

    if "ASIN" in display_df.columns:

        display_df["ASIN"] = (
            display_df["ASIN"]
            .apply(make_asin_link)
        )

    # =====================================================
    # SEARCH LINKS
    # =====================================================

    for col in display_df.columns:

        col_lower = col.lower()

        if (
            "title" in col_lower
            or "keyword" in col_lower
            or "brand" in col_lower
        ):

            display_df[col] = (
                display_df[col]
                .apply(make_search_link)
            )

    # =====================================================
    # DATASET
    # =====================================================

    st.markdown("## ASIN Dataset")

    gb = GridOptionsBuilder.from_dataframe(
        display_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        wrapText=True,
        autoHeight=True,
        minWidth=120,
        flex=1,
    )

    # =====================================================
    # URL RENDERER
    # =====================================================

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

    # =====================================================
    # IMAGE RENDERER
    # =====================================================

    image_renderer = JsCode("""
    class ImageCellRenderer {

      init(params) {

        this.eGui = document.createElement('div');

        if (!params.value) {
            this.eGui.innerHTML = '';
            return;
        }

        this.eGui.innerHTML = `
          <img
            src="${params.value}"
            style="
              width:90px;
              height:90px;
              object-fit:contain;
              border-radius:10px;
              background:white;
              padding:4px;
            "
          />
        `;
      }

      getGui() {
        return this.eGui;
      }
    }
    """)

    # =====================================================
    # GROUP STYLE
    # =====================================================

    group_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {}
        }

        if (params.value.includes('New')) {
            return {
                'backgroundColor': '#dcfce7',
                'color': '#166534',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Mid')) {
            return {
                'backgroundColor': '#dbeafe',
                'color': '#1d4ed8',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Old')) {
            return {
                'backgroundColor': '#fee2e2',
                'color': '#b91c1c',
                'fontWeight': '700'
            }
        }

        return {}
    }
    """)

    # =====================================================
    # ACTION STYLE
    # =====================================================

    action_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {}
        }

        if (params.value.includes('Avoid')) {
            return {
                'backgroundColor': '#fee2e2',
                'color': '#991b1b',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Monitor')) {
            return {
                'backgroundColor': '#fef3c7',
                'color': '#92400e',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Learn')) {
            return {
                'backgroundColor': '#dbeafe',
                'color': '#1d4ed8',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Trend')) {
            return {
                'backgroundColor': '#dcfce7',
                'color': '#166534',
                'fontWeight': '700'
            }
        }

        return {}
    }
    """)

    # =====================================================
    # COLUMN CONFIG
    # =====================================================

    for col in display_df.columns:

        col_lower = col.lower()

        # =================================================
        # IMAGE
        # =================================================

        if (
            image_col
            and col == image_col
        ):

            gb.configure_column(
                col,
                header_name="Image",
                cellRenderer=image_renderer,
                width=120,
                pinned="left",
                filter=False,
                sortable=False,
            )

        # =================================================
        # LINKS
        # =================================================

        if (
            "asin" in col_lower
            or "title" in col_lower
            or "brand" in col_lower
            or "keyword" in col_lower
        ):

            gb.configure_column(
                col,
                cellRenderer=cell_renderer
            )

        # =================================================
        # FREEZE COLUMNS
        # =================================================

        if col in [
            "ASIN",
            image_col,
            "ASIN Sales",
            "ASIN Revenue",
        ]:

            gb.configure_column(
                col,
                pinned="left"
            )

        # =================================================
        # GROUP COLORS
        # =================================================

        if col in [
            "Seller Group",
            "Listing Group",
        ]:

            gb.configure_column(
                col,
                cellStyle=group_style
            )

        # =================================================
        # ACTION COLOR
        # =================================================

        if col == "Action":

            gb.configure_column(
                col,
                cellStyle=action_style,
                width=220
            )

    # =====================================================
    # GRID OPTIONS
    # =====================================================

    grid_options = gb.build()

    grid_options["pagination"] = True

    grid_options["paginationPageSize"] = 100

    grid_options["autoSizeStrategy"] = {
        "type": "fitCellContents"
    }

    # =====================================================
    # GRID
    # =====================================================

    AgGrid(
        display_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        rowHeight=95,
        fit_columns_on_grid_load=False,
        columns_auto_size_mode="FIT_CONTENTS",
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
    )

    # =====================================================
    # COMPETITOR INTELLIGENCE
    # =====================================================

    st.markdown("---")
    st.markdown(
        "## Competitor Opportunity Intelligence"
    )

    competitor_summary = (
        filtered_df["Competitor Group"]
        .value_counts()
        .reset_index()
    )

    competitor_summary.columns = [
        "Group",
        "Count"
    ]

    # =====================================================
    # REVENUE DISTRIBUTION
    # =====================================================

    if revenue_col:

        st.markdown(
            "### Competitor Revenue Distribution"
        )

        revenue_distribution = (
            filtered_df.groupby(
                "Competitor Group"
            )[revenue_col]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.bar_chart(
            revenue_distribution
        )

    # =====================================================
    # INSIGHT CARDS
    # =====================================================

    for _, row in competitor_summary.iterrows():

        group_name = row["Group"]

        count = row["Count"]

        strategy = build_strategy(
            group_name
        )

        action = build_action(
            group_name
        )

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
                {group_name}
            </div>

            <div style="
                font-size:14px;
                color:#93c5fd;
                margin-bottom:10px;
            ">
                {count} ASINs detected
            </div>

            <div style="
                font-size:14px;
                color:#cbd5e1;
                line-height:1.6;
                margin-bottom:12px;
            ">
                {strategy}
            </div>

            <div style="
                display:inline-block;
                padding:8px 12px;
                border-radius:8px;
                background:#1e293b;
                color:#f8fafc;
                font-size:13px;
                font-weight:700;
            ">
                {action}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )
