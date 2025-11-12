# app/main.py uvicorn app.main:app --reload
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import get_db
from app.src.services.schemas import RegisterIn, LoginIn, TokenOut, UserOut, WalletRowOut, WalletCreateIn, Indice, \
    TickerResponse, ErrorResponse, Balance, Favorite, PortfolioFlow, BalanceIn
from app.security import hash_password, verify_password, create_token_pair, decode_token
from app.deps import get_current_user, CurrentUser
from app.src.services.schemas import RefreshIn
from app.src.services.compute import ticker_indicators, convert_numpy_types, get_indexes_list, indexes_metrics, \
    update_indexes_metrics
# connexion frontend
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stock Analysis API",
            description="My first API for stock analysis",
            version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["*"] en dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----point entry----
@app.get("/")
def root():
    return {
        "message": "Stock Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/ticker/{ticker}": "Obtenir les indicateurs pour un ticker",
            "/docs": "Documentation interactive"
        }
    }


# ---------- Auth ----------
@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    # email unique ?
    exists = db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": body.email}).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    # insertion avec hash direct
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    db.execute(
        text(
            "INSERT INTO users (email, password_hash, name, surname) "
            "VALUES (:e, :p, :fn, :ln)"
        ),
        {"e": body.email, "p": hash_password(body.password), "fn": first_name, "ln": last_name},
    )
    user_row = db.execute(
        text("SELECT id, email, name, surname FROM users WHERE email = :e"),
        {"e": body.email},
    ).mappings().one()
    db.commit()
    return UserOut(**user_row)


