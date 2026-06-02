"""
🏠_Inicio.py — Página principal do aplicativo Alpha Trading.
Dashboard editorial com visão geral da carteira.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    carregar_dados, calcular_retornos, vol_historica_anual,
    TICKERS_INFO, CARTEIRA, VALOR_CARTEIRA, TAXA_RF,
    var_historico, expected_shortfall,
)
from theme import THEME_CSS, plotly_tema, PALETA

# ── Configuração ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alpha Trading · Commodities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(THEME_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 12px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
             text-transform:uppercase;letter-spacing:0.12em;color:#8888aa;margin-bottom:6px;">
            Mesa de Commodities
        </div>
        <div style="font-family:'Playfair Display',serif;font-size:1.4rem;
             font-weight:900;color:#f5e6d0;line-height:1.1;">
            Banco Alpha<br>Trading
        </div>
    </div>
    <hr/>
    """, unsafe_allow_html=True)

    usar_yf = st.toggle("📡 Dados reais (yfinance)", value=False,
                         help="Ativa download real. Pode falhar se yfinance não estiver instalado.")
    taxa_rf = st.slider("Taxa Livre de Risco (%)", 1.0, 15.0, 5.25, 0.25) / 100
    janela  = st.slider("Janela Vol. Histórica (dias)", 10, 60, 21)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.68rem;color:#5555aa;line-height:1.7;">
        FGV EAESP · 2026<br>
        Prof. João Luiz Chela<br>
        Modelagem Aplicada ao<br>Mercado Financeiro
    </div>
    """, unsafe_allow_html=True)

# ── Dados ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner="Carregando dados…")
def get_dados(usar_yf):
    return carregar_dados(usar_yfinance=usar_yf)

df = get_dados(usar_yf)
ret = calcular_retornos(df)

# ── Header editorial ─────────────────────────────────────────────────────────
st.markdown("""
<div class="editorial-header">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
            <div class="editorial-sub">Banco Alpha Trading · Mesa de Commodities</div>
            <div class="editorial-title">Dashboard<br>de Risco</div>
        </div>
        <div style="text-align:right;padding-top:8px;">
            <span class="editorial-accent">FGV EAESP 2026</span><br>
            <span style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#8888a0;margin-top:6px;display:block;">
                Prof. João Luiz Chela
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
pesos = np.array([0.25, 0.20, 0.25, 0.15, 0.05, 0.05, 0.05])
tickers = list(ret.columns)
n = min(len(pesos), len(tickers))
pw = pesos[:n] / pesos[:n].sum()
ret_port = ret[tickers[:n]].values @ pw

vol_port  = ret_port.std() * np.sqrt(252)
ret_anual = ret_port.mean() * 252
var99     = -np.percentile(ret_port, 1) * VALOR_CARTEIRA
es99      = expected_shortfall(ret_port, VALOR_CARTEIRA, 0.99)
sharpe    = (ret_anual - taxa_rf) / vol_port

