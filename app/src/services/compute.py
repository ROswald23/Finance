from __future__ import annotations
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime, timedelta
import yfinance as yf
import tradingview_ta as ta
import time, pathlib
from functools import lru_cache
import streamlit as st
from sqlalchemy.testing.plugin.plugin_base import before_test

from app.db import SessionLocal

# from app.db import get_db

DATA_DIR = pathlib.Path("data_cache")
DATA_DIR.mkdir(exist_ok=True)

N_TRADING = 252
RF_ANN_DEFAULT = 0.02

INDEX_TICKERS = {
    # 🇺🇸 USA
    "S&P 500": {"index": "^GSPC", "etf": "SPY"},
    "Dow Jones 30": {"index": "^DJI", "etf": "DIA"},
    "Nasdaq Composite": {"index": "^IXIC", "etf": "ONEQ"},
    "Nasdaq 100": {"index": "^NDX", "etf": "QQQ"},
    "Russell 1000": {"index": "^RUI", "etf": "IWB"},
    "Russell 2000": {"index": "^RUT", "etf": "IWM"},
    "Russell 3000": {"index": "^RUA", "etf": "IWV"},

    # 🇨🇦 Canada
    "S&P/TSX Composite": {"index": "^GSPTSE", "etf": "XIC.TO"},  # composite broad
    "S&P/TSX 60": {"index": "^TX60", "etf": "XIU.TO"},

    # 🇬🇧 UK
    "FTSE 100": {"index": "^FTSE", "etf": "VUKE.L"},
    "FTSE 250": {"index": "^FTMC", "etf": "VMID.L"},

    # 🇫🇷 France
    "CAC 40": {"index": "^FCHI", "etf": "CAC.PA"},  # Amundi/Lyxor CAC 40
    "CAC Next 20": {"index": "^CN20", "etf": None},  # proxy ETF à compléter selon broker
    "SBF 120": {"index": "^SBF120", "etf": None},

    # 🇩🇪 Allemagne
    "DAX 40": {"index": "^GDAXI", "etf": "EXS1.DE"},  # iShares DAX (EXS1)
    "MDAX": {"index": "^MDAXI", "etf": None},
    "SDAX": {"index": "^SDAXI", "etf": None},

    # 🇪🇺 Europe
    "EURO STOXX 50": {"index": "^STOXX50E", "etf": "EXW1.DE"},  # iShares EURO STOXX 50
    "STOXX Europe 600": {"index": "^STOXX", "etf": "EXSA.DE"},

    # 🇮🇹 Italie
    "FTSE MIB": {"index": "FTSEMIB.MI", "etf": "EUNM.MI"},  # iShares FTSE MIB (EUNM)

    # 🇪🇸 Espagne
    "IBEX 35": {"index": "^IBEX", "etf": None},  # ex: Xtrackers/Amundi selon place

    # 🇳🇱 Pays-Bas
    "AEX 25": {"index": "^AEX", "etf": "IAEX.AS"},

    # 🇧🇪 Belgique
    "BEL 20": {"index": "^BFX", "etf": None},

    # 🇨🇭 Suisse
    "SMI": {"index": "^SSMI", "etf": "CSSMI.SW"},

    # 🇦🇹 Autriche
    "ATX": {"index": "^ATX", "etf": None},

    # 🇵🇹 Portugal
    "PSI": {"index": "^PSI20", "etf": None},

    # 🇸🇪🇩🇰🇫🇮 Nordics
    "OMX Stockholm 30": {"index": "^OMXS30", "etf": "XACTOMX.ST"},  # XACT OMXS30
    "OMX Copenhagen 25": {"index": "^OMXC25", "etf": None},
    "OMX Helsinki 25": {"index": "^OMXH25", "etf": None},

    # Asie-Pacifique
    "Nikkei 225": {"index": "^N225", "etf": "1321.T"},  # Nikkei ETF (TSE)
    "TOPIX": {"index": "^TOPX", "etf": "1306.T"},  # TOPIX ETF
    "Hang Seng": {"index": "^HSI", "etf": "2800.HK"},
    "Shanghai Composite": {"index": "^SSEC", "etf": None},
    "Shenzhen Component": {"index": "^SZSC", "etf": None},
    "CSI 300": {"index": "000300.SS", "etf": "3188.HK"},  # CSOP CSI 300
    "KOSPI": {"index": "^KS11", "etf": None},
    "Nifty 50": {"index": "^NSEI", "etf": "NIFTYBEES.NS"},
    "Sensex 30": {"index": "^BSESN", "etf": None},
    "ASX 200": {"index": "^AXJO", "etf": "IOZ.AX"},
    "Straits Times": {"index": "^STI", "etf": "ES3.SI"},

    # Amérique latine
    "Ibovespa (Brazil)": {"index": "^BVSP", "etf": "BOVA11.SA"},
    "IPC (Mexico)": {"index": "^MXX", "etf": None},
    "MERVAL (Argentina)": {"index": "^MERV", "etf": None},
    "IPSA (Chile)": {"index": "^IPSA", "etf": None},
}

