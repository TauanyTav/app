"""
pages/4_⚠️_VaR.py — VaR Histórico, Paramétrico, Monte Carlo, Full Valuation + ES
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    carregar_dados, calcular_retornos,
    var_historico, var_parametrico, var_monte_carlo, full_valuation_var,
    expected_shortfall, TICKERS_INFO, CARTEIRA, VALOR_CARTEIRA, TAXA_RF,
)
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="VaR & ES · Alpha Trading", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 12px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;text-transform:uppercase;
             letter-spacing:0.12em;color:#8888aa;">Mesa de Commodities</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#f5e6d0;">
            Banco Alpha<br>Trading</div>
    </div><hr/>
    """, unsafe_allow_html=True)
    usar_yf = st.toggle("📡 Dados reais (yfinance)", value=False)
    n_sim   = st.select_slider("Simulações Monte Carlo", [1000, 5000, 10000, 50000], value=10000)

@st.cache_data(ttl=600, show_spinner="Carregando dados…")
def get_dados(usar_yf):
    return carregar_dados(usar_yfinance=usar_yf)

df = get_dados(usar_yf)
ret = calcular_retornos(df)

# Retorno da carteira ponderado
pesos = np.array([0.25, 0.20, 0.25, 0.15, 0.05, 0.05, 0.05])
tickers = list(ret.columns)
n = min(len(pesos), len(tickers))
pw = pesos[:n] / pesos[:n].sum()
ret_port = ret[tickers[:n]].values @ pw

sigma_anual = ret_port.std() * np.sqrt(252)
mu_anual    = ret_port.mean() * 252
S_ref       = TICKERS_INFO["CL=F"]["preco_base"]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="editorial-header">
    <div class="editorial-sub">Módulos VII, VIII & IX · Risco de Mercado</div>
    <div class="editorial-title">VaR & Expected<br>Shortfall</div>
</div>
""", unsafe_allow_html=True)

# ── Calcular todos os VaRs ────────────────────────────────────────────────────
niveis = [0.95, 0.99, 0.995]
vh = var_historico(ret_port, VALOR_CARTEIRA, niveis)
vp = var_parametrico(ret_port, VALOR_CARTEIRA, niveis)
vm, pnl_mc = var_monte_carlo(S_ref, sigma_anual, mu_anual, VALOR_CARTEIRA, n_sim, niveis)

opcoes_carteira = [p for p in CARTEIRA if p["tipo"] in ["call", "put"]]
var_fv_99, pnl_fv = full_valuation_var(opcoes_carteira, VALOR_CARTEIRA, n_sim=min(n_sim, 10000))

es_95  = expected_shortfall(ret_port, VALOR_CARTEIRA, 0.95)
es_99  = expected_shortfall(ret_port, VALOR_CARTEIRA, 0.99)
es_995 = expected_shortfall(ret_port, VALOR_CARTEIRA, 0.995)

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)
kpis_var = [
    (col1, "VaR 99% Histórico",    vh["99.0%"],  PALETA["vermelho"]),
    (col2, "VaR 99% Paramétrico",  vp["99.0%"],  PALETA["cobre"]),
    (col3, "VaR 99% Monte Carlo",  vm["99.0%"],  PALETA["indigo"]),
    (col4, "Full Valuation VaR",   var_fv_99,    PALETA["lilas"]),
    (col5, "ES 99% (CVaR)",        es_99,        PALETA["vermelho"]),
    (col6, "ES/VaR Ratio",         es_99 / vh["99.0%"] if vh["99.0%"] > 0 else 1, PALETA["navy"]),
]
for col, label, val, cor in kpis_var:
    if label == "ES/VaR Ratio":
        fmt = f"{val:.2f}x"
    else:
        fmt = f"${val/1e6:.3f}M"
    col.markdown(f"""
    <div class="kpi-card" style="--accent:{cor};--val-color:{cor};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="font-size:1.3rem;">{fmt}</div>
        <div class="kpi-delta">carteira ${VALOR_CARTEIRA/1e6:.0f}M</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela Comparativa ────────────────────────────────────────────────────────
st.markdown("""
<div class="section-label">Comparação dos Métodos</div>
<div class="section-title">VaR por Nível de Confiança</div>
""", unsafe_allow_html=True)

