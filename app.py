import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Nassau Candy — Profitability Dashboard",
    page_icon="🍫",
    layout="wide"
)

# ── CSS: no overrides on Streamlit native widgets to avoid calendar clipping ──
st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #eeeeee; }
    .action-card {
        background: #1a1a2e; border-left: 4px solid #FFD700;
        border-radius: 6px; padding: 12px 16px; margin-bottom: 8px;
    }
    .risk-card {
        background: #1a0a0a; border-left: 4px solid #f44336;
        border-radius: 6px; padding: 12px 16px; margin-bottom: 8px;
    }
    .good-card {
        background: #0a1a0a; border-left: 4px solid #4CAF50;
        border-radius: 6px; padding: 12px 16px; margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load & Clean (no raw/cleaned counts exposed) ──────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau_Candy_Distributor.csv")
    df = df.dropna(subset=["Sales", "Gross Profit", "Cost", "Units"])
    df = df[df["Sales"]  > 0]
    df = df[df["Units"]  > 0]
    df = df[df["Cost"]   >= 0]
    df = df[abs(df["Gross Profit"] - (df["Sales"] - df["Cost"])) < 0.05]
    df["Division"]     = df["Division"].str.strip().str.title()
    df["Region"]       = df["Region"].str.strip().str.title()
    df["Product Name"] = df["Product Name"].str.strip()
    df["Ship Mode"]    = df["Ship Mode"].str.strip().str.title()
    df["Order Date"]   = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    df["Ship Date"]    = pd.to_datetime(df["Ship Date"],  dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Order Date"])
    df["Month"]            = df["Order Date"].dt.to_period("M").astype(str)
    df["Gross Margin (%)"] = (df["Gross Profit"] / df["Sales"] * 100).round(2)
    df["Profit per Unit"]  = (df["Gross Profit"] / df["Units"]).round(2)
    return df

df = load_data()

# ── Global totals (full dataset — used as contribution denominators always) ───
GLOBAL_SALES  = df["Sales"].sum()
GLOBAL_PROFIT = df["Gross Profit"].sum()

# ── Sidebar — all 4 required user capabilities ───────────────────────────────
st.sidebar.title("🍫 Nassau Candy")
st.sidebar.markdown("**Profitability Dashboard**")
st.sidebar.markdown("---")

# 1. Date range selector
min_date, max_date = df["Order Date"].min().date(), df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "📅 Date Range", (min_date, max_date), 
    min_value=min_date, max_value=max_date
)

# 2. Division filter
divisions = ["All"] + sorted(df["Division"].unique().tolist())
sel_div   = st.sidebar.selectbox("🏷 Division", divisions)

# 3. Margin threshold slider — drives ALL margin logic
margin_threshold = st.sidebar.slider(
    "⚠️ Margin Risk Threshold (%)", 0, 100, 50,
    help="Products below this margin % are flagged as at-risk across all sections"
)

# 4. Product search — display filter only, never changes benchmarks
product_search = st.sidebar.text_input(
    "🔍 Search Product", "",
    help="Filters displayed products. Benchmarks always use full portfolio."
)

# ── Apply filters ─────────────────────────────────────────────────────────────
flt = df.copy()
if sel_div != "All":
    flt = flt[flt["Division"] == sel_div]
if len(date_range) == 2:
    flt = flt[
        (flt["Order Date"] >= pd.Timestamp(date_range[0])) &
        (flt["Order Date"] <= pd.Timestamp(date_range[1]))
    ]

# BUG 3 FIX: Stop early if no records match filters
if flt.empty:
    st.warning("⚠️ No records found for the selected filters. Please adjust the Date Range or Division.")
    st.stop()

# Product search — display-only, calculated AFTER portfolio benchmarks
if product_search.strip():
    flt_product = flt[flt["Product Name"].str.contains(product_search.strip(), case=False, na=False)]
else:
    flt_product = flt.copy()

# ── Aggregation helpers ───────────────────────────────────────────────────────
# BUG 2 FIX: Contribution % always divided by GLOBAL totals, never filtered totals
def product_agg(data, global_sales=GLOBAL_SALES, global_profit=GLOBAL_PROFIT):
    prod = (
        data.groupby(["Product Name", "Division"])
        .agg(Sales=("Sales","sum"), Profit=("Gross Profit","sum"),
             Cost=("Cost","sum"), Units=("Units","sum"))
        .reset_index()
    )
    prod["Gross Margin (%)"]         = (prod["Profit"] / prod["Sales"]  * 100).round(1)
    prod["Profit per Unit"]          = (prod["Profit"] / prod["Units"]).round(2)
    prod["Revenue Contribution (%)"] = (prod["Sales"]  / global_sales  * 100).round(2)
    prod["Profit Contribution (%)"]  = (prod["Profit"] / global_profit * 100).round(2)
    return prod.sort_values("Profit", ascending=False).reset_index(drop=True)

def monthly_agg(data):
    m = (
        data.groupby("Month")
        .agg(Sales=("Sales","sum"), Profit=("Gross Profit","sum"))
        .reset_index()
        .sort_values("Month")
    )
    m["Margin (%)"] = (m["Profit"] / m["Sales"] * 100).round(2)
    return m

COLORS = {"Chocolate": "#8B4513", "Sugar": "#E91E8C", "Other": "#2196F3"}
CHART  = dict(template="plotly_dark", plot_bgcolor="#1a1a2e",
              paper_bgcolor="#1a1a2e", margin=dict(l=10, r=10, t=30, b=10))

# ── Portfolio-level aggregations (no product search applied here) ─────────────
total_sales    = flt["Sales"].sum()
total_profit   = flt["Gross Profit"].sum()
total_cost     = flt["Cost"].sum()
total_units    = flt["Units"].sum()
overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

# Portfolio product df — benchmarks always from this, NOT from flt_product
portfolio_df = product_agg(flt)
monthly_df   = monthly_agg(flt)

# BUG 1 FIX: Portfolio benchmarks calculated from full portfolio, not searched subset
portfolio_avg_sales  = portfolio_df["Sales"].mean()
portfolio_avg_margin = portfolio_df["Gross Margin (%)"].mean()
portfolio_avg_csr    = ((portfolio_df["Cost"] / portfolio_df["Sales"]) * 100).mean()
portfolio_avg_ppu    = portfolio_df["Profit per Unit"].mean()

# Display df applies product search on top of portfolio — for display only
view_df = product_agg(flt_product) if not flt_product.empty else portfolio_df.iloc[0:0]

# ── Page header & KPI strip ───────────────────────────────────────────────────
st.markdown("## 🍫 Nassau Candy — Product Line Profitability & Margin Performance")
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Total Sales",    f"${total_sales:,.0f}")
c2.metric("📈 Gross Profit",   f"${total_profit:,.0f}")
c3.metric("📊 Overall Margin", f"{overall_margin:.1f}%")
c4.metric("📉 Total Cost",     f"${total_cost:,.0f}")
c5.metric("📦 Units Sold",     f"{total_units:,.0f}")
st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 Executive Summary",
    "📦 Product Profitability",
    "🏭 Division Performance",
    "🔍 Cost & Margin Diagnostics",
    "📊 Profit Concentration",
    "📈 Profitability Trends",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — EXECUTIVE SUMMARY
# Polished: concise cards, max 3 short recommendations, no paragraphs
# BUG 3 & BUG 4 FIX: all signals use margin_threshold dynamically
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div style="background:#1a1a2e; border-left:4px solid #FFD700; border-radius:6px;
                padding:14px 20px; margin-bottom:18px;">
        <p style="color:#FFD700; font-size:11px; text-transform:uppercase;
                  letter-spacing:1px; margin:0 0 4px 0;">Executive Summary — Strategic Decision Makers</p>
        <p style="color:#eeeeee; font-size:17px; font-weight:700; margin:0;">
            How can Nassau Candy improve profitability while reducing margin risk?
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic signals — all use margin_threshold (BUG 4 FIX)
    top3    = portfolio_df.head(3)
    bottom3 = portfolio_df.sort_values("Gross Margin (%)").head(3)
    at_risk = portfolio_df[portfolio_df["Gross Margin (%)"] < margin_threshold]

    prod_pareto = portfolio_df.copy()
    prod_pareto["cum_pct"] = (prod_pareto["Profit"].cumsum() / prod_pareto["Profit"].sum() * 100)
    pareto_profit_count = int((prod_pareto["cum_pct"] <= 80).sum()) + 1

    # BUG 2 FIX: div_summary uses global totals for contribution
    div_summary = (
        flt.groupby("Division")
        .agg(Profit=("Gross Profit","sum"), Sales=("Sales","sum"))
        .reset_index()
    )
    div_summary["Margin (%)"]       = (div_summary["Profit"] / div_summary["Sales"] * 100).round(1)
    div_summary["Profit Share (%)"] = (div_summary["Profit"] / GLOBAL_PROFIT * 100).round(1)

    margin_cv = 0
    if len(monthly_df) > 1 and monthly_df["Margin (%)"].mean() > 0:
        margin_cv = (monthly_df["Margin (%)"].std() / monthly_df["Margin (%)"].mean() * 100)

    if div_summary.empty: 
        st.warning("No division data available for the selected filters.")
        top_div = None 
        worst_div = None 
        best_div = None 
    else: 
        top_div = div_summary.sort_values("Profit Share (%)", ascending=False).iloc[0]
        worst_div = div_summary.sort_values("Margin (%)").iloc[0]
        best_div = div_summary.sort_values("Margin (%)").iloc[-1]

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("#### ✅ Top 3 Profit Drivers")
        for _, r in top3.iterrows():
            st.markdown(f"""
            <div class="good-card">
            <strong>{r['Product Name']}</strong><br>
            Margin: <strong>{r['Gross Margin (%)']:.1f}%</strong> &nbsp;|&nbsp; Profit: <strong>${r['Profit']:,.0f}</strong>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown("#### 🚨 Lowest Margin Products")
        for _, r in bottom3.iterrows():
            flag = "🚨" if r["Gross Margin (%)"] < margin_threshold else "⚠️"
            st.markdown(f"""
            <div class="risk-card">
            {flag} <strong>{r['Product Name']}</strong><br>
            Margin: <strong>{r['Gross Margin (%)']:.1f}%</strong> &nbsp;|&nbsp; {r['Division']}
            </div>
            """, unsafe_allow_html=True)

    with col_c:
        st.markdown("#### 📌 Key Business Signals")
        conc_risk    = "HIGH" if pareto_profit_count <= 3 else "MODERATE"
        margin_label = "Stable" if margin_cv < 2 else "Moderate fluctuation" if margin_cv < 5 else "High instability"
        st.markdown(f"""
        <div class="action-card">
        🔢 <strong>Profit Concentration:</strong> {pareto_profit_count} products = 80% of profit &nbsp;|&nbsp; Risk: <strong>{conc_risk}</strong>
        </div>
        <div class="action-card">
        📊 <strong>Top Division:</strong> {top_div['Division']} — {top_div['Profit Share (%)']:.1f}% of company profit
        </div>
        <div class="action-card">
        📉 <strong>Margin Stability:</strong> CV = {margin_cv:.2f}% &nbsp;|&nbsp; {margin_label}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Strategic Recommendations")

    # Rec 1 — at-risk products driven by threshold (BUG 4 FIX)
    if not at_risk.empty:
        names = ", ".join(at_risk["Product Name"].tolist())
        st.markdown(f"""
        <div class="risk-card">
        🚨 <strong>Pricing Review Required</strong> &nbsp;|&nbsp;
        {len(at_risk)} product(s) below {margin_threshold}% threshold: <strong>{names}</strong>.
        Conduct cost-to-sales review. Low-margin, low-volume products may require portfolio reassessment.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="good-card">
        ✅ <strong>No products below the {margin_threshold}% threshold.</strong> Portfolio margins are healthy under current filters.
        </div>
        """, unsafe_allow_html=True)

    # Rec 2 — concentration risk
    st.markdown(f"""
    <div class="action-card">
    ⚠️ <strong>Concentration Risk</strong> &nbsp;|&nbsp;
    {pareto_profit_count} products drive 80% of profit. Margin improvements in lower-ranked products
    would reduce over-dependency on a narrow product base.
    </div>
    """, unsafe_allow_html=True)

    # Rec 3 — division efficiency
    if best_div is not None and worst_div is not None:
       st.markdown(f"""
    <div class="action-card">
    📊 <strong>Division Efficiency</strong> &nbsp;|&nbsp;
    <strong>{best_div['Division']}</strong> leads at {best_div['Margin (%)']:.1f}% margin.
    <strong>{worst_div['Division']}</strong> lags at {worst_div['Margin (%)']:.1f}% —
    cost structure review recommended.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PRODUCT PROFITABILITY
# BUG 1 FIX: segmentation always uses portfolio_avg_sales / portfolio_avg_margin
# BUG 4 FIX: margin risk table uses margin_threshold slider
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Product Profitability Overview")
    st.caption("Which product lines deliver the highest gross margin? Which high-sales products are actually profitable?")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏆 Product Margin Leaderboard")
        st.caption("Ranked by Gross Margin %. Gold line = portfolio average.")
        fig = px.bar(
            view_df.sort_values("Gross Margin (%)") if not view_df.empty else portfolio_df.sort_values("Gross Margin (%)"),
            x="Gross Margin (%)", y="Product Name",
            orientation="h", color="Division",
            color_discrete_map=COLORS, text="Gross Margin (%)"
        )
        fig.add_vline(x=overall_margin, line_dash="dash", line_color="#FFD700",
                      annotation_text=f"Avg {overall_margin:.1f}%")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(**CHART, height=420,
                          yaxis=dict(tickfont=dict(size=9)),
                          legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("#### 💰 Profit Contribution by Product")
        st.caption("Total gross profit contributed by each product line.")
        plot_df2 = view_df if not view_df.empty else portfolio_df
        fig2 = px.bar(
            plot_df2.sort_values("Profit"),
            x="Profit", y="Product Name",
            orientation="h", color="Division",
            color_discrete_map=COLORS, text="Profit Contribution (%)"
        )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(**CHART, height=420,
                           yaxis=dict(tickfont=dict(size=9)),
                           legend=dict(orientation="h", y=-0.15),
                           xaxis_title="Gross Profit ($)")
        st.plotly_chart(fig2, width="stretch")

    st.markdown("---")

    # ── Product Segmentation — BUG 1 FIX: use portfolio benchmarks, not view_df ─
    st.markdown("#### 📂 Product Segmentation")
    st.caption(f"Classified against portfolio averages — Sales avg: ${portfolio_avg_sales:,.0f} | Margin avg: {portfolio_avg_margin:.1f}%")

    seg_source = view_df if not view_df.empty else portfolio_df
    stars      = seg_source[(seg_source["Sales"] >= portfolio_avg_sales) & (seg_source["Gross Margin (%)"] >= portfolio_avg_margin)]
    drains     = seg_source[(seg_source["Sales"] >= portfolio_avg_sales) & (seg_source["Gross Margin (%)"] <  portfolio_avg_margin)]
    candidates = seg_source[(seg_source["Sales"] <  portfolio_avg_sales) & (seg_source["Gross Margin (%)"] <  portfolio_avg_margin)]
    niche      = seg_source[(seg_source["Sales"] <  portfolio_avg_sales) & (seg_source["Gross Margin (%)"] >= portfolio_avg_margin)]

    seg1, seg2, seg3, seg4 = st.columns(4)
    with seg1:
        st.markdown(f"""<div class="good-card">
        <strong>⭐ High-Sales / High-Margin</strong><br><em>Stars — Protect & Grow</em><br><br>
        {"<br>".join([f"• {r['Product Name']}" for _, r in stars.iterrows()]) or "None"}
        </div>""", unsafe_allow_html=True)
    with seg2:
        st.markdown(f"""<div class="risk-card">
        <strong>⚠️ High-Sales / Low-Margin</strong><br><em>Drains — Review Cost</em><br><br>
        {"<br>".join([f"• {r['Product Name']}" for _, r in drains.iterrows()]) or "None"}
        </div>""", unsafe_allow_html=True)
    with seg3:
        st.markdown(f"""<div class="risk-card">
        <strong>🚨 Low-Sales / Low-Margin</strong><br><em>Review for Discontinuation</em><br><br>
        {"<br>".join([f"• {r['Product Name']}" for _, r in candidates.iterrows()]) or "None"}
        </div>""", unsafe_allow_html=True)
    with seg4:
        st.markdown(f"""<div class="action-card">
        <strong>💎 Low-Sales / High-Margin</strong><br><em>Niche — Grow Volume</em><br><br>
        {"<br>".join([f"• {r['Product Name']}" for _, r in niche.iterrows()]) or "None"}
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── High-Sales / Low-Profit — BUG 1 FIX: use portfolio benchmarks ────────
    st.markdown("#### 🔎 High-Sales but Low-Profit Products")
    st.caption("Products with above-portfolio-average revenue but below-portfolio-average margin.")

    high_sales_low_margin = seg_source[
        (seg_source["Sales"] >= portfolio_avg_sales) &
        (seg_source["Gross Margin (%)"] < portfolio_avg_margin)
    ].sort_values("Gross Margin (%)")

    if not high_sales_low_margin.empty:
        hs = high_sales_low_margin[["Product Name","Division","Sales","Profit","Gross Margin (%)"]].copy()
        hs["Sales"]  = hs["Sales"].map("${:,.0f}".format)
        hs["Profit"] = hs["Profit"].map("${:,.0f}".format)
        hs["Gross Margin (%)"] = hs["Gross Margin (%)"].map("{:.1f}%".format)
        st.dataframe(hs, hide_index=True)
        st.warning(f"⚠️ {len(high_sales_low_margin)} product(s) generate above-average revenue but below-average margins.")
    else:
        st.success("✅ No high-sales / low-margin products identified under current filters.")

    st.markdown("---")

    # ── Margin Risk Table — BUG 4 FIX: fully driven by margin_threshold slider ─
    st.markdown(f"#### 🚨 Margin Risk — Products Below {margin_threshold}% Threshold")
    risk_products = seg_source[seg_source["Gross Margin (%)"] < margin_threshold].sort_values("Gross Margin (%)")

    if not risk_products.empty:
        rd = risk_products[["Product Name","Division","Sales","Profit","Gross Margin (%)"]].copy()
        rd["Sales"]  = rd["Sales"].map("${:,.0f}".format)
        rd["Profit"] = rd["Profit"].map("${:,.0f}".format)
        rd["Gross Margin (%)"] = rd["Gross Margin (%)"].map("{:.1f}%".format)
        st.dataframe(rd, hide_index=True)
        st.error(f"🚨 {len(risk_products)} product(s) below the {margin_threshold}% margin threshold.")
    else:
        st.success(f"✅ No products fall below the {margin_threshold}% margin threshold.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — DIVISION PERFORMANCE
# BUG 2 FIX: contribution % always vs GLOBAL totals
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Division Performance Dashboard")
    st.caption("How does profitability vary across product divisions?")

    div_df = (
        flt.groupby("Division")
        .agg(Sales=("Sales","sum"), Profit=("Gross Profit","sum"), Cost=("Cost","sum"))
        .reset_index()
    )
    div_df["Margin (%)"]               = (div_df["Profit"] / div_df["Sales"] * 100).round(1)
    # BUG 2 FIX: divide by GLOBAL_SALES / GLOBAL_PROFIT, not filtered totals
    div_df["Revenue Contribution (%)"] = (div_df["Sales"]  / GLOBAL_SALES  * 100).round(1)
    div_df["Profit Contribution (%)"]  = (div_df["Profit"] / GLOBAL_PROFIT * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Revenue vs Profit by Division")
        st.caption("A large gap between Sales and Profit bars signals a cost efficiency problem.")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Sales",        x=div_df["Division"], y=div_df["Sales"],  marker_color="#2196F3"))
        fig.add_trace(go.Bar(name="Gross Profit", x=div_df["Division"], y=div_df["Profit"], marker_color="#4CAF50"))
        fig.add_trace(go.Bar(name="Cost",         x=div_df["Division"], y=div_df["Cost"],   marker_color="#f44336"))
        fig.update_layout(**CHART, barmode="group", height=320, legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("#### Gross Margin % by Division")
        st.caption("Divisions below the average margin line have a weaker cost-to-revenue structure.")
        fig2 = go.Figure(go.Bar(
            x=div_df["Division"], y=div_df["Margin (%)"],
            marker_color=[COLORS.get(d, "#888") for d in div_df["Division"]],
            text=div_df["Margin (%)"].map("{:.1f}%".format), textposition="outside"
        ))
        fig2.add_hline(y=overall_margin, line_dash="dash", line_color="#FFD700",
                       annotation_text=f"Portfolio avg {overall_margin:.1f}%")
        fig2.update_layout(**CHART, height=320, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig2, width="stretch")

    st.markdown("#### Contribution Share by Division (vs Total Company)")
    st.caption("Percentages represent each division's share of TOTAL company sales and profit. Always shown across all divisions regardless of filter.")

    # Always use full dataset for pie charts so contribution % is never distorted by division filter
    pie_df = (
        df.groupby("Division")
        .agg(Sales=("Sales","sum"), Profit=("Gross Profit","sum"))
        .reset_index()
    )
    pie_df["Revenue Contribution (%)"] = (pie_df["Sales"]  / GLOBAL_SALES  * 100).round(1)
    pie_df["Profit Contribution (%)"]  = (pie_df["Profit"] / GLOBAL_PROFIT * 100).round(1)

    # Highlight selected division with a pull effect if a specific division is filtered
    pull_rev  = [0.1 if sel_div != "All" and row["Division"] == sel_div else 0 for _, row in pie_df.iterrows()]
    pull_prof = pull_rev

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.pie(pie_df, values="Revenue Contribution (%)", names="Division",
                      color="Division", color_discrete_map=COLORS, hole=0.4,
                      title="Revenue Contribution % (of Company Total)")
        fig3.update_traces(pull=pull_rev)
        fig3.update_layout(template="plotly_dark", paper_bgcolor="#1a1a2e", height=280)
        st.plotly_chart(fig3, width="stretch")
    with col4:
        fig4 = px.pie(pie_df, values="Profit Contribution (%)", names="Division",
                      color="Division", color_discrete_map=COLORS, hole=0.4,
                      title="Profit Contribution % (of Company Total)")
        fig4.update_traces(pull=pull_prof)
        fig4.update_layout(template="plotly_dark", paper_bgcolor="#1a1a2e", height=280)
        st.plotly_chart(fig4, width="stretch")

    # BUG 4 FIX: division insights use margin_threshold slider
    st.markdown("#### Division Performance Insights")
    for _, row in div_df.sort_values("Profit Contribution (%)", ascending=False).iterrows():
        margin_val   = float(row["Margin (%)"])
        profit_share = float(row["Profit Contribution (%)"])
        if margin_val < margin_threshold:
            st.error(f"🚨 **{row['Division']}** — Margin {margin_val:.1f}% is below the {margin_threshold}% threshold. Cost efficiency review recommended.")
        elif profit_share > 50:
            st.warning(f"⚠️ **{row['Division']}** — Contributes {profit_share:.1f}% of company profit. High dependency — monitor margin closely.")
        else:
            st.success(f"✅ **{row['Division']}** — Margin {margin_val:.1f}%, profit share {profit_share:.1f}% of company total.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — COST & MARGIN DIAGNOSTICS
# BUG 1 FIX: benchmarks use portfolio_avg_csr / portfolio_avg_ppu
# BUG 4 FIX: all risk flags use margin_threshold
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Cost Structure Diagnostics & Margin Risk")
    st.caption("Which products represent margin risk? Where are cost structures inefficient?")

    # Use portfolio_df for benchmarks; view_df for display
    diag_source = view_df if not view_df.empty else portfolio_df

    # BUG 4 FIX: Risk classification uses margin_threshold slider
    diag_source = diag_source.copy()
    diag_source["Risk"] = diag_source["Gross Margin (%)"].apply(
        lambda m: "High Risk" if m < margin_threshold
                  else ("Watch" if m < (margin_threshold + 10) else "Healthy")
    )
    diag_source["Cost-to-Sales Ratio (%)"] = (diag_source["Cost"] / diag_source["Sales"] * 100).round(1)

    risk_colors = {"High Risk": "#f44336", "Watch": "#FF9800", "Healthy": "#4CAF50"}

    # ── Cost vs Sales Scatter ─────────────────────────────────────────────────
    st.markdown("#### Cost vs Sales Scatter Analysis")
    st.caption("Points below the diagonal have disproportionately high cost relative to sales.")
    fig = px.scatter(
        diag_source, x="Cost", y="Sales",
        color="Risk", color_discrete_map=risk_colors,
        size="Units", size_max=35,
        hover_name="Product Name",
        hover_data={"Gross Margin (%)": True, "Division": True, "Cost": True, "Sales": True, "Risk": False}
    )
    if not diag_source.empty:
        max_val = max(diag_source["Cost"].max(), diag_source["Sales"].max()) * 1.1
        fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                                 line=dict(dash="dash", color="#FFD700", width=1),
                                 name="Equal Cost-Sales line", showlegend=True))
    fig.update_layout(**CHART, height=400, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")

    # ── Margin Risk Flags — BUG 4 FIX: color driven by margin_threshold ──────
    st.markdown("#### Margin Risk Flags")
    st.caption(f"Products classified against the {margin_threshold}% threshold set in the sidebar.")
    sorted_diag = diag_source.sort_values("Gross Margin (%)")
    if not sorted_diag.empty:
        fig2 = go.Figure(go.Bar(
            x=sorted_diag["Gross Margin (%)"],
            y=sorted_diag["Product Name"].str.replace("Wonka Bar - ","WB ").str.replace("Wonka Bar -","WB "),
            orientation="h",
            marker_color=[risk_colors[r] for r in sorted_diag["Risk"]],
            text=sorted_diag["Gross Margin (%)"].map("{:.1f}%".format),
            textposition="outside"
        ))
        fig2.add_vline(x=margin_threshold, line_dash="dash", line_color="#f44336",
                       annotation_text=f"Risk threshold {margin_threshold}%")
        fig2.update_layout(**CHART, height=400, xaxis=dict(range=[0, 100]))
        st.plotly_chart(fig2, width="stretch")

    # ── Cost-Heavy / Margin-Poor — BUG 1 & 4 FIX ────────────────────────────
    st.markdown("#### Cost-Heavy, Margin-Poor Products")
    st.caption(f"Above-portfolio cost ratio AND margin below {margin_threshold}% threshold.")
    # BUG 1 FIX: cost ratio threshold from portfolio benchmark, not display subset
    cost_heavy = diag_source[
        (diag_source["Cost-to-Sales Ratio (%)"] > portfolio_avg_csr) &
        (diag_source["Gross Margin (%)"] < margin_threshold)
    ].sort_values("Cost-to-Sales Ratio (%)", ascending=False)

    if not cost_heavy.empty:
        names_ch = ", ".join(cost_heavy["Product Name"].tolist())
        st.error(f"🚨 **Cost-Heavy Products:** {names_ch} — cost ratio above portfolio average ({portfolio_avg_csr:.1f}%) and margin below {margin_threshold}%.")
    else:
        st.success(f"✅ No cost-heavy / margin-poor products at the current {margin_threshold}% threshold.")

    # ── Pricing Inefficiency — BUG 1 FIX: benchmark from portfolio ───────────
    st.markdown("#### Pricing Inefficiency Detection")
    st.caption(f"Products with Profit per Unit below portfolio average (${portfolio_avg_ppu:.2f}).")
    pricing_ineff = diag_source[diag_source["Profit per Unit"] < portfolio_avg_ppu].sort_values("Profit per Unit")
    if not pricing_ineff.empty:
        names_pi = ", ".join(pricing_ineff["Product Name"].tolist())
        st.warning(f"⚠️ Below-average Profit per Unit (benchmark: ${portfolio_avg_ppu:.2f}): {names_pi}.")
    else:
        st.success(f"✅ All displayed products meet or exceed the portfolio Profit per Unit of ${portfolio_avg_ppu:.2f}.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — PROFIT CONCENTRATION
# BUG 2 FIX: contribution denominators use GLOBAL totals
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("### Profit Concentration Analysis")
    st.caption("What percentage of products drive 80% of revenue and 80% of profit?")

    pareto_df = portfolio_df.copy().sort_values("Profit", ascending=False).reset_index(drop=True)
    pareto_df["Short"] = (pareto_df["Product Name"]
                          .str.replace("Wonka Bar - ","WB ").str.replace("Wonka Bar -","WB "))
    pareto_df["Cumulative Profit %"]  = (pareto_df["Profit"].cumsum() / pareto_df["Profit"].sum() * 100).round(1)
    pareto_df["Cumulative Revenue %"] = (pareto_df["Sales"].cumsum()  / pareto_df["Sales"].sum()  * 100).round(1)

    if pareto_df.empty:
        st.warning("No data available for concentration analysis.")
    else:
        profit_80_count  = max(1, int((pareto_df["Cumulative Profit %"]  <= 80).sum()) + 1)
        revenue_80_count = max(1, int((pareto_df["Cumulative Revenue %"] <= 80).sum()) + 1)
        total_products   = len(pareto_df)

        pk1, pk2, pk3, pk4 = st.columns(4)
        pk1.metric("Products for 80% Profit",  f"{profit_80_count} / {total_products}")
        pk2.metric("Products for 80% Revenue", f"{revenue_80_count} / {total_products}")
        pk3.metric("Profit Concentration",  f"{profit_80_count/total_products*100:.0f}% of products")
        pk4.metric("Revenue Concentration", f"{revenue_80_count/total_products*100:.0f}% of products")

        st.markdown("#### Profit Concentration — Pareto Chart")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=pareto_df["Short"], y=pareto_df["Profit"], name="Gross Profit ($)",
                              marker_color=[COLORS.get(d,"#888") for d in pareto_df["Division"]]), secondary_y=False)
        fig1.add_trace(go.Scatter(x=pareto_df["Short"], y=pareto_df["Cumulative Profit %"],
                                  name="Cumulative Profit %", mode="lines+markers",
                                  line=dict(color="#FFD700", width=2), marker=dict(size=6)), secondary_y=True)
        fig1.add_hline(y=80, line_dash="dash", line_color="white",
                       annotation_text="80% threshold", secondary_y=True)
        fig1.update_layout(**CHART, height=340, legend=dict(orientation="h", y=-0.3), xaxis=dict(tickangle=-25))
        fig1.update_yaxes(title_text="Gross Profit ($)", secondary_y=False)
        fig1.update_yaxes(title_text="Cumulative %", range=[0,110], secondary_y=True)
        st.plotly_chart(fig1, width="stretch")

        st.markdown("#### Revenue Concentration — Pareto Chart")
        pareto_rev = portfolio_df.copy().sort_values("Sales", ascending=False).reset_index(drop=True)
        pareto_rev["Short"] = (pareto_rev["Product Name"]
                               .str.replace("Wonka Bar - ","WB ").str.replace("Wonka Bar -","WB "))
        pareto_rev["Cumulative Revenue %"] = (pareto_rev["Sales"].cumsum() / pareto_rev["Sales"].sum() * 100).round(1)

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(x=pareto_rev["Short"], y=pareto_rev["Sales"], name="Revenue ($)",
                              marker_color=[COLORS.get(d,"#888") for d in pareto_rev["Division"]]), secondary_y=False)
        fig2.add_trace(go.Scatter(x=pareto_rev["Short"], y=pareto_rev["Cumulative Revenue %"],
                                  name="Cumulative Revenue %", mode="lines+markers",
                                  line=dict(color="#2196F3", width=2), marker=dict(size=6)), secondary_y=True)
        fig2.add_hline(y=80, line_dash="dash", line_color="white",
                       annotation_text="80% threshold", secondary_y=True)
        fig2.update_layout(**CHART, height=340, legend=dict(orientation="h", y=-0.3), xaxis=dict(tickangle=-25))
        fig2.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig2.update_yaxes(title_text="Cumulative %", range=[0,110], secondary_y=True)
        st.plotly_chart(fig2, width="stretch")

        st.markdown("#### Over-Dependency Risk Indicators")
        col1, col2 = st.columns(2)
        with col1:
            dep_level = "🚨 HIGH" if profit_80_count <= 3 else "⚠️ MODERATE" if profit_80_count <= 6 else "✅ LOW"
            top_profit_list = pareto_df.head(profit_80_count)
            st.markdown(f"""<div class="{'risk-card' if profit_80_count <= 3 else 'action-card'}">
            <strong>Profit Dependency: {dep_level}</strong><br><br>
            Top {profit_80_count} products = 80% of gross profit:<br>
            {"<br>".join([f"• <b>{r['Short']}</b> — {r['Profit Contribution (%)']:.1f}%" for _, r in top_profit_list.iterrows()])}
            </div>""", unsafe_allow_html=True)
        with col2:
            rev_level = "🚨 HIGH" if revenue_80_count <= 3 else "⚠️ MODERATE" if revenue_80_count <= 6 else "✅ LOW"
            top_rev_list = pareto_rev.head(revenue_80_count)
            top_rev_list = top_rev_list.copy()
            top_rev_list["Rev Contribution (%)"] = (top_rev_list["Sales"] / top_rev_list["Sales"].sum() * 100).round(1)
            st.markdown(f"""<div class="{'risk-card' if revenue_80_count <= 3 else 'action-card'}">
            <strong>Revenue Dependency: {rev_level}</strong><br><br>
            Top {revenue_80_count} products = 80% of revenue:<br>
            {"<br>".join([f"• <b>{r['Short']}</b>" for _, r in top_rev_list.iterrows()])}
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — PROFITABILITY TRENDS
# ─────────────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown("### Profitability Trends & Margin Volatility")
    st.caption("Are we getting more or less profitable over time?")

    if monthly_df.empty:
        st.warning("No trend data available for the selected filters.")
    else:
        st.markdown("#### Monthly Revenue and Profit Trend")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=monthly_df["Month"], y=monthly_df["Sales"],
                                 name="Monthly Revenue", mode="lines",
                                 line=dict(color="#2196F3", width=2),
                                 fill="tozeroy", fillcolor="rgba(33,150,243,0.08)"), secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly_df["Month"], y=monthly_df["Profit"],
                                 name="Monthly Gross Profit", mode="lines",
                                 line=dict(color="#4CAF50", width=2)), secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly_df["Month"], y=monthly_df["Margin (%)"],
                                 name="Gross Margin %", mode="lines",
                                 line=dict(color="#FFD700", width=1.5, dash="dot")), secondary_y=True)
        fig.update_layout(**CHART, height=380, legend=dict(orientation="h", y=-0.25), xaxis=dict(tickangle=-45))
        fig.update_yaxes(title_text="Amount ($)", secondary_y=False)
        fig.update_yaxes(title_text="Gross Margin (%)", secondary_y=True)
        st.plotly_chart(fig, width="stretch")

        st.markdown("#### Margin Volatility Metrics")
        margin_mean  = monthly_df["Margin (%)"].mean()
        margin_std   = monthly_df["Margin (%)"].std() if len(monthly_df) > 1 else 0
        margin_var   = monthly_df["Margin (%)"].var() if len(monthly_df) > 1 else 0
        margin_min   = monthly_df["Margin (%)"].min()
        margin_max   = monthly_df["Margin (%)"].max()
        margin_range = margin_max - margin_min
        cv           = (margin_std / margin_mean * 100) if margin_mean > 0 else 0

        v1, v2, v3, v4, v5 = st.columns(5)
        v1.metric("Avg Margin",          f"{margin_mean:.2f}%")
        v2.metric("Std Deviation",       f"{margin_std:.2f}%")
        v3.metric("Variance",            f"{margin_var:.3f}")
        v4.metric("Min → Max Range",     f"{margin_range:.2f}%", help=f"{margin_min:.1f}% to {margin_max:.1f}%")
        v5.metric("Coeff. of Variation", f"{cv:.2f}%", help="Std ÷ Mean × 100. Lower = more consistent.")

        st.markdown("#### Gross Margin Stability Over Time")
        fig2 = go.Figure()
        fig2.add_hrect(y0=margin_mean - margin_std, y1=margin_mean + margin_std,
                       fillcolor="rgba(255,215,0,0.07)", line_width=0,
                       annotation_text="±1 Std Dev", annotation_position="top left")
        fig2.add_trace(go.Scatter(x=monthly_df["Month"], y=monthly_df["Margin (%)"],
                                  mode="lines+markers", name="Gross Margin %",
                                  line=dict(color="#FFD700", width=2), marker=dict(size=5)))
        fig2.add_hline(y=margin_mean, line_dash="dash", line_color="#aaa",
                       annotation_text=f"Mean {margin_mean:.1f}%")
        fig2.update_layout(**CHART, height=280, xaxis=dict(tickangle=-45), yaxis=dict(title="Gross Margin (%)"))
        st.plotly_chart(fig2, width="stretch")

        if cv < 2:
            st.success(f"✅ **Low Volatility** — CV {cv:.2f}%. Gross margins are highly consistent month-to-month.")
        elif cv < 5:
            st.warning(f"⚠️ **Moderate Volatility** — CV {cv:.2f}%. Margins range {margin_min:.1f}%–{margin_max:.1f}%.")
        else:
            st.error(f"🚨 **High Volatility** — CV {cv:.2f}%. Investigate which products or divisions are driving margin swings.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='color:#555; font-size:11px; text-align:center;'>"
    "Nassau Candy Distributor &nbsp;·&nbsp; "
    "Analysis based on: Order Date · Division · Product Name · Sales · Cost · Units · Gross Profit"
    "</p>",
    unsafe_allow_html=True
)
