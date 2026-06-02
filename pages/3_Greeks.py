"""
pages/3_🏛️_Greeks.py — Greeks completos da carteira + análises de exposição
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import greeks, black_scholes, TICKERS_INFO, CARTEIRA, TAXA_RF, VALOR_CARTEIRA
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="Greeks · Alpha Trading", layout="wide")
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
    choque_s = st.slider("Choque Spot p/ Simulação (%)", -30, 30, 0, 1)
    choque_v = st.slider("Choque Volatilidade (%)", -50, 100, 0, 5)

st.markdown("""
<div class="editorial-header">
    <div class="editorial-sub">Módulo VI · Sensibilidades</div>
    <div class="editorial-title">Greeks da<br>Carteira</div>
</div>
""", unsafe_allow_html=True)

# ── Calcular Greeks para toda a carteira ─────────────────────────────────────
opcoes = [p for p in CARTEIRA if p["tipo"] in ["call", "put"]]
rows_g = []
for pos in opcoes:
    info  = TICKERS_INFO[pos["ativo"]]
    S0    = info["preco_base"] * (1 + choque_s / 100)
    sigma = info["vol_base"]   * (1 + choque_v / 100)
    K     = info["preco_base"]   # ATM strike
    T     = pos["venc_dias"] / 365
    sinal = pos["direcao"]
    qtd   = pos["qtd"]
    g     = greeks(S0, K, T, TAXA_RF, sigma, pos["tipo"])
    preco_op = black_scholes(S0, K, T, TAXA_RF, sigma, pos["tipo"])
    rows_g.append({
        "ID":             pos["id"],
        "Ativo":          f"{info['emoji']} {pos['ativo']}",
        "Tipo":           pos["tipo"].upper(),
        "Dir.":           "▲" if sinal > 0 else "▼",
        "Qtd":            qtd,
        "Preço (USD)":    round(preco_op, 4),
        "Δ Delta unit.":  round(g["delta"], 4),
        "Γ Gamma unit.":  round(g["gamma"], 6),
        "ν Vega unit.":   round(g["vega"],  4),
        "Θ Theta unit.":  round(g["theta"], 4),
        "Δ Delta total":  round(g["delta"] * qtd * sinal, 2),
        "Γ Gamma total":  round(g["gamma"] * qtd * sinal, 6),
        "ν Vega total":   round(g["vega"]  * qtd * sinal, 2),
        "Θ Theta total":  round(g["theta"] * qtd * sinal, 4),
        "_g": g, "_sinal": sinal, "_qtd": qtd, "_nome": info["nome"],
    })

df_greeks = pd.DataFrame(rows_g)

# Totais
delta_total = df_greeks["Δ Delta total"].sum()
gamma_total = df_greeks["Γ Gamma total"].sum()
vega_total  = df_greeks["ν Vega total"].sum()
theta_total = df_greeks["Θ Theta total"].sum()

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
kpis_g = [
    (col1, "Δ Delta Líquido",  f"{delta_total:+.2f}", PALETA["indigo"], "exp. direcional"),
    (col2, "Γ Gamma Líquido",  f"{gamma_total:+.6f}", PALETA["cobre"],  "curvatura"),
    (col3, "ν Vega Líquido",   f"{vega_total:+.2f}",  PALETA["verde"] if vega_total > 0 else PALETA["vermelho"], "sens. vol"),
    (col4, "Θ Theta Líquido",  f"{theta_total:+.4f}", PALETA["lilas"],  "decaimento/dia"),
    (col5, "Posição Vol.",
     "COMPRADA" if vega_total > 0 else "VENDIDA",
     PALETA["verde"] if vega_total > 0 else PALETA["vermelho"],
     f"Vega = {vega_total:+.2f}"),
]
for col, label, val, cor, delta in kpis_g:
    col.markdown(f"""
    <div class="kpi-card" style="--accent:{cor};--val-color:{cor};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="font-size:1.4rem;">{val}</div>
        <div class="kpi-delta">{delta}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela Greeks ─────────────────────────────────────────────────────────────
tab_t1, tab_t2, tab_t3 = st.tabs(["Tabela Completa", "Exposição por Greek", "Cenário P&L"])

with tab_t1:
    colunas_show = ["ID","Ativo","Tipo","Dir.","Qtd","Preço (USD)",
                    "Δ Delta total","Γ Gamma total","ν Vega total","Θ Theta total"]
    st.dataframe(df_greeks[colunas_show].style
                 .applymap(lambda v: f"color:{PALETA['verde']}" if isinstance(v,(int,float)) and v > 0
                            else f"color:{PALETA['vermelho']}" if isinstance(v,(int,float)) and v < 0 else "",
                            subset=["Δ Delta total","Γ Gamma total","ν Vega total","Θ Theta total"]),
                 use_container_width=True, hide_index=True)

