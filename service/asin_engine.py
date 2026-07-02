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
# CLEAN NUMERIC
# =========================================================

def clean_numeric(value):

    if pd.isna(value):
        return 0

    value = str(value).strip()

    # remove currency
    value = value.replace("$", "")

    # remove spaces
    value = value.replace(" ", "")

    # =====================================================
    # HANDLE BOTH 1,234 and 1.234
    # =====================================================

    if "," in value and "." in value:

        value = value.replace(",", "")

    elif "," in value:

        value = value.replace(",", "")

    try:
        return float(value)

    except:
        return 0


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

    value = clean_numeric(value)

    if value > 1000:
        return "High Sales"

    elif value >= 500:
        return "Stable Sales"

    elif value > 0:
        return "Low Sales"

    return "No Sale"


# =========================================================
# SELLER GROUP
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
# LISTING GROUP
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
# GROUP BEFORE SALES
# =========================================================

def build_group_before_sales(row):

    seller = row.get("Seller Group")
    listing = row.get("Listing Group")

    if pd.isna(seller) or pd.isna(listing):
        return None

    return f"{seller} + {listing}"


# =========================================================
# FULL COMPETITOR GROUP
# =========================================================

def build_competitor_group(row):

    seller = row.get("Seller Group")
    listing = row.get("Listing Group")
    sales = row.get("Sales Group")

    if (
        pd.isna(seller)
        or pd.isna(listing)
        or pd.isna(sales)
    ):
        return None

    return f"{seller} + {listing} + {sales}"


# =========================================================
# STRATEGY
# =========================================================

def build_strategy(group):

    strategies = {

        "Old Seller + Old Listing + High Sales":
        "Strong moat. Avoid direct competition.",

        "Old Seller + New Listing + High Sales":
        "Large seller testing new market.",

        "Mid Seller + Mid Listing + Stable Sales":
        "Stable seller. Learn and follow patterns.",

        "Mid Seller + Mid Listing + High Sales":
        "Growing market opportunity. Research deeper.",

        "New Seller + New Listing + High Sales":
        "Trending product with strong momentum.",

        "New Seller + Mid Listing + Low Sales":
        "Weak market signal. Avoid scaling.",

        "New Seller + New Listing + Stable Sales":
        "Emerging seller with potential.",
    }

    return strategies.get(
        group,
        "Further competitor validation required."
    )


# =========================================================
# ACTION
# =========================================================

