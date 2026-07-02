# =========================================================
# app.py
# =========================================================

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

.stButton>button {
    width: 100%;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

# -----------------------------
# Keyword Dataset
# -----------------------------

if "keyword_df" not in st.session_state:
    st.session_state.keyword_df = None

if "keyword_file_names" not in st.session_state:
    st.session_state.keyword_file_names = []

# -----------------------------
# ASIN Dataset
# -----------------------------

if "asin_df" not in st.session_state:
    st.session_state.asin_df = None

if "asin_file_names" not in st.session_state:
    st.session_state.asin_file_names = []

# -----------------------------
# Ranking Dataset
# -----------------------------

if "ranking_df" not in st.session_state:
    st.session_state.ranking_df = None

if "ranking_file_names" not in st.session_state:
    st.session_state.ranking_file_names = []

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

st.sidebar.markdown("### Amazon Research Framework")

# =========================================================
# NAVIGATION
# =========================================================

selected_menu = st.sidebar.radio(
    "Select Intelligence Engine",
    [
        "Keyword Intelligence",
        "ASIN Intelligence",
        "Ranking Engine"
    ]
)

st.sidebar.markdown("---")

# =========================================================
# KEYWORD ENGINE SIDEBAR
# =========================================================

if selected_menu == "Keyword Intelligence":

    st.sidebar.markdown("## Keyword CSV Import")

    uploaded_files = st.sidebar.file_uploader(
        "Upload Keyword CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="keyword_uploader"
    )

    # =====================================================
    # PROCESS CSV
    # =====================================================

    if uploaded_files:

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                raw_df = read_csv_safe(uploaded_file)

                if raw_df is None:
                    st.sidebar.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )
                    continue

                # ==========================================
                # HEADER
                # ==========================================

                first_row = (
                    raw_df.iloc[0]
                    .fillna("")
                    .astype(str)
                    .tolist()
                )

                meta_text = " | ".join(first_row)

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

                        niche = meta_text.split(
                            'Search Term=["'
                        )[1].split('"]')[0]

                    except:
                        pass

                data_df["Niche"] = niche

                # ==========================================
                # YEAR
                # ==========================================

                year = ""

                if 'Select year=["' in meta_text:

                    try:

                        year = meta_text.split(
                            'Select year=["'
                        )[1].split('"]')[0]

                    except:
                        pass

                data_df["Year"] = year

                # ==========================================
                # REPORTING DATE
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

                st.sidebar.error(
                    f"{uploaded_file.name}: {e}"
                )

        # =================================================
        # SAVE SESSION
        # =================================================

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.keyword_df = final_df

            st.session_state.keyword_file_names = [
                f.name for f in uploaded_files
            ]

    # =====================================================
    # DATASET STATUS
    # =====================================================

    if st.session_state.keyword_file_names:

        st.sidebar.success("Keyword Dataset Loaded")

        for file_name in st.session_state.keyword_file_names:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear Keyword Dataset"
        ):

            st.session_state.keyword_df = None

            st.session_state.keyword_file_names = []

            st.rerun()

# =========================================================
# ASIN ENGINE SIDEBAR
# =========================================================

elif selected_menu == "ASIN Intelligence":

    st.sidebar.markdown("## ASIN CSV Import")

    uploaded_files = st.sidebar.file_uploader(
        "Upload ASIN CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="asin_uploader"
    )

    if uploaded_files:

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:

                    st.sidebar.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )

                    continue

                all_data.append(df)

            except Exception as e:

                st.sidebar.error(
                    f"{uploaded_file.name}: {e}"
                )

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
    # DATASET STATUS
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

# =========================================================
# RANKING ENGINE SIDEBAR
# =========================================================

elif selected_menu == "Ranking Engine":

    st.sidebar.markdown("## Ranking CSV Import")

    uploaded_files = st.sidebar.file_uploader(
        "Upload Ranking CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="ranking_uploader"
    )

    if uploaded_files:

        all_data = []

        for uploaded_file in uploaded_files:

            try:

                df = read_csv_safe(uploaded_file)

                if df is None:

                    st.sidebar.warning(
                        f"Cannot read file: {uploaded_file.name}"
                    )

                    continue

                all_data.append(df)

            except Exception as e:

                st.sidebar.error(
                    f"{uploaded_file.name}: {e}"
                )

        if all_data:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.session_state.ranking_df = final_df

            st.session_state.ranking_file_names = [
                f.name for f in uploaded_files
            ]

    # =====================================================
    # DATASET STATUS
    # =====================================================

    if st.session_state.ranking_file_names:

        st.sidebar.success("Ranking Dataset Loaded")

        for file_name in st.session_state.ranking_file_names:

            st.sidebar.caption(f"• {file_name}")

        if st.sidebar.button(
            "Clear Ranking Dataset"
        ):

            st.session_state.ranking_df = None

            st.session_state.ranking_file_names = []

            st.rerun()

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
# ROUTER
# =========================================================

if selected_menu == "Keyword Intelligence":

    if st.session_state.keyword_df is None:

        st.info(
            "Upload keyword CSV files to begin."
        )

    else:

        render_keyword_engine(
            st.session_state.keyword_df
        )

# =========================================================

elif selected_menu == "ASIN Intelligence":

    render_asin_engine()

# =========================================================

elif selected_menu == "Ranking Engine":

    render_ranking_engine()
