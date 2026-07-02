import streamlit as st
import pandas as pd
import numpy as np

from datetime import datetime

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# LINK HELPERS
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):
        return asin

    asin = str(asin)

    return f"""
    <a href="https://www.amazon.com/dp/{asin}"
       target="_blank">
       {asin}
    </a>
    """

# =========================================================
# LISTING AGE
# =========================================================

def calculate_listing_age(created_date):

    try:

        created_date = pd.to_datetime(
            created_date,
            errors="coerce"
        )

        if pd.isna(created_date):
            return np.nan

        today = pd.Timestamp.today()

        age_days = (
            today - created_date
        ).days

        age_months = round(
            age_days / 30,
            1
        )

        return age_months

    except:

        return np.nan

# =========================================================
# AGE SCORE
# =========================================================

def detect_listing_stage(age):

    if pd.isna(age):
        return "Unknown"

    if age <= 3:
        return "New Launch"

    elif age <= 12:
        return "Growth"

    elif age <= 36:
        return "Mature"

    else:
        return "Old Listing"

# =========================================================
# COMPETITION LEVEL
# =========================================================

def detect_competition(row):

    try:

        reviews = float(
            row.get("Review Count", 0)
        )

        rating = float(
            row.get("Review Rating", 0)
        )

        if reviews <= 50:
            return "Low Competition"

        elif reviews <= 300:
            return "Medium Competition"

        else:
            return "High Competition"

    except:

        return "Unknown"

# =========================================================
# SALES LEVEL
# =========================================================

def detect_sales_level(row):

    try:

        sales = float(
            row.get("Monthly Sales", 0)
        )

        if sales >= 5000:
            return "Best Seller"

        elif sales >= 1000:
            return "Strong Seller"

        elif sales >= 300:
            return "Average Seller"

        else:
            return "Weak Seller"

    except:

        return "Unknown"

# =========================================================
# OPPORTUNITY SCORE
# =========================================================

def calculate_opportunity_score(row):

    score = 0

    try:

        sales = float(
            row.get("Monthly Sales", 0)
        )

        reviews = float(
            row.get("Review Count", 0)
        )

        rating = float(
            row.get("Review Rating", 0)
        )

        age = float(
            row.get("Listing Age (Months)", 0)
        )

        # -------------------------------------------------
        # SALES
        # -------------------------------------------------

        if sales >= 5000:
            score += 40

        elif sales >= 1000:
            score += 30

        elif sales >= 300:
            score += 20

        # -------------------------------------------------
        # REVIEWS
        # -------------------------------------------------

        if reviews <= 50:
            score += 30

        elif reviews <= 300:
            score += 20

        else:
            score += 10

        # -------------------------------------------------
        # RATING
        # -------------------------------------------------

        if rating >= 4.5:
            score += 15

        elif rating >= 4:
            score += 10

        # -------------------------------------------------
        # LISTING AGE
        # -------------------------------------------------

        if age <= 6:
            score += 15

        elif age <= 24:
            score += 10

        return score

    except:

        return 0

# =========================================================
# COLOR TAGS
# =========================================================

def detect_color_group(score):

    if score >= 80:
        return "🟢 High Opportunity"

    elif score >= 60:
        return "🟡 Medium Opportunity"

    else:
        return "🔴 Difficult Market"

# =========================================================
# MAIN ENGINE
# =========================================================

