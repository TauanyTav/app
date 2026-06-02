"""
theme.py — Tema editorial/luz compartilhado entre todas as páginas.
Estilo: papel branco + acentos índigo/cobre + tipografia editorial bold.
"""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset geral ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #fafaf8;
    color: #1a1a2e;
}
.stApp { background: #fafaf8; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1a1a2e;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #252540;
    border: 1px solid #3a3a60;
    color: #e8e8f0;
}
[data-testid="stSidebar"] label { color: #8888aa !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stSidebar"] .stSlider > div { padding: 0; }
[data-testid="stSidebar"] hr { border-color: #2a2a50; }

/* ── Cabeçalho editorial ── */
.editorial-header {
    border-bottom: 3px solid #1a1a2e;
    padding-bottom: 16px;
    margin-bottom: 32px;
}
.editorial-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 900;
    color: #1a1a2e;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.editorial-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #8888a0;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 6px;
}
.editorial-accent {
    display: inline-block;
    background: #1a1a2e;
    color: #f5e6d0;
    padding: 2px 10px;
    border-radius: 3px;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── Cards de KPI ── */
.kpi-grid { display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: white;
    border: 1.5px solid #e8e8ec;
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #1a1a2e);
}
.kpi-card:hover { box-shadow: 0 4px 20px rgba(26,26,46,0.1); }
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8888a0;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--val-color, #1a1a2e);
    line-height: 1;
}
.kpi-delta {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    margin-top: 4px;
    color: #8888a0;
}

/* ── Cards de seção ── */
.section-card {
    background: white;
    border: 1.5px solid #e8e8ec;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 12px 0;
}
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #c8925a;
    margin-bottom: 4px;
}
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #1a1a2e;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.06em;
    font-weight: 500;
    text-transform: uppercase;
}
.badge-blue   { background: #e8eeff; color: #2d4ec0; }
.badge-green  { background: #e6f7ed; color: #1a7a40; }
.badge-red    { background: #fde8e8; color: #c02d2d; }
.badge-amber  { background: #fef3e2; color: #b56a0a; }
.badge-dark   { background: #1a1a2e; color: #f5e6d0; }

/* ── Callouts ── */
.callout {
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 0.85rem;
    line-height: 1.6;
}
.callout-info  { background: #f0f3ff; border-left: 4px solid #4a6cf7; color: #2a3a8a; }
.callout-warn  { background: #fffbf0; border-left: 4px solid #f59e0b; color: #7a4a0a; }
.callout-risk  { background: #fff0f0; border-left: 4px solid #ef4444; color: #7a1a1a; }
.callout-ok    { background: #f0fff5; border-left: 4px solid #22c55e; color: #0a4a20; }

/* ── Dividers ── */
.divider-heavy {
    border: none;
    border-top: 2px solid #1a1a2e;
    margin: 20px 0;
}
.divider-light {
    border: none;
    border-top: 1px solid #e8e8ec;
    margin: 16px 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid #e8e8ec;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #8888a0;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 10px 20px;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #1a1a2e !important;
    border-bottom: 2px solid #1a1a2e !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #1a1a2e;
    color: #f5e6d0;
    border: none;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.83rem;
    padding: 8px 22px;
    transition: all 0.2s;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    background: #2d2d60;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26,26,46,0.2);
}

/* ── DataFrames ── */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
    border: 1.5px solid #e8e8ec !important;
}

/* ── Métricas nativas ── */
[data-testid="stMetric"] {
    background: white;
    border: 1.5px solid #e8e8ec;
    border-radius: 10px;
    padding: 16px 18px;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8888a0 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.6rem !important;
    color: #1a1a2e !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: white !important;
    border: 1.5px solid #e8e8ec !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    color: #1a1a2e !important;
}

/* ── Formulários ── */
.stSlider > div > div > div { background: #4a6cf7; }
.stSelectbox > div > div {
    background: white;
    border: 1.5px solid #e8e8ec;
    border-radius: 8px;
}
</style>
"""


def plotly_tema():
    """Retorna dict com layout base para todos os gráficos Plotly."""
    return dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e", size=12),
        xaxis=dict(gridcolor="#f0f0f4", linecolor="#e8e8ec", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#f0f0f4", linecolor="#e8e8ec", tickfont=dict(size=11)),
        legend=dict(bgcolor="white", bordercolor="#e8e8ec", borderwidth=1),
        margin=dict(l=0, r=0, t=36, b=0),
        colorway=["#1a1a2e", "#4a6cf7", "#c8925a", "#22c55e", "#ef4444", "#8b5cf6", "#0ea5e9"],
    )


PALETA = {
    "navy":    "#1a1a2e",
    "indigo":  "#4a6cf7",
    "cobre":   "#c8925a",
    "verde":   "#22c55e",
    "vermelho":"#ef4444",
    "lilas":   "#8b5cf6",
    "ceu":     "#0ea5e9",
    "papel":   "#fafaf8",
    "creme":   "#f5e6d0",
    "cinza":   "#8888a0",
    "borda":   "#e8e8ec",
}
