import streamlit as st
import pandas as pd

from service.keyword_engine import render_keyword_engine
from service.asin_engine import render_asin_engine
from service.ranking_engine import render_ranking_engine

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Amazon Research Dashboard",
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
# SAFE CSV READER
# =========================================================

@st.cache_data
def read_csv_safe(uploaded_file):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin1",
        "cp1252"
    ]

    separators = [
        ",",
        ";",
        "\t"
    ]

    for enc in encodings:

        for sep in separators:

            try:

                uploaded_file.seek(0)

                df = pd.read_csv(
                    uploaded_file,
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip"
                )

                if len(df.columns) > 1:
                    return df

            except:
                continue

    return None

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

st.sidebar.markdown("### Amazon Research Intelligence")

# =========================================================
# MAIN TITLE
# =========================================================

st.markdown(
    """
    <div class="dashboard-title">
        Amazon Research Intelligence System
    </div>
    """,
    unsafe_allow_html=True
)

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

    st.markdown("## Upload Keyword CSV")

    keyword_files = st.file_uploader(
        "Upload Keyword CSV",
        type=["csv"],
        accept_multiple_files=True,
        key="keyword_upload"
    )

    keyword_data = []

    if keyword_files:

        for file in keyword_files:

            df = read_csv_safe(file)

            if df is not None:

                keyword_data.append(df)

            else:

                st.error(f"Cannot read file: {file.name}")

    if keyword_data:

        keyword_df = pd.concat(
            keyword_data,
            ignore_index=True
        )

        # =================================================
        # FILTERS
        # =================================================

        st.markdown("## Keyword Filters")

        filter_cols = st.columns(3)

        with filter_cols[0]:

            search_value = st.text_input(
                "Quick Search",
                placeholder="Search keyword..."
            )

        with filter_cols[1]:

            column_filter = st.selectbox(
                "Keyword Column",
                options=keyword_df.columns.tolist()
            )

        with filter_cols[2]:

            row_limit = st.slider(
                "Rows",
                100,
                50000,
                5000
            )

        filtered_df = keyword_df.copy()

        if search_value:

            filtered_df = filtered_df[
                filtered_df[column_filter]
                .astype(str)
                .str.contains(
                    search_value,
                    case=False,
                    na=False
                )
            ]

        filtered_df = filtered_df.head(row_limit)

        # =================================================
        # METRICS
        # =================================================

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Rows",
            f"{len(filtered_df):,}"
        )

        m2.metric(
            "Columns",
            len(filtered_df.columns)
        )

        m3.metric(
            "Unique Keywords",
            filtered_df.nunique().max()
        )

        # =================================================
        # ENGINE
        # =================================================

        render_keyword_engine(filtered_df)

    else:

        st.info("Upload keyword CSV files.")

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