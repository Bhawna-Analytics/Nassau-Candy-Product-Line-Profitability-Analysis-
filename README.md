# 🍫 Nassau Candy — Product Line Profitability & Margin Performance Analysis

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=flat-square&logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=flat-square&logo=pandas)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?style=flat-square&logo=plotly)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen?style=flat-square)

> **Internship Project 2 — Unified Mentor Analytics Programme**
> A data-driven profitability study and interactive business intelligence dashboard for Nassau Candy Distributor, analysing product-line and division-level margin performance across 10,194 transaction records.

---

## 📌 Project Overview

For distributors like Nassau Candy, **sales volume alone is misleading**. Some products sell in high volume but generate low profit, consume disproportionate cost, or appear successful while quietly weakening overall margins.

This project moves beyond revenue reporting to deliver a rigorous, product-level profitability analysis that answers four core business questions:

- Which product lines deliver the **highest gross margin**?
- Are **high-revenue products** actually generating proportional profit?
- How does **profitability vary** across product divisions?
- Which products represent a **margin risk** to the business?

---

## 📁 Repository Structure

```
Nassau-Candy-Product-Line-Profitability-Analysis/
│
├── app.py                          # Streamlit dashboard — main application
├── Nassau_Candy_Distributor.csv    # Source dataset (10,194 transaction records)
├── Nassau_Candy_Requirements.docx  # Business analysis & requirements document
└── README.md                       # Project documentation
```

---

## 📊 Dataset

| Field | Description |
|-------|-------------|
| Order ID | Unique order identifier |
| Order Date | Date of order placement |
| Ship Date | Date of shipment |
| Ship Mode | Shipping method |
| Customer ID | Unique customer identifier |
| Country / Region | Customer location |
| Division | Product division — Chocolate, Sugar, Other |
| Region | Sales region — Pacific, Atlantic, Interior, Gulf |
| Product Name | Full product name (15 products) |
| Sales | Total revenue value of order |
| Units | Units sold per order |
| Gross Profit | Sales minus Cost |
| Cost | Product cost |

**Coverage:** January 2024 – December 2025 &nbsp;|&nbsp; **Records:** 10,194 &nbsp;|&nbsp; **Products:** 15 &nbsp;|&nbsp; **Divisions:** 3

---

## 🛠 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- pip

### Step 1 — Clone the repository
```bash
git clone https://github.com/Bhawna-Analytics/Nassau-Candy-Product-Line-Profitability-Analysis-.git
cd Nassau-Candy-Product-Line-Profitability-Analysis-
```

### Step 2 — Create a virtual environment (recommended)
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac / Linux
```

### Step 3 — Install dependencies
```bash
pip install streamlit pandas plotly
```

### Step 4 — Run the dashboard
```bash
streamlit run app.py
```

The dashboard will open automatically at **[https://business-profitability-dashboard.streamlit./](https://business-profitability-dashboard.streamlit./)**

---

## 📈 Dashboard Features

### Sidebar Controls
| Control | Purpose |
|---------|---------|
| 📅 Date Range Selector | Filter all analysis to a specific time window |
| 🏷 Division Filter | Isolate analysis to Chocolate, Sugar, or Other |
| ⚠️ Margin Risk Threshold | Dynamically controls ALL risk classifications across every tab |
| 🔍 Product Search | Filter displayed products by name (benchmarks always use full portfolio) |

### Dashboard Tabs

| Tab | Business Question Answered |
|-----|---------------------------|
| 🎯 Executive Summary | What does management need to know right now? |
| 📦 Product Profitability | Which products should we grow, fix, or cut? |
| 🏭 Division Performance | Which divisions need strategic attention? |
| 🔍 Cost & Margin Diagnostics | Where are cost structures inefficient? |
| 📊 Profit Concentration | What drives 80% of our revenue and profit? |
| 📈 Profitability Trends | Are we getting more or less profitable over time? |

---

## 🔢 KPI Framework

| KPI | Formula |
|-----|---------|
| Gross Margin (%) | Gross Profit ÷ Sales × 100 |
| Profit per Unit | Gross Profit ÷ Units |
| Revenue Contribution (%) | Product Sales ÷ **Global** Total Sales × 100 |
| Profit Contribution (%) | Product Profit ÷ **Global** Total Profit × 100 |
| Cost-to-Sales Ratio (%) | Cost ÷ Sales × 100 |
| Margin Std Deviation | Monthly margin spread |
| Coefficient of Variation | Std Dev ÷ Mean × 100 — normalised stability measure |

> **Note:** Revenue and Profit Contribution % are always calculated against **global company totals** — not filtered totals — ensuring accurate contribution percentages regardless of active filters.

---

## 🗂 Analytical Methodology

1. **Data Cleaning** — Removed missing values, zero-sales records, negative costs, and records failing the Gross Profit = Sales − Cost validation
2. **Label Standardisation** — Consistent title-casing across Division, Region, Product Name, Ship Mode
3. **KPI Engineering** — Gross Margin %, Profit per Unit, Revenue Contribution %, Profit Contribution %
4. **Product Segmentation** — Four strategic buckets: Stars, Drains, Discontinuation Candidates, Niche
5. **Division Analysis** — Revenue vs Profit comparison, margin benchmarking, contribution pie charts
6. **Cost Diagnostics** — Cost vs Sales scatter, cost-heavy product flagging, pricing inefficiency detection
7. **Pareto Analysis** — Separate 80/20 charts for both profit and revenue concentration
8. **Trend & Volatility** — Monthly trend tracking, standard deviation, variance, coefficient of variation

---

## 🐛 Key Bug Fixes Implemented

| Bug | Fix Applied |
|-----|-------------|
| Product search broke segmentation (products always classified as Stars) | Benchmarks computed from full portfolio, never from search subset |
| Division filter caused 100% contribution display | Contribution % divided by global totals, not filtered totals |
| Dashboard crashed on empty filter results (`IndexError`) | Empty dataframe guard clause added before all calculations |
| Margin threshold only moved a visual line | Threshold now drives ALL margin-based logic across every tab |

---

## 💻 Tech Stack

| Tool | Role |
|------|------|
| Python 3 | Core language |
| Pandas | Data cleaning, aggregation, KPI calculation |
| Plotly Express | Bar charts, scatter plots, pie charts |
| Plotly Graph Objects | Dual-axis charts, custom traces |
| Streamlit | Dashboard framework, sidebar controls, tabs |

---

## 📄 Deliverables

- ✅ `app.py` — Interactive Streamlit dashboard
- ✅ `Nassau_Candy_Requirements.docx` — Business analysis & requirements document
- ✅ Research Paper — Product Line Profitability & Margin Performance Analysis
- ✅ GitHub Repository — Version controlled project submission

---

## 👤 Author

**Bhawna Singh**
Unified Mentor Internship Programme — Business Analytics
📁 GitHub: [Bhawna-Analytics](https://github.com/Bhawna-Analytics)