with tab_t2:
    fig_exp = make_subplots(rows=2, cols=2,
                             subplot_titles=["Delta por Posição","Vega por Posição",
                                             "Gamma por Posição","Theta por Posição"])
    nomes_pos = [f"{r['ID']} {r['Ativo']}" for _, r in df_greeks.iterrows()]
    cor_bar = lambda vals: [PALETA["verde"] if v >= 0 else PALETA["vermelho"] for v in vals]

    for (row_i, col_i), col_name in [
        ((1,1), "Δ Delta total"),
        ((1,2), "ν Vega total"),
        ((2,1), "Γ Gamma total"),
        ((2,2), "Θ Theta total"),
    ]:
        vals = df_greeks[col_name].tolist()
        fig_exp.add_trace(go.Bar(
            x=nomes_pos, y=vals,
            marker_color=cor_bar(vals), showlegend=False,
            text=[f"{v:.4g}" for v in vals], textposition="outside",
        ), row=row_i, col=col_i)

    layout_exp = plotly_tema(); layout_exp["height"] = 500
    fig_exp.update_layout(**layout_exp)
    fig_exp.update_xaxes(gridcolor="#f0f0f4", tickangle=30, tickfont=dict(size=9))
    fig_exp.update_yaxes(gridcolor="#f0f0f4")
    st.plotly_chart(fig_exp, use_container_width=True)

with tab_t3:
    st.markdown("""
    <div class="callout callout-info">
    Estimativa P&L usando aproximação de segunda ordem:
    <strong>ΔP ≈ Δ·ΔS + ½·Γ·(ΔS)² + ν·Δσ + Θ·Δt</strong>
    </div>
    """, unsafe_allow_html=True)

    ds_range = np.linspace(-0.20, 0.20, 200)
    dv_range = np.linspace(-0.20, 0.20, 200)

    # P&L por choque de preço (Δσ=0)
    pnl_ds = np.zeros(len(ds_range))
    for _, row in df_greeks.iterrows():
        S0 = TICKERS_INFO[row["Ativo"].split()[-1]]["preco_base"]
        g  = row["_g"]
        for j, ds in enumerate(ds_range):
            dS = S0 * ds
            pnl_ds[j] += row["_qtd"] * row["_sinal"] * (
                g["delta"] * dS + 0.5 * g["gamma"] * dS**2
            )

    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(
        x=ds_range * 100, y=pnl_ds / 1e6,
        name="P&L (Δ + Γ)", line=dict(color=PALETA["indigo"], width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba(74,108,247,{0.1 if pnl_ds[-1] > 0 else 0.05})",
    ))
    fig_pnl.add_hline(y=0, line_color=PALETA["borda"])
    fig_pnl.add_vline(x=choque_s, line_dash="dot", line_color=PALETA["cobre"],
                       annotation_text=f"Choque atual: {choque_s:+.0f}%",
                       annotation_font_color=PALETA["cobre"])

    layout_pnl = plotly_tema(); layout_pnl["height"] = 360
    fig_pnl.update_layout(**layout_pnl,
                           title="P&L Estimado da Carteira de Opções (2ª Ordem)",
                           xaxis_title="Choque no Spot (%)",
                           yaxis_title="P&L (USD Milhões)")
    st.plotly_chart(fig_pnl, use_container_width=True)

# ── Questões obrigatórias ─────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)

maior_vega_row = df_greeks.loc[df_greeks["ν Vega total"].abs().idxmax()]
maior_gamma_row = df_greeks.loc[df_greeks["Γ Gamma total"].abs().idxmax()]

col_qa, col_qb, col_qc, col_qd = st.columns(4)
qas = [
    (col_qa, "Comprada ou vendida em vol?",
     f"{'COMPRADA' if vega_total > 0 else 'VENDIDA'} em volatilidade",
     f"Vega total: {vega_total:+.2f}",
     PALETA["verde"] if vega_total > 0 else PALETA["vermelho"]),
    (col_qb, "Ganha ou perde com ↑ vol?",
     f"{'GANHA' if vega_total > 0 else 'PERDE'} com aumento de vol",
     f"Posição: Vega {vega_total:+.2f}",
     PALETA["verde"] if vega_total > 0 else PALETA["vermelho"]),
    (col_qc, "Maior Vega?",
     f"{maior_vega_row['Ativo']} ({maior_vega_row['ID']})",
     f"Vega total: {maior_vega_row['ν Vega total']:+.2f}",
     PALETA["indigo"]),
    (col_qd, "Maior risco não-linear?",
     f"{maior_gamma_row['Ativo']} ({maior_gamma_row['ID']})",
     f"Gamma total: {maior_gamma_row['Γ Gamma total']:+.6f}",
     PALETA["cobre"]),
]
for col, pergunta, resp, detalhe, cor in qas:
    col.markdown(f"""
    <div class="section-card" style="border-top:3px solid {cor};">
        <div style="font-size:0.72rem;color:#8888a0;margin-bottom:6px;">{pergunta}</div>
        <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;
             color:{cor};line-height:1.2;">{resp}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#8888a0;margin-top:6px;">{detalhe}</div>
    </div>""", unsafe_allow_html=True)
