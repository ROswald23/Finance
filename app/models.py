# app/models.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from xmlrpc.client import Boolean

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, ForeignKey, Numeric, DateTime, func, Index


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    surname: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    principal: Mapped[int] = mapped_column(Numeric(18,6), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class Indexes(Base):
    __tablename__ = "indexes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    performance: Mapped[float] = mapped_column(Numeric(18, 6), nullable=True)


class Portfolios(Base):
    __tablename__ = "users_portfolios"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(32), index=True, nullable=True
    )
    principal : Mapped[int] = mapped_column(Numeric(18,6), nullable=True)
    user: Mapped["User"] = relationship("User")


class Wallet(Base):
    __tablename__ = "wallet"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18,6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # mets timezone=True si tu préfères
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    wallet: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")


class Stocks(Base):
    __tablename__ = "stocks"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    wallet: Mapped[str] = mapped_column(String(32), nullable=True)
    full_name: Mapped[str] = mapped_column(String(32),  nullable=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    sector: Mapped[str] = mapped_column(String(32), nullable=True)
    industry: Mapped[str] = mapped_column(String(32),  nullable=True)
    type: Mapped[str] = mapped_column(String(32),  nullable=True)
    market: Mapped[str] = mapped_column(String(32),  nullable=True)
    benchmark: Mapped[str] = mapped_column(String(32), nullable=True)
    weight: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    price: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    rate: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    principal: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    market_worth: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=True)
    price_at_buy: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    rate_at_buy: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    principal_at_buy: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    yld: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    eve_price: Mapped[int] = mapped_column(Numeric(), nullable=True)
    performance: Mapped[int] = mapped_column(Numeric(), nullable=True)
    eps: Mapped[int] = mapped_column(Numeric(), nullable=True)
    total_return: Mapped[int] = mapped_column(Numeric(), nullable=True)
    market_return: Mapped[int] = mapped_column(Numeric(), nullable=True)
    market_annual_return: Mapped[int] = mapped_column(Numeric(), nullable=True)
    expected_return_capm: Mapped[int] = mapped_column(Numeric(), nullable=True)
    shares_outstanding: Mapped[int] = mapped_column(Numeric(), nullable=True)
    cagr: Mapped[int] = mapped_column(Numeric(), nullable=True)
    ebitda: Mapped[int] = mapped_column(Numeric(), nullable=True)
    pe_ratio: Mapped[int] = mapped_column(Numeric(), nullable=True)
    book_value: Mapped[int] = mapped_column(Numeric(), nullable=True)
    pb_ratio: Mapped[int] = mapped_column(Numeric(), nullable=True)
    return_: Mapped[int] = mapped_column(Numeric(), nullable=True)
    roe: Mapped[int] = mapped_column(Numeric(), nullable=True)
    fin_cash_flow_yield: Mapped[int] = mapped_column(Numeric(), nullable=True)
    duration_dividend: Mapped[str] = mapped_column(String(32), nullable=True)
    duration_fin_cash_flow: Mapped[str] = mapped_column(String(32), nullable=True)
    duration_earnings: Mapped[str] = mapped_column(String(32), nullable=True)
    rsi: Mapped[int] = mapped_column(Numeric(), nullable=True)
    daily_risk: Mapped[int] = mapped_column(Numeric(), nullable=True)
    annual_risk: Mapped[int] = mapped_column(Numeric(), nullable=True)
    max_drawdown: Mapped[int] = mapped_column(Numeric(), nullable=True)
    var95: Mapped[int] = mapped_column(Numeric(), nullable=True)
    cVar95: Mapped[int] = mapped_column(Numeric(), nullable=True)
    annual_volatility: Mapped[int] = mapped_column(Numeric(), nullable=True)
    beta_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    daily_alpha: Mapped[int] = mapped_column(Numeric(), nullable=True)
    alpha_1y_pct: Mapped[int] = mapped_column(Numeric(), nullable=True)
    R_square_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    Tracking_Error_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    IR_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    treynor: Mapped[int] = mapped_column(Numeric(), nullable=True)
    sharpe_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    sortino_1y: Mapped[int] = mapped_column(Numeric(), nullable=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    soldout: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # mets timezone=True si tu préfères
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")

Index("ix_wallet_user_created", Wallet.user_id, Wallet.created_at)
