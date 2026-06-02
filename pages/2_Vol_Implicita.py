"""
pages/2_🔬_Vol_Implícita.py — Volatilidade Implícita + Comparação de Métodos Numéricos
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    black_scholes, comparar_metodos, bissecao, newton_raphson, secante, brent,
    TICKERS_INFO, TAXA_RF, gerar_smile,
)
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="Vol. Implícita · Alpha Trading", layout="wide")
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
    ativo_sel = st.selectbox("Ativo", list(TICKERS_INFO.keys()),
                              format_func=lambda x: f"{TICKERS_INFO[x]['emoji']} {TICKERS_INFO[x]['nome']}")
    tipo_op = st.radio("Tipo", ["call", "put"])
    vol_real = st.slider("Vol. Real para Simular (%)", 5.0, 80.0,
                          float(TICKERS_INFO[ativo_sel]["vol_base"] * 100), 0.5) / 100

info = TICKERS_INFO[ativo_sel]
S = info["preco_base"]

st.markdown("""
<div class="editorial-header">
    <div class="editorial-sub">Módulo III & IV · Volatilidade Implícita</div>
    <div class="editorial-title">Inversão Numérica<br>do Modelo</div>
</div>
""", unsafe_allow_html=True)

# ── Inputs da Opção ───────────────────────────────────────────────────────────
st.markdown("""<div class="section-card">
<div class="section-label">Parâmetros da Opção de Referência</div>""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: K_inp = st.number_input("Strike K", value=float(S), step=0.5)
with col2: T_inp = st.number_input("Tempo T (anos)", value=0.25, step=0.01, min_value=0.001, format="%.3f")
with col3:
    preco_justo = black_scholes(S, K_inp, T_inp, TAXA_RF, vol_real, tipo_op)
    pm_inp = st.number_input("Preço de Mercado", value=round(preco_justo * 1.05, 4),
                               step=0.001, min_value=0.0001, format="%.4f",
                               help="Preço observado — ligeiramente acima do justo para simular prêmio de vol")
