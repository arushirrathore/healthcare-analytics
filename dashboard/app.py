"""Hospital Operations & Readmission Risk — premium minimal dashboard.

Design principles:
- One accent colour (muted gold) on a deep slate canvas; data carries the colour.
- No chart junk: no gridwalls, no borders, no redundant legends.
- KPI cards rendered as custom HTML for a refined, product-grade feel.

Run from the project root:
    python -m streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.clean_data import clean  # noqa: E402

st.set_page_config(page_title="Hospital Analytics", page_icon="\U0001f3e5",
                   layout="wide")

# ------------------------------------------------------------- palette
GOLD = "#C9A96A"
TEAL = "#4FD1C5"
TEXT = "#E8ECF1"
MUTED = "#8A94A6"
SEQ = [GOLD, TEAL, "#7C9CF5", "#E89B9B", "#A78BFA", "#E8B05C", "#5C6B82"]
HEAT = [[0.0, "#141A22"], [0.5, "#6E5F3C"], [1.0, GOLD]]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="st-"], h1, h2, h3 { font-family: 'Inter', sans-serif; }
.stApp { background: #0B0F14; }
section[data-testid="stSidebar"] {
  background: #10151C; border-right: 1px solid rgba(255,255,255,0.06);
}
h1 { font-weight: 700; letter-spacing: -0.5px; font-size: 1.55rem !important; }
.block-container { padding-top: 2.2rem; }
.kpi-card {
  background: linear-gradient(160deg, #161D26 0%, #10151C 100%);
  border: 1px solid rgba(201,169,106,0.18);
  border-radius: 14px; padding: 18px 22px;
}
.kpi-label { color: #8A94A6; font-size: 0.70rem; text-transform: uppercase;
             letter-spacing: 1.6px; margin-bottom: 6px; }
.kpi-value { color: #E8ECF1; font-size: 1.85rem; font-weight: 700;
             line-height: 1.1; }
.kpi-sub { color: #C9A96A; font-size: 0.76rem; margin-top: 6px; }
.subtitle { color: #8A94A6; font-size: 0.85rem; margin-top: -10px; }
hr { border-color: rgba(255,255,255,0.06); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data
@st.cache_data
def load_data() -> pd.DataFrame:
    """Prefer the processed dataset; fall back to cleaning raw on the fly."""
    processed = ROOT / "data/processed/hospital_admissions_clean.csv"
    raw = ROOT / "data/raw/hospital_admissions.csv"
    if processed.exists():
        df = pd.read_csv(processed, parse_dates=["admission_date"])
    elif raw.exists():
        df = clean(pd.read_csv(raw))
    else:
        st.error("No data found. Run `python scripts/generate_data.py` first.")
        st.stop()
    df["admission_month"] = df["admission_date"].dt.to_period("M").astype(str)
    return df


def styled(fig, title: str, height: int = 330):
    """Apply the shared minimal chart style (one place, every chart)."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT), x=0.01),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=MUTED, size=12),
        margin=dict(l=8, r=8, t=46, b=8), height=height,
        colorway=SEQ, showlegend=fig.layout.showlegend,
        legend=dict(orientation="h", y=-0.22, title=None),
        coloraxis_showscale=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, title=None)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False,
                     title=None)
    return fig


def kpi(col, label: str, value: str, sub: str) -> None:
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)


df = load_data()

# ------------------------------------------------------------- sidebar
st.sidebar.markdown("## \U0001f3e5 Hospital Analytics")
st.sidebar.caption("Patient Flow & 30-Day Readmission Risk")
st.sidebar.markdown("---")

depts = st.sidebar.multiselect("Department",
                               sorted(df["department"].unique()),
                               default=sorted(df["department"].unique()))
min_d, max_d = df["admission_date"].min(), df["admission_date"].max()
date_range = st.sidebar.date_input("Admission date range", (min_d, max_d),
                                   min_value=min_d, max_value=max_d)

mask = df["department"].isin(depts)
if len(date_range) == 2:
    mask &= df["admission_date"].between(pd.Timestamp(date_range[0]),
                                         pd.Timestamp(date_range[1]))
view = df[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(view):,} records in view")

if view.empty:
    st.warning("No records match the current filters.")
    st.stop()

