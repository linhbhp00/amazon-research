import io
import streamlit as st
import pandas as pd
import numpy as np

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode,
)

# =========================================================
# HEADER FIX
# =========================================================

EXPECTED_COLUMNS = [
    "ASIN",
    "Image URL",
    "Creation Date",
]


def is_valid_header(columns):

    cols = [str(c).strip() for c in columns]

    score = 0

    for expected in EXPECTED_COLUMNS:

        if expected in cols:
            score += 1

    return score >= 2


def auto_fix_headers(df):

    if df is None or df.empty:
        return df

    if is_valid_header(df.columns):
        return df

    # first row
    first_row = (
        df.iloc[0]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if is_valid_header(first_row):

        fixed_df = df.copy()

        fixed_df.columns = first_row

        fixed_df = (
            fixed_df.iloc[1:]
            .reset_index(drop=True)
        )

        return fixed_df

    # second row
    if len(df) > 1:

        second_row = (
            df.iloc[1]
            .fillna("")
            .astype(str)
            .tolist()
        )

        if is_valid_header(second_row):

            fixed_df = df.copy()

            fixed_df.columns = second_row

            fixed_df = (
                fixed_df.iloc[2:]
                .reset_index(drop=True)
            )

            return fixed_df

    return df


# =========================================================
# CLEAN NUMERIC
# SUPPORT:
# 15.424,74
# 15,424.74
# =========================================================

def clean_numeric(value):

    if pd.isna(value):
        return 0

    value = str(value).strip()

    value = (
        value
        .replace("$", "")
        .replace("€", "")
        .replace(" ", "")
    )

    # EU FORMAT
    # 15.424,74
    if "," in value and "." in value:

        if value.rfind(",") > value.rfind("."):

            value = value.replace(".", "")
            value = value.replace(",", ".")

        else:

            value = value.replace(",", "")

    # ONLY COMMA
    elif "," in value:

        value = value.replace(",", ".")

    try:
        return float(value)

    except:
        return 0


# =========================================================
# FORMAT US CURRENCY
# =========================================================

def format_us_currency(value):

    try:
        return f"{float(value):,.2f}"

    except:
        return "0.00"


# =========================================================
# ASIN LINK
# =========================================================

def make_asin_link(asin):

    if pd.isna(asin):
        return ""

    asin = str(asin)

    return f"""
    <a href="https://www.amazon.com/dp/{asin}"
    target="_blank"
    style="
        color:#60a5fa;
        text-decoration:none;
        font-weight:600;
    ">
    {asin}
    </a>
    """


# =========================================================
# IMAGE RENDER
# =========================================================

def make_image_html(url):

    if pd.isna(url):
        return ""

    url = str(url)

    return f"""
    <img src="{url}"
    style="
        width:72px;
        height:72px;
        object-fit:contain;
        border-radius:8px;
        background:white;
        padding:4px;
    ">
    """


# =========================================================
# AGE CALCULATOR
# =========================================================

def calculate_age_months(date_value):

    try:

        date_value = pd.to_datetime(
            date_value,
            errors="coerce"
        )

        if pd.isna(date_value):
            return 0

        today = pd.Timestamp.now()

        months = (
            (today.year - date_value.year) * 12
            + (today.month - date_value.month)
        )

        return max(months, 0)

    except:
        return 0


# =========================================================
# GROUPS
# =========================================================

def get_seller_group(months):

    if months <= 12:
        return "New Seller"

    elif months <= 36:
        return "Mid Seller"

    return "Old Seller"


def get_listing_group(months):

    if months <= 6:
        return "New Listing"

    elif months <= 24:
        return "Mid Listing"

    return "Old Listing"


def get_sales_group(sales):

    if sales == 0:
        return "No Sale"

    elif sales < 100:
        return "Low Sales"

    elif 100 <= sales <= 500:
        return "Stable Sales"

    return "High Sales"


# =========================================================
# ACTION
# =========================================================

def get_action(group):

    group = str(group)

    if (
        "Old Seller" in group
        and "Old Listing" in group
        and "High Sales" in group
    ):
        return "Avoid"

    if (
        "Old Seller" in group
        and "New Listing" in group
    ):
        return "Monitor"

    if (
        "Mid Seller" in group
        and "Mid Listing" in group
        and "Stable Sales" in group
    ):
        return "Learn"

    if (
        "Mid Seller" in group
        and "Mid Listing" in group
        and "High Sales" in group
    ):
        return "Research"

    if (
        "New Seller" in group
        and "New Listing" in group
        and "High Sales" in group
    ):
        return "Scale"

    if (
        "Low Sales" in group
        or "No Sale" in group
    ):
        return "Skip"

    return "Analyze"


# =========================================================
# STRATEGY
# =========================================================

def get_strategy(action):

    action = str(action)

    if action == "Avoid":
        return (
            "Strong moat competitor. "
            "Avoid direct competition."
        )

    if action == "Monitor":
        return (
            "Large seller testing market. "
            "Monitor closely."
        )

    if action == "Learn":
        return (
            "Stable competitor. "
            "Learn winning patterns."
        )

    if action == "Scale":
        return (
            "Fast growing opportunity. "
            "Scale aggressively."
        )

    if action == "Research":
        return (
            "Market still open. "
            "Research deeper."
        )

    if action == "Skip":
        return (
            "Weak demand signal. "
            "Avoid entering."
        )

    return "Analyze deeper."


# =========================================================
# MAIN ENGINE
# =========================================================

def render_asin_engine(final_df):

    st.markdown("# ASIN Intelligence")

    # =====================================================
    # EMPTY
    # =====================================================

    if final_df is None or final_df.empty:

        st.info(
            "Upload ASIN CSV files to begin."
        )

        return

    # =====================================================
    # FIX HEADERS
    # =====================================================

    final_df = auto_fix_headers(
        final_df
    )

    final_df = final_df.loc[
        :,
        ~final_df.columns.duplicated()
    ]

    # =====================================================
    # IMAGE
    # =====================================================

    if "Image URL" in final_df.columns:

        final_df["Image"] = (
            final_df["Image URL"]
            .apply(make_image_html)
        )

    # =====================================================
    # ASIN LINK
    # =====================================================

    if "ASIN" in final_df.columns:

        final_df["ASIN"] = (
            final_df["ASIN"]
            .apply(make_asin_link)
        )

    # =====================================================
    # SALES / REVENUE
    # =====================================================

    sales_col = None
    revenue_col = None

    for col in [
        "ASIN Sales",
        "Sales",
    ]:

        if col in final_df.columns:

            sales_col = col
            break

    for col in [
        "ASIN Revenue",
        "Revenue",
        "Parent Level Revenue",
    ]:

        if col in final_df.columns:

            revenue_col = col
            break

    # SALES

    if sales_col:

        final_df["ASIN Sales"] = (
            final_df[sales_col]
            .apply(clean_numeric)
            .astype(int)
        )

    else:

        final_df["ASIN Sales"] = 0

    # REVENUE

    if revenue_col:

        final_df["_ASIN Revenue Numeric"] = (
            final_df[revenue_col]
            .apply(clean_numeric)
        )

        final_df["ASIN Revenue"] = (
            final_df["_ASIN Revenue Numeric"]
            .apply(format_us_currency)
        )

    else:

        final_df["_ASIN Revenue Numeric"] = 0

        final_df["ASIN Revenue"] = "0.00"

    # =====================================================
    # LISTING AGE
    # =====================================================

    creation_col = None

    for col in [
        "Creation Date",
        "Created Date",
        "Date Created",
    ]:

        if col in final_df.columns:

            creation_col = col
            break

    if creation_col:

        final_df["Listing Age (mo)"] = (
            final_df[creation_col]
            .apply(calculate_age_months)
        )

    else:

        final_df["Listing Age (mo)"] = 0

    # =====================================================
    # SELLER AGE
    # =====================================================

    final_df["Seller Age (mo)"] = (
        final_df["Listing Age (mo)"]
    )

    # =====================================================
    # GROUPS
    # =====================================================

    final_df["Seller Group"] = (
        final_df["Seller Age (mo)"]
        .apply(get_seller_group)
    )

    final_df["Listing Group"] = (
        final_df["Listing Age (mo)"]
        .apply(get_listing_group)
    )

    final_df["Sales Group"] = (
        final_df["ASIN Sales"]
        .apply(get_sales_group)
    )

    final_df["Group Before Sales"] = (
        final_df["Seller Group"]
        + " + "
        + final_df["Listing Group"]
    )

    final_df["Competitor Group"] = (
        final_df["Group Before Sales"]
        + " + "
        + final_df["Sales Group"]
    )

    final_df["Action"] = (
        final_df["Competitor Group"]
        .apply(get_action)
    )

    final_df["Strategy"] = (
        final_df["Action"]
        .apply(get_strategy)
    )

    # =====================================================
    # FILTERS
    # =====================================================

    f1, f2, f3, f4 = st.columns(4)

    with f1:

        seller_filter = st.multiselect(
            "Seller Group",
            sorted(
                final_df["Seller Group"]
                .dropna()
                .unique()
            )
        )

    with f2:

        listing_filter = st.multiselect(
            "Listing Group",
            sorted(
                final_df["Listing Group"]
                .dropna()
                .unique()
            )
        )

    with f3:

        sales_filter = st.multiselect(
            "Sales Group",
            sorted(
                final_df["Sales Group"]
                .dropna()
                .unique()
            )
        )

    with f4:

        action_filter = st.multiselect(
            "Action",
            sorted(
                final_df["Action"]
                .dropna()
                .unique()
            )
        )

    # =====================================================
    # FILTER DATA
    # =====================================================

    filtered_df = final_df.copy()

    if seller_filter:

        filtered_df = filtered_df[
            filtered_df["Seller Group"]
            .isin(seller_filter)
        ]

    if listing_filter:

        filtered_df = filtered_df[
            filtered_df["Listing Group"]
            .isin(listing_filter)
        ]

    if sales_filter:

        filtered_df = filtered_df[
            filtered_df["Sales Group"]
            .isin(sales_filter)
        ]

    if action_filter:

        filtered_df = filtered_df[
            filtered_df["Action"]
            .isin(action_filter)
        ]

    # =====================================================
    # REMOVE IMAGE URL
    # =====================================================

    if "Image URL" in filtered_df.columns:

        filtered_df = filtered_df.drop(
            columns=["Image URL"]
        )

    # =====================================================
    # DATASET
    # =====================================================

    st.markdown("## ASIN Dataset")

    gb = GridOptionsBuilder.from_dataframe(
        filtered_df
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        floatingFilter=True,
        wrapText=False,
        autoHeight=False,
    )

    # AUTO FIT
    for col in filtered_df.columns:

        gb.configure_column(
            col,
            flex=1,
            minWidth=120,
        )

    # FREEZE
    for col in [
        "ASIN",
        "Image",
        "ASIN Sales",
        "ASIN Revenue",
    ]:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                pinned="left"
            )

    # IMAGE RENDERER

    image_renderer = JsCode("""
    class ImgCellRenderer {
      init(params) {
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = params.value || '';
      }
      getGui() {
        return this.eGui;
      }
    }
    """)

    link_renderer = JsCode("""
    class UrlCellRenderer {
      init(params) {
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = params.value || '';
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
            width=110,
            minWidth=110,
            maxWidth=110,
            autoHeight=True,
        )

        gb.configure_grid_options(
            rowHeight=90
        )

    if "ASIN" in filtered_df.columns:

        gb.configure_column(
            "ASIN",
            cellRenderer=link_renderer,
        )

    # =====================================================
    # COLOR STYLE
    # =====================================================

    group_color_js = JsCode("""
    function(params) {

        if (!params.value) {
            return {};
        }

        const value = params.value.toString();

        if (value.includes("Old")) {
            return {
                backgroundColor: "#7f1d1d",
                color: "white",
                fontWeight: "700"
            };
        }

        if (
            value.includes("Mid")
            || value.includes("Stable")
        ) {
            return {
                backgroundColor: "#1d4ed8",
                color: "white",
                fontWeight: "700"
            };
        }

        if (
            value.includes("New")
            || value.includes("High")
        ) {
            return {
                backgroundColor: "#15803d",
                color: "white",
                fontWeight: "700"
            };
        }

        if (
            value.includes("Low")
            || value.includes("No")
        ) {
            return {
                backgroundColor: "#374151",
                color: "white",
                fontWeight: "700"
            };
        }

        return {};
    }
    """)

    action_color_js = JsCode("""
    function(params) {

        if (!params.value) {
            return {};
        }

        const value = params.value.toString();

        if (
            value.includes("Avoid")
            || value.includes("Skip")
        ) {
            return {
                backgroundColor: "#7f1d1d",
                color: "white",
                fontWeight: "700"
            };
        }

        if (
            value.includes("Learn")
            || value.includes("Monitor")
        ) {
            return {
                backgroundColor: "#1d4ed8",
                color: "white",
                fontWeight: "700"
            };
        }

        if (
            value.includes("Scale")
            || value.includes("Research")
        ) {
            return {
                backgroundColor: "#15803d",
                color: "white",
                fontWeight: "700"
            };
        }

        return {};
    }
    """)

    for col in [
        "Seller Group",
        "Listing Group",
        "Sales Group",
    ]:

        if col in filtered_df.columns:

            gb.configure_column(
                col,
                cellStyle=group_color_js
            )

    if "Action" in filtered_df.columns:

        gb.configure_column(
            "Action",
            cellStyle=action_color_js
        )

    # =====================================================
    # GRID TOOLBAR + EXPORT + COLUMN MENU
    # =====================================================
    
    gb.configure_side_bar(
        filters_panel=True,
        columns_panel=True,
    )
    
    gb.configure_grid_options(
        enableRangeSelection=True,
        enableCharts=True,
        rowSelection="multiple",
    
        # MENU 3 CHẤM
        suppressMenuHide=False,
    
        # SIDEBAR
        sideBar={
            "toolPanels": [
                {
                    "id": "columns",
                    "labelDefault": "Columns",
                    "labelKey": "columns",
                    "iconKey": "columns",
                    "toolPanel": "agColumnsToolPanel",
                },
                {
                    "id": "filters",
                    "labelDefault": "Filters",
                    "labelKey": "filters",
                    "iconKey": "filter",
                    "toolPanel": "agFiltersToolPanel",
                },
            ],
            "defaultToolPanel": "",
        },
    
        # STATUS BAR
        statusBar={
            "statusPanels": [
                {
                    "statusPanel": "agTotalAndFilteredRowCountComponent",
                    "align": "left",
                },
                {
                    "statusPanel": "agAggregationComponent",
                    "align": "right",
                },
            ]
        },
    
        # AUTO SIZE
        domLayout="normal",
    )
    
    # =====================================================
    # EXPORT BUTTONS
    # =====================================================
    
    c1, c2 = st.columns(2)
    
    with c1:
    
        csv = filtered_df.to_csv(index=False).encode("utf-8")
    
        st.download_button(
            "⬇ Export CSV",
            csv,
            "asin_dataset.csv",
            "text/csv",
            use_container_width=True,
        )
    
    with c2:
    
        excel_buffer = io.BytesIO()
    
        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:
    
            filtered_df.to_excel(
                writer,
                index=False,
                sheet_name="ASIN Dataset"
            )
    
        st.download_button(
            "⬇ Export Excel",
            excel_buffer.getvalue(),
            "asin_dataset.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    grid_options = gb.build()

    AgGrid(
        filtered_df,
        gridOptions=grid_options,
        theme="alpine-dark",
        height=760,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        reload_data=False,
    )

    # =====================================================
    # REVENUE DISTRIBUTION
    # =====================================================

    st.markdown(
        "## Competitor Revenue Distribution"
    )

    revenue_chart = (
        filtered_df
        .groupby("Group Before Sales")[
            "_ASIN Revenue Numeric"
        ]
        .sum()
        .sort_values(ascending=False)
    )

    import plotly.express as px

    revenue_df = revenue_chart.reset_index()
    revenue_df.columns = ["Group Before Sales", "Revenue"]
    
    fig = px.bar(
        revenue_df,
        x="Group Before Sales",
        y="Revenue"
    )
    
    fig.update_layout(
        xaxis_tickangle=0,      # hoặc -20, -30
        height=450
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # CATEGORY MARKET SHARE
    # =====================================================

    st.markdown(
        "## Category Market Share by Group"
    )

    category_col = None

    for col in [
        "Category",
        "Categories",
        "Main Category",
        "Product Category",
    ]:

        if col in filtered_df.columns:

            category_col = col
            break

    if category_col:

        group_options = sorted(
            filtered_df[
                "Group Before Sales"
            ]
            .dropna()
            .unique()
        )

        selected_group = st.selectbox(
            "Select Group Before Sales",
            options=group_options
        )

        category_df = filtered_df[
            filtered_df[
                "Group Before Sales"
            ] == selected_group
        ]

        if not category_df.empty:

            category_share = (
                category_df[category_col]
                .fillna("Unknown")
                .astype(str)
                .value_counts(normalize=True)
                .mul(100)
                .round(1)
                .reset_index()
            )

            category_share.columns = [
                "Category",
                "Market Share %",
            ]

            st.dataframe(
                category_share,
                use_container_width=True,
                height=320
            )

            fig = px.bar(
                category_share,
                x="Category",
                y="Market Share %"
            )
            
            fig.update_layout(
                xaxis_tickangle=0,      # hoặc -20
                height=450
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # COMPETITOR OPPORTUNITY INTELLIGENCE
    # =====================================================
    
    st.markdown(
        "## Competitor Opportunity Intelligence"
    )
    
    competitor_summary = (
        filtered_df
        .groupby("Group Before Sales")
        .agg({
    
            "ASIN": "count",
            "_ASIN Revenue Numeric": "sum",
            "ASIN Sales": "sum",
    
        })
        .reset_index()
    )
    
    competitor_summary.columns = [
    
        "Competitor Group",
        "Total ASINs",
        "Total Revenue",
        "Total Sales",
    
    ]
    
    # =====================================================
    # MARKET METRICS
    # =====================================================
    
    market_revenue = competitor_summary[
        "Total Revenue"
    ].sum()
    
    market_sales = competitor_summary[
        "Total Sales"
    ].sum()
    
    competitor_summary["Revenue Share %"] = (
        competitor_summary["Total Revenue"]
        / market_revenue
        * 100
    ).round(1)
    
    competitor_summary["Sales Share %"] = (
        competitor_summary["Total Sales"]
        / market_sales
        * 100
    ).round(1)
    
    competitor_summary["Avg Revenue / ASIN"] = (
        competitor_summary["Total Revenue"]
        / competitor_summary["Total ASINs"]
    ).round(2)
    
    competitor_summary["Avg Sales / ASIN"] = (
        competitor_summary["Total Sales"]
        / competitor_summary["Total ASINs"]
    ).round(1)
    
    # =====================================================
    # ACTION ENGINE
    # =====================================================
    
    def generate_action(row):
    
        revenue = row["Revenue Share %"]
        avg_sales = row["Avg Sales / ASIN"]
        asins = row["Total ASINs"]
    
        if revenue >= 40:
    
            return "Avoid"
    
        elif revenue >= 25 and avg_sales >= 800:
    
            return "Research"
    
        elif asins >= 20 and revenue < 20:
    
            return "Opportunity"
    
        elif avg_sales < 300:
    
            return "Monitor"
    
        return "Analyze"
    
    # =====================================================
    # STRATEGY ENGINE
    # =====================================================
    
    def generate_strategy(row):
    
        action = row["Action"]
    
        if action == "Avoid":
    
            return (
                "This competitor group dominates category revenue. "
                "Compete only with strong product differentiation."
            )
    
        elif action == "Research":
    
            return (
                "Strong revenue and sales performance. "
                "Analyze pricing, reviews and best-selling listings before entering."
            )
    
        elif action == "Opportunity":
    
            return (
                "Large number of competitors but low revenue concentration. "
                "Potential market gap for differentiated products."
            )
    
        elif action == "Monitor":
    
            return (
                "Demand remains limited. "
                "Monitor market trends before investing."
            )
    
        return (
            "Balanced competitor landscape. "
            "Continue evaluating product positioning and customer demand."
        )
    
    competitor_summary["Action"] = (
        competitor_summary
        .apply(generate_action, axis=1)
    )
    
    competitor_summary["Strategy"] = (
        competitor_summary
        .apply(generate_strategy, axis=1)
    )
    
    # =====================================================
    # FORMAT
    # =====================================================
    
    competitor_summary["Total Revenue"] = (
        competitor_summary["Total Revenue"]
        .apply(format_us_currency)
    )
    
    competitor_summary["Avg Revenue / ASIN"] = (
        competitor_summary["Avg Revenue / ASIN"]
        .apply(format_us_currency)
    )
    
    competitor_summary = competitor_summary[
    
        [
            "Competitor Group",
            "Total ASINs",
            "Total Revenue",
            "Total Sales",
            "Revenue Share %",
            "Sales Share %",
            "Avg Revenue / ASIN",
            "Avg Sales / ASIN",
            "Action",
            "Strategy",
        ]
    
    ]
    
    st.dataframe(
    
        competitor_summary,
        use_container_width=True,
        height=420,
    
    )
