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
    # CASE 1
    # HEADER ALREADY CORRECT
    # ==========================================

    if is_valid_asin_header(df.columns):
        return df

    # ==========================================
    # CASE 2
    # HEADER IN FIRST ROW
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
    # CASE 3
    # HEADER IN SECOND ROW
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
# AMAZON SEARCH LINK
# =========================================================

def make_search_link(text):

    if pd.isna(text):
        return text

    text = str(text)

    return f"""
    <a href="https://www.amazon.com/s?k={quote_plus(text)}"
    target="_blank"
    style="color:#60a5fa;text-decoration:none;font-weight:500;">
    {text}
    </a>
    """


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
    style="color:#60a5fa;text-decoration:none;font-weight:500;">
    {asin}
    </a>
    """


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
    # HEADER FIX
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
    # SEARCH
    # =====================================================

    search_value = st.text_input(
        "Quick Search",
        placeholder="Search ASIN, title, brand..."
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
    # DISPLAY DATAFRAME
    # =====================================================

    display_df = filtered_df.copy()

    # ==========================================
    # ASIN LINKS
    # ==========================================

    for col in display_df.columns:

        if "asin" in col.lower():

            display_df[col] = (
                display_df[col]
                .apply(make_asin_link)
            )

    # ==========================================
    # TITLE LINKS
    # ==========================================

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
    # METRICS
    # =====================================================

    c1, c2, c3 = st.columns(3)

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

    # =====================================================
    # TABLE
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
        wrapText=False,
        autoHeight=False,
    )

    # =====================================================
    # LINK RENDERER
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

    for col in display_df.columns:

        col_lower = col.lower()

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

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    # =====================================================
    # GRID
    # =====================================================

    AgGrid(
        display_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        columns_auto_size_mode="FIT_CONTENTS",
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
    )

    # =====================================================
    # QUICK INSIGHTS
    # =====================================================

    st.markdown("---")
    st.markdown("## ASIN Research Insights")

    insights = [

        {
            "title": "Winning ASIN Detection",
            "desc": (
                "Identify high-frequency ASINs appearing repeatedly across keyword demand."
            )
        },

        {
            "title": "Brand Expansion Opportunities",
            "desc": (
                "Analyze brands dominating multiple search clusters and niches."
            )
        },

        {
            "title": "Keyword-to-ASIN Mapping",
            "desc": (
                "Track which products capture the highest buyer intent keywords."
            )
        },

        {
            "title": "Listing Optimization",
            "desc": (
                "Improve titles, SEO structure, and conversion-focused keyword coverage."
            )
        },

        {
            "title": "Competitive Intelligence",
            "desc": (
                "Monitor overlapping ASIN visibility across multiple market segments."
            )
        },
    ]

    for item in insights:

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
                {item['title']}
            </div>

            <div style="
                font-size:14px;
                color:#cbd5e1;
                line-height:1.6;
            ">
                {item['desc']}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )
