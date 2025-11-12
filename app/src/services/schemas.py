# app/schemas.py
import pandas as pd
# from compute import ticker_full_mane, ticker_market, ticker_performance
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from typing import List

# ---- Auth ----
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ---- Users ----
class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# ---- Wallet ----
class WalletRowOut(BaseModel):
    id: int
    ticker: str
    quantity: float
    created_at: str

class WalletCreateIn(BaseModel):
    ticker: str
    quantity: float

class RefreshIn(BaseModel):
    token: str

# ---- Indexes ----
class Indice(BaseModel):
    ticker: str
    full_name: str
    price: int
    performance: float

class TickerResponse(BaseModel):
    """Modèle de réponse pour les indicateurs d'un ticker"""
    ticker: str
    timestamp: str
    data: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Modèle de réponse d'erreur"""
    error: str
    detail: Optional[str] = None

class Stocks(BaseModel):
    # --- state ---
    long_name: str
    ticker: str
    price: int
    eve_price: int
    market: str
    benchmark: str
    performance: int
    # dataframe: pd.DataFrame
    eps: int
    sector: str
    industry: str
    type: str

    # --- performance ---
    total_return: int
    market_return: int
    market_annual_return: int
    expected_return_capm: int
    shares_outstanding: int
    yld: int
    cagr: int
    ebitda: int
    pe_ratio: int
    book_value: int
    pb_ratio: int
    return_: int
    roe: int
    fin_cash_flow_yield: int
    duration_dividend: int
    duration_fin_cash_flow: int
    duration_earnings: str

    # --- risk ---
    rsi: int
    daily_risk: int
    annual_risk: int
    max_drawdown: int
    var95: int
    cVar95: int
    annual_volatility: int
    beta_1y: int
    daily_alpha: int
    alpha_1y_pct: int
    R_square_1y: int
    Tracking_Error_1y: int
    IR_1y: int
    treynor: int
    sharpe_1y: int
    sortino_1y: int

# pyarrow, fastparquet