EXCHANGE_TO_BENCH = {
    "NasdaqGS": INDEX_TICKERS["Nasdaq 100"],
    "NasdaqCM": INDEX_TICKERS["Nasdaq Composite"],
    "Nasdaq": INDEX_TICKERS["Nasdaq Composite"],
    "NMS": INDEX_TICKERS["Nasdaq Composite"],
    "NYSE": INDEX_TICKERS["S&P 500"],
    "ARCA": INDEX_TICKERS["S&P 500"],
    "Euronext Paris": INDEX_TICKERS["CAC 40"],
    "XPAR": INDEX_TICKERS["CAC 40"],
    "EPA": INDEX_TICKERS["CAC 40"],
    "Paris": INDEX_TICKERS["CAC 40"],
    "XETRA": INDEX_TICKERS["DAX 40"],
    "FWB": INDEX_TICKERS["DAX 40"],
    "LSE": INDEX_TICKERS["FTSE 100"],
    "London": INDEX_TICKERS["FTSE 100"],
    "Toronto": INDEX_TICKERS["S&P/TSX Composite"],
    "TSX": INDEX_TICKERS["S&P/TSX Composite"],
    "EBS": INDEX_TICKERS["SMI"],
    "SWX": INDEX_TICKERS["SMI"],

    # Canada
    "TSXV": INDEX_TICKERS["S&P/TSX Composite"],

    # Italie
    "Milan": INDEX_TICKERS["FTSE MIB"],
    "Borsa Italiana": INDEX_TICKERS["FTSE MIB"],

    # Espagne
    "Madrid": INDEX_TICKERS["IBEX 35"],
    "BME": INDEX_TICKERS["IBEX 35"],

    # Suisse
    "SIX Swiss Exchange": INDEX_TICKERS["SMI"],

    # Benelux
    "Amsterdam": INDEX_TICKERS["AEX 25"],
    "Brussels": INDEX_TICKERS["BEL 20"],

    # Nordics (Euronext / Nasdaq Nordic)
    "Stockholm": INDEX_TICKERS["OMX Stockholm 30"],
    "Copenhagen": INDEX_TICKERS["OMX Copenhagen 25"],
    "Helsinki": INDEX_TICKERS["OMX Helsinki 25"],

    # Autriche / Portugal
    "Vienna": INDEX_TICKERS["ATX"],
    "Lisbon": INDEX_TICKERS["PSI"],

    # Asie-Pacifique
    "Tokyo": INDEX_TICKERS["TOPIX"],  # ou Nikkei 225 selon préférence
    "TSE": INDEX_TICKERS["TOPIX"],
    "Hong Kong": INDEX_TICKERS["Hang Seng"],
    "HKSE": INDEX_TICKERS["Hang Seng"],
    "Shanghai": INDEX_TICKERS["Shanghai Composite"],
    "Shenzhen": INDEX_TICKERS["Shenzhen Component"],
    "Korea": INDEX_TICKERS["KOSPI"],
    "KOSDAQ": INDEX_TICKERS["KOSPI"],
    "ASX": INDEX_TICKERS["ASX 200"],
    "Singapore": INDEX_TICKERS["Straits Times"],
    "NSE": INDEX_TICKERS["Nifty 50"],
    "BSE": INDEX_TICKERS["Sensex 30"],

    # Amérique latine
    "B3": INDEX_TICKERS["Ibovespa (Brazil)"],  # B3 (Brasil Bolsa Balcão)
    "Mexican Stock Exchange": INDEX_TICKERS["IPC (Mexico)"],
    "Buenos Aires": INDEX_TICKERS["MERVAL (Argentina)"],
    "Santiago": INDEX_TICKERS["IPSA (Chile)"],
}

