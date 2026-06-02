"""
pages/5_🔁_Backtesting.py — Backtesting do VaR com janela móvel + Teste de Kupiec
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    carregar_dados, calcular_retornos, backtest_var, kupiec,
    VALOR_CARTEIRA,
)
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="Backtesting · Alpha Trading", layout="wide")
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
    usar_yf  = st.toggle("📡 Dados reais (yfinance)", value=False)
    nivel_bt = st.select_slider("Nível de Confiança", [0.95, 0.99, 0.995], value=0.99)
    janela   = st.slider("Janela Rolling (dias)", 60, 500, 250, 10)

@st.cache_data(ttl=600, show_spinner="Carregando dados…")
def get_dados(usar_yf):
    return carregar_dados(usar_yfinance=usar_yf)

df = get_dados(usar_yf)
ret = calcular_retornos(df)

pesos = np.array([0.25, 0.20, 0.25, 0.15, 0.05, 0.05, 0.05])
tickers = list(ret.columns)
n = min(len(pesos), len(tickers))
pw = pesos[:n] / pesos[:n].sum()
ret_port = ret[tickers[:n]].values @ pw

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="editorial-header">
    <div class="editorial-sub">Módulo X · Validação do Modelo</div>
    <div class="editorial-title">Backtesting<br>& Teste de Kupiec</div>
</div>
""", unsafe_allow_html=True)

