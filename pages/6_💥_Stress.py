"""
pages/6_💥_Stress.py — Stress Testing com 7 cenários + análise de impacto
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import stress_carteira, CENARIOS_STRESS, CARTEIRA, TICKERS_INFO, VALOR_CARTEIRA
from theme import THEME_CSS, plotly_tema, PALETA

st.set_page_config(page_title="Stress Testing · Alpha Trading", layout="wide")
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
    cenario_sel = st.selectbox("Cenário em Destaque", list(CENARIOS_STRESS.keys()))

st.markdown("""
<div class="editorial-header">
    <div class="editorial-sub">Módulo XI · Análise de Cenários Extremos</div>
    <div class="editorial-title">Stress Testing<br>de Commodities</div>
</div>
""", unsafe_allow_html=True)

# ── Rodar todos os cenários ───────────────────────────────────────────────────
resultados_macro = []
for nome_c, choques in CENARIOS_STRESS.items():
    perda, df_det = stress_carteira(CARTEIRA, choques)
    resultados_macro.append({
        "Cenário": nome_c,
        "Perda (USD M)": perda / 1e6,
        "% Carteira": perda / VALOR_CARTEIRA * 100,
        "_detalhes": df_det,
    })

df_stress_macro = pd.DataFrame(resultados_macro).sort_values("Perda (USD M)", ascending=False)

# ── KPIs rápidos ─────────────────────────────────────────────────────────────
pior = df_stress_macro.iloc[0]
melhor = df_stress_macro.iloc[-1]
perda_media = df_stress_macro["Perda (USD M)"].mean()
n_positivo = (df_stress_macro["Perda (USD M)"] > 0).sum()

col1, col2, col3, col4 = st.columns(4)
kpis_st = [
    (col1, "Pior Cenário",    pior["Cenário"].split(" ", 1)[-1],  f"${pior['Perda (USD M)']:.2f}M",  PALETA["vermelho"]),
    (col2, "Melhor Cenário",  melhor["Cenário"].split(" ", 1)[-1], f"${melhor['Perda (USD M)']:.2f}M", PALETA["verde"]),
    (col3, "Perda Média",     "Todos os Cenários",                 f"${perda_media:.2f}M",              PALETA["cobre"]),
    (col4, "Cenários c/ Perda", f"de {len(df_stress_macro)}",     f"{n_positivo}",                     PALETA["navy"]),
]
for col, label, sub, val, cor in kpis_st:
    col.markdown(f"""
    <div class="kpi-card" style="--accent:{cor};--val-color:{cor};">
        <div class="kpi-label">{label}</div>
        <div style="font-size:0.72rem;color:#8888a0;margin-bottom:4px;">{sub}</div>
        <div class="kpi-value" style="font-size:1.4rem;">{val}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gráfico tornado ───────────────────────────────────────────────────────────
col_g1, col_g2 = st.columns([3, 2], gap="large")

with col_g1:
    st.markdown("""
    <div class="section-label">Impacto por Cenário</div>
    <div class="section-title">Diagrama Tornado — Perda Total (USD M)</div>
    """, unsafe_allow_html=True)

    fig_tornado = go.Figure(go.Bar(
        x=df_stress_macro["Perda (USD M)"],
        y=df_stress_macro["Cenário"],
        orientation="h",
        marker_color=[PALETA["vermelho"] if v > 0 else PALETA["verde"]
                      for v in df_stress_macro["Perda (USD M)"]],
        text=[f"${v:+.2f}M ({pct:+.1f}%)"
              for v, pct in zip(df_stress_macro["Perda (USD M)"], df_stress_macro["% Carteira"])],
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=11),
    ))
    fig_tornado.add_vline(x=0, line_color=PALETA["borda"], line_width=2)
    layout_t = plotly_tema(); layout_t["height"] = 400
    fig_tornado.update_layout(**layout_t, showlegend=False,
                               xaxis_title="Perda (USD Milhões)",
                               xaxis=dict(gridcolor="#f0f0f4"))
    fig_tornado.update_yaxes(showgrid=False)
    st.plotly_chart(fig_tornado, use_container_width=True)

with col_g2:
    st.markdown("""
    <div class="section-label">Distribuição de Impacto</div>
    <div class="section-title">Perda % da Carteira</div>
    """, unsafe_allow_html=True)

    fig_gauge_area = go.Figure()
    for _, row in df_stress_macro.iterrows():
        cor_p = PALETA["vermelho"] if row["Perda (USD M)"] > 0 else PALETA["verde"]
        fig_gauge_area.add_trace(go.Bar(
            x=[row["% Carteira"]],
            y=[row["Cenário"][:25]],
            orientation="h",
            marker_color=cor_p,
            showlegend=False,
            text=f"{row['% Carteira']:+.1f}%",
            textposition="outside",
            textfont=dict(size=10),
        ))
    fig_gauge_area.add_vline(x=0, line_color=PALETA["borda"])
    layout_ga = plotly_tema(); layout_ga["height"] = 400
    fig_gauge_area.update_layout(**layout_ga, showlegend=False,
                                  xaxis_title="% da Carteira",
                                  xaxis_ticksuffix="%")
    fig_gauge_area.update_yaxes(showgrid=False)
    st.plotly_chart(fig_gauge_area, use_container_width=True)