SUFFIX_TO_BENCH = {
    "PA": INDEX_TICKERS["CAC 40"],  # France
    "DE": INDEX_TICKERS["DAX 40"],  # Allemagne
    "MI": INDEX_TICKERS["FTSE MIB"],  # Italie
    "AS": INDEX_TICKERS["AEX 25"],  # Pays-Bas
    "BR": INDEX_TICKERS["BEL 20"],  # Belgique
    "SW": INDEX_TICKERS["SMI"],  # Suisse
    "LS": INDEX_TICKERS["PSI"],  # Portugal
    "ST": INDEX_TICKERS["OMX Stockholm 30"],  # Suède
    "CO": INDEX_TICKERS["OMX Copenhagen 25"],  # Danemark
    "HE": INDEX_TICKERS["OMX Helsinki 25"],  # Finlande
    "L": INDEX_TICKERS["FTSE 100"],  # UK
    "T": INDEX_TICKERS["Nikkei 225"],  # Japon
    "HK": INDEX_TICKERS["Hang Seng"],  # Hong Kong
    "SS": INDEX_TICKERS["Shanghai Composite"],  # Chine (Shanghai)
    "SZ": INDEX_TICKERS["Shenzhen Component"],  # Chine (Shenzhen)
    "KS": INDEX_TICKERS["KOSPI"],  # Corée du Sud
    "AX": INDEX_TICKERS["ASX 200"],  # Australie
    "SI": INDEX_TICKERS["Straits Times"],  # Singapour
    "TO": INDEX_TICKERS["S&P/TSX Composite"],  # Canada
    "SA": INDEX_TICKERS["Ibovespa (Brazil)"],  # Brésil
    "MX": INDEX_TICKERS["IPC (Mexico)"],  # Mexique
}

suffix_map = {
            "PA": INDEX_TICKERS["CAC 40"],  # France
            "DE": INDEX_TICKERS["DAX 40"],  # Allemagne
            "MI": INDEX_TICKERS["FTSE MIB"],  # Italie
            "AS": INDEX_TICKERS["AEX 25"],  # Pays-Bas
            "BR": INDEX_TICKERS["BEL 20"],  # Belgique
            "SW": INDEX_TICKERS["SMI"],  # Suisse
            "LS": INDEX_TICKERS["PSI"],  # Portugal
            "ST": INDEX_TICKERS["OMX Stockholm 30"],  # Suède
            "CO": INDEX_TICKERS["OMX Copenhagen 25"],  # Danemark
            "HE": INDEX_TICKERS["OMX Helsinki 25"],  # Finlande
            "L": INDEX_TICKERS["FTSE 100"],  # UK
            "T": INDEX_TICKERS["Nikkei 225"],  # Japon
            "HK": INDEX_TICKERS["Hang Seng"],  # Hong Kong
            "SS": INDEX_TICKERS["Shanghai Composite"],  # Chine (Shanghai)
            "SZ": INDEX_TICKERS["Shenzhen Component"],  # Chine (Shenzhen)
            "KS": INDEX_TICKERS["KOSPI"],  # Corée du Sud
            "AX": INDEX_TICKERS["ASX 200"],  # Australie
            "SI": INDEX_TICKERS["Straits Times"],  # Singapour
            "TO": INDEX_TICKERS["S&P/TSX Composite"],  # Canada
            "SA": INDEX_TICKERS["Ibovespa (Brazil)"],  # Brésil
            "MX": INDEX_TICKERS["IPC (Mexico)"],  # Mexique
        }


# ---------- Cache disque : download + sauvegarde parquet ----------
def _cache_path(ticker: str) -> pathlib.Path:
    return DATA_DIR / f"{ticker.upper()}_history.parquet"



# --- acces info ---
@lru_cache(maxsize=256)
def _yf_ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker)

@lru_cache(maxsize=256)
def _history_close(ticker: str, period: str = "10y", auto_adjust: bool = True) -> pd.Series:
    hist = _yf_ticker(ticker).history(period=period, auto_adjust=auto_adjust)
    if hist.empty or "Close" not in hist.columns:
        return pd.Series(dtype=float)
    return hist["Close"].rename(ticker)

@lru_cache(maxsize=512)
def _dividends(ticker: str) -> pd.Series:
    div = _yf_ticker(ticker).dividends
    return div if isinstance(div, pd.Series) else pd.Series(dtype=float)


