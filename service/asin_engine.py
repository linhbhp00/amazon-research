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

from utils.csv_utils import read_csv_safe


# =========================================================
# HELPERS
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):
        return ""

    asin = str(asin).strip()

    return f"""
    <a href="https://www.amazon.com/dp/{asin}"
       target="_blank"
       style="color:#60a5fa;font-weight:600;text-decoration:none;">
       {asin}
    </a>
    """


def classify_listing_age(days):

    if pd.isna(days):
        return "Unknown"

    if days <= 180:
        return "New Listing"

    elif days <= 720:
        return "Growing Listing"

    return "Mature Listing"


def age_score_color(group):

    if group == "New Listing":
        return "#16a34a"

    elif group == "Growing Listing":
        return "#eab308"

    return "#dc2626"


# =========================================================
# MAIN ENGINE
# =========================================================

def render_asin_engine():

    st.markdown("# ASIN Intelligence Engine")

    uploaded_file = st.file_uploader(
        "Upload ASIN Intelligence CSV",
        type=["csv"],
        key="asin_engine_upload"
    )

    if uploaded_file is None:
        st.info("Upload ASIN CSV to begin.")
        return

    # =====================================================
    # READ CSV SAFE
    # =====================================================

    df = read_csv_safe(uploaded_file)

    if df.empty:
        st.error("Cannot read CSV.")
        return

    # =====================================================
    # CLEAN COLUMNS
    # =====================================================

    df.columns = [str(col).strip() for col in df.columns]

    # =====================================================
    # REQUIRED COLUMN CHECK
    # =====================================================

    asin_col = None

    possible_asin_cols = [
        "ASIN",
        "asin"
    ]

    for col in possible_asin_cols:

        if col in df.columns:
            asin_col = col
            break

    if asin_col is None:
        st.error("ASIN column not found.")
        return

    # =====================================================
    # CREATION DATE
    # =====================================================

    creation_col = None

    possible_creation_cols = [
        "Creation Date",
        "creation_date",
        "Created",
    ]

    for col in possible_creation_cols:

        if col in df.columns:
            creation_col = col
            break

    if creation_col:

        df[creation_col] = pd.to_datetime(
            df[creation_col],
            errors="coerce"
        )

        today = pd.Timestamp.now()

        df["Listing Age Days"] = (
            today - df[creation_col]
        ).dt.days

        df["Listing Age Years"] = (
            df["Listing Age Days"] / 365
        ).round(1)

        df["Listing Status"] = df[
            "Listing Age Days"
        ].apply(classify_listing_age)

    else:

        df["Listing Age Days"] = np.nan
        df["Listing Age Years"] = np.nan
        df["Listing Status"] = "Unknown"

    # =====================================================
    # ASIN LINK
    # =====================================================

    df["ASIN Link"] = df[asin_col].apply(
        make_asin_link
    )

    # =====================================================
    # REVIEW COUNT
    # =====================================================

    review_col = None

    possible_review_cols = [
        "Review Count",
        "Reviews",
        "review_count"
    ]

    for col in possible_review_cols:

        if col in df.columns:
            review_col = col
            break

    if review_col:

        df[review_col] = pd.to_numeric(
            df[review_col],
            errors="coerce"
        )

    # =====================================================
    # PRICE
    # =====================================================

    price_col = None

    possible_price_cols = [
        "Price",
        "price"
    ]

    for col in possible_price_cols:

        if col in df.columns:
            price_col = col
            break

    if price_col:

        df[price_col] = (
            df[price_col]
            .astype(str)
            .str.replace("$", "", regex=False)
        )

        df[price_col] = pd.to_numeric(
            df[price_col],
            errors="coerce"
        )

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    with c1:

        status_filter = st.multiselect(
            "Listing Status",
            options=sorted(
                df["Listing Status"]
                .dropna()
                .unique()
            )
        )

    with c2:

        if review_col:

            review_threshold = st.slider(
                "Min Reviews",
                0,
                int(df[review_col].max())
                if not df[review_col].isna().all()
                else 1000,
                0
            )

        else:

            review_threshold = 0

    with c3:

        search_value = st.text_input(
            "Search",
            placeholder="Search ASIN / title..."
        )

    # =====================================================
    # FILTER DF
    # =====================================================

    filtered_df = df.copy()

    if status_filter:

        filtered_df = filtered_df[
            filtered_df["Listing Status"]
            .isin(status_filter)
        ]

    if review_col:

        filtered_df = filtered_df[
            filtered_df[review_col]
            >= review_threshold
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

    st.markdown("## Market Overview")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total ASINs",
        f"{len(filtered_df):,}"
    )

    m2.metric(
        "New Listings",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "New Listing"
            ]
        )
    )

    m3.metric(
        "Growing Listings",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "Growing Listing"
            ]
        )
    )

    m4.metric(
        "Mature Listings",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "Mature Listing"
            ]
        )
    )

    # =====================================================
    # STRATEGIC INSIGHTS
    # =====================================================

    st.markdown("## Strategic Insights")

    insight_rows = []

    if review_col:

        low_review_new = filtered_df[
            (filtered_df["Listing Status"] == "New Listing")
            &
            (filtered_df[review_col] <= 100)
        ]

        if len(low_review_new) >= 5:

            insight_rows.append({
                "Insight":
                "Many new low-review listings detected",
                "Signal":
                "Possible fast-growing niche",
                "Priority":
                "High Opportunity"
            })

    mature_count = len(
        filtered_df[
            filtered_df["Listing Status"]
            == "Mature Listing"
        ]
    )

    if mature_count >= (
        len(filtered_df) * 0.6
    ):

        insight_rows.append({
            "Insight":
            "Market dominated by mature sellers",
            "Signal":
            "High barrier to entry",
            "Priority":
            "High Competition"
        })

    insight_df = pd.DataFrame(insight_rows)

    if not insight_df.empty:

        st.dataframe(
            insight_df,
            use_container_width=True,
            height=180
        )

    # =====================================================
    # AGGRID
    # =====================================================

    st.markdown("## ASIN Intelligence Table")

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        minWidth=140,
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

    gb.configure_column(
        "ASIN Link",
        headerName="ASIN",
        cellRenderer=cell_renderer,
        width=140,
        pinned="left"
    )

    # =====================================================
    # STATUS COLOR
    # =====================================================

    status_style = JsCode("""
    function(params) {

        if (params.value == 'New Listing') {

            return {
                'backgroundColor': '#052e16',
                'color': '#4ade80',
                'fontWeight': '600'
            }
        }

        else if (params.value == 'Growing Listing') {

            return {
                'backgroundColor': '#422006',
                'color': '#fde047',
                'fontWeight': '600'
            }
        }

        else if (params.value == 'Mature Listing') {

            return {
                'backgroundColor': '#450a0a',
                'color': '#f87171',
                'fontWeight': '600'
            }
        }
    }
    """)

    gb.configure_column(
        "Listing Status",
        cellStyle=status_style,
        width=180
    )

    # =====================================================
    # IMAGE RENDERER
    # =====================================================

    image_col = None

    possible_image_cols = [
        "Image URL",
        "image",
        "image_url"
    ]

    for col in possible_image_cols:

        if col in filtered_df.columns:
            image_col = col
            break

    if image_col:

        image_renderer = JsCode("""
        class ImgCellRenderer {

            init(params) {

                this.eGui =
                    document.createElement('img');

                this.eGui.setAttribute(
                    'src',
                    params.value
                );

                this.eGui.setAttribute(
                    'width',
                    '60'
                );

                this.eGui.style.borderRadius = '8px';
            }

            getGui() {
                return this.eGui;
            }
        }
        """)

        gb.configure_column(
            image_col,
            cellRenderer=image_renderer,
            width=90
        )

    # =====================================================
    # GRID OPTIONS
    # =====================================================

    grid_options = gb.build()

    grid_options["rowHeight"] = 72

    grid_options["animateRows"] = True

    grid_options["domLayout"] = "normal"

    # =====================================================
    # RENDER GRID
    # =====================================================

    AgGrid(
        filtered_df,

        gridOptions=grid_options,

        theme="alpine-dark",

        allow_unsafe_jscode=True,

        update_mode=GridUpdateMode.NO_UPDATE,

        fit_columns_on_grid_load=True,

        enable_enterprise_modules=True,

        height=720,
    )
