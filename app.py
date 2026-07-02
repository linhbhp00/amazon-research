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

if "keyword_df" not in st.session_state:
    st.session_state.keyword_df = None

if "keyword_file_names" not in st.session_state:
    st.session_state.keyword_file_names = []

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

st.sidebar.markdown("### Amazon Research Framework")

uploaded_files = st.sidebar.file_uploader(
    "Upload Keyword CSV",
    type=["csv"],
    accept_multiple_files=True,
    key="keyword_uploader"
)

# =========================================================
# PROCESS CSV
# =========================================================

if uploaded_files:

    all_data = []

    for uploaded_file in uploaded_files:

        try:

            raw_df = read_csv_safe(uploaded_file)

            if raw_df is None:
                st.warning(f"Cannot read file: {uploaded_file.name}")
                continue

            # ==========================================
            # HEADER
            # ==========================================

            first_row = raw_df.iloc[0].fillna("").astype(str).tolist()
            meta_text = " | ".join(first_row)

            header_row = raw_df.iloc[1].fillna("").astype(str).tolist()

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

            st.error(
                f"Error processing {uploaded_file.name}: {e}"
            )

    # ==============================================
    # SAVE TO SESSION
    # ==============================================

    if all_data:

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        st.session_state.keyword_df = final_df

        st.session_state.keyword_file_names = [
            f.name for f in uploaded_files
        ]

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
# ACTIVE DATA
# =========================================================

final_df = st.session_state.keyword_df

# =========================================================
# FILE STATUS
# =========================================================

if st.session_state.keyword_file_names:

    st.sidebar.success("Keyword Dataset Loaded")

    for file_name in st.session_state.keyword_file_names:
        st.sidebar.caption(f"• {file_name}")

    if st.sidebar.button("Clear Keyword Dataset"):

        st.session_state.keyword_df = None
        st.session_state.keyword_file_names = []

        st.rerun()

# =========================================================
# EMPTY STATE
# =========================================================

if final_df is None:

    st.info("Upload keyword CSV files to begin.")
    st.stop()

# =========================================================
# MAIN TABS
# =========================================================

main_tab1, main_tab2, main_tab3 = st.tabs([
    "Keyword Intelligence",
    "ASIN Intelligence",
    "Ranking Engine"
])

# =========================================================
# TAB 1 — KEYWORD ENGINE
# =========================================================

with main_tab1:

    render_keyword_engine(final_df)

# =========================================================
# TAB 2 — ASIN ENGINE
# =========================================================

with main_tab2:

    render_asin_engine()

# =========================================================
# TAB 3 — RANKING ENGINE
# =========================================================

with main_tab3:

    render_ranking_engine()