def ticker_benchmark(ticker: str)-> dict:
    ticker = ticker.upper().strip()
    try:
        exchange = ticker_market(ticker)
    except Exception:
        exchange = None
    if exchange in EXCHANGE_TO_BENCH:
        return EXCHANGE_TO_BENCH[exchange]
    if "." in ticker:
        suffix = ticker.split(".")[-1]
        if suffix in suffix_map:
            return suffix_map[suffix]
    # Fallback
    return INDEX_TICKERS["S&P 500"]


# --- market ---
def ticker_market(ticker: str) -> str:
    t = _yf_ticker(ticker)
    exchange = None
    try:
        fi = t.fast_info
        exchange = getattr(fi, "exchange", None) or fi.get("exchange")
    except Exception:
        pass
    if exchange is None:
        try:
            info = t.get_info()
            exchange = exchange or info.get("fullExchangeName") or info.get("exchange")
        except Exception:
            pass
    return exchange


# --- download full history ---
def ticker_max_history(ticker: str, max_age_hours: int = 24) -> pd.DataFrame:
    """
    - Utilise un cache Parquet local
    - Rafraîchit si fichier > max_age_hours
    """
    p = _cache_path(ticker)
    now = time.time()
    if p.exists() and (now - p.stat().st_mtime) < max_age_hours * 3600:
        df = pd.read_parquet(p)
    else:
        df = _yf_ticker(ticker).history(period="max")
        if df.empty:
            return df
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        keep = [c for c in ["Date","Open","High","Low","Close","Adj Close","Volume"] if c in df.columns]
        df = df[keep]
        df.to_parquet(p, index=False)
    return df

def _yrl_history(ticker: str) -> pd.DataFrame:
    p = _cache_path(ticker)
    now = pd.Timestamp.now(tz="America/New_York")
    start = now - pd.Timedelta(days=252)
    if p.exists():
        df = pd.read_parquet(p)
        # df.mask((df['Date'] >= now) & (df['Date'] <= start))
    else:
        df = _yf_ticker(ticker).history(period="1y", interval="1d")
        if df.empty:
            return df
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        keep = [c for c in ["Date","Open","High","Low","Close","Volume"] if c in df.columns]
        df = df[keep]
        df.to_parquet(p, index=False)
    return df


