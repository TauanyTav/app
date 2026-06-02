"""
utils.py — Motor financeiro compartilhado entre todas as páginas.
Contém: modelos de precificação, métodos numéricos, VaR, Greeks, dados.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
import time
import warnings

warnings.filterwarnings("ignore")

# ─── CONSTANTES ───────────────────────────────────────────────────────────────

TAXA_RF = 0.0525  # 5.25% a.a.

TICKERS_INFO = {
    "CL=F": {"nome": "Petróleo WTI",   "emoji": "🛢️",  "preco_base": 78.50,  "vol_base": 0.32, "categoria": "energia"},
    "GC=F": {"nome": "Ouro",            "emoji": "🥇",  "preco_base": 2350.0, "vol_base": 0.18, "categoria": "metais"},
    "ZS=F": {"nome": "Soja",            "emoji": "🌱",  "preco_base": 1180.0, "vol_base": 0.22, "categoria": "agricola"},
    "NG=F": {"nome": "Gás Natural",     "emoji": "💨",  "preco_base": 2.85,   "vol_base": 0.55, "categoria": "energia"},
    "GLD":  {"nome": "Ouro ETF",        "emoji": "🏅",  "preco_base": 222.0,  "vol_base": 0.17, "categoria": "etf"},
    "USO":  {"nome": "Petróleo ETF",    "emoji": "⛽",  "preco_base": 74.50,  "vol_base": 0.33, "categoria": "etf"},
    "SLV":  {"nome": "Prata ETF",       "emoji": "🪙",  "preco_base": 26.80,  "vol_base": 0.28, "categoria": "etf"},
}

CARTEIRA = [
    {"id": "F1", "ativo": "CL=F", "tipo": "futuro", "direcao": +1, "venc_dias": 90,  "qtd": 120,    "mult": 1000},
    {"id": "F2", "ativo": "GC=F", "tipo": "futuro", "direcao": -1, "venc_dias": 180, "qtd": 80,     "mult": 100},
    {"id": "F3", "ativo": "ZS=F", "tipo": "futuro", "direcao": +1, "venc_dias": 120, "qtd": 150,    "mult": 50},
    {"id": "F4", "ativo": "NG=F", "tipo": "futuro", "direcao": -1, "venc_dias": 60,  "qtd": 100,    "mult": 10000},
    {"id": "O1", "ativo": "GLD",  "tipo": "call",   "direcao": +1, "venc_dias": 90,  "qtd": 25000,  "mult": 1},
    {"id": "O2", "ativo": "USO",  "tipo": "put",    "direcao": -1, "venc_dias": 120, "qtd": 40000,  "mult": 1},
    {"id": "O3", "ativo": "SLV",  "tipo": "call",   "direcao": -1, "venc_dias": 180, "qtd": 30000,  "mult": 1},
]

VALOR_CARTEIRA = 50_000_000


# ─── DADOS HISTÓRICOS ─────────────────────────────────────────────────────────

def carregar_dados(usar_yfinance: bool = True, n_dias: int = 504) -> pd.DataFrame:
    """Tenta yfinance; cai para GBM sintético em caso de falha."""
    tickers = list(TICKERS_INFO.keys())
    if usar_yfinance:
        try:
            import yfinance as yf
            raw = yf.download(tickers, period="2y", auto_adjust=True, progress=False)["Close"]
            if raw.empty or raw.shape[0] < 60:
                raise ValueError("Dados insuficientes")
            raw = raw.dropna(how="all").ffill().bfill()
            # Garante que só colunas conhecidas estejam presentes
            raw = raw[[c for c in tickers if c in raw.columns]]
            return raw
        except Exception:
            pass
    return _gerar_gbm(n_dias)


def _gerar_gbm(n_dias: int = 504) -> pd.DataFrame:
    """Gera séries GBM sintéticas com correlação realista entre commodities."""
    np.random.seed(2026)
    datas = pd.date_range(end=pd.Timestamp.today(), periods=n_dias, freq="B")
    # Matriz de correlação entre ativos (CL, GC, ZS, NG, GLD, USO, SLV)
    corr = np.array([
        [1.00, 0.15, 0.05, 0.35, 0.14, 0.92, 0.22],
        [0.15, 1.00, 0.08, 0.05, 0.98, 0.13, 0.75],
        [0.05, 0.08, 1.00, 0.03, 0.07, 0.04, 0.06],
        [0.35, 0.05, 0.03, 1.00, 0.04, 0.30, 0.08],
        [0.14, 0.98, 0.07, 0.04, 1.00, 0.12, 0.73],
        [0.92, 0.13, 0.04, 0.30, 0.12, 1.00, 0.20],
        [0.22, 0.75, 0.06, 0.08, 0.73, 0.20, 1.00],
    ])
    L = np.linalg.cholesky(corr)
    tickers = list(TICKERS_INFO.keys())
    vols = np.array([TICKERS_INFO[t]["vol_base"] for t in tickers])
    mu_anual = 0.06
    dt = 1 / 252
    inovacoes = np.random.standard_normal((n_dias, len(tickers)))
    inovacoes_corr = inovacoes @ L.T
    retornos = (mu_anual - 0.5 * vols**2) * dt + vols * np.sqrt(dt) * inovacoes_corr
    precos = np.zeros((n_dias, len(tickers)))
    precos[0] = [TICKERS_INFO[t]["preco_base"] for t in tickers]
    for i in range(1, n_dias):
        precos[i] = precos[i - 1] * np.exp(retornos[i])
    return pd.DataFrame(precos, index=datas, columns=tickers)


def calcular_retornos(df: pd.DataFrame) -> pd.DataFrame:
    return np.log(df / df.shift(1)).dropna()


def vol_historica_anual(retornos: pd.Series) -> float:
    return float(retornos.std() * np.sqrt(252))


# ─── BLACK-SCHOLES ────────────────────────────────────────────────────────────

def black_scholes(S: float, K: float, T: float, r: float, sigma: float, tipo: str = "call") -> float:
    if T <= 0 or sigma <= 0:
        return max(S - K, 0) if tipo == "call" else max(K - S, 0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if tipo == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


# ─── BLACK-76 ─────────────────────────────────────────────────────────────────

def black76(F: float, K: float, T: float, r: float, sigma: float, tipo: str = "call") -> float:
    if T <= 0 or sigma <= 0:
        return max(F - K, 0) if tipo == "call" else max(K - F, 0)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    e = np.exp(-r * T)
    if tipo == "call":
        return e * (F * norm.cdf(d1) - K * norm.cdf(d2))
    return e * (K * norm.cdf(-d2) - F * norm.cdf(-d1))


# ─── GREEKS ───────────────────────────────────────────────────────────────────

def greeks(S: float, K: float, T: float, r: float, sigma: float, tipo: str = "call") -> dict:
    if T <= 0 or sigma <= 0:
        return dict(delta=0, gamma=0, vega=0, theta=0, rho=0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    sgn = 1 if tipo == "call" else -1
    delta = sgn * norm.cdf(sgn * d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega  = S * np.sqrt(T) * norm.pdf(d1) / 100
    base_theta = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    if tipo == "call":
        theta = (base_theta - r * K * np.exp(-r * T) * norm.cdf(d2)) / 252
        rho   = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        theta = (base_theta + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 252
        rho   = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    return dict(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)


def vega_bs(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return 1e-10
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * np.sqrt(T) * norm.pdf(d1)


# ─── MÉTODOS NUMÉRICOS ────────────────────────────────────────────────────────

def _f(sigma, S, K, T, r, pm, tipo):
    return black_scholes(S, K, T, r, sigma, tipo) - pm


def bissecao(S, K, T, r, pm, tipo="call", tol=1e-6, max_iter=500):
    t0 = time.perf_counter()
    a, b = 1e-4, 5.0
    fa = _f(a, S, K, T, r, pm, tipo)
    fb = _f(b, S, K, T, r, pm, tipo)
    if fa * fb > 0:
        return None, 0, None, time.perf_counter() - t0
    historico = []
    for i in range(1, max_iter + 1):
        m = (a + b) / 2
        fm = _f(m, S, K, T, r, pm, tipo)
        historico.append(abs(fm))
        if abs(fm) < tol:
            break
        if fa * fm < 0:
            b = m
        else:
            a = m
            fa = fm
    return m, i, historico, time.perf_counter() - t0


def newton_raphson(S, K, T, r, pm, tipo="call", tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    sigma = 0.30
    historico = []
    for i in range(1, max_iter + 1):
        f = _f(sigma, S, K, T, r, pm, tipo)
        v = vega_bs(S, K, T, r, sigma)
        historico.append(abs(f))
        if abs(v) < 1e-10:
            return None, i, None, time.perf_counter() - t0
        sigma_new = sigma - f / v
        if sigma_new <= 0 or sigma_new > 10:
            sigma_new = sigma / 2
        if abs(sigma_new - sigma) < tol:
            sigma = sigma_new
            break
        sigma = sigma_new
    if sigma <= 0 or sigma > 10:
        return None, i, None, time.perf_counter() - t0
    return sigma, i, historico, time.perf_counter() - t0


def secante(S, K, T, r, pm, tipo="call", tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    s0, s1 = 0.20, 0.30
    historico = []
    for i in range(1, max_iter + 1):
        f0 = _f(s0, S, K, T, r, pm, tipo)
        f1 = _f(s1, S, K, T, r, pm, tipo)
        historico.append(abs(f1))
        if abs(f1 - f0) < 1e-12:
            return None, i, None, time.perf_counter() - t0
        s2 = s1 - f1 * (s1 - s0) / (f1 - f0)
        if s2 <= 0 or s2 > 10:
            return None, i, None, time.perf_counter() - t0
        if abs(s2 - s1) < tol:
            s1 = s2
            break
        s0, s1 = s1, s2
    return s1, i, historico, time.perf_counter() - t0


def brent(S, K, T, r, pm, tipo="call", tol=1e-6):
    t0 = time.perf_counter()
    cnt = [0]
    def f(s):
        cnt[0] += 1
        return _f(s, S, K, T, r, pm, tipo)
    fa, fb = f(1e-4), f(5.0)
    if fa * fb > 0:
        return None, cnt[0], None, time.perf_counter() - t0
    try:
        sigma = brentq(f, 1e-4, 5.0, xtol=tol, maxiter=500)
        err = abs(_f(sigma, S, K, T, r, pm, tipo))
        return sigma, cnt[0], [err], time.perf_counter() - t0
    except Exception:
        return None, cnt[0], None, time.perf_counter() - t0


def comparar_metodos(S, K, T, r, pm, tipo="call") -> pd.DataFrame:
    metodos = {
        "Bisseção":        bissecao(S, K, T, r, pm, tipo),
        "Newton-Raphson":  newton_raphson(S, K, T, r, pm, tipo),
        "Secante":         secante(S, K, T, r, pm, tipo),
        "Brent":           brent(S, K, T, r, pm, tipo),
    }
    rows = []
    for nome, (sigma, iters, hist, tempo) in metodos.items():
        convergiu = sigma is not None and 0 < sigma < 5
        erro = abs(_f(sigma, S, K, T, r, pm, tipo)) if convergiu else None
        rows.append({
            "Método":          nome,
            "Vol Implícita":   f"{sigma*100:.4f}%" if convergiu else "—",
            "Iterações":       iters,
            "Erro Final":      f"{erro:.2e}" if erro is not None else "—",
            "Tempo (µs)":      f"{tempo*1e6:.1f}",
            "Convergiu":       "✓" if convergiu else "✗",
            "_sigma":          sigma,
            "_hist":           hist,
        })
    return pd.DataFrame(rows)


# ─── SMILE DE VOLATILIDADE ────────────────────────────────────────────────────

def gerar_smile(S, r, T, vol_atm=0.25, n_strikes=11) -> pd.DataFrame:
    """Smile com skew negativo realista (put skew)."""
    moneyness = np.linspace(0.75, 1.25, n_strikes)
    strikes = moneyness * S
    # Skew: OTM puts mais caras, OTM calls ligeiramente mais baratas
    skew_term = -0.06 * (moneyness - 1)
    smile_term = 0.07 * (moneyness - 1) ** 2
    vols = np.clip(vol_atm + skew_term + smile_term, 0.04, 2.0)
    rows = []
    for K, vol_iv, m in zip(strikes, vols, moneyness):
        pc = black_scholes(S, K, T, r, vol_iv, "call")
        pp = black_scholes(S, K, T, r, vol_iv, "put")
        rows.append({
            "Strike": round(K, 2),
            "Moneyness": round(m, 3),
            "Preço Call": round(pc, 4),
            "Preço Put":  round(pp, 4),
            "Vol Impl. (%)": round(vol_iv * 100, 2),
        })
    return pd.DataFrame(rows)


def superficie_vol(S, r, vencimentos_dias, vol_atm=0.25, n_strikes=15):
    moneyness = np.linspace(0.75, 1.25, n_strikes)
    strikes = moneyness * S
    Z = np.zeros((len(vencimentos_dias), n_strikes))
    for i, Td in enumerate(vencimentos_dias):
        T = Td / 365
        term_str = 0.04 * np.exp(-T * 2)          # vol decai com prazo
        skew = -0.06 * (moneyness - 1)
        curv = 0.07 * (moneyness - 1) ** 2
        Z[i] = np.clip(vol_atm - term_str + skew + curv, 0.04, 2.0) * 100
    return strikes, vencimentos_dias, Z


# ─── VaR ──────────────────────────────────────────────────────────────────────

def var_historico(ret_carteira, valor, niveis=(0.95, 0.99, 0.995)):
    return {f"{n*100:.1f}%": -np.percentile(ret_carteira, (1 - n) * 100) * valor for n in niveis}


def var_parametrico(ret_carteira, valor, niveis=(0.95, 0.99, 0.995)):
    mu, sigma = ret_carteira.mean(), ret_carteira.std()
    return {f"{n*100:.1f}%": -(mu + norm.ppf(1 - n) * sigma) * valor for n in niveis}


def var_monte_carlo(S, sigma_anual, mu_anual, valor, n_sim=10_000, niveis=(0.95, 0.99, 0.995)):
    np.random.seed(42)
    dt = 1 / 252
    Z = np.random.standard_normal(n_sim)
    ST = S * np.exp((mu_anual - 0.5 * sigma_anual**2) * dt + sigma_anual * np.sqrt(dt) * Z)
    pnl = (ST / S - 1) * valor
    vars_ = {f"{n*100:.1f}%": -np.percentile(pnl, (1 - n) * 100) for n in niveis}
    return vars_, pnl


def full_valuation_var(carteira_opcoes, valor, n_sim=10_000, nivel=0.99):
    """Reprecia cada opção em cada cenário simulado."""
    np.random.seed(42)
    pnl_total = np.zeros(n_sim)
    for pos in carteira_opcoes:
        info = TICKERS_INFO[pos["ativo"]]
        S0    = info["preco_base"]
        sigma = info["vol_base"]
        T     = pos["venc_dias"] / 365
        K     = S0
        tipo  = pos["tipo"]
        sinal = pos["direcao"]
        # Cenários
        Z  = np.random.standard_normal(n_sim)
        ST = S0 * np.exp((-0.5 * sigma**2) * (1/252) + sigma * np.sqrt(1/252) * Z)
        p0 = black_scholes(S0, K, T, TAXA_RF, sigma, tipo)
        p1 = np.array([black_scholes(s, K, T - 1/252, TAXA_RF, sigma, tipo) for s in ST])
        pnl_total += sinal * pos["qtd"] * (p1 - p0)
    var_fv = -np.percentile(pnl_total, (1 - nivel) * 100)
    return var_fv, pnl_total


def expected_shortfall(ret_carteira, valor, nivel=0.99):
    threshold = np.percentile(ret_carteira, (1 - nivel) * 100)
    tail = ret_carteira[ret_carteira < threshold]
    return (-tail.mean() * valor) if len(tail) > 0 else 0.0


# ─── BACKTESTING ──────────────────────────────────────────────────────────────

def backtest_var(ret_array, valor, nivel=0.99, janela=250):
    n = len(ret_array)
    var_serie, violacao = [], []
    for i in range(janela, n):
        win = ret_array[i - janela : i]
        v = -np.percentile(win, (1 - nivel) * 100) * valor
        var_serie.append(v)
        pnl = ret_array[i] * valor
        violacao.append(int(-pnl > v))
    return np.array(var_serie), np.array(violacao)


def kupiec(N, T, p):
    if N == 0 or N == T:
        return 0.0, 1.0
    ph = N / T
    LR = -2 * np.log(
        ((1 - p) ** (T - N) * p**N) /
        ((1 - ph) ** (T - N) * ph**N)
    )
    from scipy.stats import chi2
    return float(LR), float(1 - chi2.cdf(LR, df=1))


# ─── STRESS TESTING ───────────────────────────────────────────────────────────

CENARIOS_STRESS = {
    "🌍 Recessão Global":       {"CL=F": -0.25, "GC=F": +0.15, "ZS=F": -0.10, "NG=F": -0.15, "USO": -0.22, "GLD": +0.14, "SLV": +0.05},
    "🛡️ Fuga para Segurança":    {"GC=F": +0.20, "GLD": +0.19, "SLV": +0.12, "CL=F": -0.08, "USO": -0.07},
    "💥 Choque de Oferta (Gás)": {"NG=F": +0.40, "CL=F": +0.08, "USO": +0.06},
    "🌾 Safra Recorde (Soja)":   {"ZS=F": -0.20, "CL=F": -0.03},
    "💱 Stress Brasil (BRL)":   {"GC=F": +0.08, "CL=F": +0.04, "ZS=F": -0.05, "GLD": +0.07},
    "📈 Crise de Volatilidade":  {"_vol_shock": +0.50},
    "🔗 Contágio Sistêmico":     {"_corr_shock": 0.85, "CL=F": -0.15, "GC=F": -0.05, "ZS=F": -0.12, "NG=F": -0.20},
}


def stress_carteira(carteira, cenario_choques):
    perda_total = 0.0
    detalhes = []
    vol_shock = cenario_choques.get("_vol_shock", 0)
    for pos in carteira:
        ativo  = pos["ativo"]
        info   = TICKERS_INFO[ativo]
        S0     = info["preco_base"]
        sigma0 = info["vol_base"]
        sinal  = pos["direcao"]
        qtd    = pos["qtd"]
        T      = pos["venc_dias"] / 365
        chq_p  = cenario_choques.get(ativo, 0)
        S1     = S0 * (1 + chq_p)
        sigma1 = sigma0 * (1 + vol_shock)

        if pos["tipo"] == "futuro":
            mult  = pos.get("mult", 1)
            perda = (S0 - S1) * qtd * sinal * mult / mult  # P&L normalizado
        else:
            K  = S0
            p0 = black_scholes(S0, K, T, TAXA_RF, sigma0, pos["tipo"])
            p1 = black_scholes(S1, K, T, TAXA_RF, sigma1, pos["tipo"])
            perda = (p0 - p1) * qtd * sinal

        perda_total += perda
        detalhes.append({
            "Posição": pos["id"],
            "Ativo":   f"{info['emoji']} {ativo}",
            "Tipo":    pos["tipo"].upper(),
            "Choque Preço": f"{chq_p*100:+.1f}%",
            "Perda (USD)": perda,
        })
    return perda_total, pd.DataFrame(detalhes)