# -------------------------------------------------------------- header
st.title("Hospital Operations & Readmission Risk")
st.markdown('<p class="subtitle">Jan 2023 – May 2025 · '
            'synthetic mid-size hospital dataset</p>', unsafe_allow_html=True)
st.markdown("")

# ---------------------------------------------------------------- KPIs
hosp_readmit = df["readmitted_30d"].mean() * 100
view_readmit = view["readmitted_30d"].mean() * 100
delta = view_readmit - hosp_readmit

c1, c2, c3, c4 = st.columns(4, gap="medium")
kpi(c1, "Avg wait time", f"{view['wait_time_minutes'].mean():.0f} min",
    f"p90 · {view['wait_time_minutes'].quantile(0.9):.0f} min")
kpi(c2, "30-day readmission", f"{view_readmit:.1f}%",
    f"{delta:+.1f} pts vs hospital avg")
kpi(c3, "Avg length of stay", f"{view['length_of_stay_days'].mean():.1f} days",
    f"{view['length_of_stay_days'].sum():,.0f} total bed-days")
kpi(c4, "Avg treatment cost", f"${view['treatment_cost'].mean():,.0f}",
    f"${view['treatment_cost'].sum() / 1e6:.1f}M total spend")

st.markdown("---")

# ----------------------------------------------------------------- row 1
r1a, r1b = st.columns((3, 2), gap="medium")

with r1a:
    monthly = view.groupby("admission_month").size().reset_index(name="n")
    fig = px.area(monthly, x="admission_month", y="n")
    fig.update_traces(line=dict(color=GOLD, width=2.2),
                      fillcolor="rgba(201,169,106,0.12)")
    st.plotly_chart(styled(fig, "Monthly admissions · winter surge Dec–Feb"),
                    use_container_width=True)

with r1b:
    by_dept = (view.groupby("department")["readmitted_30d"].mean() * 100) \
        .sort_values().reset_index(name="rate")
    fig = px.bar(by_dept, x="rate", y="department", orientation="h")
    fig.update_traces(marker_color=GOLD, marker_line_width=0)
    fig.add_vline(x=hosp_readmit, line_dash="dot", line_color=MUTED,
                  annotation_text="hospital avg",
                  annotation_font_color=MUTED)
    st.plotly_chart(styled(fig, "Readmission rate by department (%)"),
                    use_container_width=True)

# ----------------------------------------------------------------- row 2
r2a, r2b = st.columns(2, gap="medium")

with r2a:
    pivot = view.pivot_table(index="department", columns="age_group",
                             values="readmitted_30d", aggfunc="mean",
                             observed=True) * 100
    fig = px.imshow(pivot.round(0), text_auto=True, aspect="auto",
                    color_continuous_scale=HEAT)
    fig.update_traces(textfont=dict(size=11))
    st.plotly_chart(styled(fig, "Readmission risk · department × age group (%)"),
                    use_container_width=True)

with r2b:
    waits = view.groupby("department")["wait_time_minutes"] \
        .agg(avg="mean", p90=lambda s: s.quantile(0.9)) \
        .sort_values("avg").reset_index()
    fig = px.bar(waits.melt(id_vars="department", var_name="metric",
                            value_name="minutes"),
                 y="department", x="minutes", color="metric",
                 orientation="h", barmode="group",
                 color_discrete_map={"avg": GOLD, "p90": TEAL})
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=True)
    st.plotly_chart(styled(fig, "Wait time · average vs 90th percentile (min)"),
                    use_container_width=True)

# ----------------------------------------------------------------- row 3
r3a, r3b = st.columns(2, gap="medium")

with r3a:
    fig = px.histogram(view, x="length_of_stay_days", nbins=40)
    fig.update_traces(marker_color=TEAL, marker_line_width=0, opacity=0.85)
    st.plotly_chart(styled(fig, "Length-of-stay distribution (days)"),
                    use_container_width=True)

with r3b:
    cost = view.groupby("insurance_type")["treatment_cost"].sum().reset_index()
    fig = px.pie(cost, names="insurance_type", values="treatment_cost",
                 hole=0.62)
    fig.update_traces(marker=dict(colors=SEQ,
                                  line=dict(color="#0B0F14", width=2)),
                      textfont=dict(size=12))
    fig.update_layout(showlegend=True)
    st.plotly_chart(styled(fig, "Revenue mix by insurance type"),
                    use_container_width=True)
