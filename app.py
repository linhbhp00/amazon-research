import streamlit as st
import pandas as pd

from service.keyword_engine import render_keyword_engine
from service.asin_engine import render_asin_engine
from service.ranking_engine import render_ranking_engine

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Amazon Research Intelligence System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html,
body,
[class*="css"]{
    background:#050816;
    color:white;
}

.block-container{
    padding-top:1rem;
    padding-bottom:1rem;
    max-width:100%;
}

/* ---------------- Sidebar ---------------- */

section[data-testid="stSidebar"]{
    background:#111827;
    border-right:1px solid #1f2937;
}

section[data-testid="stSidebar"] *{
    color:white;
}

.dashboard-title{
    font-size:42px;
    font-weight:800;
    margin-bottom:20px;
}

/* ---------------- Metric ---------------- */

div[data-testid="stMetric"]{
    background:#111827;
    border:1px solid #1f2937;
    border-radius:12px;
    padding:14px;
}

/* ---------------- Sidebar Radio ---------------- */

div[role="radiogroup"] > label{

    background:#111827;

    border:1px solid #1f2937;

    padding:12px;

    border-radius:10px;

    margin-bottom:8px;

    transition:0.2s;
}

div[role="radiogroup"] > label:hover{

    background:#1f2937;

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
                pass

    return None

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

st.sidebar.markdown("### Amazon Research Intelligence")

page = st.sidebar.radio(
    "",
    [
        "Keyword Intelligence",
        "ASIN Intelligence",
        "Ranking Engine"
    ]
)

# =========================================================
# MAIN HEADER
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
# PAGE : KEYWORD ENGINE
# =========================================================

if page == "Keyword Intelligence":

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

                st.error(f"Cannot read file : {file.name}")

    if keyword_data:

        keyword_df = pd.concat(
            keyword_data,
            ignore_index=True
        )

        # ==========================================
        # FILTER
        # ==========================================

        st.markdown("## Keyword Filters")

        c1, c2, c3 = st.columns(3)

        with c1:

            search_value = st.text_input(
                "Quick Search",
                placeholder="Search keyword..."
            )

        with c2:

            column_filter = st.selectbox(
                "Keyword Column",
                keyword_df.columns.tolist()
            )

        with c3:

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

        # ==========================================
        # METRIC
        # ==========================================

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

        st.divider()

        render_keyword_engine(filtered_df)

    else:

        st.info("Upload one or multiple keyword CSV files.")

# =========================================================
# PAGE : ASIN ENGINE
# =========================================================

elif page == "ASIN Intelligence":

    render_asin_engine()

# =========================================================
# PAGE : RANKING ENGINE
# =========================================================

elif page == "Ranking Engine":

    render_ranking_engine()