with col4:
    st.markdown(f"""
    <div style="padding-top:28px;font-family:'DM Mono',monospace;font-size:0.72rem;">
        <div style="color:#8888a0;">Preço Justo (σ={vol_real*100:.1f}%)</div>
        <div style="font-size:1.1rem;font-weight:600;color:{PALETA['indigo']};">${preco_justo:.4f}</div>
        <div style="color:#8888a0;margin-top:4px;">Spread: ${pm_inp-preco_justo:+.4f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Comparação ────────────────────────────────────────────────────────────────
col_btn, _ = st.columns([1, 3])
executar = col_btn.button("▶ Executar Todos os Métodos", type="primary")

if executar or True:  # Exibe sempre com valores padrão
    df_comp = comparar_metodos(S, K_inp, T_inp, TAXA_RF, pm_inp, tipo_op)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-label">Resultado Comparativo</div>
    <div class="section-title">Bisseção · Newton-Raphson · Secante · Brent</div>
    """, unsafe_allow_html=True)

    # Cards por método
    cols_m = st.columns(4)
    cores_metodo = [PALETA["navy"], PALETA["indigo"], PALETA["cobre"], PALETA["verde"]]
    for i, (_, row) in enumerate(df_comp.iterrows()):
        conv = row["Convergiu"] == "✓"
        sigma_val = row["_sigma"]
        with cols_m[i]:
            badge_cls = "badge-green" if conv else "badge-red"
            st.markdown(f"""
            <div class="kpi-card" style="--accent:{cores_metodo[i]};--val-color:{cores_metodo[i]};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div class="kpi-label">{row['Método']}</div>
                    <span class="badge {badge_cls}">{row['Convergiu']}</span>
                </div>
                <div class="kpi-value">{row['Vol Implícita']}</div>
                <div class="kpi-delta">{row['Iterações']} iter · {row['Tempo (µs)']} µs</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#8888a0;margin-top:4px;">
                    Erro: {row['Erro Final']}
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Gráfico de convergência ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_conv1, col_conv2 = st.columns(2, gap="large")

    with col_conv1:
        st.markdown("""
        <div class="section-label">Convergência</div>
        <div class="section-title">Histórico de Erro por Iteração</div>
        """, unsafe_allow_html=True)

        fig_conv = go.Figure()
        metodos_fn = [
            ("Bisseção",       bissecao(S, K_inp, T_inp, TAXA_RF, pm_inp, tipo_op)),
            ("Newton-Raphson", newton_raphson(S, K_inp, T_inp, TAXA_RF, pm_inp, tipo_op)),
            ("Secante",        secante(S, K_inp, T_inp, TAXA_RF, pm_inp, tipo_op)),
        ]
        for (nome, (sig, itr, hist, _)), cor in zip(metodos_fn, cores_metodo):
            if hist and len(hist) > 1:
                fig_conv.add_trace(go.Scatter(
                    x=list(range(1, len(hist) + 1)), y=hist,
                    name=nome, line=dict(color=cor, width=2),
                    mode="lines+markers", marker=dict(size=4),
                ))
        layout_conv = plotly_tema(); layout_conv["height"] = 340
        fig_conv.update_layout(**layout_conv, yaxis_type="log",
                                xaxis_title="Iteração", yaxis_title="|f(σ)| — Erro (log)",
                                title="Convergência dos Métodos Iterativos")
        fig_conv.update_xaxes(showgrid=True)
        fig_conv.update_yaxes(showgrid=True)
        st.plotly_chart(fig_conv, use_container_width=True)

    with col_conv2:
        st.markdown("""
        <div class="section-label">Sensibilidade</div>
        <div class="section-title">f(σ) = Preço Modelo − Preço Mercado</div>
        """, unsafe_allow_html=True)

        sigmas = np.linspace(0.01, 1.5, 300)
        f_vals = np.array([black_scholes(S, K_inp, T_inp, TAXA_RF, s, tipo_op) - pm_inp for s in sigmas])

        fig_fval = go.Figure()
        fig_fval.add_trace(go.Scatter(x=sigmas * 100, y=f_vals, name="f(σ)",
                                       line=dict(color=PALETA["navy"], width=2.5)))
        fig_fval.add_hline(y=0, line_color=PALETA["vermelho"], line_width=2,
                            annotation_text="f(σ) = 0 → Vol Implícita", annotation_font_color=PALETA["vermelho"])
        # Marcar vol implícita encontrada (Brent)
        sig_brent = df_comp[df_comp["Método"] == "Brent"]["_sigma"].values[0]
        if sig_brent:
            fig_fval.add_vline(x=sig_brent * 100, line_dash="dot", line_color=PALETA["verde"],
                                annotation_text=f"σ* = {sig_brent*100:.2f}%",
                                annotation_font_color=PALETA["verde"])
        layout_fval = plotly_tema(); layout_fval["height"] = 340
        fig_fval.update_layout(**layout_fval, xaxis_title="σ (%)", yaxis_title="f(σ)",
                                title="Função Objetivo f(σ) — Busca da Raiz")
        st.plotly_chart(fig_fval, use_container_width=True)

    # ── Tabela detalhada ──
    st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-label">Tabela Completa</div>
    <div class="section-title">Múltiplos Strikes — Todos os Métodos</div>
    """, unsafe_allow_html=True)

    moneyness_range = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]
    rows_tab = []
    for m in moneyness_range:
        K_t = S * m
        pm_t = black_scholes(S, K_t, T_inp, TAXA_RF, vol_real, tipo_op) * (1 + 0.05 * abs(m - 1) + 0.02)
        for nm, fn in [
            ("Bisseção",       bissecao),
            ("Newton-Raphson", newton_raphson),
            ("Secante",        secante),
            ("Brent",          brent),
        ]:
            sig, itr, hist, tempo = fn(S, K_t, T_inp, TAXA_RF, pm_t, tipo_op)
            conv = sig is not None and 0 < sig < 5
            rows_tab.append({
                "Strike": f"{K_t:.2f}",
                "Moneyness": f"{m:.2f}x",
                "Método": nm,
                "Vol Impl. (%)": f"{sig*100:.4f}" if conv else "—",
                "Iter.": itr,
                "Tempo (µs)": f"{tempo*1e6:.1f}",
                "Convergiu": "✓" if conv else "✗",
            })

    df_tab = pd.DataFrame(rows_tab)
    st.dataframe(df_tab, use_container_width=True, hide_index=True, height=320)

    # ── Análise qualitativa ──
    st.markdown("<br>", unsafe_allow_html=True)
    cols_q = st.columns(4)
    analises = [
        ("Bisseção", PALETA["navy"],
         "Garantida no intervalo [0.0001, 5]. Convergência linear O(log n) — reduz o intervalo à metade a cada iteração. Nunca falha, mas é a mais lenta (~50–200 iter)."),
        ("Newton-Raphson", PALETA["indigo"],
         "Convergência quadrática quando funciona. Usa Vega analítico como derivada. Falha quando Vega ≈ 0: opções deep OTM/ITM ou vencimentos muito curtos."),
        ("Secante", PALETA["cobre"],
         "Aproxima a derivada por diferença finita. Convergência superlinear (~1.618x). Mais rápida que bisseção sem exigir Vega analítico. Sensível ao chute inicial."),
        ("Brent", PALETA["verde"],
         "Combina bisseção + secante + interpolação quadrática inversa. Convergência garantida como bisseção, velocidade próxima a Newton. Recomendado para produção."),
    ]
    for col, (nome, cor, desc) in zip(cols_q, analises):
        col.markdown(f"""
        <div class="section-card" style="border-top:3px solid {cor};padding:16px 18px;">
            <div style="font-family:'DM Mono',monospace;font-size:0.68rem;text-transform:uppercase;
                 letter-spacing:0.08em;color:{cor};margin-bottom:6px;">{nome}</div>
            <div style="font-size:0.8rem;line-height:1.6;color:#4a4a6a;">{desc}</div>
        </div>""", unsafe_allow_html=True)

