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
# ASIN ENGINE
# =========================================================

def render_asin_engine():

    st.markdown("# ASIN Intelligence")

    # =====================================================
    # SESSION STATE
    # =====================================================

    if "asin_df" not in st.session_state:
        st.session_state.asin_df = None

    if "asin_file_names" not in st.session_state:
        st.session_state.asin_file_names = []

    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "### ASIN Intelligence"
    )

    uploaded_files = st.sidebar.file_uploader(
        "Upload ASIN CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="asin_uploader"
    )

    # =====================================================
    # PROCESS ONLY WHEN FILE CHANGED
    # =====================================================

    current_uploaded_names = []

    if uploaded_files:

        current_uploaded_names = [
            f.name for f in uploaded_files
        ]

    if (
        uploaded_files
        and current_uploaded_names
        != st.session_state.asin_file_names
    ):

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:

                    st.warning(
                        f"Cannot read file: "
                        f"{uploaded_file.name}"
                    )

                    continue

                # ==========================================
                # CLEAN HEADER
                # ==========================================

                df.columns = [
                    str(col).strip()
                    for col in df.columns
                ]

                # ==========================================
                # NUMERIC COLUMNS
                # ==========================================

                numeric_cols = [
                    "Price",
                    "Review Count",
                    "Review Rating",
                    "BSR",
                    "Bought in past month"
                ]

                for col in numeric_cols:

                    if col in df.columns:

                        df[col] = (
                            df[col]
                            .astype(str)
                            .str.replace(",", "")
                            .str.replace("$", "")
                        )

                        df[col] = pd.to_numeric(
                            df[col],
                            errors="coerce"
                        )

                # ==========================================
                # CREATION DATE
                # ==========================================

                if "Creation Date" in df.columns:

                    df["Creation Date"] = (
                        pd.to_datetime(
                            df["Creation Date"],
                            errors="coerce"
                        )
                    )

                    today = pd.Timestamp.today()

                    df["Listing Age Days"] = (
                        today - df["Creation Date"]
                    ).dt.days

                    df["Listing Age Months"] = (
                        df["Listing Age Days"] / 30
                    ).round(1)

                # ==========================================
                # LISTING AGE GROUP
                # ==========================================

                if "Listing Age Months" in df.columns:

                    def classify_listing_age(months):

                        if pd.isna(months):
                            return "Unknown"

                        if months <= 3:
                            return "🟢 New Launch"

                        elif months <= 12:
                            return "🟡 Growth"

                        elif months <= 36:
                            return "🟠 Mature"

                        else:
                            return "🔴 Old Listing"

                    df["Listing Stage"] = (
                        df["Listing Age Months"]
                        .apply(classify_listing_age)
                    )

                # ==========================================
                # SCORE ENGINE
                # ==========================================

                score = np.zeros(len(df))

                # Reviews
                if "Review Count" in df.columns:

                    score += np.where(
                        df["Review Count"] < 50,
                        25,
                        0
                    )

                    score += np.where(
                        (
                            df["Review Count"] >= 50
                        )
                        &
                        (
                            df["Review Count"] < 300
                        ),
                        15,
                        0
                    )

                # Listing age
                if "Listing Age Months" in df.columns:

                    score += np.where(
                        df["Listing Age Months"] <= 6,
                        25,
                        0
                    )

                    score += np.where(
                        (
                            df["Listing Age Months"] > 6
                        )
                        &
                        (
                            df["Listing Age Months"] <= 18
                        ),
                        15,
                        0
                    )

                # BSR
                if "BSR" in df.columns:

                    score += np.where(
                        df["BSR"] <= 5000,
                        25,
                        0
                    )

                    score += np.where(
                        (
                            df["BSR"] > 5000
                        )
                        &
                        (
                            df["BSR"] <= 20000
                        ),
                        15,
                        0
                    )

                # Rating
                if "Review Rating" in df.columns:

                    score += np.where(
                        df["Review Rating"] >= 4.5,
                        25,
                        0
                    )

                    score += np.where(
                        (
                            df["Review Rating"] >= 4.0
                        )
                        &
                        (
                            df["Review Rating"] < 4.5
                        ),
                        15,
                        0
                    )

                df["Opportunity Score"] = score

                # ==========================================
                # OPPORTUNITY LEVEL
                # ==========================================

                def classify_opportunity(score):

                    if score >= 80:
                        return "🟢 High Opportunity"

                    elif score >= 55:
                        return "🟡 Medium Opportunity"

                    else:
                        return "🔴 Competitive"

                df["Opportunity Level"] = (
                    df["Opportunity Score"]
                    .apply(classify_opportunity)
                )

                # ==========================================
                # IMAGE HTML
                # ==========================================

                if "Image URL" in df.columns:

                    df["Image"] = (
                        df["Image URL"]
                        .apply(
                            lambda x:
                            f"""
                            <img src="{x}"
                            width="70">
                            """
                            if pd.notna(x)
                            else ""
                        )
                    )

                # ==========================================
                # ASIN LINK
                # ==========================================

                if "ASIN" in df.columns:

                    if "URL" in df.columns:

                        df["ASIN Link"] = df.apply(
                            lambda row:
                            f"""
                            <a href="{row['URL']}"
                            target="_blank">
                            {row['ASIN']}
                            </a>
                            """,
                            axis=1
                        )

                    else:

                        df["ASIN Link"] = (
                            df["ASIN"]
                            .apply(
                                lambda x:
                                f"""
                                <a href=
                                "https://www.amazon.com/dp/{x}"
                                target="_blank">
                                {x}
                                </a>
                                """
                            )
                        )

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing "
                    f"{uploaded_file.name}: {e}"
                )

        # ==============================================
        # SAVE SESSION
        # ==============================================

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.asin_df = final_df

            st.session_state.asin_file_names = (
                current_uploaded_names
            )

    # =====================================================
    # ACTIVE DATA
    # =====================================================

    df = st.session_state.asin_df

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.asin_file_names:

        st.sidebar.success(
            "ASIN Dataset Loaded"
        )

        for file_name in (
            st.session_state.asin_file_names
        ):

            st.sidebar.caption(
                f"• {file_name}"
            )

        if st.sidebar.button(
            "Clear ASIN Dataset"
        ):

            st.session_state.asin_df = None

            st.session_state.asin_file_names = []

            st.rerun()

    # =====================================================
    # EMPTY
    # =====================================================

    if df is None or df.empty:

        st.info(
            "Upload ASIN CSV to begin."
        )

        return

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        opportunity_filter = st.multiselect(
            "Opportunity Level",
            options=sorted(
                df["Opportunity Level"]
                .dropna()
                .unique()
            )
        )

    with col2:

        listing_filter = st.multiselect(
            "Listing Stage",
            options=sorted(
                df["Listing Stage"]
                .dropna()
                .unique()
            )
        )

    with col3:

        keyword_search = st.text_input(
            "Keyword Search"
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = df.copy()

    if opportunity_filter:

        filtered_df = filtered_df[
            filtered_df["Opportunity Level"]
            .isin(opportunity_filter)
        ]

    if listing_filter:

        filtered_df = filtered_df[
            filtered_df["Listing Stage"]
            .isin(listing_filter)
        ]

    if keyword_search:

        filtered_df = filtered_df[
            filtered_df.astype(str)
            .apply(
                lambda row:
                row.str.contains(
                    keyword_search,
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
        "Total ASINs",
        f"{len(filtered_df):,}"
    )

    c2.metric(
        "Avg Opportunity",
        round(
            filtered_df[
                "Opportunity Score"
            ].mean(),
            1
        )
    )

    c3.metric(
        "New Listings",
        len(
            filtered_df[
                filtered_df[
                    "Listing Stage"
                ] == "🟢 New Launch"
            ]
        )
    )

    c4.metric(
        "High Opportunity",
        len(
            filtered_df[
                filtered_df[
                    "Opportunity Level"
                ] == "🟢 High Opportunity"
            ]
        )
    )

    # =====================================================
    # INSIGHTS
    # =====================================================

    st.markdown("## Strategic Insights")

    high_opportunity = filtered_df[
        filtered_df["Opportunity Level"]
        == "🟢 High Opportunity"
    ]

    if len(high_opportunity) > 0:

        st.success(
            f"""
            Detected {len(high_opportunity)}
            high-opportunity ASINs with:

            • low reviews
            • strong BSR
            • newer listings
            • high ratings

            Potential niche expansion opportunity.
            """
        )

    # =====================================================
    # GRID
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
        editable=False,
        minWidth=120
    )

    # ==============================================
    # IMAGE RENDERER
    # ==============================================

    image_renderer = JsCode("""
    class ImgCellRenderer {
        init(params) {
            this.eGui =
            document.createElement('div');

            this.eGui.innerHTML =
            params.value;
        }

        getGui() {
            return this.eGui;
        }
    }
    """)

    # ==============================================
    # LINK RENDERER
    # ==============================================

    link_renderer = JsCode("""
    class UrlCellRenderer {
        init(params) {
            this.eGui =
            document.createElement('div');

            this.eGui.innerHTML =
            params.value;
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

    if "ASIN Link" in filtered_df.columns:

        gb.configure_column(
            "ASIN Link",
            cellRenderer=link_renderer,
            width=140
        )

    grid_options = gb.build()

    grid_options["rowHeight"] = 90

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=850,
        fit_columns_on_grid_load=False,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
    )