def build_action(group):

    actions = {

        "Old Seller + Old Listing + High Sales":
        "Avoid Competition",

        "Old Seller + New Listing + High Sales":
        "Monitor",

        "Mid Seller + Mid Listing + Stable Sales":
        "Learn",

        "Mid Seller + Mid Listing + High Sales":
        "Deep Research",

        "New Seller + New Listing + High Sales":
        "Trend Opportunity",

        "New Seller + Mid Listing + Low Sales":
        "Avoid",

        "New Seller + New Listing + Stable Sales":
        "Follow",
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

    # =====================================================
    # CLEAN SALES
    # =====================================================

    if sales_col:

        final_df[sales_col] = (
            final_df[sales_col]
            .apply(clean_numeric)
            .astype(int)
        )

        final_df["Sales Group"] = (
            final_df[sales_col]
            .apply(classify_sales_level)
        )

    else:

        final_df["Sales Group"] = "No Sale"

    # =====================================================
    # CLEAN REVENUE
    # =====================================================

    if revenue_col:

        final_df[revenue_col] = (
            final_df[revenue_col]
            .apply(clean_numeric)
            .astype(float)
        )

    # =====================================================
    # GROUPS
    # =====================================================

    final_df["Group Before Sales"] = (
        final_df.apply(
            build_group_before_sales,
            axis=1
        )
    )

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
    # IMAGE COLUMN
    # =====================================================

    image_col = None

    possible_image_cols = [
        "Image",
        "Image URL",
        "Main Image",
    ]

    for col in possible_image_cols:

        if col in final_df.columns:

            image_col = col
            break

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("## Filters")

    f1, f2, f3, f4 = st.columns(4)

    with f1:

        seller_filter = st.multiselect(
            "Seller Group",
            options=sorted(
                final_df["Seller Group"]
                .dropna()
                .unique()
            )
            if "Seller Group" in final_df.columns
            else []
        )

    with f2:

        listing_filter = st.multiselect(
            "Listing Group",
            options=sorted(
                final_df["Listing Group"]
                .dropna()
                .unique()
            )
            if "Listing Group" in final_df.columns
            else []
        )

    with f3:

        sales_filter = st.multiselect(
            "Sales Group",
            options=sorted(
                final_df["Sales Group"]
                .dropna()
                .unique()
            )
            if "Sales Group" in final_df.columns
            else []
        )

    with f4:

        action_filter = st.multiselect(
            "Action",
            options=sorted(
                final_df["Action"]
                .dropna()
                .unique()
            )
            if "Action" in final_df.columns
            else []
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
            filtered_df["Action"]
            .isin(action_filter)
        ]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search ASIN, keyword..."
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
    # DISPLAY DF
    # =====================================================

    display_df = filtered_df.copy()

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
                'backgroundColor': '#22c55e',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Mid')) {
            return {
                'backgroundColor': '#3b82f6',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Old')) {
            return {
                'backgroundColor': '#ef4444',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        return {}
    }
    """)

    # =====================================================
    # SALES STYLE
    # =====================================================

    sales_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {}
        }

        if (params.value.includes('High')) {
            return {
                'backgroundColor': '#16a34a',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Stable')) {
            return {
                'backgroundColor': '#2563eb',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Low')) {
            return {
                'backgroundColor': '#f59e0b',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        return {
            'backgroundColor': '#6b7280',
            'color': 'white',
            'fontWeight': '700'
        }
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
                'backgroundColor': '#ef4444',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Monitor')) {
            return {
                'backgroundColor': '#f59e0b',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Learn')) {
            return {
                'backgroundColor': '#3b82f6',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        if (params.value.includes('Trend')) {
            return {
                'backgroundColor': '#22c55e',
                'color': 'white',
                'fontWeight': '700'
            }
        }

        return {
            'backgroundColor': '#6b7280',
            'color': 'white',
            'fontWeight': '700'
        }
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
        # FREEZE
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
        # GROUP COLOR
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
        # SALES COLOR
        # =================================================

        if col == "Sales Group":

            gb.configure_column(
                col,
                cellStyle=sales_style
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

    # =====================================================
    # REVENUE DISTRIBUTION
    # =====================================================

    if revenue_col:

        st.markdown(
            "### Competitor Revenue Distribution"
        )

        revenue_distribution = (
            filtered_df.groupby(
                "Group Before Sales"
            )[revenue_col]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.bar_chart(
            revenue_distribution
        )

    # =========================================================
# CATEGORY MARKET SHARE BY GROUP BEFORE SALES
# =========================================================

st.markdown("---")
st.markdown("## Category Market Share Intelligence")

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

# =====================================================
# CATEGORY ANALYSIS
# =====================================================

if category_col:

    available_groups = sorted(
        filtered_df["Group Before Sales"]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_group = st.selectbox(
        "Select Group Before Sales",
        options=available_groups
    )

    group_df = filtered_df[
        filtered_df["Group Before Sales"]
        .astype(str)
        == selected_group
    ]

    # =================================================
    # CATEGORY SHARE
    # =================================================

    category_share_df = (
        group_df[category_col]
        .fillna("Unknown")
        .astype(str)
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .reset_index()
    )

    category_share_df.columns = [
        "Category",
        "Market Share %"
    ]

    # =================================================
    # DATAFRAME
    # =================================================

    st.dataframe(
        category_share_df,
        use_container_width=True,
        height=320
    )

    # =================================================
    # BAR CHART
    # =================================================

    chart_df = (
        category_share_df
        .set_index("Category")
    )

    st.bar_chart(
        chart_df
    )

    # =================================================
    # TOP CATEGORY
    # =================================================

    if not category_share_df.empty:

        top_category = (
            category_share_df.iloc[0]["Category"]
        )

        top_share = (
            category_share_df.iloc[0]["Market Share %"]
        )

        st.markdown(
            f"""
            <div style="
                padding:18px;
                margin-top:14px;
                border-radius:14px;
                background:#0b1220;
                border:1px solid #1f2937;
            ">

            <div style="
                font-size:18px;
                font-weight:700;
                color:#f8fafc;
                margin-bottom:10px;
            ">
                Category Intelligence
            </div>

            <div style="
                font-size:15px;
                color:#cbd5e1;
                line-height:1.8;
            ">

                <b>{top_category}</b>
                dominates this competitor structure with
                <b>{top_share}% market share</b>.

                <br><br>

                This indicates where most competitors
                are focusing inventory, traffic,
                and revenue concentration.

                <br><br>

                Recommended next step:
                analyze saturation,
                pricing strategy,
                review velocity,
                and sub-niche opportunities
                inside this category.

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

else:

    st.info(
        "No category column detected."
    )
    
    # =====================================================
    # COMPETITOR SUMMARY
    # =====================================================

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
    
    # =====================================================
    # FORMAT
    # =====================================================
    
    competitor_summary["Total Revenue"] = (
        competitor_summary["Total Revenue"]
        .fillna(0)
        .astype(float)
        .round(0)
    )
    
    competitor_summary["Total Sales"] = (
        competitor_summary["Total Sales"]
        .fillna(0)
        .astype(int)
    )
    
    # =====================================================
    # TABLE
    # =====================================================
    
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
    
        # ================================================
        # COLOR
        # ================================================
    
        strategy_lower = strategy.lower()
    
        if "avoid" in strategy_lower:
    
            bg_color = "#3b0d0d"
            border_color = "#ef4444"
    
        elif "follow" in strategy_lower:
    
            bg_color = "#0f172a"
            border_color = "#3b82f6"
    
        elif "scale" in strategy_lower:
    
            bg_color = "#052e16"
            border_color = "#22c55e"
    
        else:
    
            bg_color = "#1e293b"
            border_color = "#64748b"
    
        # ================================================
        # CARD
        # ================================================
    
        st.markdown(
            f"""
            <div style="
                padding:18px;
                margin-bottom:14px;
                border-radius:14px;
                background:{bg_color};
                border-left:6px solid {border_color};
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