# ── Backtesting ───────────────────────────────────────────────────────────────
vars_bt, violacoes = backtest_var(ret_port, VALOR_CARTEIRA, nivel_bt, janela)
datas_bt = ret.index[janela:]
pnl_obs  = ret_port[janela:] * VALOR_CARTEIRA
n_viols  = int(violacoes.sum())
T_bt     = len(violacoes)
p_esp    = 1 - nivel_bt
LR, p_val = kupiec(n_viols, T_bt, p_esp)
taxa_viol = n_viols / T_bt if T_bt > 0 else 0
aprovado  = p_val > 0.05

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
kpis_bt = [
    (col1, "Observações",       f"{T_bt:,}",                      PALETA["navy"]),
    (col2, "Violações Obs.",    f"{n_viols}",                     PALETA["vermelho"] if taxa_viol > p_esp * 1.5 else PALETA["verde"]),
    (col3, "Taxa Observada",    f"{taxa_viol*100:.2f}%",          PALETA["vermelho"] if taxa_viol > p_esp * 1.5 else PALETA["cobre"]),
    (col4, "Kupiec LR Stat",    f"{LR:.3f}",                      PALETA["indigo"]),
    (col5, "Resultado",         "APROVADO" if aprovado else "REPROVADO",
     PALETA["verde"] if aprovado else PALETA["vermelho"]),
]
for col, label, val, cor in kpis_bt:
    col.markdown(f"""
    <div class="kpi-card" style="--accent:{cor};--val-color:{cor};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="font-size:1.3rem;">{val}</div>
        <div class="kpi-delta">nível {nivel_bt*100:.0f}% | p = {p_val:.4f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gráfico principal ─────────────────────────────────────────────────────────
fig_bt = go.Figure()

# Área P&L
fig_bt.add_trace(go.Scatter(
    x=datas_bt, y=pnl_obs / 1e6,
    name="P&L Observado", mode="lines",
    line=dict(color=PALETA["navy"], width=1.2),
    fill="tozeroy",
    fillcolor="rgba(26,26,46,0.06)",
))

# VaR rolling
fig_bt.add_trace(go.Scatter(
    x=datas_bt, y=-vars_bt / 1e6,
    name=f"−VaR {nivel_bt*100:.0f}%", mode="lines",
    line=dict(color=PALETA["cobre"], width=2, dash="dot"),
))

# Upper bound espelho
fig_bt.add_trace(go.Scatter(
    x=datas_bt, y=vars_bt / 1e6,
    name=f"+VaR {nivel_bt*100:.0f}%", mode="lines",
    line=dict(color=PALETA["borda"], width=1, dash="dot"),
    showlegend=False,
))

# Violações
idx_viols = np.where(violacoes == 1)[0]
if len(idx_viols) > 0:
    datas_viol = [datas_bt[i] for i in idx_viols if i < len(datas_bt)]
    pnl_viol   = [pnl_obs[i] / 1e6 for i in idx_viols if i < len(pnl_obs)]
    fig_bt.add_trace(go.Scatter(
        x=datas_viol, y=pnl_viol,
        mode="markers", name=f"Violações ({n_viols})",
        marker=dict(color=PALETA["vermelho"], size=9, symbol="x",
                    line=dict(color=PALETA["vermelho"], width=2)),
    ))

layout_bt = plotly_tema(); layout_bt["height"] = 440
fig_bt.update_layout(**layout_bt,
                      title=f"VaR {nivel_bt*100:.0f}% — Janela Móvel {janela} Dias",
                      xaxis_title="Data", yaxis_title="P&L (USD Milhões)",
                      legend=dict(orientation="h", y=1.02))
st.plotly_chart(fig_bt, use_container_width=True)

# ── Painel Kupiec ─────────────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
col_k1, col_k2 = st.columns([3, 2], gap="large")

with col_k1:
    st.markdown("""
    <div class="section-label">Comparação Multi-Nível</div>
    <div class="section-title">Kupiec para Diferentes Níveis de Confiança</div>
    """, unsafe_allow_html=True)

    rows_kup = []
    for nv in [0.90, 0.95, 0.99, 0.995]:
        vbt, viol = backtest_var(ret_port, VALOR_CARTEIRA, nv, janela)
        nv_ = int(viol.sum())
        T_  = len(viol)
        lr, pv = kupiec(nv_, T_, 1 - nv)
        rows_kup.append({
            "Nível": f"{nv*100:.1f}%",
            "Viols Esp.": f"{T_*(1-nv):.1f}",
            "Viols Obs.": nv_,
            "Taxa Obs.":  f"{nv_/T_*100:.2f}%",
            "LR Stat":    f"{lr:.4f}",
            "p-valor":    f"{pv:.4f}",
            "Resultado":  "✓ Aprovado" if pv > 0.05 else "✗ Reprovado",
        })
    df_kup = pd.DataFrame(rows_kup)
    st.dataframe(df_kup, use_container_width=True, hide_index=True)

    # Gráfico de violações acumuladas
    fig_viols_cum = go.Figure()
    viols_cum = np.cumsum(violacoes)
    esp_cum   = np.arange(1, len(violacoes) + 1) * p_esp
    fig_viols_cum.add_trace(go.Scatter(
        x=list(range(len(viols_cum))), y=viols_cum,
        name="Violações Acumuladas", line=dict(color=PALETA["vermelho"], width=2),
    ))
    fig_viols_cum.add_trace(go.Scatter(
        x=list(range(len(esp_cum))), y=esp_cum,
        name="Esperado", line=dict(color=PALETA["navy"], width=1.5, dash="dash"),
    ))
    layout_vc = plotly_tema(); layout_vc["height"] = 300
    fig_viols_cum.update_layout(**layout_vc,
                                 title="Violações Acumuladas vs Esperado",
                                 xaxis_title="Dias", yaxis_title="# Violações")
    st.plotly_chart(fig_viols_cum, use_container_width=True)

with col_k2:
    # Histograma dos retornos com threshold VaR
    fig_tail = go.Figure()
    fig_tail.add_trace(go.Histogram(
        x=ret_port * 100, nbinsx=60,
        marker_color=PALETA["navy"], opacity=0.7, name="Retornos (%)",
    ))
    var_pct = np.percentile(ret_port, (1 - nivel_bt) * 100) * 100
    fig_tail.add_vline(x=var_pct, line_dash="dash", line_color=PALETA["vermelho"],
                        line_width=2,
                        annotation_text=f"VaR {nivel_bt*100:.0f}%<br>{var_pct:.3f}%",
                        annotation_font_color=PALETA["vermelho"])
    # Destacar cauda
    bins_cauda = np.array(ret_port[ret_port < var_pct/100]) * 100
    if len(bins_cauda) > 0:
        fig_tail.add_trace(go.Histogram(
            x=bins_cauda, nbinsx=20,
            marker_color=PALETA["vermelho"], opacity=0.8, name="Cauda",
        ))
    layout_tail = plotly_tema(); layout_tail["height"] = 350
    fig_tail.update_layout(**layout_tail, barmode="overlay",
                            title="Distribuição dos Retornos — Cauda em Destaque",
                            xaxis_title="Retorno Diário (%)", yaxis_title="Frequência")
    st.plotly_chart(fig_tail, use_container_width=True)

    # Interpretação
    st.markdown(f"""
    <div class="callout {'callout-ok' if aprovado else 'callout-risk'}" style="margin-top:12px;">
    <strong>Resultado Kupiec:</strong><br>
    H₀: taxa de violações = {p_esp*100:.1f}% (nível esperado)<br>
    LR = {LR:.4f} ~ χ²(1)<br>
    p-valor = {p_val:.4f}<br><br>
    {"✅ <strong>Não rejeitamos H₀</strong> — O modelo está bem calibrado." if aprovado else
     "❌ <strong>Rejeitamos H₀</strong> — O modelo está mal calibrado. Rever parâmetros."}
    </div>
    """, unsafe_allow_html=True)