df_var_table = pd.DataFrame({
    "Nível": ["95%", "99%", "99.5%"],
    "Histórico":    [f"${vh[f'{n*100:.1f}%']/1e6:.3f}M" for n in niveis],
    "Paramétrico":  [f"${vp[f'{n*100:.1f}%']/1e6:.3f}M" for n in niveis],
    "Monte Carlo":  [f"${vm[f'{n*100:.1f}%']/1e6:.3f}M" for n in niveis],
    "ES":           [f"${es/1e6:.3f}M" for es in [es_95, es_99, es_995]],
})
st.dataframe(df_var_table, use_container_width=True, hide_index=True)

# ── Gráficos ──────────────────────────────────────────────────────────────────
tab_v1, tab_v2, tab_v3 = st.tabs(["Distribuição P&L","Retornos Históricos","Full Valuation"])

with tab_v1:
    col_g1, col_g2 = st.columns(2, gap="large")

    with col_g1:
        fig_hist_dist = go.Figure()
        fig_hist_dist.add_trace(go.Histogram(
            x=ret_port * VALOR_CARTEIRA / 1e6,
            nbinsx=60, name="P&L Histórico",
            marker_color=PALETA["navy"], opacity=0.75,
        ))
        for nivel, cor_l in [(0.95, PALETA["cobre"]), (0.99, PALETA["vermelho"]), (0.995, PALETA["lilas"])]:
            v = vh[f"{nivel*100:.1f}%"]
            fig_hist_dist.add_vline(x=-v/1e6, line_dash="dash", line_color=cor_l, line_width=2,
                                     annotation_text=f"VaR {nivel*100:.0f}%",
                                     annotation_font_color=cor_l)
        layout_hd = plotly_tema(); layout_hd["height"] = 360
        fig_hist_dist.update_layout(**layout_hd,
                                     title="Distribuição P&L — VaR Histórico",
                                     xaxis_title="P&L (USD Milhões)", yaxis_title="Frequência")
        st.plotly_chart(fig_hist_dist, use_container_width=True)

    with col_g2:
        fig_mc_dist = go.Figure()
        fig_mc_dist.add_trace(go.Histogram(
            x=pnl_mc / 1e6, nbinsx=80, name="P&L Monte Carlo",
            marker_color=PALETA["indigo"], opacity=0.75,
        ))
        for nivel, cor_l in [(0.95, PALETA["cobre"]), (0.99, PALETA["vermelho"]), (0.995, PALETA["lilas"])]:
            v = vm[f"{nivel*100:.1f}%"]
            fig_mc_dist.add_vline(x=-v/1e6, line_dash="dash", line_color=cor_l, line_width=2,
                                   annotation_text=f"{nivel*100:.0f}%",
                                   annotation_font_color=cor_l)
        layout_mcd = plotly_tema(); layout_mcd["height"] = 360
        fig_mc_dist.update_layout(**layout_mcd,
                                   title=f"Distribuição Monte Carlo ({n_sim:,} cenários)",
                                   xaxis_title="P&L (USD Milhões)", yaxis_title="Frequência")
        st.plotly_chart(fig_mc_dist, use_container_width=True)

with tab_v2:
    fig_ret = go.Figure()
    pnl_hist = ret_port * VALOR_CARTEIRA
    fig_ret.add_trace(go.Bar(
        x=list(range(len(pnl_hist))), y=pnl_hist / 1e6,
        marker_color=[PALETA["verde"] if v >= 0 else PALETA["vermelho"] for v in pnl_hist],
        name="P&L Diário", showlegend=False,
    ))
    var99_line = vh["99.0%"] / 1e6
    fig_ret.add_hline(y=-var99_line, line_dash="dash", line_color=PALETA["cobre"],
                       annotation_text=f"−VaR 99%: ${var99_line:.3f}M",
                       annotation_font_color=PALETA["cobre"])
    layout_ret = plotly_tema(); layout_ret["height"] = 380
    fig_ret.update_layout(**layout_ret,
                           title="P&L Histórico Diário da Carteira",
                           xaxis_title="Dia", yaxis_title="P&L (USD Milhões)")
    st.plotly_chart(fig_ret, use_container_width=True)