# ── Smile de Volatilidade ─────────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown("""
<div class="section-label">Módulo V · Smile & Superfície</div>
<div class="section-title">Smile de Volatilidade por Vencimento</div>
""", unsafe_allow_html=True)

vencimentos_smile = [30, 60, 90, 180, 360]
vol_bases_smile   = [0.30, 0.27, vol_real, vol_real * 0.95, vol_real * 0.90]

col_sm1, col_sm2 = st.columns([3, 2], gap="large")

with col_sm1:
    fig_smile = go.Figure()
    cores_smile = [PALETA["navy"], PALETA["indigo"], PALETA["cobre"], PALETA["verde"], PALETA["lilas"]]
    for Tv, vb, cor in zip(vencimentos_smile, vol_bases_smile, cores_smile):
        df_sm = gerar_smile(S, TAXA_RF, Tv / 365, vb)
        fig_smile.add_trace(go.Scatter(
            x=df_sm["Moneyness"], y=df_sm["Vol Impl. (%)"],
            name=f"{Tv}d", line=dict(color=cor, width=2),
            mode="lines+markers", marker=dict(size=5),
        ))
    fig_smile.add_hline(y=info["vol_base"] * 100, line_dash="dash",
                         line_color=PALETA["cinza"], line_width=1.5,
                         annotation_text=f"Vol Histórica {info['vol_base']*100:.1f}%",
                         annotation_font_color=PALETA["cinza"])
    fig_smile.add_vline(x=1.0, line_dash="dot", line_color=PALETA["borda"])
    layout_sm = plotly_tema(); layout_sm["height"] = 380
    fig_smile.update_layout(**layout_sm, xaxis_title="Moneyness (K/S)",
                              yaxis_title="Vol Implícita (%)",
                              title="Smile com Skew Negativo (Put Skew)")
    st.plotly_chart(fig_smile, use_container_width=True)

with col_sm2:
    # Superfície 3D compacta
    from utils import superficie_vol
    strikes_surf, vencs_surf, Z_surf = superficie_vol(S, TAXA_RF, vencimentos_smile, vol_real)
    fig_surf = go.Figure(go.Surface(
        x=strikes_surf / S, y=vencs_surf, z=Z_surf,
        colorscale=[[0, "#1a1a2e"], [0.5, "#4a6cf7"], [1, "#c8925a"]],
        opacity=0.88,
    ))
    fig_surf.update_layout(
        scene=dict(
            xaxis_title="Moneyness", yaxis_title="Dias", zaxis_title="Vol (%)",
            bgcolor="white",
            xaxis=dict(gridcolor="#e8e8ec"), yaxis=dict(gridcolor="#e8e8ec"),
            zaxis=dict(gridcolor="#e8e8ec"),
        ),
        paper_bgcolor="white",
        font=dict(family="DM Sans", color="#1a1a2e"),
        height=380, margin=dict(l=0, r=0, t=36, b=0),
        title="Superfície de Volatilidade",
    )
    st.plotly_chart(fig_surf, use_container_width=True)

st.markdown("""
<div class="callout callout-info">
<strong>Skew de Volatilidade:</strong> Em mercados de commodities, puts OTM são mais caras que calls OTM simétricas — 
reflexo da demanda por proteção. O <em>skew negativo</em> (vol maior para K/S &lt; 1) é a assinatura de uma distribuição 
com cauda esquerda pesada. A superfície de volatilidade combina o smile com a estrutura a termo.
</div>
""", unsafe_allow_html=True)
