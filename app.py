import streamlit as st
import pandas as pd

from utils.csv_utils import read_csv_safe

from service.keyword_engine import render_keyword_engine
from service.asin_engine import render_asin_engine
from service.ranking_engine import render_ranking_engine

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
# APP LOCK
# =========================================================
#
# app.py RESPONSIBILITIES ONLY
#
# ✔ Upload CSV
# ✔ Session State
# ✔ Sidebar Navigation
# ✔ Route dataframe into engine
#
# DO NOT ADD
#
# ✘ Header fixing
# ✘ Metadata parsing
# ✘ Business logic
# ✘ NLP
# ✘ Dashboard logic
# ✘ Data preprocessing
#
# ALL DATA PROCESSING BELONGS TO:
#
# keyword_engine.py
# asin_engine.py
# ranking_engine.py
#
# =========================================================

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"]{
    background:#050816;
    color:white;
}

.block-container{
    max-width:100%;
    padding-top:1rem;
}

section[data-testid="stSidebar"]{
    background:#111827;
}

.dashboard-title{
    font-size:42px;
    font-weight:800;
    margin-bottom:10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION
# =========================================================

DEFAULT_SESSION = {

    "keyword_df":None,
    "keyword_files":[],

    "asin_df":None,
    "asin_files":[],

    "ranking_df":None,
    "ranking_files":[]

}

for k,v in DEFAULT_SESSION.items():

    if k not in st.session_state:

        st.session_state[k]=v

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("MRnD")

engine = st.sidebar.radio(

    "Engine",

    [

        "Keyword Intelligence",
        "ASIN Intelligence",
        "Ranking Engine"

    ]

)

# =========================================================
# TITLE
# =========================================================

st.markdown("""

<div class="dashboard-title">

Amazon Research Dashboard

</div>

""",unsafe_allow_html=True)

# =========================================================
# GENERIC UPLOADER
# =========================================================

def upload_dataset(

    title,
    uploader_key,
    session_df,
    session_files

):

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {title}")

    files = st.sidebar.file_uploader(

        f"Import {title}",

        type=["csv"],

        accept_multiple_files=True,

        key=uploader_key

    )

    if files:

        dfs=[]

        for file in files:

            df = read_csv_safe(file)

            if df is None or df.empty:

                st.warning(f"Cannot read {file.name}")

                continue

            dfs.append(df)

        if dfs:

            st.session_state[session_df]=pd.concat(

                dfs,

                ignore_index=True

            )

            st.session_state[session_files]=[

                f.name for f in files

            ]

    if st.session_state[session_files]:

        st.sidebar.success("Dataset Loaded")

        for f in st.session_state[session_files]:

            st.sidebar.caption(f"• {f}")

        if st.sidebar.button(

            "Clear Dataset",

            key=session_df+"_clear"

        ):

            st.session_state[session_df]=None

            st.session_state[session_files]=[]

            st.rerun()

# =========================================================
# KEYWORD
# =========================================================

if engine=="Keyword Intelligence":

    upload_dataset(

        "Keyword CSV",

        "keyword_upload",

        "keyword_df",

        "keyword_files"

    )

    if st.session_state.keyword_df is not None:

        render_keyword_engine(

            st.session_state.keyword_df.copy()

        )

    else:

        st.info("Upload Keyword CSV.")

# =========================================================
# ASIN
# =========================================================

elif engine=="ASIN Intelligence":

    upload_dataset(

        "ASIN CSV",

        "asin_upload",

        "asin_df",

        "asin_files"

    )

    if st.session_state.asin_df is not None:

        render_asin_engine(

            st.session_state.asin_df.copy()

        )

    else:

        st.info("Upload ASIN CSV.")

# =========================================================
# RANKING
# =========================================================

elif engine=="Ranking Engine":

    upload_dataset(

        "Ranking CSV",

        "ranking_upload",

        "ranking_df",

        "ranking_files"

    )

    if st.session_state.ranking_df is not None:

        render_ranking_engine(

            st.session_state.ranking_df.copy()

        )

    else:

        st.info("Upload Ranking CSV.")