with tab_v3:
    col_fv1, col_fv2 = st.columns(2, gap="large")
    with col_fv1:
        fig_fv = go.Figure()
        fig_fv.add_trace(go.Histogram(
            x=pnl_fv / 1e6, nbinsx=60,
            marker_color=PALETA["lilas"], opacity=0.8, name="Full Valuation P&L",
        ))
        fig_fv.add_vline(x=-var_fv_99/1e6, line_dash="dash", line_color=PALETA["vermelho"],
                          annotation_text=f"FV VaR 99%: ${var_fv_99/1e6:.3f}M",
                          annotation_font_color=PALETA["vermelho"])
        layout_fv = plotly_tema(); layout_fv["height"] = 360
        fig_fv.update_layout(**layout_fv,
                              title="Full Valuation VaR (Opções Reprecificadas)",
                              xaxis_title="P&L (USD M)", yaxis_title="Frequência")
        st.plotly_chart(fig_fv, use_container_width=True)

    with col_fv2:
        # Scatter: Full Valuation vs Delta-Normal por cenário
        np.random.seed(42)
        Z_sc = np.random.standard_normal(min(n_sim, 5000))
        pnl_delta_normal = (
            sum(
                p["direcao"] * p["qtd"] *
                TICKERS_INFO[p["ativo"]]["vol_base"] *
                TICKERS_INFO[p["ativo"]]["preco_base"] *
                (1/252)**0.5
                for p in opcoes_carteira
            ) * Z_sc
        )
        fig_scatter = go.Figure()
        n_pts = min(len(pnl_fv), len(pnl_delta_normal))
        fig_scatter.add_trace(go.Scatter(
            x=pnl_delta_normal[:n_pts] / 1e3,
            y=pnl_fv[:n_pts] / 1e3,
            mode="markers",
            marker=dict(color=PALETA["indigo"], size=3, opacity=0.4),
            name="Cenários",
        ))
        fig_scatter.add_shape(type="line", x0=-200, x1=200, y0=-200, y1=200,
                               line=dict(color=PALETA["cobre"], width=1.5, dash="dash"))
        layout_sc = plotly_tema(); layout_sc["height"] = 360
        fig_scatter.update_layout(**layout_sc,
                                   title="Full Valuation vs Delta-Normal (USD mil)",
                                   xaxis_title="Delta-Normal P&L", yaxis_title="Full Valuation P&L")
        st.plotly_chart(fig_scatter, use_container_width=True)

# ── Análise ES ────────────────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown("""
<div class="section-label">Expected Shortfall</div>
<div class="section-title">Comparação VaR × ES × Razão de Cauda</div>
""", unsafe_allow_html=True)

col_es1, col_es2 = st.columns([2, 3], gap="large")

with col_es1:
    niveis_plot = [95, 99, 99.5]
    vars_plot = [vh["95.0%"], vh["99.0%"], vh["99.5%"]]
    es_plot   = [es_95, es_99, es_995]
    excesso   = [e - v for e, v in zip(es_plot, vars_plot)]

    fig_es = go.Figure()
    fig_es.add_trace(go.Bar(
        name="VaR", x=[f"{n}%" for n in niveis_plot],
        y=[v/1e6 for v in vars_plot],
        marker_color=PALETA["indigo"],
    ))
    fig_es.add_trace(go.Bar(
        name="Excesso ES−VaR", x=[f"{n}%" for n in niveis_plot],
        y=[e/1e6 for e in excesso],
        marker_color=PALETA["vermelho"], opacity=0.75,
    ))
    layout_es = plotly_tema(); layout_es["height"] = 360
    fig_es.update_layout(**layout_es, barmode="stack",
                          title="VaR vs ES (Excesso Adicional)",
                          yaxis_title="USD Milhões")
    st.plotly_chart(fig_es, use_container_width=True)

with col_es2:
    st.markdown("""
    <div class="callout callout-risk" style="margin-top:20px;">
    <strong>Por que ES supera VaR na gestão de risco?</strong><br><br>
    O <strong>VaR α</strong> responde: "Qual é o pior P&L no percentil (1−α)?" Ele ignora o que acontece 
    nas caudas além desse ponto.<br><br>
    O <strong>ES α</strong> (também chamado CVaR) responde: "Dado que estamos além do VaR, qual é 
    a perda média?" É uma medida <em>coerente</em> — satisfaz sub-aditividade, o que significa que 
    diversificar nunca aumenta o risco segundo o ES.<br><br>
    Para carteiras com <strong>opções</strong>, as distribuições são assimétricas (skew negativo, 
    fat tails). O VaR paramétrico (que assume normalidade) subestima sistematicamente o risco. 
    O ES captura exatamente o que importa em crises.
    </div>
    <div class="callout callout-warn" style="margin-top:12px;">
    <strong>Full Valuation vs Delta-Normal:</strong> O Delta-Normal usa apenas a sensibilidade linear 
    (Delta) para projetar perdas. O Full Valuation reprecifica cada opção em cada cenário — capturando 
    a <em>convexidade</em> (Gamma). A diferença é especialmente grande para posições vendidas em opções 
    com Gamma negativo, onde as perdas crescem de forma acelerada.
    </div>
    """, unsafe_allow_html=True)
