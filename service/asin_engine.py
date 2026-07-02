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

    # ==========================================
    # HEADER ALREADY CORRECT
    # ==========================================

    if is_valid_asin_header(df.columns):
        return df

    # ==========================================
    # FIRST ROW HEADER
    # ==========================================

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

    # ==========================================
    # SECOND ROW HEADER
    # ==========================================

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

    if pd.isna(seller) or pd.isna(listing):
        return None

    return f"{seller} + {listing}"


# =========================================================
# STRATEGY
# =========================================================

def build_strategy(group):

    strategies = {

        "Old Seller + Old Listing":
        "Strong moat competitor. Avoid direct competition.",

        "Old Seller + New Listing":
        "Large seller testing niche. Monitor closely.",

        "Mid Seller + Mid Listing":
        "Stable seller. Learn and follow patterns.",

        "New Seller + New Listing":
        "Trend opportunity. Watch acceleration.",

        "New Seller + Mid Listing":
        "Weak demand. Low priority.",
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

        "Old Seller + Old Listing":
        "Avoid",

        "Old Seller + New Listing":
        "Monitor",

        "Mid Seller + Mid Listing":
        "Learn",

        "New Seller + New Listing":
        "Scale",

        "New Seller + Mid Listing":
        "Ignore",
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

        final_df["Listing Age Months"] = (
            (
                current_date -
                final_df[creation_col]
            ).dt.days / 30
        ).round(0)

        final_df["Listing Age Months"] = (
            final_df["Listing Age Months"]
            .fillna(0)
            .astype(int)
        )

        final_df["Seller Age Months"] = (
            final_df["Listing Age Months"]
        )

        # ==========================================
        # GROUPS
        # ==========================================

        final_df["Seller Group"] = (
            final_df["Seller Age Months"]
            .apply(classify_seller_age)
        )

        final_df["Listing Group"] = (
            final_df["Listing Age Months"]
            .apply(classify_listing_age)
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
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search ASIN, title, keyword..."
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

        this.eGui.innerHTML = `
          <img
            src="${params.value}"
            style="
              width:80px;
              height:80px;
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

        if (params.value.includes('Scale')) {
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

        # ==========================================
        # IMAGE
        # ==========================================

        if col in IMAGE_COLUMNS:

            gb.configure_column(
                col,
                header_name="Image",
                cellRenderer=image_renderer,
                width=120,
                pinned="left",
            )

        # ==========================================
        # LINKS
        # ==========================================

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

        # ==========================================
        # FREEZE ASIN
        # ==========================================

        if "asin" in col_lower:

            gb.configure_column(
                col,
                pinned="left",
                width=130
            )

        # ==========================================
        # AGE COLOR
        # ==========================================

        if (
            col == "Listing Age Months"
            or col == "Seller Age Months"
        ):

            gb.configure_column(
                col,
                cellStyle=age_cell_style
            )

        # ==========================================
        # ACTION COLOR
        # ==========================================

        if col == "Action":

            gb.configure_column(
                col,
                cellStyle=action_cell_style,
                width=180
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
        rowHeight=90,
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
        # BAR CHART
        # =================================================

        st.markdown(
            "### Competitor Distribution"
        )

        chart_df = competitor_summary.set_index(
            "Group"
        )

        st.bar_chart(
            chart_df["Count"]
        )

        # =================================================
        # AREA CHART
        # =================================================

        st.markdown(
            "### Market Opportunity Trend"
        )

        st.area_chart(
            chart_df["Count"]
        )

        # =================================================
        # LINE CHART
        # =================================================

        st.markdown(
            "### Competitor Growth Signals"
        )

        st.line_chart(
            chart_df["Count"]
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
