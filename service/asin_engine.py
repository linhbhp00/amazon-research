# =========================================================
# service/asin_engine.py
# =========================================================

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

def calculate_listing_age(date_value):

    try:

        created = pd.to_datetime(
            date_value,
            errors="coerce"
        )

        if pd.isna(created):
            return np.nan

        today = pd.Timestamp.today()

        age_days = (today - created).days

        return round(age_days / 30)

    except:
        return np.nan


def classify_listing_age(months):

    if pd.isna(months):
        return "Unknown"

    if months <= 3:
        return "New Launch"

    elif months <= 12:
        return "Growing"

    elif months <= 36:
        return "Mature"

    return "Established"


def age_color(status):

    mapping = {
        "New Launch": "#22c55e",
        "Growing": "#3b82f6",
        "Mature": "#f59e0b",
        "Established": "#ef4444",
        "Unknown": "#6b7280"
    }

    return mapping.get(status, "#6b7280")


# =========================================================
# MAIN ENGINE
# =========================================================

def render_asin_engine():

    st.markdown("# ASIN Intelligence")

    # =====================================================
    # SESSION
    # =====================================================

    if "asin_df" not in st.session_state:
        st.session_state.asin_df = None

    if "asin_file_names" not in st.session_state:
        st.session_state.asin_file_names = []

    # =====================================================
    # SIDEBAR IMPORT
    # =====================================================

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ASIN Intelligence")

    uploaded_files = st.sidebar.file_uploader(
        "Upload ASIN CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="asin_csv"
    )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    if uploaded_files:

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:
                    st.warning(
                        f"Cannot read {uploaded_file.name}"
                    )
                    continue

                # =========================================
                # FIX HEADER
                # =========================================

                if df.columns.tolist()[0] == 0:

                    header_row = df.iloc[0]

                    df = df[1:].copy()

                    df.columns = header_row

                df = df.reset_index(drop=True)

                # =========================================
                # STANDARDIZE COLUMNS
                # =========================================

                df.columns = [
                    str(col).strip()
                    for col in df.columns
                ]

                # =========================================
                # LISTING AGE
                # =========================================

                creation_col = None

                possible_dates = [
                    "Creation Date",
                    "creation date",
                    "Created",
                    "Date First Available"
                ]

                for col in possible_dates:

                    if col in df.columns:
                        creation_col = col
                        break

                if creation_col:

                    df["Listing Age (Months)"] = (
                        df[creation_col]
                        .apply(calculate_listing_age)
                    )

                    df["Listing Status"] = (
                        df["Listing Age (Months)"]
                        .apply(classify_listing_age)
                    )

                else:

                    df["Listing Age (Months)"] = np.nan

                    df["Listing Status"] = "Unknown"

                # =========================================
                # ASIN URL
                # =========================================

                if "ASIN" in df.columns:

                    df["Amazon Link"] = (
                        "https://www.amazon.com/dp/"
                        + df["ASIN"].astype(str)
                    )

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing "
                    f"{uploaded_file.name}: {e}"
                )

        # =============================================
        # SAVE SESSION
        # =============================================

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.asin_df = final_df

            st.session_state.asin_file_names = [
                f.name for f in uploaded_files
            ]

    # =====================================================
    # ACTIVE DATA
    # =====================================================

    final_df = st.session_state.asin_df

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.asin_file_names:

        st.sidebar.success("ASIN Dataset Loaded")

        for file_name in st.session_state.asin_file_names:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear ASIN Dataset"
        ):

            st.session_state.asin_df = None

            st.session_state.asin_file_names = []

            st.rerun()

    # =====================================================
    # EMPTY STATE
    # =====================================================

    if final_df is None or final_df.empty:

        st.info("Upload ASIN CSV files.")
        return

    # =====================================================
    # FILTERS
    # =====================================================

    c1, c2 = st.columns(2)

    with c1:

        status_filter = st.multiselect(
            "Listing Status",
            options=sorted(
                final_df["Listing Status"]
                .dropna()
                .unique()
            )
        )

    with c2:

        search_value = st.text_input(
            "Quick Search",
            placeholder="Search ASIN..."
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if status_filter:

        filtered_df = filtered_df[
            filtered_df["Listing Status"]
            .isin(status_filter)
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

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total ASIN",
        f"{len(filtered_df):,}"
    )

    m2.metric(
        "New Launch",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "New Launch"
            ]
        )
    )

    m3.metric(
        "Growing",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "Growing"
            ]
        )
    )

    m4.metric(
        "Established",
        len(
            filtered_df[
                filtered_df["Listing Status"]
                == "Established"
            ]
        )
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("## ASIN Market Insights")

    insight_rows = []

    for status in [
        "New Launch",
        "Growing",
        "Mature",
        "Established"
    ]:

        temp_df = filtered_df[
            filtered_df["Listing Status"]
            == status
        ]

        if len(temp_df) > 0:

            insight_rows.append({

                "Group": status,

                "Total ASIN": len(temp_df),

                "Avg Listing Age": round(
                    temp_df[
                        "Listing Age (Months)"
                    ].mean(),
                    1
                )
            })

    insight_df = pd.DataFrame(insight_rows)

    st.dataframe(
        insight_df,
        use_container_width=True
    )

    # =====================================================
    # AGGRID
    # =====================================================

    st.markdown("## ASIN Intelligence Dashboard")

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        minWidth=140
    )

    # =====================================================
    # IMAGE RENDERER
    # =====================================================

    image_renderer = JsCode("""
    class ThumbnailRenderer {
        init(params) {
            this.eGui = document.createElement('img');
            this.eGui.src = params.value;
            this.eGui.width = 60;
            this.eGui.height = 60;
            this.eGui.style.borderRadius = '8px';
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
    class LinkRenderer {
        init(params) {

            this.eGui = document.createElement('a');

            this.eGui.innerText = params.value;

            this.eGui.setAttribute(
                'href',
                'https://www.amazon.com/dp/' + params.value
            );

            this.eGui.setAttribute(
                'target',
                '_blank'
            );

            this.eGui.style.color = '#60a5fa';
        }

        getGui() {
            return this.eGui;
        }
    }
    """)

    # =====================================================
    # STATUS COLOR
    # =====================================================

    status_style = JsCode("""
    function(params) {

        if (params.value == 'New Launch') {
            return {
                'backgroundColor': '#14532d',
                'color': 'white'
            }
        }

        if (params.value == 'Growing') {
            return {
                'backgroundColor': '#1e3a8a',
                'color': 'white'
            }
        }

        if (params.value == 'Mature') {
            return {
                'backgroundColor': '#78350f',
                'color': 'white'
            }
        }

        if (params.value == 'Established') {
            return {
                'backgroundColor': '#7f1d1d',
                'color': 'white'
            }
        }
    }
    """)

    # =====================================================
    # COLUMN CONFIG
    # =====================================================

    if "Image URL" in filtered_df.columns:

        gb.configure_column(
            "Image URL",
            header_name="Image",
            cellRenderer=image_renderer,
            width=90
        )

    if "ASIN" in filtered_df.columns:

        gb.configure_column(
            "ASIN",
            cellRenderer=link_renderer,
            width=140
        )

    if "Listing Status" in filtered_df.columns:

        gb.configure_column(
            "Listing Status",
            cellStyle=status_style,
            width=150
        )

    # =====================================================
    # BUILD GRID
    # =====================================================

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=720,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.NO_UPDATE
    )