# ── Detalhes do cenário selecionado ──────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown(f"""
<div class="section-label">Análise Detalhada</div>
<div class="section-title">Cenário: {cenario_sel}</div>
""", unsafe_allow_html=True)

perda_sel, df_det_sel = stress_carteira(CARTEIRA, CENARIOS_STRESS[cenario_sel])
choques_sel = {k: v for k, v in CENARIOS_STRESS[cenario_sel].items() if not k.startswith("_")}

col_d1, col_d2 = st.columns([2, 3], gap="large")

with col_d1:
    # Choques aplicados
    st.markdown("""<div class="section-card" style="padding:16px 18px;">
    <div class="section-label">Choques Aplicados</div>""", unsafe_allow_html=True)
    for ativo_chq, chq in choques_sel.items():
        info = TICKERS_INFO.get(ativo_chq, {"emoji": "📌", "nome": ativo_chq, "preco_base": 0})
        cor_chq = PALETA["verde"] if chq > 0 else PALETA["vermelho"]
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:8px 0;
             border-bottom:1px solid #f0f0f4;">
            <span style="font-size:0.82rem;">{info.get('emoji','')} {ativo_chq}</span>
            <span style="font-family:'DM Mono',monospace;font-weight:600;color:{cor_chq};">
                {chq*100:+.1f}%</span>
        </div>""", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-top:16px;padding-top:12px;border-top:2px solid #1a1a2e;">
        <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#8888a0;">
            Perda Total do Cenário</div>
        <div style="font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;
             color:{PALETA['vermelho'] if perda_sel > 0 else PALETA['verde']};">
            ${perda_sel/1e6:+.3f}M</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#8888a0;">
            {perda_sel/VALOR_CARTEIRA*100:+.2f}% da carteira</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_d2:
    # Waterfall por posição
    df_det_sorted = df_det_sel.sort_values("Perda (USD)", ascending=True)
    fig_wf = go.Figure(go.Waterfall(
        name="P&L por Posição",
        orientation="h",
        y=df_det_sorted["Posição"].tolist() + ["TOTAL"],
        x=df_det_sorted["Perda (USD)"].tolist() + [perda_sel],
        connector=dict(line=dict(color=PALETA["borda"])),
        decreasing=dict(marker_color=PALETA["vermelho"]),
        increasing=dict(marker_color=PALETA["verde"]),
        totals=dict(marker_color=PALETA["navy"]),
        textposition="outside",
        text=[f"${v/1e3:+.1f}K" for v in df_det_sorted["Perda (USD)"].tolist()] + [f"${perda_sel/1e6:+.2f}M"],
        textfont=dict(family="DM Mono", size=10),
    ))
    layout_wf = plotly_tema(); layout_wf["height"] = 380
    fig_wf.update_layout(**layout_wf, title="Contribuição de Cada Posição",
                          xaxis_title="USD")
    st.plotly_chart(fig_wf, use_container_width=True)

# ── Tabela todos os cenários ──────────────────────────────────────────────────
st.markdown("<hr class='divider-light'>", unsafe_allow_html=True)
st.markdown("""
<div class="section-label">Resumo Completo</div>
<div class="section-title">Todos os Cenários de Stress</div>
""", unsafe_allow_html=True)

df_show = df_stress_macro[["Cenário","Perda (USD M)","% Carteira"]].copy()
df_show["Perda (USD M)"] = df_show["Perda (USD M)"].round(4)
df_show["% Carteira"]    = df_show["% Carteira"].round(4)
st.dataframe(
    df_show.style
    .format({"Perda (USD M)": "${:+.4f}M", "% Carteira": "{:+.2f}%"})
    .applymap(lambda v: f"color:{PALETA['vermelho']};font-weight:600" if isinstance(v,(int,float)) and v > 0
               else (f"color:{PALETA['verde']};font-weight:600" if isinstance(v,(int,float)) and v < 0 else ""),
              subset=["Perda (USD M)","% Carteira"]),
    use_container_width=True, hide_index=True
)

st.markdown(f"""
<div class="callout callout-risk" style="margin-top:16px;">
<strong>Cenário de Maior Perda: {pior['Cenário']}</strong><br>
Perda estimada de <strong>${pior['Perda (USD M)']:.2f}M</strong> ({pior['% Carteira']:.1f}% da carteira).
Recomenda-se avaliar hedge com opções de proteção nos ativos mais expostos,
redução de posições vendidas em opções (que criam perdas convexas em choques de vol),
e revisão dos limites de risco junto ao Comitê de Risco.
</div>
""", unsafe_allow_html=True)
