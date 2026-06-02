"""
pages/1_💹_Precificação.py — Black-Scholes + Black-76 + Greeks
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import black_scholes, black76, greeks, TICKERS_INFO, TAXA_RF, carregar_dados, calcular_retornos, vol_historica_anual
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="Precificação · Alpha Trading", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 12px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;text-transform:uppercase;
             letter-spacing:0.12em;color:#8888aa;">Mesa de Commodities</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#f5e6d0;">
            Banco Alpha<br>Trading</div>
    </div><hr/>
    """, unsafe_allow_html=True)
    ativo_sel = st.selectbox("Ativo Base", list(TICKERS_INFO.keys()),
                              format_func=lambda x: f"{TICKERS_INFO[x]['emoji']} {TICKERS_INFO[x]['nome']}")
    modelo = st.radio("Modelo", ["Black-Scholes (ETF/Spot)", "Black-76 (Futuro)"])
    tipo_op = st.radio("Tipo de Opção", ["call", "put"])

info = TICKERS_INFO[ativo_sel]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="editorial-header">
    <div class="editorial-sub">Módulo II · Precificação de Opções</div>
    <div class="editorial-title">Black-Scholes<br>& Black-76</div>
</div>
""", unsafe_allow_html=True)

# ── Formulário de entrada ─────────────────────────────────────────────────────
st.markdown("""<div class="section-card">
<div class="section-label">Parâmetros da Opção</div>
<div class="section-title" style="margin-bottom:20px;">Configure o Contrato</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    S_inp = st.number_input(f"{'F — Futuro' if 'Black-76' in modelo else 'S — Spot'}", 
                             value=float(info["preco_base"]), step=0.5,
                             help="Preço do ativo subjacente (ou do futuro no Black-76)")
with col2:
    K_inp = st.number_input("K — Strike", value=float(info["preco_base"]), step=0.5)
with col3:
    T_inp = st.number_input("T — Tempo (anos)", value=0.25, step=0.01, min_value=0.001, format="%.3f")
with col4:
    r_inp = st.number_input("r — Taxa Livre (%)", value=TAXA_RF * 100, step=0.1, format="%.2f") / 100
with col5:
    sigma_inp = st.number_input("σ — Volatilidade (%)", value=float(info["vol_base"] * 100),
                                 step=0.5, min_value=0.1, format="%.2f") / 100

st.markdown("</div>", unsafe_allow_html=True)

# ── Cálculo ───────────────────────────────────────────────────────────────────
if "Black-76" in modelo:
    preco = black76(S_inp, K_inp, T_inp, r_inp, sigma_inp, tipo_op)
    label_modelo = "Black-76"
else:
    preco = black_scholes(S_inp, K_inp, T_inp, r_inp, sigma_inp, tipo_op)
    label_modelo = "Black-Scholes"

g = greeks(S_inp, K_inp, T_inp, r_inp, sigma_inp, tipo_op)

moneyness = S_inp / K_inp
estado = "ATM" if abs(moneyness - 1) < 0.01 else ("ITM" if moneyness > 1 and tipo_op == "call" or moneyness < 1 and tipo_op == "put" else "OTM")
cor_estado = {"ATM": "badge-blue", "ITM": "badge-green", "OTM": "badge-amber"}[estado]

# ── Resultado + Greeks ────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_r, col_g_area = st.columns([2, 3], gap="large")

