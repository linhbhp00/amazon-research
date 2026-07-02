# =========================================================
# utils/html_export.py
# =========================================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime


# =========================================================
# SAFE DF
# =========================================================

def safe_df(df):

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    return df.copy()


# =========================================================
# FORMAT NUMBER
# =========================================================

def format_number(value):

    try:

        return f"{float(value):,.2f}"

    except:

        return value


# =========================================================
# FORMAT DATAFRAME
# =========================================================

def format_dataframe(df):

    if df.empty:
        return df

    formatted_df = df.copy()

    currency_keywords = [

        "revenue",
        "price",
        "sales",
        "bid",
        "cpc",
        "cost",
    ]

    for col in formatted_df.columns:

        col_lower = str(col).lower()

        if any(
            keyword in col_lower
            for keyword in currency_keywords
        ):

            try:

                formatted_df[col] = (
                    pd.to_numeric(
                        formatted_df[col],
                        errors="coerce"
                    )
                    .fillna(0)
                    .apply(format_number)
                )

            except:
                pass

    return formatted_df


# =========================================================
# TABLE HTML
# =========================================================

def dataframe_to_html(df):

    if df is None or df.empty:

        return """
        <div class="empty-box">
            No data available
        </div>
        """

    display_df = format_dataframe(df)

    return display_df.to_html(
        index=False,
        escape=False,
        classes="dashboard-table"
    )


# =========================================================
# KPI CARD
# =========================================================

def build_kpi_card(
    title,
    value,
    color="#2563eb"
):

    return f"""
    <div class="kpi-card">

        <div class="kpi-title">
            {title}
        </div>

        <div
            class="kpi-value"
            style="color:{color};"
        >
            {value}
        </div>

    </div>
    """


# =========================================================
# PLOTLY CHART
# =========================================================

def build_plotly_chart(fig):

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn"
    )


# =========================================================
# ASIN CHART
# =========================================================

def generate_asin_chart(asin_df):

    if (
        asin_df is None
        or asin_df.empty
        or "Sales Group" not in asin_df.columns
        or "ASIN Revenue" not in asin_df.columns
    ):

        return ""

    chart_df = (
        asin_df
        .groupby("Sales Group")[
            "ASIN Revenue"
        ]
        .sum()
        .reset_index()
    )

    fig = px.bar(

        chart_df,

        x="Sales Group",
        y="ASIN Revenue",

        title="Revenue Distribution",

        template="plotly_dark"
    )

    fig.update_layout(
        height=450
    )

    return build_plotly_chart(fig)


# =========================================================
# KEYWORD CHART
# =========================================================

def generate_keyword_chart(keyword_df):

    if (
        keyword_df is None
        or keyword_df.empty
    ):

        return ""

    possible_cols = [

        "Search Volume",
        "Keyword Sales",
    ]

    metric_col = None

    for col in possible_cols:

        if col in keyword_df.columns:

            metric_col = col
            break

    if metric_col is None:
        return ""

    top_df = (
        keyword_df
        .sort_values(
            by=metric_col,
            ascending=False
        )
        .head(20)
    )

    keyword_col = None

    for col in [

        "Search Term",
        "Keyword Phrase",
        "Keyword",

    ]:

        if col in top_df.columns:

            keyword_col = col
            break

    if keyword_col is None:
        return ""

    fig = px.bar(

        top_df,

        x=keyword_col,
        y=metric_col,

        title="Top Keywords",

        template="plotly_dark"
    )

    fig.update_layout(
        height=500
    )

    return build_plotly_chart(fig)


# =========================================================
# RANKING CHART
# =========================================================

def generate_ranking_chart(ranking_df):

    if (
        ranking_df is None
        or ranking_df.empty
        or "Keyword Classification"
        not in ranking_df.columns
    ):

        return ""

    chart_df = (
        ranking_df[
            "Keyword Classification"
        ]
        .value_counts()
        .reset_index()
    )

    chart_df.columns = [
        "Classification",
        "Count"
    ]

    fig = px.pie(

        chart_df,

        names="Classification",
        values="Count",

        title="Keyword Classification",

        template="plotly_dark"
    )

    fig.update_layout(
        height=500
    )

    return build_plotly_chart(fig)


# =========================================================
# MAIN HTML REPORT
# =========================================================