# --- indicators ----
def ticker_indicators(ticker: str, p = 0.05, n = 14, rf_ann = 0.02) -> dict:
    ticker_eve_price: float
    t = _yf_ticker(ticker)
    fi = t.fast_info

    # fundamentals
    fin_q = safe_df(t.quarterly_income_stmt)
    fin_a = safe_df(t.financials)
    bs_q = safe_df(t.quarterly_balance_sheet)
    bs_a = safe_df(t.balance_sheet)
    cf_q = safe_df(t.quarterly_cashflow)
    cf_a = safe_df(t.cashflow)

    # --- status ---
    long_name: str = t.info['longName']
    ticker_price: int = getattr(fi, "last_price", None)
    ticker_eve_price = fi.get("previous_close")
    market = ticker_benchmark(ticker)['index']
    print("market", market)
    market_ticker = ticker_market(ticker)
    print("market ticker", market_ticker)
    epss = t.income_stmt.loc['Diluted EPS', :].iloc[0]
    sector = t.info.get("sector")
    industry = t.info.get("industry")
    classe = t.info.get("quoteType")
    print("type: ", classe)
    payout_ratio = t.info["payoutRatio"]
    shares_outstanding = t.info['sharesOutstanding']
    market_cap = t.info.get("marketCap", None)
    eps_ttm = t.info.get("trailingEps", None)

    if ticker_eve_price is None:
        try:
            # hist = t.history(period="10d", interval="1d", auto_adjust=False)
            hist = _yrl_history(ticker)
            if not hist.empty:
                ticker_eve_price = hist["Close"].iloc[-2]
        except Exception:
            pass

    ticker_performance = (ticker_eve_price - ticker_price) / ticker_eve_price

    # --- dividends ---
    dividends = t.dividends
    if dividends is None or dividends.empty:
        hist = t.history(period="10y", auto_adjust=False)
        dividends = hist["Dividends"]
    div_ttm = trailing_12m_dividend(dividends)
    dividend_yield = (div_ttm / ticker_price) if (div_ttm and ticker_price) else None

    # FCF TTM (fallback annuel
    financial_cash_flow_ttm = None
    fcf_ttm = ttm_sum(cf_q, "Free Cash Flow")
    if np.isnan(fcf_ttm) and not (cf_a is None or cf_a.empty) and "Free Cash Flow" in cf_a.index:
        financial_cash_flow_ttm = float(cf_a.loc["Free Cash Flow"].iloc[0])

    # Net Income TTM
    ni_ttm = ttm_sum(fin_q, "Net Income")
    if np.isnan(ni_ttm) and not (fin_a is None or fin_a.empty) and "Net Income" in fin_a.index:
        ni_ttm = float(fin_a.loc["Net Income"].iloc[0])

    # Equity (dernier bilan)
    equity = None
    if not (bs_a is None or bs_a.empty) and "Stockholders Equity" in bs_a.index:
        equity = float(bs_a.loc["Stockholders Equity"].iloc[0])
    elif not (bs_q is None or bs_q.empty) and "Stockholders Equity" in bs_q.index:
        equity = float(bs_q.loc["Stockholders Equity"].iloc[0])

    # ROE ≈ NI_TTM / Equity
    roe = (ni_ttm / equity) if (not np.isnan(ni_ttm) and not np.isnan(equity) and equity != 0) else None

    # P/E (trailing)
    pe = t.info.get("trailingPE", None)
    if (not pe) and (eps_ttm and eps_ttm != 0):
        pe = ticker_price / eps_ttm

    # P/CF (par action) -> Price / (FCF/share)
    price_to_cash_flow_ratio = None
    if (not np.isnan(fcf_ttm)) and (not np.isnan(shares_outstanding)) and shares_outstanding > 0:
        fcf_per_share = fcf_ttm / shares_outstanding
        if fcf_per_share != 0:
            price_to_cash_flow_ratio = ticker_price / fcf_per_share

    # Earnings yield (utile pour duration)
    earning_yield = earnings_yield_from_info(t.info, ticker_price)

    # FCF yield = FCF / MarketCap
    financial_cash_flow_yield = (fcf_ttm / market_cap) if (
            not np.isnan(fcf_ttm) and not np.isnan(market_cap) and market_cap > 0) else None

    # --- dataframe element ---
    ticker_df = _yrl_history(ticker)
    close = ticker_df["Close"]
    market_df = _yrl_history(market)
    market_close = market_df["Close"]

    # ---- performance ----
    ebitda = t.income_stmt.loc['EBITDA', :].iloc[0]

    ticker_total_return = close.iloc[-1] / close.iloc[0] - 1
    market_returns =  market_close.iloc[-1] / market_close.iloc[0] - 1
    price_earning_ratio = ticker_price / epss
    book_value = t.info['bookValue']
    price_to_book_ratio =ticker_price / book_value
    ticker_return = close.pct_change()
    market_return = market_close.pct_change()
    ticker_log_return = np.log(close).diff()

    # --- volatility ---
    common = ticker_return.dropna().index.intersection(market_return.dropna().index)
    ticker_series = ticker_return.loc[common]
    market_series = market_return.loc[common]
    annual_volatility = ticker_return.rolling(window=20).std().iloc[-1] * np.sqrt(N_TRADING) * 100

    # --- drawdown ---
    px_1y = close.iloc[-N_TRADING:]
    cummax = px_1y.cummax()
    drawdown = px_1y / cummax - 1.0
    drawdown = drawdown.min() * 100

    # --- var ---
    var95 = np.percentile(ticker_return.dropna(), 100 * p) * 100
    cvar95 = ticker_return[ticker_return <= np.percentile(ticker_return.dropna(), 100 * p)].mean() * 100

    # --- RSI ---
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi14 = 100 - (100 / (1 + rs))
    rsi = rsi14.iloc[-1]

    # --- beta ---
    x = np.vstack([np.ones(len(market_series)), market_series.values]).T  # [const, marché]
    y = ticker_series.values
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    daily_alpha, ticker_beta_1y = beta[0], beta[1]

    # R²
    y_hat = x @ beta
    ss_res = ((y - y_hat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2_1y = 1 - ss_res / ss_tot

    # Annual alpha
    alpha_1y_pct = ((1 + daily_alpha) ** N_TRADING - 1) * 100

    # tracking error & info ratio
    active = ticker_series - market_series
    te_1y = active.std() * np.sqrt(N_TRADING) * 100  # en %

    # Information Ratio = (Perf ann relative) / TE
    rel_ann = ((1 + ticker_series.mean()) ** N_TRADING - 1) - ((1 + market_series.mean()) ** N_TRADING - 1)
    ir_1y = rel_ann / (te_1y / 100) if te_1y != 0 else None

    # treynor
    er_ann = (1 + ticker_series.mean()) ** N_TRADING - 1
    treynor = (er_ann - rf_ann) / ticker_beta_1y if ticker_beta_1y != 0 else None

    # sharpe ratio
    rf_daily = (1 + rf_ann) ** (1 / N_TRADING) - 1
    excess = market_series - rf_daily
    sharpe_1y = (excess.mean() / excess.std()) * np.sqrt(N_TRADING)

    # sortino
    neg = excess.copy()
    neg[neg > 0] = 0
    semidev = np.sqrt((neg ** 2).mean())
    sortino_1y = (excess.mean() * np.sqrt(N_TRADING)) / semidev if semidev != 0 else None

    # expected return
    market_annual = (1 + market_series.mean()) ** N_TRADING - 1
    expected_return_capm = rf_ann + ticker_beta_1y * (market_annual - rf_ann)
    g_sgr = estimate_g_sgr(roe, payout_ratio)

    # Duration proxies
    duration_div = equity_duration_proxy(dividend_yield, g_sgr)
    duration_fcf = equity_duration_proxy(financial_cash_flow_yield, g_sgr)
    duration_earning = equity_duration_proxy(earning_yield, g_sgr)

    # 3) Sensibilité aux taux (rate beta)
    beta_rate = rate_beta_10y(ticker, market)

    # yield
    df = ticker_df.copy()
    df["return"] = df['Close'].pct_change()
    df["log_return"] = np.log1p(df["return"])
    df = df.dropna(subset=["return", "log_return"])

    n_years = (df["Date"].iloc[-1] - df["Date"].iloc[0]).days / 365.25
    growth_rate = (1 + ticker_total_return) ** (1 / n_years) - 1 if n_years > 0 else None

    volatility_daily = df["log_return"].std(ddof=1)
    volalitity_annual = volatility_daily * np.sqrt(N_TRADING) if pd.notna(volatility_daily) else np.nan

    return {
                "Full Name": long_name,
                "sector": sector,
                "industry": industry,
                "type": classe,
                "Price": round(ticker_price,2),
                "Ticker eve price": round(ticker_eve_price,2),
                "Ticker performance": round(ticker_performance*100,2),
                "market": market,
                "Benchmark": market_ticker,
                "eps": epss,
                "payout ratio": payout_ratio,

                "ebitda": ebitda,
                "shares outstanding": shares_outstanding,
                "ticker total return": round(ticker_total_return,4),
                "market return": round(market_returns,4),
                "price earning ratio": round(price_earning_ratio,2),
                "book value": book_value,
                "price to book ratio": round(price_to_book_ratio,2),


                "expected return": round(expected_return_capm,4),
                "cagr": round(growth_rate,4),
                "roe" : round(roe*100,2),
                "dividend yield": dividend_yield,
                "financial cash flow": financial_cash_flow_ttm,
                "Price to Cash Flow Ratio": price_to_cash_flow_ratio,
                "earning yield": round(earning_yield*100,2),
                "financial cash flow yield": financial_cash_flow_yield,
                "duration dividends": duration_div,
                "duration financial cash flow": duration_fcf,
                "duration earning": duration_earning,
                "market sensibility": beta_rate,

                "annual volatility": volalitity_annual,
                "daily volatility": volatility_daily,
                "drawdown": drawdown,
                "var95": var95,
                "cvar95": cvar95,
                "rsi": rsi,
                "daily alpha": daily_alpha,
                "ticker beta 1year": ticker_beta_1y,
                "R²": r2_1y,
                "alpha 1year percent": alpha_1y_pct,
                "tracking error": te_1y,
                "information ratio": ir_1y,
                "treynor": treynor,
                "sharpe ratio": sharpe_1y,
                "sortino": sortino_1y,
    }


def ttm_sum(df: pd.DataFrame, row_name: str) -> float:
    if isinstance(df, pd.DataFrame) and not df.empty and row_name in df.index:
        return float(df.loc[row_name].iloc[:4].sum())  # quarterly: 4 derniers trimestres
    return np.nan

def safe_df(obj) -> pd.DataFrame:
    if obj is None:
        return pd.DataFrame()
    if isinstance(obj, pd.DataFrame) and not obj.empty:
        return obj
    return pd.DataFrame()

def earnings_yield_from_info(info: dict, price: float):
    pe_trailing = info.get("trailingPE")
    eps_ttm = info.get("trailingEps")
    if pe_trailing and pe_trailing > 0:
        return 1.0 / pe_trailing
    if eps_ttm and price:
        return eps_ttm / price
    return None

def trailing_12m_dividend(div: pd.Series) -> float:
    if div is None or div.empty:
        return np.nan
    last = div.index.max()
    return float(div[div.index > last - pd.Timedelta(days=365)].sum())

def estimate_g_sgr(roe: float, payout_ratio_cash: float):
    if (roe is None) or (payout_ratio_cash is None) or np.isnan(roe) or np.isnan(payout_ratio_cash):
        return np.nan
    return roe * (1 - payout_ratio_cash)

def equity_duration_proxy(yield_value: float, g: float):
    if (yield_value is None) or (g is None) or np.isnan(yield_value) or np.isnan(g):
        return None
    if yield_value <= g:
        return '+Inf'
    return 1.0 / (yield_value - g)

def compute_beta_alpha(xr: pd.Series, xm: pd.Series):
    # OLS: r_stock = a + b * r_mkt
    idx = xr.dropna().index.intersection(xm.dropna().index)
    y = xr.loc[idx].values
    X = np.vstack([np.ones(len(idx)), xm.loc[idx].values]).T
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]
    y_hat = X @ np.array([a, b])
    r2 = 1 - ((y - y_hat)**2).sum() / ((y - y.mean())**2).sum()
    return a, b, r2

def rate_beta_10y(ticker: str, market: str) -> float:
    y10 = _history_close(market)
    stock_ret = _history_close(ticker)
    y10 = y10 / 100.0
    # stock_ret = stock_ret.diff()
    dy = y10.diff()
    idx = stock_ret.dropna().index.intersection(dy.dropna().index)
    print('data idx', idx)
    if len(idx) < 60:
        print('lenght market', len(idx))
        return None
    X = np.vstack([np.ones(len(idx)), dy.loc[idx].values]).T
    y = stock_ret.loc[idx].values
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]
    return b