def render_asin_engine(df):

    # =====================================================
    # EMPTY
    # =====================================================

    if df is None or df.empty:

        st.warning("No ASIN dataset loaded.")

        return

    # =====================================================
    # TITLE
    # =====================================================

    st.markdown("# ASIN Intelligence")

    # =====================================================
    # COPY DF
    # =====================================================

    working_df = df.copy()

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    if "Creation Date" in working_df.columns:

        working_df["Listing Age (Months)"] = (
            working_df["Creation Date"]
            .apply(calculate_listing_age)
        )

    else:

        working_df["Listing Age (Months)"] = np.nan

    # =====================================================
    # STAGE
    # =====================================================

    working_df["Listing Stage"] = (
        working_df["Listing Age (Months)"]
        .apply(detect_listing_stage)
    )

    # =====================================================
    # SALES LEVEL
    # =====================================================

    working_df["Sales Level"] = (

        working_df.apply(
            detect_sales_level,
            axis=1
        )
    )

    # =====================================================
    # COMPETITION
    # =====================================================

    working_df["Competition Level"] = (

        working_df.apply(
            detect_competition,
            axis=1
        )
    )

    # =====================================================
    # OPPORTUNITY
    # =====================================================

    working_df["Opportunity Score"] = (

        working_df.apply(
            calculate_opportunity_score,
            axis=1
        )
    )

    # =====================================================
    # COLOR GROUP
    # =====================================================

    working_df["Market Opportunity"] = (

        working_df["Opportunity Score"]

        .apply(detect_color_group)
    )

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown("## Dataset Filters")

    col1, col2, col3 = st.columns(3)

    filtered_df = working_df.copy()

    # -----------------------------------------------------
    # STAGE
    # -----------------------------------------------------

    with col1:

        stage_filter = st.multiselect(

            "Listing Stage",

            options=sorted(
                filtered_df["Listing Stage"]
                .dropna()
                .unique()
            )
        )

        if stage_filter:

            filtered_df = filtered_df[
                filtered_df["Listing Stage"]
                .isin(stage_filter)
            ]

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

    with col2:

        sales_filter = st.multiselect(

            "Sales Level",

            options=sorted(
                filtered_df["Sales Level"]
                .dropna()
                .unique()
            )
        )

        if sales_filter:

            filtered_df = filtered_df[
                filtered_df["Sales Level"]
                .isin(sales_filter)
            ]

    # -----------------------------------------------------
    # OPPORTUNITY
    # -----------------------------------------------------

    with col3:

        opportunity_filter = st.multiselect(

            "Market Opportunity",

            options=sorted(
                filtered_df["Market Opportunity"]
                .dropna()
                .unique()
            )
        )

        if opportunity_filter:

            filtered_df = filtered_df[
                filtered_df["Market Opportunity"]
                .isin(opportunity_filter)
            ]

    # =====================================================
    # SEARCH
    # =====================================================

    search_value = st.text_input(

        "Quick Search",

        placeholder="Search ASIN, keyword, brand..."
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
    # METRICS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "ASIN Count",
        f"{len(filtered_df):,}"
    )

    c2.metric(
        "Avg Listing Age",
        f"{round(filtered_df['Listing Age (Months)'].mean(),1)} M"
        if "Listing Age (Months)" in filtered_df.columns
        else "0"
    )

    c3.metric(
        "Avg Opportunity",
        f"{round(filtered_df['Opportunity Score'].mean(),1)}"
        if "Opportunity Score" in filtered_df.columns
        else "0"
    )

    c4.metric(
        "Unique Keywords",
        filtered_df["Keyword Search"]
        .nunique()
        if "Keyword Search" in filtered_df.columns
        else 0
    )

    # =====================================================
    # DISPLAY DF
    # =====================================================

    display_df = filtered_df.copy()

    # =====================================================
    # ASIN LINK
    # =====================================================

    asin_col_candidates = [

        "ASIN",
        "Asin",
        "asin"
    ]

    asin_col = None

    for col in asin_col_candidates:

        if col in display_df.columns:

            asin_col = col

            break

    if asin_col:

        display_df[asin_col] = (

            display_df[asin_col]

            .apply(make_asin_link)
        )

    # =====================================================
    # IMAGE HTML
    # =====================================================

    image_col_candidates = [

        "Image URL",
        "Image",
        "Main Image"
    ]

    image_col = None

    for col in image_col_candidates:

        if col in display_df.columns:

            image_col = col

            break

    if image_col:

        display_df[image_col] = (

            display_df[image_col]

            .apply(

                lambda x:

                f"""
                <img src="{x}"
                     width="70"
                     style="border-radius:8px;">
                """

                if pd.notna(x)
                else ""
            )
        )

    # =====================================================
    # GRID
    # =====================================================

    gb = GridOptionsBuilder.from_dataframe(
        display_df
    )

    gb.configure_default_column(

        sortable=True,
        filter=True,
        resizable=True,
        editable=False,
        floatingFilter=True,

        minWidth=140,
        flex=1,
    )

    # =====================================================
    # PIN FIRST
    # =====================================================

    first_col = display_df.columns[0]

    gb.configure_column(

        first_col,

        pinned="left",
        width=160
    )

    # =====================================================
    # WIDTHS
    # =====================================================

    for col in display_df.columns:

        width = 160

        col_lower = col.lower()

        if "title" in col_lower:
            width = 420

        elif "keyword" in col_lower:
            width = 240

        elif "image" in col_lower:
            width = 120

        elif "asin" in col_lower:
            width = 140

        elif "score" in col_lower:
            width = 150

        gb.configure_column(
            col,
            width=width
        )

    # =====================================================
    # HTML RENDERER
    # =====================================================

    cell_renderer = JsCode("""

    class UrlCellRenderer {

      init(params) {

        this.eGui = document.createElement('div');

        this.eGui.innerHTML = params.value || "";
      }

      getGui() {

        return this.eGui;
      }
    }

    """)

    if asin_col:

        gb.configure_column(

            asin_col,

            cellRenderer=cell_renderer
        )

    if image_col:

        gb.configure_column(

            image_col,

            cellRenderer=cell_renderer
        )

    # =====================================================
    # COLOR RULES
    # =====================================================

    gb.configure_column(

        "Market Opportunity",

        cellStyle=JsCode("""

        function(params) {

            if (params.value.includes("🟢")) {

                return {
                    'backgroundColor': '#14532d',
                    'color': 'white',
                    'fontWeight': 'bold'
                }
            }

            if (params.value.includes("🟡")) {

                return {
                    'backgroundColor': '#854d0e',
                    'color': 'white',
                    'fontWeight': 'bold'
                }
            }

            return {
                'backgroundColor': '#7f1d1d',
                'color': 'white',
                'fontWeight': 'bold'
            }
        }

        """)
    )

    # =====================================================
    # GRID OPTIONS
    # =====================================================

    grid_options = gb.build()

    grid_options["domLayout"] = "normal"

    grid_options["animateRows"] = True

    grid_options["rowHeight"] = 90

    # =====================================================
    # TABLE
    # =====================================================

    st.markdown("## ASIN Market Intelligence")

    try:

        AgGrid(

            display_df,

            gridOptions=grid_options,

            theme="alpine-dark",

            height=720,

            fit_columns_on_grid_load=False,

            update_mode=GridUpdateMode.NO_UPDATE,

            allow_unsafe_jscode=True,

            enable_enterprise_modules=False,

            reload_data=False,
        )

    except Exception as e:

        st.error(f"AgGrid Error: {e}")

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("---")

    st.markdown("# Strategic ASIN Insights")

    # =====================================================
    # HIGH OPPORTUNITY
    # =====================================================

    high_opportunity_df = filtered_df[

        filtered_df["Market Opportunity"]

        == "🟢 High Opportunity"
    ]

    # =====================================================
    # NEW LISTINGS
    # =====================================================

    new_listing_df = filtered_df[

        filtered_df["Listing Stage"]

        == "New Launch"
    ]

    # =====================================================
    # BEST SELLERS
    # =====================================================

    best_seller_df = filtered_df[

        filtered_df["Sales Level"]

        == "Best Seller"
    ]

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3 = st.tabs([

        "High Opportunity",
        "New Listings",
        "Best Sellers"
    ])

    # =====================================================
    # TAB 1
    # =====================================================

    with tab1:

        st.metric(
            "High Opportunity ASINs",
            len(high_opportunity_df)
        )

        st.dataframe(
            high_opportunity_df,
            use_container_width=True,
            height=500
        )

    # =====================================================
    # TAB 2
    # =====================================================

    with tab2:

        st.metric(
            "New Listings",
            len(new_listing_df)
        )

        st.dataframe(
            new_listing_df,
            use_container_width=True,
            height=500
        )

    # =====================================================
    # TAB 3
    # =====================================================

    with tab3:

        st.metric(
            "Best Sellers",
            len(best_seller_df)
        )

        st.dataframe(
            best_seller_df,
            use_container_width=True,
            height=500
        )