with col_r:
    st.markdown(f"""
    <div class="section-card" style="border-left:4px solid {PALETA['indigo']};">
        <div class="section-label">Resultado · {label_modelo}</div>
        <div class="section-title">{info['emoji']} {ativo_sel} · {tipo_op.upper()}</div>
        <br>
        <div style="display:flex;gap:8px;margin-bottom:16px;">
            <span class="badge badge-dark">{label_modelo}</span>
            <span class="badge {cor_estado}">{estado}</span>
            <span class="badge badge-blue">K/S = {K_inp/S_inp:.3f}</span>
        </div>
        <div style="font-family:'Playfair Display',serif;font-size:3rem;font-weight:900;
             color:{PALETA['indigo']};line-height:1;">
            ${preco:,.4f}
        </div>
        <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#8888a0;margin-top:6px;">
            Preço Teórico da Opção
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    greeks_info = [
        ("Δ Delta",  g["delta"],  "Sensibilidade ao preço do ativo",    ""),
        ("Γ Gamma",  g["gamma"],  "Variação do Delta",                  ""),
        ("ν Vega",   g["vega"],   "Sensib. à vol. (por 1%)",            "/1%"),
        ("Θ Theta",  g["theta"],  "Decaimento temporal (1 dia)",        "/dia"),
        ("ρ Rho",    g["rho"],    "Sensib. à taxa (por 1%)",             "/1%"),
    ]
    for nome, val, desc, suf in greeks_info:
        cor = PALETA["verde"] if val >= 0 else PALETA["vermelho"]
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
             padding:10px 0;border-bottom:1px solid #f0f0f4;">
            <div>
                <div style="font-family:'DM Mono',monospace;font-size:0.78rem;font-weight:500;
                     color:#1a1a2e;">{nome}</div>
                <div style="font-size:0.68rem;color:#8888a0;">{desc}</div>
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:1rem;font-weight:600;color:{cor};">
                {val:+.6f}{suf}
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_g_area:
    tab1, tab2, tab3 = st.tabs(["Payoff no Vencimento", "Perfil Delta", "Superfície de Preço"])

    with tab1:
        S_range = np.linspace(S_inp * 0.6, S_inp * 1.4, 200)
        payoff  = np.array([max(s - K_inp, 0) if tipo_op == "call" else max(K_inp - s, 0) for s in S_range])
        premium = np.full_like(S_range, preco)
        pnl_comprado = payoff - preco
        pnl_vendido  = preco - payoff

        fig_payoff = go.Figure()
        fig_payoff.add_trace(go.Scatter(x=S_range, y=payoff, name="Payoff Bruto",
                                         line=dict(color=PALETA["navy"], width=2)))
        fig_payoff.add_trace(go.Scatter(x=S_range, y=pnl_comprado, name="P&L Comprado",
                                         line=dict(color=PALETA["verde"], width=2, dash="dash"),
                                         fill="tozeroy", fillcolor="rgba(34,197,94,0.08)"))
        fig_payoff.add_vline(x=K_inp, line_dash="dot", line_color=PALETA["cobre"],
                              annotation_text=f"K = {K_inp:.2f}", annotation_font_color=PALETA["cobre"])
        fig_payoff.add_vline(x=S_inp, line_dash="dot", line_color=PALETA["cinza"],
                              annotation_text=f"S = {S_inp:.2f}")
        fig_payoff.add_hline(y=0, line_color="#e8e8ec")
        layout = plotly_tema(); layout["height"] = 360
        fig_payoff.update_layout(**layout, title="Payoff e P&L no Vencimento",
                                  xaxis_title="Preço do Ativo (S)", yaxis_title="Valor ($)")
        st.plotly_chart(fig_payoff, use_container_width=True)

    with tab2:
        deltas_range = np.array([
            greeks(s, K_inp, T_inp, r_inp, sigma_inp, tipo_op)["delta"]
            for s in S_range
        ])
        fig_delta = go.Figure()
        fig_delta.add_trace(go.Scatter(x=S_range, y=deltas_range, name="Delta",
                                        line=dict(color=PALETA["indigo"], width=2.5)))
        fig_delta.add_vline(x=S_inp, line_dash="dot", line_color=PALETA["cinza"])
        fig_delta.add_hline(y=g["delta"], line_dash="dash", line_color=PALETA["cobre"],
                             annotation_text=f"Δ atual = {g['delta']:.4f}")
        layout2 = plotly_tema(); layout2["height"] = 360
        fig_delta.update_layout(**layout2, title="Perfil de Delta vs Preço do Ativo",
                                  xaxis_title="Spot (S)", yaxis_title="Delta")
        st.plotly_chart(fig_delta, use_container_width=True)

    with tab3:
        strikes_3d = np.linspace(S_inp * 0.7, S_inp * 1.3, 30)
        vols_3d    = np.linspace(0.05, 0.80, 30)
        KK, VV = np.meshgrid(strikes_3d, vols_3d)
        ZZ = np.vectorize(lambda k, v: black_scholes(S_inp, k, T_inp, r_inp, v, tipo_op))(KK, VV)
        fig_3d = go.Figure(go.Surface(x=strikes_3d, y=vols_3d * 100, z=ZZ,
                                       colorscale="Blues", opacity=0.9))
        fig_3d.update_layout(
            title="Preço vs Strike vs Volatilidade",
            scene=dict(
                xaxis_title="Strike (K)", yaxis_title="Vol (%)", zaxis_title="Preço",
                bgcolor="white",
                xaxis=dict(gridcolor="#e8e8ec"), yaxis=dict(gridcolor="#e8e8ec"),
                zaxis=dict(gridcolor="#e8e8ec"),
            ),
            paper_bgcolor="white",
            font=dict(family="DM Sans", color="#1a1a2e"),
            height=400, margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_3d, use_container_width=True)

# ── Comparação BS vs B76 ──────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown("""
<div class="section-label">Comparação de Modelos</div>
<div class="section-title">Black-Scholes vs Black-76 — Diferença por Strike</div>
""", unsafe_allow_html=True)

strikes_cmp = np.linspace(S_inp * 0.80, S_inp * 1.20, 40)
precos_bs  = [black_scholes(S_inp, K, T_inp, r_inp, sigma_inp, tipo_op) for K in strikes_cmp]
precos_b76 = [black76(S_inp, K, T_inp, r_inp, sigma_inp, tipo_op) for K in strikes_cmp]
diff = np.array(precos_bs) - np.array(precos_b76)

fig_cmp = make_subplots(rows=1, cols=2,
                         subplot_titles=["Preços: BS vs Black-76", "Diferença BS − B76"])
fig_cmp.add_trace(go.Scatter(x=strikes_cmp, y=precos_bs, name="Black-Scholes",
                               line=dict(color=PALETA["indigo"], width=2)), row=1, col=1)
fig_cmp.add_trace(go.Scatter(x=strikes_cmp, y=precos_b76, name="Black-76",
                               line=dict(color=PALETA["cobre"], width=2, dash="dash")), row=1, col=1)
fig_cmp.add_trace(go.Bar(x=strikes_cmp, y=diff, name="Diferença",
                           marker_color=[PALETA["verde"] if d >= 0 else PALETA["vermelho"] for d in diff],
                           showlegend=False), row=1, col=2)
layout_cmp = plotly_tema(); layout_cmp["height"] = 280
fig_cmp.update_layout(**layout_cmp)
fig_cmp.update_xaxes(gridcolor="#f0f0f4")
fig_cmp.update_yaxes(gridcolor="#f0f0f4")
st.plotly_chart(fig_cmp, use_container_width=True)

st.markdown("""
<div class="callout callout-info">
<strong>Black-76 vs Black-Scholes:</strong> O Black-76 usa o preço a <em>futuro</em> F como subjacente ao invés do spot S,
e incorpora o desconto e<sup>−rT</sup> de forma diferente. Para futuros de commodities (CL, GC, NG, ZS), 
o Black-76 é o modelo padrão de mercado. Para ETFs (GLD, USO, SLV), usa-se Black-Scholes.
</div>
""", unsafe_allow_html=True)