@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, password_hash FROM users WHERE email = :e"),
        {"e": body.email},
    ).first()
    if not row or not verify_password(body.password, row.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")
    # 🔁 migration transparente vers bcrypt_sha256 si besoin
    from app.security import needs_rehash, hash_password
    if needs_rehash(row.password_hash):
        new_hash = hash_password(body.password)
        db.execute(
            text("UPDATE users SET password_hash = :p WHERE id = :i"),
            {"p": new_hash, "i": row.id},
        )
        db.commit()
    access, refresh = create_token_pair(row.id)
    print('access', access)
    return TokenOut(access_token=access, refresh_token=refresh)


@app.post("/auth/refresh", response_model=TokenOut)
def refresh(body: RefreshIn):
    """
    Attendez du frontend: { "token": "<refresh_token>" }
    """
    try:
        payload = decode_token(body.token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user_id = int(payload.get("sub"))
    access, refresh_token = create_token_pair(user_id)
    return TokenOut(access_token=access, refresh_token=refresh_token)


# ---------- Endpoints /home... ----------
@app.get("/home", response_model=list[Indice])
def get_followed(db: Session = Depends(get_db)):
    a = get_indexes_list()
    b = indexes_metrics(a)
    update_indexes_metrics(b)
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.post("/home/{ticker}", response_model=Indice, status_code=201)
def add_followed(ticker: str, db: Session = Depends(get_db)):
    try:

        clean_metrics = ticker_indicators(ticker)
        metrics = convert_numpy_types(clean_metrics)

        check = db.execute(text('SELECT ticker from indexes')).mappings().fetchall()

        if any(item['ticker'] == ticker.upper() for item in check):
            raise HTTPException(status_code=404, detail="Ticker already on list")
        row = db.execute(
            text("""
                INSERT INTO indexes (ticker, full_name, price, performance)
                VALUES (:t, :f, :pc, :pr)
                RETURNING ticker, full_name, price, performance
                """),
                {
                    "t": ticker.upper(),
                    "f": metrics.get('Full Name'),
                    "pc": metrics.get('Price'),
                    "pr": metrics.get('Ticker performance')
                }
            ).mappings().fetchone()
        db.commit()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to add index")

        return dict(row)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding index: {str(e)}")


@app.delete("/home/{id}", response_model=list[Indice])
def remove_followed(db: Session = Depends(get_db)):
    a = get_indexes_list()
    b = indexes_metrics(a)
    update_indexes_metrics(b)
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]



@app.get("/news", response_model=list[Indice])
def get_news(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


# ---------- Endpoints /api/me/... ----------
@app.get("/api/me", response_model=UserOut)
def get_me(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, email, first_name, last_name FROM users WHERE id = :i"),
        {"i": me.id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(**row)


@app.get("/api/me/balance", response_model=Balance)
def get_my_balance(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT principal
            FROM users
            WHERE id = :uid
            
        """),
        {"uid": me.id},
    ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Balance not found")
    return row


@app.post("/api/me/balance/{amount}", response_model=BalanceIn, status_code=201)
def set_my_balance(amount: float, me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            UPDATE users SET principal = principal + :p 
            WHERE id = :uid
            """),
        {"uid": me.id, "p": amount})
    db.commit()

    row = db.execute(
        text("""SELECT principal AS amount
                FROM users
                WHERE id = :uid
             """),
        {"uid": me.id}
    ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Balance not found")
    return row


@app.get("/api/me/favorite", response_model=list[Favorite])
def get_favorite(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text('''
    SELECT ticker, full_name, price, performance FROM stocks
    WHERE favorite = true AND
    user_id = :uid
    '''),
        {"uid": me.id},
    ).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="favorite not found")
    return [dict(r) for r in rows]


@app.delete("/api/me/favorite/{ticker}", response_model=list[Favorite])
def remove_favorite(
        ticker: str,
        me: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        # 1. Vérifier si le stock existe
        stock = db.execute(
            text("""
                SELECT principal, favorite 
                FROM stocks 
                WHERE ticker = :t AND user_id = :uid
            """),
            {"uid": me.id, "t": ticker.upper()}
        ).mappings().fetchone()

        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")

        # 2. Vérifier si le principal est > 0 (stock détenu)
        if stock['principal'] and stock['principal'] > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove favorite: stock is currently held in portfolio"
            )

        # 3. Mettre à jour le favori pour CE ticker uniquement
        db.execute(
            text("""
                UPDATE stocks 
                SET favorite = false
                WHERE ticker = :t AND user_id = :uid
            """),
            {"uid": me.id, "t": ticker.upper()}
        )
        db.commit()

        # 4. Retourner la liste mise à jour des favoris
        rows = db.execute(
            text("""
                SELECT ticker, full_name, price, performance 
                FROM stocks
                WHERE favorite = true AND user_id = :uid
            """),
            {"uid": me.id}
        ).mappings().all()

        return [dict(r) for r in rows]

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")


@app.post("/api/me/favorite/{ticker}", response_model=Favorite, status_code=201)
def add_favorite(
        ticker,
        me: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Ajoute un stock aux favoris avec tous ses indicateurs"""

    try:
        # 1. Récupérer les indicateurs du ticker
        indicators = get_ticker_indicators(
            ticker=ticker,
            p=0.05,
            n=14,
            rf_ann=0.02
        )

        data = indicators.data

        # 2. Vérifier si le stock existe déjà pour cet utilisateur
        existing = db.execute(
            text("""
                SELECT id FROM stocks 
                WHERE ticker = :ticker AND user_id = :uid
            """),
            {"ticker": ticker.upper(), "uid": me.id}
        ).fetchone()

        if existing:
            # Mettre à jour le favori
            db.execute(
                text("""
                    UPDATE stocks 
                    SET favorite = true,
                        price = :price,
                        performance = :performance,
                        eve_price = :eve_price,
                        full_name = :full_name,
                        sector = :sector,
                        industry = :industry,
                        type = :type,
                        market = :market,
                        benchmark = :benchmark,
                        eps = :eps,
                        total_return = :total_return,
                        market_return = :market_return,
                        expected_return_capm = :expected_return,
                        cagr = :cagr,
                        ebitda = :ebitda,
                        pe_ratio = :pe_ratio,
                        book_value = :book_value,
                        pb_ratio = :pb_ratio,
                        roe = :roe,
                        fin_cash_flow_yield = :fin_cash_flow_yield,
                        duration_dividend = :duration_dividend,
                        duration_fin_cash_flow = :duration_fin_cash_flow,
                        duration_earnings = :duration_earnings,
                        rsi = :rsi,
                        daily_risk = :daily_risk,
                        annual_risk = :annual_risk,
                        max_drawdown = :max_drawdown,
                        var95 = :var95,
                        "cVar95" = :cvar95,
                        annual_volatility = :annual_volatility,
                        beta_1y = :beta_1y,
                        daily_alpha = :daily_alpha,
                        alpha_1y_pct = :alpha_1y_pct,
                        "R_square_1y" = :r_square,
                        "Tracking_Error_1y" = :tracking_error,
                        "IR_1y" = :ir,
                        treynor = :treynor,
                        sharpe_1y = :sharpe,
                        sortino_1y = :sortino,
                        shares_outstanding = :shares_outstanding
                    WHERE ticker = :ticker AND user_id = :uid
                """),
                {
                    "ticker": ticker.upper(),
                    "uid": me.id,
                    "price": data.get("Price"),
                    "performance": data.get("Ticker performance"),
                    "eve_price": data.get("Ticker eve price"),
                    "full_name": data.get("Full Name"),
                    "sector": data.get("sector"),
                    "industry": data.get("industry"),
                    "type": data.get("type"),
                    "market": data.get("market"),
                    "benchmark": data.get("Benchmark"),
                    "eps": data.get("eps"),
                    "total_return": data.get("ticker total return"),
                    "market_return": data.get("market return"),
                    "expected_return": data.get("expected return"),
                    "cagr": data.get("cagr"),
                    "ebitda": data.get("ebitda"),
                    "pe_ratio": data.get("price earning ratio"),
                    "book_value": data.get("book value"),
                    "pb_ratio": data.get("price to book ratio"),
                    "roe": data.get("roe"),
                    "fin_cash_flow_yield": data.get("financial cash flow yield"),
                    "duration_dividend": data.get("duration dividends"),
                    "duration_fin_cash_flow": data.get("duration financial cash flow"),
                    "duration_earnings": data.get("duration earning"),
                    "rsi": data.get("rsi"),
                    "daily_risk": data.get("daily volatility"),
                    "annual_risk": data.get("annual volatility"),
                    "max_drawdown": data.get("drawdown"),
                    "var95": data.get("var95"),
                    "cvar95": data.get("cvar95"),
                    "annual_volatility": data.get("annual volatility"),
                    "beta_1y": data.get("ticker beta 1year"),
                    "daily_alpha": data.get("daily alpha"),
                    "alpha_1y_pct": data.get("alpha 1year percent"),
                    "r_square": data.get("R²"),
                    "tracking_error": data.get("tracking error"),
                    "ir": data.get("information ratio"),
                    "treynor": data.get("treynor"),
                    "sharpe": data.get("sharpe ratio"),
                    "sortino": data.get("sortino"),
                    "shares_outstanding": data.get("shares outstanding")
                }
            )
        else:
            # Insérer un nouveau stock
            db.execute(
                text("""
                    INSERT INTO stocks (
                        user_id, ticker, full_name, sector, industry, type, 
                        market, benchmark, price, performance, eve_price, 
                        eps, total_return, market_return, expected_return_capm,
                        cagr, ebitda, pe_ratio, book_value, pb_ratio, roe,
                        fin_cash_flow_yield, duration_dividend, duration_fin_cash_flow,
                        duration_earnings, rsi, daily_risk, annual_risk, max_drawdown,
                        var95, "cVar95", annual_volatility, beta_1y, daily_alpha,
                        alpha_1y_pct, "R_square_1y", "Tracking_Error_1y", "IR_1y",
                        treynor, sharpe_1y, sortino_1y, shares_outstanding, favorite
                    ) VALUES (
                        :uid, :ticker, :full_name, :sector, :industry, :type,
                        :market, :benchmark, :price, :performance, :eve_price,
                        :eps, :total_return, :market_return, :expected_return,
                        :cagr, :ebitda, :pe_ratio, :book_value, :pb_ratio, :roe,
                        :fin_cash_flow_yield, :duration_dividend, :duration_fin_cash_flow,
                        :duration_earnings, :rsi, :daily_risk, :annual_risk, :max_drawdown,
                        :var95, :cvar95, :annual_volatility, :beta_1y, :daily_alpha,
                        :alpha_1y_pct, :r_square, :tracking_error, :ir,
                        :treynor, :sharpe, :sortino, :shares_outstanding, true
                    )
                """),
                {
                    "uid": me.id,
                    "ticker": ticker.upper(),
                    "full_name": data.get("Full Name"),
                    "sector": data.get("sector"),
                    "industry": data.get("industry"),
                    "type": data.get("type"),
                    "market": data.get("market"),
                    "benchmark": data.get("Benchmark"),
                    "price": data.get("Price"),
                    "performance": data.get("Ticker performance"),
                    "eve_price": data.get("Ticker eve price"),
                    "eps": data.get("eps"),
                    "total_return": data.get("ticker total return"),
                    "market_return": data.get("market return"),
                    "expected_return": data.get("expected return"),
                    "cagr": data.get("cagr"),
                    "ebitda": data.get("ebitda"),
                    "pe_ratio": data.get("price earning ratio"),
                    "book_value": data.get("book value"),
                    "pb_ratio": data.get("price to book ratio"),
                    "roe": data.get("roe"),
                    "fin_cash_flow_yield": data.get("financial cash flow yield"),
                    "duration_dividend": data.get("duration dividends"),
                    "duration_fin_cash_flow": data.get("duration financial cash flow"),
                    "duration_earnings": data.get("duration earning"),
                    "rsi": data.get("rsi"),
                    "daily_risk": data.get("daily volatility"),
                    "annual_risk": data.get("annual volatility"),
                    "max_drawdown": data.get("drawdown"),
                    "var95": data.get("var95"),
                    "cvar95": data.get("cvar95"),
                    "annual_volatility": data.get("annual volatility"),
                    "beta_1y": data.get("ticker beta 1year"),
                    "daily_alpha": data.get("daily alpha"),
                    "alpha_1y_pct": data.get("alpha 1year percent"),
                    "r_square": data.get("R²"),
                    "tracking_error": data.get("tracking error"),
                    "ir": data.get("information ratio"),
                    "treynor": data.get("treynor"),
                    "sharpe": data.get("sharpe ratio"),
                    "sortino": data.get("sortino"),
                    "shares_outstanding": data.get("shares outstanding")
                }
            )
        db.commit()
        # 3. Retourner le stock ajouté
        result = db.execute(
            text("""
                SELECT ticker, full_name, price, performance 
                FROM stocks
                WHERE ticker = :ticker AND user_id = :uid
            """),
            {"ticker": ticker.upper(), "uid": me.id}
        ).mappings().fetchone()
        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")



@app.get("/api/me/wallet", response_model=list[WalletRowOut])
async def get_my_wallet(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, ticker, quantity, to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') AS created_at
            FROM wallet
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": me.id},
    ).mappings().all()
    return [dict(r) for r in rows]


@app.post("/api/me/wallet", response_model=WalletRowOut, status_code=201)
def add_to_wallet(body: WalletCreateIn, me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        text("INSERT INTO wallet (user_id, ticker, quantity) VALUES (:u, :t, :q)"),
        {"u": me.id, "t": body.ticker.upper(), "q": body.quantity},
    )
    new_row = db.execute(
        text("""
            SELECT id, ticker, quantity, to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') AS created_at
            FROM wallet
            WHERE user_id = :u
            ORDER BY id DESC
            LIMIT 1
        """),
        {"u": me.id},
    ).mappings().one()
    db.commit()
    return dict(new_row)


@app.delete("/api/me/wallet/{row_id}", status_code=204)
def delete_wallet_row(row_id: int, me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Sécurité: ne supprimer que si la ligne appartient à l'utilisateur
    deleted = db.execute(
        text("DELETE FROM wallet WHERE id = :id AND user_id = :u"),
        {"id": row_id, "u": me.id},
    )
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ligne introuvable")
    db.commit()
    return


@app.get("/api/me/portfolios", response_model=list[Indice])
def get_wallet_distribuion(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/api/me/summary", response_model=list[Indice])
def get_wallet_summary(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/api/me/data_viz/{ticker}", response_model=list[Indice])
def get_dataframe(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/indicators/{ticker}",response_model=TickerResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Ticker introuvable"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
              }
)
def get_ticker_indicators(
        ticker: str,
        p: float = Query(0.05, ge=0.01, le=0.5, description="Percentile pour VaR (default: 0.05)"),
        n: int = Query(14, ge=5, le=100, description="Période pour RSI (default: 14)"),
        rf_ann: float = Query(0.02, ge=0.0, le=0.2, description="Taux sans risque annuel (default: 0.02)")
):

    try:
        # Appel de votre fonction
        indicators = ticker_indicators(
            ticker=ticker.upper(),
            p=p,
            n=n,
            rf_ann=rf_ann
        )

        indicators_clean = convert_numpy_types(indicators)

        # Gestion des valeurs infinies et NaN
        for key, value in indicators_clean.items():
            if isinstance(value, float):
                if np.isnan(value):
                    indicators_clean[key] = None
                elif np.isinf(value):
                    indicators_clean[key] = "Infinity" if value > 0 else "-Infinity"

        return TickerResponse(
            ticker=ticker.upper(),
            timestamp=datetime.now().isoformat(),
            data=indicators_clean
        )

    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' introuvable ou données manquantes: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul des indicateurs: {str(e)}"
        )


@app.get("/ticker/{ticker}/metric/{metric_name}")
async def get_specific_metric(
        ticker: str,
        metric_name: str,
        p: float = Query(0.05, ge=0.01, le=0.5),
        n: int = Query(14, ge=5, le=100),
        rf_ann: float = Query(0.02, ge=0.0, le=0.2)
):

    try:
        indicators = ticker_indicators(ticker.upper(), p, n, rf_ann)
        indicators_clean = convert_numpy_types(indicators)

        if metric_name not in indicators_clean:
            available_metrics = list(indicators_clean.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Métrique '{metric_name}' non trouvée. Métriques disponibles: {available_metrics[:10]}..."
            )

        value = indicators_clean[metric_name]
        if isinstance(value, float) and np.isnan(value):
            value = None

        return {
            "ticker": ticker.upper(),
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# uvicorn app.main:app --reload
