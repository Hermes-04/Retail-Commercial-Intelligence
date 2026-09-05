from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Retail Commercial Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "dashboard"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .block-container {
        padding-top: 1.15rem;
        padding-bottom: 1.25rem;
        max-width: 1450px;
    }

    h1 {
        font-size: 2.1rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.6px;
        margin-bottom: 0.1rem !important;
    }

    h2 {
        font-size: 1.18rem !important;
        font-weight: 700 !important;
        margin-top: 0.35rem !important;
        margin-bottom: 0.3rem !important;
    }

    h3 {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    p {
        margin-bottom: 0.25rem;
    }


    /* ========================================================
       SECTION LABEL
       ======================================================== */

    .section-label {
        font-size: 0.67rem;
        font-weight: 800;
        letter-spacing: 1.35px;
        text-transform: uppercase;
        color: #6b7280;
        margin-top: 0.65rem;
        margin-bottom: 0.2rem;
    }


    .dashboard-subtitle {
        font-size: 0.88rem;
        color: #6b7280;
        margin-bottom: 0.45rem;
    }


    /* ========================================================
       TABLES
       ======================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }


    /* ========================================================
       PRINT PAGE BREAKS
       ======================================================== */

    .pdf-page-break {
        height: 0;
        margin: 0;
        padding: 0;
        break-before: page;
        page-break-before: always;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    [data-testid="stSidebar"] {
        background: #f7f8fa;
    }


    /* ========================================================
       PRINT OPTIMIZATION
       ======================================================== */

    @media print {

        .pdf-page-break {
            break-before: page !important;
            page-break-before: always !important;
        }

        .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    filenames = {
        "kpis": "executive_kpis.csv",
        "monthly": "monthly_performance.csv",
        "country": "country_performance.csv",
        "rfm": "customer_rfm_dashboard.csv",
        "risk": "high_value_at_risk.csv",
        "products": "product_master_dashboard.csv",
        "cross_sell": "cross_sell_opportunities.csv",
    }

    loaded = {}

    for key, filename in filenames.items():

        path = DATA_DIR / filename

        if not path.exists():

            raise FileNotFoundError(
                f"Missing dashboard file:\n{path}"
            )

        loaded[key] = pd.read_csv(path)

    return loaded


try:

    data = load_data()

except Exception as e:

    st.error(
        "Dashboard data could not be loaded."
    )

    st.code(str(e))

    st.stop()


kpis = data["kpis"]
monthly = data["monthly"]
country = data["country"]
rfm = data["rfm"]
risk = data["risk"]
products = data["products"]
cross_sell = data["cross_sell"]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def find_column(df, candidates):

    mapping = {
        str(column).lower().strip(): column
        for column in df.columns
    }

    for candidate in candidates:

        key = candidate.lower().strip()

        if key in mapping:

            return mapping[key]

    return None


def get_value(row, candidates, default=0):

    for candidate in candidates:

        if candidate in row.index:

            value = row[candidate]

            if pd.notna(value):

                try:
                    return float(value)

                except (ValueError, TypeError):

                    return value

    return default


# ============================================================
# NORMALIZE MONTH
# ============================================================

month_column = find_column(
    monthly,
    [
        "Month",
        "YearMonth",
        "Year_Month",
        "Period",
        "Date",
        "InvoiceMonth",
    ],
)


if month_column is None:

    for column in monthly.columns:

        converted = pd.to_datetime(
            monthly[column],
            errors="coerce",
        )

        if converted.notna().sum() >= 3:

            month_column = column
            break


if month_column is None:

    st.error(
        "Could not identify the date column in "
        "`monthly_performance.csv`."
    )

    st.write(
        "Available columns:",
        list(monthly.columns),
    )

    st.stop()


monthly["Month"] = pd.to_datetime(
    monthly[month_column],
    errors="coerce",
)


# ============================================================
# NORMALIZE OTHER DATA
# ============================================================

if "Country" in country.columns:

    country["Country"] = (
        country["Country"]
        .astype(str)
        .str.strip()
    )


if "Segment" in rfm.columns:

    rfm["Segment"] = (
        rfm["Segment"]
        .astype(str)
        .str.strip()
    )


if "Segment" in risk.columns:

    risk["Segment"] = (
        risk["Segment"]
        .astype(str)
        .str.strip()
    )


# ============================================================
# REMOVE NON-MERCHANDISE PRODUCTS
# ============================================================

NON_MERCHANDISE_CODES = {
    "POST",
    "DOT",
    "AMAZONFEE",
    "BANK CHARGES",
    "D",
    "S",
    "M",
    "gift_0001_10",
    "gift_0001_20",
    "gift_0001_30",
    "gift_0001_40",
    "gift_0001_50",
    "gift_0001_60",
    "gift_0001_70",
    "gift_0001_80",
    "gift_0001_90",
    "gift_0001_100",
}


if "StockCode" in products.columns:

    products["StockCode"] = (
        products["StockCode"]
        .astype(str)
        .str.strip()
    )

    products = products[
        ~products["StockCode"].isin(
            NON_MERCHANDISE_CODES
        )
    ].copy()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "Dashboard Controls"
)

st.sidebar.caption(
    "Retail Commercial Intelligence"
)

st.sidebar.divider()


markets = ["All Markets"]

if "Country" in country.columns:

    markets += sorted(
        country["Country"]
        .dropna()
        .unique()
        .tolist()
    )


selected_market = st.sidebar.selectbox(
    "Market",
    markets,
)


segments = ["All Segments"]

if "Segment" in rfm.columns:

    segments += sorted(
        rfm["Segment"]
        .dropna()
        .unique()
        .tolist()
    )


selected_segment = st.sidebar.selectbox(
    "Customer Segment",
    segments,
)


st.sidebar.divider()

st.sidebar.caption(
    "Source: UCI Online Retail II"
)

st.sidebar.caption(
    "Transaction-level retail data covering 2009–2011."
)


# ============================================================
# ============================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# ============================================================
# ============================================================


st.title(
    "Retail Commercial Intelligence"
)

st.markdown(
    """
    <div class="dashboard-subtitle">
        Executive view of revenue performance, customer value,
        retention, commercial risk, and growth opportunities.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPI VALUES
# ============================================================

kpi_row = kpis.iloc[0]


net_revenue = get_value(
    kpi_row,
    [
        "net_revenue",
        "NetRevenue",
        "net_revenue_value",
    ],
    19_379_041.03,
)


gross_revenue = get_value(
    kpi_row,
    [
        "gross_sales_revenue",
        "GrossRevenue",
        "gross_revenue",
    ],
    20_902_829.41,
)


orders = get_value(
    kpi_row,
    [
        "unique_orders",
        "UniqueOrders",
        "orders",
    ],
    53_627,
)


repeat_rate = 71.61


# ============================================================
# KPI CARDS
# ============================================================

st.markdown(
    '<div class="section-label">Executive Performance</div>',
    unsafe_allow_html=True,
)


st.html(
    f"""
    <div style="
        display:grid;
        grid-template-columns:
            repeat(4, minmax(0, 1fr));
        gap:11px;
        width:100%;
        margin:5px 0 9px 0;
        font-family:Arial,sans-serif;
    ">


        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:12px 14px;
            min-height:86px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:1px;
                color:#6b7280;
                margin-bottom:5px;
            ">
                NET REVENUE
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
                line-height:1.05;
                color:#111827;
                white-space:nowrap;
            ">
                £{net_revenue / 1_000_000:.2f}M
            </div>

            <div style="
                font-size:9px;
                color:#9ca3af;
                margin-top:5px;
            ">
                After returns & cancellations
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:12px 14px;
            min-height:86px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:1px;
                color:#6b7280;
                margin-bottom:5px;
            ">
                GROSS REVENUE
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
                line-height:1.05;
                color:#111827;
                white-space:nowrap;
            ">
                £{gross_revenue / 1_000_000:.2f}M
            </div>

            <div style="
                font-size:9px;
                color:#9ca3af;
                margin-top:5px;
            ">
                Commercial sales before returns
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:12px 14px;
            min-height:86px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:1px;
                color:#6b7280;
                margin-bottom:5px;
            ">
                ORDERS
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
                line-height:1.05;
                color:#111827;
                white-space:nowrap;
            ">
                {orders:,.0f}
            </div>

            <div style="
                font-size:9px;
                color:#9ca3af;
                margin-top:5px;
            ">
                Unique commercial orders
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:12px 14px;
            min-height:86px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:1px;
                color:#6b7280;
                margin-bottom:5px;
            ">
                REPEAT CUSTOMER RATE
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
                line-height:1.05;
                color:#111827;
                white-space:nowrap;
            ">
                {repeat_rate:.2f}%
            </div>

            <div style="
                font-size:9px;
                color:#9ca3af;
                margin-top:5px;
            ">
                Customers with more than one order
            </div>

        </div>

    </div>
    """
)


# ============================================================
# EXECUTIVE SIGNAL
# ============================================================

st.markdown(
    '<div class="section-label">Executive Signal</div>',
    unsafe_allow_html=True,
)


st.html(
    """
    <div style="
        border-left:4px solid #111827;
        background:#f8fafc;
        border-radius:6px;
        padding:9px 12px;
        margin:3px 0 8px 0;
        font-family:Arial,sans-serif;
    ">

        <div style="
            font-size:11px;
            font-weight:700;
            color:#111827;
            margin-bottom:3px;
        ">
            Revenue is concentrated, but repeat behaviour is strong.
        </div>

        <div style="
            font-size:10px;
            line-height:1.4;
            color:#4b5563;
        ">
            The commercial opportunity is not simply acquiring more
            customers. Management should protect high-value accounts,
            recover valuable inactive customers, and use product
            affinity to expand customer value.
        </div>

    </div>
    """
)


# ============================================================
# MANAGEMENT INTERPRETATION
# ============================================================

st.markdown(
    '<div class="section-label">Management Interpretation</div>',
    unsafe_allow_html=True,
)


champion_revenue = 12_071_223.84
at_risk_revenue = 1_014_154.48
top_10_concentration = 63.83


st.html(
    f"""
    <div style="
        display:grid;
        grid-template-columns:
            repeat(3, minmax(0, 1fr));
        gap:10px;
        margin:3px 0 8px 0;
        font-family:Arial,sans-serif;
    ">

        <div style="
            border:1px solid #e5e7eb;
            border-radius:8px;
            padding:9px 11px;
            min-height:73px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                color:#374151;
                margin-bottom:4px;
            ">
                CUSTOMER CONCENTRATION
            </div>

            <div style="
                font-size:10px;
                line-height:1.35;
                color:#6b7280;
            ">
                Top 10% of identified customers contribute
                approximately
                <strong>{top_10_concentration:.1f}%</strong>
                of customer revenue.
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:8px;
            padding:9px 11px;
            min-height:73px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                color:#374151;
                margin-bottom:4px;
            ">
                CHAMPION CUSTOMERS
            </div>

            <div style="
                font-size:10px;
                line-height:1.35;
                color:#6b7280;
            ">
                Champion customers generate approximately
                <strong>£{champion_revenue / 1_000_000:.2f}M</strong>
                in historical gross revenue.
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:8px;
            padding:9px 11px;
            min-height:73px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                color:#374151;
                margin-bottom:4px;
            ">
                RECOVERY OPPORTUNITY
            </div>

            <div style="
                font-size:10px;
                line-height:1.35;
                color:#6b7280;
            ">
                <strong>226</strong> high-value customers are
                At Risk High Value, representing approximately
                <strong>£{at_risk_revenue / 1_000_000:.2f}M</strong>
                in historical gross revenue.
            </div>

        </div>

    </div>
    """
)


# ============================================================
# ACTIONS
# ============================================================

st.markdown(
    '<div class="section-label">Recommended Commercial Actions</div>',
    unsafe_allow_html=True,
)


actions = pd.DataFrame(
    {
        "Priority": [
            "1",
            "2",
            "3",
            "4",
        ],
        "Management Action": [
            "Protect and deepen relationships with Champion customers.",
            "Launch targeted recovery campaigns for high-value at-risk customers.",
            "Use product affinity relationships to increase cross-sell penetration.",
            "Monitor high-return products and customer accounts before scaling campaigns.",
        ],
        "Business Objective": [
            "Revenue retention",
            "Revenue recovery",
            "Customer value expansion",
            "Revenue quality",
        ],
    }
)


st.dataframe(
    actions,
    width="stretch",
    hide_index=True,
    height=158,
)


# ============================================================
# EXPLICIT PAGE BREAK
# ============================================================

st.html(
    '<div class="pdf-page-break"></div>'
)


# ============================================================
# ============================================================
# PAGE 2 — COMMERCIAL PERFORMANCE
# ============================================================
# ============================================================


st.markdown(
    '<div class="section-label">Commercial Performance</div>',
    unsafe_allow_html=True,
)

st.subheader(
    "Monthly Net Commercial Revenue"
)


# ============================================================
# MONTHLY REVENUE
# ============================================================

monthly_revenue_column = find_column(
    monthly,
    [
        "NetRevenue",
        "net_revenue",
        "Net Revenue",
        "Revenue",
        "revenue",
    ],
)


if monthly_revenue_column is None:

    numeric_columns = monthly.select_dtypes(
        include="number"
    ).columns.tolist()

    if numeric_columns:

        monthly_revenue_column = numeric_columns[-1]


if monthly_revenue_column is None:

    st.error(
        "Could not identify monthly revenue."
    )

    st.stop()


fig_monthly = px.line(
    monthly.sort_values("Month"),
    x="Month",
    y=monthly_revenue_column,
    markers=True,
)


fig_monthly.update_layout(
    height=280,
    margin=dict(
        l=15,
        r=10,
        t=5,
        b=15,
    ),
    hovermode="x unified",
)


fig_monthly.update_yaxes(
    tickprefix="£",
    tickformat=",.0f",
    title="Net Revenue",
)


fig_monthly.update_xaxes(
    title="",
)


st.plotly_chart(
    fig_monthly,
    width="stretch",
)


# ============================================================
# MARKET + RFM
# ============================================================

st.markdown(
    '<div class="section-label">Commercial Portfolio</div>',
    unsafe_allow_html=True,
)


geo_col, rfm_col = st.columns(2)


# ============================================================
# MARKET
# ============================================================

with geo_col:

    st.subheader(
        "Market Performance"
    )


    country_chart = country.copy()


    if selected_market != "All Markets":

        country_chart = country_chart[
            country_chart["Country"]
            == selected_market
        ]


    country_revenue_column = find_column(
        country_chart,
        [
            "NetRevenue",
            "net_revenue",
            "Net Revenue",
            "Revenue",
            "revenue",
        ],
    )


    if country_revenue_column is not None:

        country_chart = (
            country_chart
            .sort_values(
                country_revenue_column,
                ascending=False,
            )
            .head(8)
        )


        fig_country = px.bar(
            country_chart.sort_values(
                country_revenue_column,
                ascending=True,
            ),
            x=country_revenue_column,
            y="Country",
            orientation="h",
        )


        fig_country.update_layout(
            height=270,
            margin=dict(
                l=5,
                r=8,
                t=5,
                b=15,
            ),
        )


        fig_country.update_xaxes(
            tickprefix="£",
            tickformat=",.0f",
            title="Net Revenue",
        )


        fig_country.update_yaxes(
            title="",
        )


        st.plotly_chart(
            fig_country,
            width="stretch",
        )


# ============================================================
# RFM
# ============================================================

with rfm_col:

    st.subheader(
        "Customer Segment Value"
    )


    rfm_chart = rfm.copy()


    if selected_segment != "All Segments":

        rfm_chart = rfm_chart[
            rfm_chart["Segment"]
            == selected_segment
        ]


    if "Monetary" in rfm_chart.columns:

        segment_value = (
            rfm_chart
            .groupby(
                "Segment",
                as_index=False,
            )["Monetary"]
            .sum()
            .sort_values(
                "Monetary",
                ascending=False,
            )
        )


        fig_rfm = px.bar(
            segment_value,
            x="Segment",
            y="Monetary",
        )


        fig_rfm.update_yaxes(
            tickprefix="£",
            tickformat=",.0f",
            title="Gross Revenue",
        )


    else:

        segment_value = (
            rfm_chart
            .groupby("Segment")
            .size()
            .reset_index(
                name="Customers"
            )
        )


        fig_rfm = px.bar(
            segment_value,
            x="Segment",
            y="Customers",
        )


    fig_rfm.update_layout(
        height=270,
        margin=dict(
            l=5,
            r=8,
            t=5,
            b=15,
        ),
        xaxis_tickangle=-30,
    )


    fig_rfm.update_xaxes(
        title="",
    )


    st.plotly_chart(
        fig_rfm,
        width="stretch",
    )


# ============================================================
# RISK SUMMARY
# ============================================================

st.markdown(
    '<div class="section-label">Customer Risk</div>',
    unsafe_allow_html=True,
)


risk_value = 0


if "Monetary" in risk.columns:

    risk_value = risk[
        "Monetary"
    ].sum()

elif "NetRevenue" in risk.columns:

    risk_value = risk[
        "NetRevenue"
    ].sum()


st.html(
    f"""
    <div style="
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:10px;
        margin:3px 0 5px 0;
        font-family:Arial,sans-serif;
    ">

        <div style="
            border:1px solid #e5e7eb;
            border-radius:8px;
            padding:9px 12px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:.7px;
                color:#6b7280;
            ">
                AT-RISK HIGH-VALUE CUSTOMERS
            </div>

            <div style="
                font-size:22px;
                font-weight:700;
                color:#111827;
                margin-top:3px;
            ">
                {len(risk):,}
            </div>

        </div>


        <div style="
            border:1px solid #e5e7eb;
            border-radius:8px;
            padding:9px 12px;
            background:#ffffff;
        ">

            <div style="
                font-size:9px;
                font-weight:700;
                letter-spacing:.7px;
                color:#6b7280;
            ">
                HISTORICAL GROSS VALUE
            </div>

            <div style="
                font-size:22px;
                font-weight:700;
                color:#111827;
                margin-top:3px;
                white-space:nowrap;
            ">
                £{risk_value:,.0f}
            </div>

        </div>

    </div>
    """
)


# ============================================================
# EXPLICIT PAGE BREAK
# ============================================================

st.html(
    '<div class="pdf-page-break"></div>'
)


# ============================================================
# ============================================================
# PAGE 3 — CUSTOMER & PRODUCT INTELLIGENCE
# ============================================================
# ============================================================


st.markdown(
    '<div class="section-label">Customer Intelligence</div>',
    unsafe_allow_html=True,
)

st.subheader(
    "High-Value Customers at Risk"
)


# ============================================================
# RISK TABLE
# ============================================================

risk_columns = [
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
    "Segment",
]


risk_columns = [
    column
    for column in risk_columns
    if column in risk.columns
]


risk_display = (
    risk[
        risk_columns
    ]
    .head(6)
    .copy()
)


if "Monetary" in risk_display.columns:

    risk_display["Monetary"] = (
        risk_display["Monetary"]
        .map(
            lambda x:
                f"£{x:,.0f}"
        )
    )


st.dataframe(
    risk_display,
    width="stretch",
    hide_index=True,
    height=245,
)


# ============================================================
# PRODUCT INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-label">Product Intelligence</div>',
    unsafe_allow_html=True,
)

st.subheader(
    "Top Commercial Products"
)


product_revenue_column = find_column(
    products,
    [
        "NetRevenue",
        "net_revenue",
        "Net Revenue",
    ],
)


if product_revenue_column is not None:

    product_display = (
        products
        .sort_values(
            product_revenue_column,
            ascending=False,
        )
        .head(6)
        .copy()
    )

else:

    product_display = (
        products
        .head(6)
        .copy()
    )


product_display = product_display.rename(
    columns={
        "StockCode": "Product",
        "Description": "Description",
        "GrossRevenue": "Gross Revenue",
        "NetRevenue": "Net Revenue",
        "UnitsSold": "Units Sold",
        "ReturnValueRate": "Return Rate",
        "RevenueRank": "Rank",
    }
)


if "Net Revenue" in product_display.columns:

    product_display["Net Revenue"] = (
        product_display["Net Revenue"]
        .map(
            lambda x:
                f"£{x:,.0f}"
        )
    )


if "Units Sold" in product_display.columns:

    product_display["Units Sold"] = (
        product_display["Units Sold"]
        .map(
            lambda x:
                f"{x:,.0f}"
        )
    )


product_columns = [
    "Product",
    "Description",
    "Net Revenue",
    "Units Sold",
]


product_columns = [
    column
    for column in product_columns
    if column in product_display.columns
]


st.dataframe(
    product_display[
        product_columns
    ],
    width="stretch",
    hide_index=True,
    height=245,
)


# ============================================================
# CROSS-SELL
# ============================================================

st.markdown(
    '<div class="section-label">Growth Opportunities</div>',
    unsafe_allow_html=True,
)

st.subheader(
    "Executive Cross-Sell Opportunities"
)


cross_sell_display = cross_sell.copy()


# ============================================================
# DESCRIPTION LOOKUP
# ============================================================

description_lookup = {}


if (
    "StockCode" in products.columns
    and "Description" in products.columns
):

    description_lookup = (
        products
        .dropna(
            subset=["StockCode"]
        )
        .drop_duplicates(
            "StockCode"
        )
        .set_index(
            "StockCode"
        )["Description"]
        .to_dict()
    )


if "ProductA" in cross_sell_display.columns:

    cross_sell_display["Product A"] = (
        cross_sell_display["ProductA"]
        .astype(str)
        .map(description_lookup)
        .fillna(
            cross_sell_display[
                "ProductA"
            ].astype(str)
        )
    )


if "ProductB" in cross_sell_display.columns:

    cross_sell_display["Product B"] = (
        cross_sell_display["ProductB"]
        .astype(str)
        .map(description_lookup)
        .fillna(
            cross_sell_display[
                "ProductB"
            ].astype(str)
        )
    )


if "Lift" in cross_sell_display.columns:

    cross_sell_display["Lift"] = (
        cross_sell_display["Lift"]
        .map(
            lambda x:
                f"{x:.1f}x"
        )
    )


if "Confidence_A_to_B" in cross_sell_display.columns:

    cross_sell_display["Confidence"] = (
        cross_sell_display[
            "Confidence_A_to_B"
        ]
        .map(
            lambda x:
                f"{x:.1%}"
        )
    )


cross_sell_display = (
    cross_sell_display
    .head(6)
)


cross_sell_columns = [
    "Product A",
    "Product B",
    "PairOrders",
    "Lift",
    "Confidence",
]


cross_sell_columns = [
    column
    for column in cross_sell_columns
    if column in cross_sell_display.columns
]


st.dataframe(
    cross_sell_display[
        cross_sell_columns
    ],
    width="stretch",
    hide_index=True,
    height=245,
)


# ============================================================
# EXECUTIVE TAKEAWAY
# ============================================================

st.markdown(
    '<div class="section-label">Executive Takeaway</div>',
    unsafe_allow_html=True,
)


st.html(
    """
    <div style="
        border:1px solid #e5e7eb;
        border-radius:8px;
        background:#f8fafc;
        padding:10px 13px;
        margin:4px 0 7px 0;
        font-family:Arial,sans-serif;
    ">

        <div style="
            font-size:10px;
            line-height:1.45;
            color:#4b5563;
        ">

            <strong style="color:#111827;">
                Commercial priority:
            </strong>

            protect the existing high-value customer base,
            recover valuable inactive accounts, and increase
            customer value through targeted product cross-selling.

            The portfolio demonstrates meaningful customer
            concentration, strong repeat purchasing behaviour,
            and identifiable opportunities for commercial intervention.

        </div>

    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Retail Commercial Intelligence • Business Analytics Portfolio Project"
)

st.caption(
    "Data source: UCI Online Retail II • "
    "Transaction-level commercial analysis."
)