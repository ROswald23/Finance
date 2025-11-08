# app/models.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Numeric, DateTime, func, Index


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
    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[int] = mapped_column(Numeric(18, 6), nullable=True)
    performance: Mapped[float] = mapped_column(Numeric(18, 6), nullable=True)


class Portfolios(Base):
    __tablename__ = "users_portfolios"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(32), index=True, nullable=True
    )
    user: Mapped["User"] = relationship("User")


class Wallet(Base):
    __tablename__ = "wallet"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18,6), nullable=False)
    '''
    add other indicators later on
    '''
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # mets timezone=True si tu préfères
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")


class Stocks(Base):
    __tablename__ = "stocks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    wallet: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
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
    '''
    
    '''
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # mets timezone=True si tu préfères
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User")

Index("ix_wallet_user_created", Wallet.user_id, Wallet.created_at)