def generate_html_report(

    asin_df=None,
    keyword_df=None,
    ranking_df=None,

):

    # =====================================================
    # SAFE DATA
    # =====================================================

    asin_df = safe_df(asin_df)

    keyword_df = safe_df(keyword_df)

    ranking_df = safe_df(ranking_df)

    # =====================================================
    # KPI
    # =====================================================

    asin_count = len(asin_df)

    keyword_count = len(keyword_df)

    ranking_count = len(ranking_df)

    total_revenue = 0

    if (
        not asin_df.empty
        and "ASIN Revenue" in asin_df.columns
    ):

        try:

            total_revenue = (
                pd.to_numeric(
                    asin_df["ASIN Revenue"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        except:
            total_revenue = 0

    # =====================================================
    # CHARTS
    # =====================================================

    asin_chart = generate_asin_chart(
        asin_df
    )

    keyword_chart = generate_keyword_chart(
        keyword_df
    )

    ranking_chart = generate_ranking_chart(
        ranking_df
    )

    # =====================================================
    # TABLES
    # =====================================================

    asin_table = dataframe_to_html(
        asin_df.head(200)
    )

    keyword_table = dataframe_to_html(
        keyword_df.head(200)
    )

    ranking_table = dataframe_to_html(
        ranking_df.head(200)
    )

    # =====================================================
    # HTML
    # =====================================================

    html = f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>
Amazon Research Dashboard
</title>

<style>

body{{
    background:#020617;
    color:#f8fafc;
    font-family:Arial,sans-serif;
    margin:0;
    padding:30px;
}}

h1{{
    font-size:38px;
    margin-bottom:10px;
}}

h2{{
    font-size:26px;
    margin-top:0;
}}

.subtitle{{
    color:#94a3b8;
    margin-bottom:30px;
}}

.section{{
    background:#0f172a;
    padding:24px;
    border-radius:18px;
    margin-bottom:30px;
    border:1px solid #1e293b;
}}

.kpi-grid{{
    display:grid;
    grid-template-columns:
    repeat(auto-fit,minmax(220px,1fr));
    gap:20px;
    margin-bottom:30px;
}}

.kpi-card{{
    background:#111827;
    border-radius:14px;
    padding:22px;
    border:1px solid #374151;
}}

.kpi-title{{
    color:#94a3b8;
    font-size:14px;
    margin-bottom:10px;
}}

.kpi-value{{
    font-size:34px;
    font-weight:700;
}}

.dashboard-table{{
    width:100%;
    border-collapse:collapse;
    margin-top:20px;
}}

.dashboard-table th{{
    background:#1e293b;
    color:#f8fafc;
    padding:10px;
    border:1px solid #334155;
    position:sticky;
    top:0;
}}

.dashboard-table td{{
    padding:10px;
    border:1px solid #334155;
    color:#e2e8f0;
}}

.dashboard-table tr:nth-child(even){{
    background:#111827;
}}

.dashboard-table tr:hover{{
    background:#1e293b;
}}

.empty-box{{
    padding:30px;
    background:#111827;
    border-radius:14px;
    color:#94a3b8;
}}

.footer{{
    margin-top:50px;
    text-align:center;
    color:#64748b;
    font-size:13px;
}}

</style>

</head>

<body>

<h1>
Amazon Research Dashboard
</h1>

<div class="subtitle">

Generated:
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

</div>

<div class="kpi-grid">

{build_kpi_card(
    "ASIN Records",
    f"{asin_count:,}",
    "#22c55e"
)}

{build_kpi_card(
    "Keyword Records",
    f"{keyword_count:,}",
    "#3b82f6"
)}

{build_kpi_card(
    "Ranking Records",
    f"{ranking_count:,}",
    "#a855f7"
)}

{build_kpi_card(
    "Total Revenue",
    f"${total_revenue:,.2f}",
    "#f59e0b"
)}

</div>

"""

    # =====================================================
    # ASIN SECTION
    # =====================================================

    if not asin_df.empty:

        html += f"""

<div class="section">

<h2>
ASIN Intelligence
</h2>

{asin_chart}

{asin_table}

</div>

"""

    # =====================================================
    # KEYWORD SECTION
    # =====================================================

    if not keyword_df.empty:

        html += f"""

<div class="section">

<h2>
Keyword Intelligence
</h2>

{keyword_chart}

{keyword_table}

</div>

"""

    # =====================================================
    # RANKING SECTION
    # =====================================================

    if not ranking_df.empty:

        html += f"""

<div class="section">

<h2>
Ranking Intelligence
</h2>

{ranking_chart}

{ranking_table}

</div>

"""

    # =====================================================
    # FOOTER
    # =====================================================

    html += """

<div class="footer">

Amazon Research Intelligence Dashboard

</div>

</body>

</html>

"""

    return html