col1, col2, col3, col4, col5, col6 = st.columns(6)
kpis = [
    (col1, "Ativos", "7", "#1a1a2e", "#1a1a2e", "commodities + ETFs"),
    (col2, "Vol. Carteira", f"{vol_port*100:.1f}%", "#c8925a", "#c8925a", "anualizada"),
    (col3, "Retorno Anual", f"{ret_anual*100:.1f}%", "#22c55e" if ret_anual > 0 else "#ef4444",
     "#22c55e" if ret_anual > 0 else "#ef4444", "média histórica"),
    (col4, "VaR 99% (1d)", f"${var99/1e6:.2f}M", "#ef4444", "#ef4444", "histórico"),
    (col5, "ES 99%", f"${es99/1e6:.2f}M", "#ef4444", "#ef4444", "cauda esperada"),
    (col6, "Sharpe", f"{sharpe:.2f}", "#4a6cf7", "#4a6cf7", "carteira"),
]
for col, label, val, accent, vc, delta in kpis:
    col.markdown(f"""
    <div class="kpi-card" style="--accent:{accent};--val-color:{vc};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val}</div>
        <div class="kpi-delta">{delta}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gráficos principais ───────────────────────────────────────────────────────
col_g1, col_g2 = st.columns([3, 2], gap="large")

with col_g1:
    st.markdown("""
    <div class="section-label">Evolução de Preços</div>
    <div class="section-title">Série Histórica Normalizada (base 100)</div>
    """, unsafe_allow_html=True)

    df_norm = (df / df.iloc[0] * 100)
    fig_precos = go.Figure()
    cores_seq = [PALETA["navy"], PALETA["indigo"], PALETA["cobre"],
                 PALETA["verde"], PALETA["vermelho"], PALETA["lilas"], PALETA["ceu"]]
    for i, col_t in enumerate(df_norm.columns):
        info = TICKERS_INFO[col_t]
        fig_precos.add_trace(go.Scatter(
            x=df_norm.index, y=df_norm[col_t],
            name=f"{info['emoji']} {info['nome']}",
            line=dict(color=cores_seq[i % len(cores_seq)], width=1.8),
            hovertemplate=f"<b>{info['nome']}</b><br>%{{x|%d/%m/%Y}}: %{{y:.1f}}<extra></extra>",
        ))
    base = plotly_tema()
    base.update(height=360)
    fig_precos.update_layout(**base)
    fig_precos.update_xaxes(showgrid=True)
    fig_precos.update_yaxes(showgrid=True)
    st.plotly_chart(fig_precos, use_container_width=True)

with col_g2:
    st.markdown("""
    <div class="section-label">Risco</div>
    <div class="section-title">Volatilidade Histórica Anualizada</div>
    """, unsafe_allow_html=True)

    vols_dict = {
        TICKERS_INFO[t]["nome"]: vol_historica_anual(ret[t]) * 100
        for t in tickers if t in ret.columns
    }
    nomes_v = list(vols_dict.keys())
    vals_v  = list(vols_dict.values())
    cores_v = [PALETA["vermelho"] if v > 40 else PALETA["cobre"] if v > 25 else PALETA["verde"] for v in vals_v]

    fig_vol = go.Figure(go.Bar(
        x=vals_v, y=nomes_v, orientation="h",
        marker_color=cores_v,
        text=[f"{v:.1f}%" for v in vals_v],
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=11),
    ))
    base2 = plotly_tema()
    base2.update(height=360, showlegend=False)
    fig_vol.update_layout(**base2)
    fig_vol.update_xaxes(ticksuffix="%", showgrid=True)
    fig_vol.update_yaxes(showgrid=False)
    st.plotly_chart(fig_vol, use_container_width=True)

# ── Correlação ────────────────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
col_c1, col_c2 = st.columns([2, 3], gap="large")

with col_c1:
    st.markdown("""
    <div class="section-label">Carteira</div>
    <div class="section-title">Posições da Mesa</div>
    """, unsafe_allow_html=True)

    rotulos = {+1: "Comprado", -1: "Vendido"}
    rows_cart = []
    for p in CARTEIRA:
        info = TICKERS_INFO[p["ativo"]]
        rows_cart.append({
            "": f"{info['emoji']} {p['ativo']}",
            "Instrumento": p["tipo"].replace("call","Call").replace("put","Put").replace("futuro","Futuro"),
            "Direção": rotulos[p["direcao"]],
            "Venc.": f"{p['venc_dias']}d",
            "Qtd": f"{p['qtd']:,}",
        })
    df_cart = pd.DataFrame(rows_cart)
    st.dataframe(df_cart, use_container_width=True, hide_index=True, height=280)

with col_c2:
    st.markdown("""
    <div class="section-label">Estrutura de Risco</div>
    <div class="section-title">Matriz de Correlação dos Retornos</div>
    """, unsafe_allow_html=True)

    nomes_curtos = {t: TICKERS_INFO[t]["nome"][:10] for t in tickers}
    corr_m = ret.rename(columns=nomes_curtos).corr()
    fig_corr = px.imshow(
        corr_m, text_auto=".2f",
        color_continuous_scale=[[0,"#ef4444"],[0.5,"white"],[1,"#1a1a2e"]],
        zmin=-1, zmax=1,
    )
    base3 = plotly_tema()
    base3.update(height=320)
    fig_corr.update_layout(**base3)
    fig_corr.update_traces(textfont=dict(size=10))
    st.plotly_chart(fig_corr, use_container_width=True)

# ── Volatilidade Rolante ──────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown("""
<div class="section-label">Dinâmica de Risco</div>
<div class="section-title">Volatilidade Realizada Rolante — Todos os Ativos</div>
""", unsafe_allow_html=True)

fig_vr = go.Figure()
for i, col_t in enumerate(tickers[:6]):
    vr = ret[col_t].rolling(janela).std() * np.sqrt(252) * 100
    info = TICKERS_INFO[col_t]
    fig_vr.add_trace(go.Scatter(
        x=vr.index, y=vr.values,
        name=f"{info['emoji']} {info['nome']}",
        line=dict(color=cores_seq[i], width=1.5),
    ))
base4 = plotly_tema()
base4.update(height=280)
base4["yaxis"]["ticksuffix"] = "%"
fig_vr.update_layout(**base4, title=f"Janela {janela} dias")
st.plotly_chart(fig_vr, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="border-top:1.5px solid #e8e8ec;padding-top:14px;
     font-family:'DM Mono',monospace;font-size:0.65rem;color:#bbbbcc;
     display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
    <span>Banco Alpha Trading · Mesa de Commodities</span>
    <span>FGV EAESP 2026 · Prof. João Luiz Chela · Modelagem Aplicada ao Mercado Financeiro</span>
</div>
""", unsafe_allow_html=True)
