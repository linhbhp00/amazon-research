import streamlit as st
import pandas as pd

from service.keyword_engine import render_keyword_engine
from service.asin_engine import render_asin_engine
from service.ranking_engine import render_ranking_engine

from utils.csv_utils import read_csv_safe

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Amazon Research Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"]  {
    background-color: #050816;
    color: white;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1f2937;
}

section[data-testid="stSidebar"] * {
    color: white;
}

.dashboard-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
}

div[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #1f2937;
    padding: 14px;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

SESSION_KEYS = {
    "keyword_df": None,
    "keyword_files": [],

    "asin_df": None,
    "asin_files": [],

    "ranking_df": None,
    "ranking_files": [],
}

for key, default in SESSION_KEYS.items():

    if key not in st.session_state:
        st.session_state[key] = default

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

st.sidebar.markdown("### Amazon Research Framework")

# =========================================================
# MENU
# =========================================================

selected_menu = st.sidebar.radio(

    "Engine",

    [
        "Keyword Intelligence",
        "ASIN Intelligence",
        "Ranking Engine"
    ]
)

# =========================================================
# MAIN TITLE
# =========================================================

st.markdown(
    """
    <div class="dashboard-title">
        Amazon Research Dashboard
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# KEYWORD ENGINE
# =========================================================

if selected_menu == "Keyword Intelligence":

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Upload Keyword CSV")

    keyword_files = st.sidebar.file_uploader(
        "Import Keyword CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="keyword_csv_uploader"
    )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    if keyword_files:

        all_data = []

        for uploaded_file in keyword_files:

            try:

                raw_df = read_csv_safe(uploaded_file)

                if raw_df is None:
                    st.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )
                    continue

                # ==========================================
                # META
                # ==========================================

                first_row = (
                    raw_df.iloc[0]
                    .fillna("")
                    .astype(str)
                    .tolist()
                )

                meta_text = " | ".join(first_row)

                # ==========================================
                # HEADER
                # ==========================================

                header_row = (
                    raw_df.iloc[1]
                    .fillna("")
                    .astype(str)
                    .tolist()
                )

                data_df = raw_df.iloc[2:].copy()

                data_df.columns = header_row

                data_df = data_df.reset_index(drop=True)

                # ==========================================
                # NICHE
                # ==========================================

                niche = ""

                if 'Search Term=["' in meta_text:

                    try:

                        niche = (
                            meta_text
                            .split('Search Term=["')[1]
                            .split('"]')[0]
                        )

                    except:
                        pass

                data_df["Niche"] = niche

                # ==========================================
                # YEAR
                # ==========================================

                year = ""

                if 'Select year=["' in meta_text:

                    try:

                        year = (
                            meta_text
                            .split('Select year=["')[1]
                            .split('"]')[0]
                        )

                    except:
                        pass

                data_df["Year"] = year

                # ==========================================
                # DATE
                # ==========================================

                if "Reporting Date" in data_df.columns:

                    data_df["Reporting Date"] = pd.to_datetime(
                        data_df["Reporting Date"],
                        errors="coerce"
                    )

                    data_df["Month"] = (
                        data_df["Reporting Date"].dt.month
                    )

                    data_df["Quarter"] = (
                        data_df["Reporting Date"].dt.quarter
                    )

                all_data.append(data_df)

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {e}"
                )

        # =================================================
        # SAVE SESSION
        # =================================================

        if all_data:

            st.session_state.keyword_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.keyword_files = [
                f.name for f in keyword_files
            ]

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.keyword_files:

        st.sidebar.success("Keyword Dataset Loaded")

        for file_name in st.session_state.keyword_files:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear Keyword Dataset"
        ):

            st.session_state.keyword_df = None
            st.session_state.keyword_files = []

            st.rerun()

    # =====================================================
    # RENDER
    # =====================================================

    if st.session_state.keyword_df is not None:

        render_keyword_engine(
            st.session_state.keyword_df
        )

    else:

        st.info(
            "Upload keyword CSV files to begin."
        )

# =========================================================
# ASIN ENGINE
# =========================================================

elif selected_menu == "ASIN Intelligence":

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Upload ASIN CSV")

    asin_files = st.sidebar.file_uploader(
        "Import ASIN CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="asin_csv_uploader"
    )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    if asin_files:

        all_data = []

        for uploaded_file in asin_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:

                    st.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )

                    continue

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {e}"
                )

        if all_data:

            st.session_state.asin_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.asin_files = [
                f.name for f in asin_files
            ]

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.asin_files:

        st.sidebar.success("ASIN Dataset Loaded")

        for file_name in st.session_state.asin_files:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear ASIN Dataset"
        ):

            st.session_state.asin_df = None
            st.session_state.asin_files = []

            st.rerun()

    # =====================================================
    # RENDER
    # =====================================================

    if st.session_state.asin_df is not None:

        render_asin_engine(
            st.session_state.asin_df
        )

    else:

        st.info(
            "Upload ASIN CSV files to begin."
        )

# =========================================================
# RANKING ENGINE
# =========================================================

elif selected_menu == "Ranking Engine":

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Upload Ranking CSV")

    ranking_files = st.sidebar.file_uploader(
        "Import Ranking CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="ranking_csv_uploader"
    )

    # =====================================================
    # PROCESS FILES
    # =====================================================

    if ranking_files:

        all_data = []

        for uploaded_file in ranking_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:

                    st.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )

                    continue

                all_data.append(df)

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {e}"
                )

        if all_data:

            st.session_state.ranking_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.ranking_files = [
                f.name for f in ranking_files
            ]

    # =====================================================
    # FILE STATUS
    # =====================================================

    if st.session_state.ranking_files:

        st.sidebar.success("Ranking Dataset Loaded")

        for file_name in st.session_state.ranking_files:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear Ranking Dataset"
        ):

            st.session_state.ranking_df = None
            st.session_state.ranking_files = []

            st.rerun()

    # =====================================================
    # RENDER
    # =====================================================

    if st.session_state.ranking_df is not None:

        render_ranking_engine(
            st.session_state.ranking_df
        )

    else:

        st.info(
            "Upload ranking CSV files to begin."
        )