def convert_numpy_types(obj):
    """Convertit les types numpy en types Python natifs pour la sérialisation JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def indexes_metrics(indexes: list) -> list:
    """Calcule les métriques (prix et performance) pour chaque ticker"""
    results = []

    for ticker in indexes:
        try:
            # Récupération du prix actuel
            price = _yf_ticker(ticker).fast_info.last_price
            eve_price = None
            performance = None

            # Récupération du prix de veille
            try:
                hist = _yrl_history(ticker)
                if not hist.empty:
                    eve_price = hist["Close"].iloc[-2]
                    # Calcul de la performance
                    if eve_price and eve_price != 0:
                        performance = ((price - eve_price) / eve_price) * 100


            except Exception:
                pass
            # convert_numpy_types(performance)
            # convert_numpy_types(price)
            results.append({
                "ticker": ticker,
                "price": float(price),
                "performance": float(performance)
            })

        except Exception as e:
            # En cas d'erreur sur un ticker, on l'ajoute quand même avec des valeurs None
            results.append({
                "ticker": ticker,
                "price": None,
                "performance": None
            })
    return results


def get_indexes_list() -> list:
    """Récupère la liste des tickers depuis la base de données"""
    db = SessionLocal()  # Créer directement une session
    try:
        rows = db.execute(text("SELECT ticker FROM indexes;")).mappings().fetchall()
        return [row['ticker'] for row in rows if row['ticker']]
    finally:
        db.close()


def update_indexes_metrics(metrics: list):
    db = SessionLocal()
    try:
        # Mettre à jour
        for metric in metrics:
            if metric["price"] is not None:
                db.execute(
                    text("""
                        UPDATE indexes 
                        SET price = :price, 
                            performance = :performance
                        WHERE ticker = :ticker
                    """),
                    metric
                )

        db.commit()
        print("✅ Base de données mise à jour avec succès!")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
    finally:
        db.close()



# a = ticker_indicators("BTC-EUR", 0.05,  14,  0.02)
# # a
# print(a)
