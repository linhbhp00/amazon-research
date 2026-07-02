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

IMAGE_COLUMNS = [
    "Image URL",
    "Image",
    "Main Image",
    "image_url",
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
        font-weight:600;
    ">
    {text}
    </a>
    """


# =========================================================
# URL LINK
# =========================================================

def make_url_link(url):

    if pd.isna(url):
        return url

    url = str(url)

    return f"""
    <a href="{url}"
    target="_blank"
    style="
        color:#60a5fa;
        text-decoration:none;
        font-weight:600;
    ">
    Open URL
    </a>
    """


# =========================================================
# SALES GROUP
# =========================================================

def classify_sales_level(value):

    try:
        value = float(value)
    except:
        return "Unknown"

    if value >= 50000:
        return "High Sales"

    elif value >= 10000:
        return "Mid Sales"

    return "Low Sales"


# =========================================================
# SELLER AGE
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
# LISTING AGE
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
        "Strong moat competitor. Avoid direct competition.",

        "Old Seller + New Listing + High Sales":
        "Large seller testing niche. Monitor closely.",

        "Mid Seller + Mid Listing + Mid Sales":
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

        "Mid Seller + Mid Listing + Mid Sales":
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

    # =====================================================
    # REMOVE DUPLICATE COLUMNS
    # =====================================================

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

        # =================================================
        # LISTING AGE
        # =================================================

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

        # =================================================
        # SELLER AGE
        # =================================================

        final_df["Seller Age (mo)"] = (
            final_df["Listing Age (mo)"]
        )

        # =================================================
        # SELLER GROUP
        # =================================================

        final_df["Seller Group"] = (
            final_df["Seller Age (mo)"]
            .apply(classify_seller_age)
        )

        # =================================================
        # LISTING GROUP
        # =================================================

        final_df["Listing Group"] = (
            final_df["Listing Age (mo)"]
            .apply(classify_listing_age)
        )

    # =====================================================
    # SALES COLUMN
    # =====================================================

    sales_col = None

    possible_sales_cols = [
        "Revenue",
        "Monthly Revenue",
        "Sales",
        "Monthly Sales",
        "Est Revenue",
    ]

    for col in possible_sales_cols:

        if col in final_df.columns:

            sales_col = col
            break

    if sales_col:

        final_df[sales_col] = pd.to_numeric(
            final_df[sales_col],
            errors="coerce"
        ).fillna(0)

        final_df["Sales Group"] = (
            final_df[sales_col]
            .apply(classify_sales_level)
        )

    else:

        final_df["Sales Group"] = "Unknown"

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
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search ASIN, keyword, title..."
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
    # KW SEARCH POSITION
    # =====================================================

    if "KW Search" in display_df.columns:

        kw_col = display_df.pop("KW Search")

        display_df.insert(
            2,
            "KW Search",
            kw_col
        )

    # =====================================================
    # ASIN LINKS
    # =====================================================

    for col in display_df.columns:

        if "asin" in col.lower():

            display_df[col] = (
                display_df[col]
                .apply(make_asin_link)
            )

    # =====================================================
    # SEARCH LINKS
    # =====================================================

    for col in display_df.columns:

        col_lower = col.lower()

        if (
            "title" in col_lower
            or "brand" in col_lower
            or "keyword" in col_lower
        ):

            display_df[col] = (
                display_df[col]
                .apply(make_search_link)
            )

    # =====================================================
    # URL LINKS
    # =====================================================

    for col in display_df.columns:

        if (
            "url" in col.lower()
            and col not in IMAGE_COLUMNS
        ):

            display_df[col] = (
                display_df[col]
                .apply(make_url_link)
            )

    # =====================================================
    # METRICS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Rows",
        f"{len(filtered_df):,}"
    )

    c2.metric(
        "Columns",
        len(filtered_df.columns)
    )

    c3.metric(
        "Unique ASINs",
        filtered_df["ASIN"].nunique()
        if "ASIN" in filtered_df.columns
        else 0
    )

    c4.metric(
        "Competitor Groups",
        filtered_df["Competitor Group"].nunique()
        if "Competitor Group" in filtered_df.columns
        else 0
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
              border:1px solid #334155;
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
    # AGE STYLE
    # =====================================================

    age_cell_style = JsCode("""
    function(params) {

        if (params.value <= 6) {
            return {
                'backgroundColor': '#dcfce7',
                'color': '#166534',
                'fontWeight': '700'
            }
        }

        else if (params.value <= 24) {
            return {
                'backgroundColor': '#dbeafe',
                'color': '#1d4ed8',
                'fontWeight': '700'
            }
        }

        return {
            'backgroundColor': '#fee2e2',
            'color': '#b91c1c',
            'fontWeight': '700'
        }
    }
    """)

    # =====================================================
    # ACTION STYLE
    # =====================================================

    action_cell_style = JsCode("""
    function(params) {

        if (!params.value) {
            return {}
        }

        if (params.value.includes('Avoid')) {
            return {
                'backgroundColor': '#fee2e2',
                'color': '#b91c1c',
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

        return {
            'backgroundColor': '#f3f4f6',
            'color': '#374151',
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
            "image" in col_lower
            or "image url" in col_lower
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
            or "url" in col_lower
        ):

            gb.configure_column(
                col,
                cellRenderer=cell_renderer
            )

        # =================================================
        # FREEZE ASIN
        # =================================================

        if "asin" in col_lower:

            gb.configure_column(
                col,
                pinned="left",
                width=130
            )

        # =================================================
        # AGE COLOR
        # =================================================

        if (
            col == "Listing Age (mo)"
            or col == "Seller Age (mo)"
        ):

            gb.configure_column(
                col,
                cellStyle=age_cell_style
            )

        # =================================================
        # ACTION COLOR
        # =================================================

        if col == "Action":

            gb.configure_column(
                col,
                cellStyle=action_cell_style,
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

    if "Competitor Group" in filtered_df.columns:

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

        # =================================================
        # REVENUE DISTRIBUTION
        # =================================================

        st.markdown(
            "### Competitor Revenue Distribution"
        )

        if sales_col:

            revenue_chart_df = (
                filtered_df.groupby(
                    "Competitor Group"
                )[sales_col]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            st.bar_chart(
                revenue_chart_df
            )

        else:

            fallback_chart_df = (
                competitor_summary
                .set_index("Group")
            )

            st.bar_chart(
                fallback_chart_df["Count"]
            )

        # =================================================
        # CATEGORY SHARE
        # =================================================

        possible_category_cols = [
            "Category",
            "Main Category",
            "Product Category",
        ]

        category_col = None

        for col in possible_category_cols:

            if col in filtered_df.columns:

                category_col = col
                break

        if category_col:

            st.markdown(
                "### Category Market Share"
            )

            selected_group = st.selectbox(
                "Select Competitor Group",
                options=sorted(
                    filtered_df[
                        "Competitor Group"
                    ]
                    .dropna()
                    .unique()
                )
            )

            category_df = filtered_df[
                filtered_df["Competitor Group"]
                == selected_group
            ]

            category_summary = (
                category_df[category_col]
                .astype(str)
                .value_counts(normalize=True)
                .mul(100)
                .round(1)
                .reset_index()
            )

            category_summary.columns = [
                "Category",
                "Market Share %"
            ]

            st.dataframe(
                category_summary,
                use_container_width=True,
                height=350
            )

            chart_data = category_summary.set_index(
                "Category"
            )

            st.bar_chart(
                chart_data["Market Share %"]
            )

        # =================================================
        # INSIGHT CARDS
        # =================================================

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
