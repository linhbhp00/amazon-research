import streamlit as st
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import CountVectorizer

# =========================================================
# RENDER ENGINE
# =========================================================

def render_keyword_engine(filtered_df):

    # =====================================================
    # VALIDATE
    # =====================================================

    if filtered_df is None:

        st.warning("No dataframe found.")
        return

    if filtered_df.empty:

        st.warning("Keyword dataframe is empty.")
        return

    # =====================================================
    # TITLE
    # =====================================================

    st.markdown("---")
    st.markdown("# NLP Market Intelligence Engine")

    # =====================================================
    # DETECT NLP COLUMN
    # =====================================================

    candidate_columns = [

        "Search Term",
        "Keyword",
        "Keywords",
        "Keyword Phrase",
        "Query",
        "Title",
        "Product Title",
    ]

    nlp_source_column = None

    for col in candidate_columns:

        if col in filtered_df.columns:

            nlp_source_column = col
            break

    # fallback

    if nlp_source_column is None:

        text_scores = {}

        for col in filtered_df.columns:

            try:

                avg_length = (
                    filtered_df[col]
                    .astype(str)
                    .str.len()
                    .mean()
                )

                text_scores[col] = avg_length

            except:
                pass

        if text_scores:

            nlp_source_column = max(
                text_scores,
                key=text_scores.get
            )

    # final validate

    if nlp_source_column is None:

        st.error("Cannot detect NLP source column.")
        return

    # =====================================================
    # SETTINGS
    # =====================================================

    with st.expander("NLP Settings", expanded=False):

        s1, s2, s3 = st.columns(3)

        with s1:

            min_freq = st.slider(
                "Minimum Frequency",
                1,
                20,
                2
            )

        with s2:

            top_n = st.slider(
                "Top Results",
                10,
                100,
                30
            )

        with s3:

            st.markdown(
                f"""
                **Detected NLP Column**
                
                `{nlp_source_column}`
                """
            )

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    def clean_text(text):

        if pd.isna(text):
            return ""

        text = str(text).lower()

        text = re.sub(r"<.*?>", " ", text)

        text = re.sub(r"http\S+", " ", text)

        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # =====================================================
    # CORPUS
    # =====================================================

    nlp_series = (
        filtered_df[nlp_source_column]
        .astype(str)
        .apply(clean_text)
    )

    corpus = tuple(
        nlp_series.tolist()
    )

    # =====================================================
    # NGRAM ENGINE
    # =====================================================

    @st.cache_data
    def extract_ngrams(
        corpus,
        ngram_range=(1,1),
        min_freq=2,
        top_n=30
    ):

        try:

            vectorizer = CountVectorizer(
                ngram_range=ngram_range,
                stop_words="english",
                min_df=min_freq
            )

            X = vectorizer.fit_transform(corpus)

            sums = np.array(
                X.sum(axis=0)
            ).flatten()

            words_freq = [

                (word, sums[idx])

                for word, idx
                in vectorizer.vocabulary_.items()
            ]

            words_freq = sorted(
                words_freq,
                key=lambda x: x[1],
                reverse=True
            )

            return pd.DataFrame(
                words_freq[:top_n],
                columns=[
                    "Phrase",
                    "Frequency"
                ]
            )

        except:

            return pd.DataFrame(
                columns=[
                    "Phrase",
                    "Frequency"
                ]
            )

    # =====================================================
    # TABLES
    # =====================================================

    single_word_df = extract_ngrams(
        corpus,
        (1,1),
        min_freq,
        top_n
    )

    bigram_df = extract_ngrams(
        corpus,
        (2,2),
        min_freq,
        top_n
    )

    trigram_df = extract_ngrams(
        corpus,
        (3,3),
        min_freq,
        top_n
    )

    # =====================================================
    # KEYWORD CLUSTERS
    # =====================================================

    cluster_definitions = {

        "Pet Memorial": [
            "pet",
            "dog",
            "cat",
            "rainbow bridge",
        ],

        "Personalized Memorial": [
            "personalized",
            "custom",
            "engraved",
        ],

        "Outdoor Memorial Decor": [
            "garden",
            "stone",
            "wind chime",
            "plaque",
        ],

        "Funeral Service": [
            "funeral",
            "guest book",
            "cards",
        ],

        "Family Loss": [
            "dad",
            "mom",
            "father",
            "mother",
        ],
    }

    cluster_rows = []

    for cluster_name, keywords in cluster_definitions.items():

        total_freq = 0

        matched = []

        for _, row in trigram_df.iterrows():

            phrase = str(row["Phrase"]).lower()

            for keyword in keywords:

                if keyword in phrase:

                    total_freq += int(
                        row["Frequency"]
                    )

                    matched.append(
                        row["Phrase"]
                    )

        if total_freq > 0:

            # competition

            if total_freq >= 15:
                competition = "High"

            elif total_freq >= 7:
                competition = "Medium"

            else:
                competition = "Low"

            # opportunity

            opportunity_score = min(
                100,
                int(total_freq * 8)
            )

            # strategy

            if opportunity_score >= 90:
                strategy = "Launch aggressively"

            elif opportunity_score >= 75:
                strategy = "SEO + PPC"

            else:
                strategy = "Test slowly"

            cluster_rows.append({

                "Cluster": cluster_name,

                "Signals": ", ".join(
                    list(set(matched))[:5]
                ),

                "Frequency": total_freq,

                "Competition": competition,

                "Opportunity Score": opportunity_score,

                "Strategy": strategy
            })

    cluster_df = pd.DataFrame(cluster_rows)

    if not cluster_df.empty:

        cluster_df = cluster_df.sort_values(
            by="Opportunity Score",
            ascending=False
        )

    # =====================================================
    # METRICS
    # =====================================================

    st.markdown("## Strategic Market Intelligence")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Single Words",
        len(single_word_df)
    )

    m2.metric(
        "Bigram",
        len(bigram_df)
    )

    m3.metric(
        "Trigram",
        len(trigram_df)
    )

    m4.metric(
        "Clusters",
        len(cluster_df)
    )

    # =====================================================
    # EXECUTIVE INSIGHTS
    # =====================================================

    st.markdown("## Executive Insights")

    if not single_word_df.empty:

        top_keyword = (
            single_word_df.iloc[0]["Phrase"]
        )

        st.info(
            f"""
            Core market signal detected:
            
            '{top_keyword}' dominates search language.
            """
        )

    if not cluster_df.empty:

        best_cluster = cluster_df.iloc[0]

        st.success(
            f"""
            Strongest Opportunity:
            
            • Cluster: {best_cluster['Cluster']}
            • Opportunity Score: {best_cluster['Opportunity Score']}
            • Competition: {best_cluster['Competition']}
            • Strategy: {best_cluster['Strategy']}
            """
        )

    # =====================================================
    # TABS
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([

        "Single Word",
        "Bigram",
        "Trigram",
        "Keyword Clusters"
    ])

    # =====================================================
    # SINGLE WORD
    # =====================================================

    with tab1:

        st.markdown(
            "### Keyword Frequency Analysis"
        )

        st.dataframe(
            single_word_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # BIGRAM
    # =====================================================

    with tab2:

        st.markdown(
            "### Bigram Analysis"
        )

        st.dataframe(
            bigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # TRIGRAM
    # =====================================================

    with tab3:

        st.markdown(
            "### Trigram Analysis"
        )

        st.dataframe(
            trigram_df,
            use_container_width=True,
            height=700
        )

    # =====================================================
    # CLUSTER
    # =====================================================

    with tab4:

        st.markdown(
            "### Keyword Clustering"
        )

        st.dataframe(
            cluster_df,
            use_container_width=True,
            height=650
        )