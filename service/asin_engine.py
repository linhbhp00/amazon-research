import streamlit as st
import pandas as pd


def render_asin_engine():

    st.markdown("# ASIN Intelligence")

    uploaded_file = st.file_uploader(
        "Upload ASIN CSV",
        type=["csv"],
        key="asin_upload"
    )

    if uploaded_file is None:
        st.info("Upload ASIN CSV")
        return

    try:

        df = pd.read_csv(
            uploaded_file,
            engine="python",
            on_bad_lines="skip"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    except Exception as e:

        st.error(e)
