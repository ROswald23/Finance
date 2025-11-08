# app/main.py
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import get_db
from app.src.services.schemas import RegisterIn, LoginIn, TokenOut, UserOut, WalletRowOut, WalletCreateIn, Indice, \
    TickerResponse, ErrorResponse
from app.security import hash_password, verify_password, create_token_pair, decode_token
from app.deps import get_current_user, CurrentUser
from app.src.services.schemas import RefreshIn
from .src.services.compute import ticker_indicators, convert_numpy_types
# connexion frontend
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stock Analysis API",
            description="API for analysing stocks",
            version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["*"] en dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Auth ----------


@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    # email unique ?
    exists = db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": body.email}).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    # insertion avec hash direct
    db.execute(
        text("INSERT INTO users (email, password_hash) VALUES (:e, :p)"),
        {"e": body.email, "p": hash_password(body.password)},
    )
    user_id = db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": body.email}).scalar_one()
    db.commit()
    return UserOut(id=user_id, email=body.email)


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
def get_indexes(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/indicators")
def get_stock_indicator():
    indicator = ticker_indicators("tsla", 0.05,  14,  0.02)
    return indicator


@app.get("/news", response_model=list[Indice])
def get_news(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


# ---------- Endpoints /api/me/... ----------
@app.get("/api/me", response_model=UserOut)
def get_me(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id, email FROM users WHERE id = :i"), {"i": me.id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=row.id, email=row.email)


@app.get("/api/me/wallet", response_model=list[WalletRowOut])
def get_my_wallet(me: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
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


@app.get("/api/me/favorite", response_model=list[Indice])
def get_indexes(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM favorite")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/api/me/portfolios", response_model=list[Indice])
def get_indexes(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/api/me/summary", response_model=list[Indice])
def get_indexes(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]


@app.get("/api/me/data_viz", response_model=list[Indice])
def get_indexes(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT ticker, full_name, price, performance FROM indexes")).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Indexes not found")
    return [dict(r) for r in rows]



@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Stock Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/ticker/{ticker}": "Obtenir les indicateurs pour un ticker",
            "/docs": "Documentation interactive"
        }
    }

@app.get(
    "/ticker/{ticker}",
    response_model=TickerResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Ticker introuvable"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)
async def get_ticker_indicators(
        ticker: str,
        p: float = Query(0.05, ge=0.01, le=0.5, description="Percentile pour VaR (default: 0.05)"),
        n: int = Query(14, ge=5, le=100, description="Période pour RSI (default: 14)"),
        rf_ann: float = Query(0.02, ge=0.0, le=0.2, description="Taux sans risque annuel (default: 0.02)")
):
    """
    Récupère tous les indicateurs financiers pour un ticker donné

    - **ticker**: Symbol du ticker (ex: AAPL, TSLA, MSFT)
    - **p**: Percentile pour le calcul de VaR (Value at Risk)
    - **n**: Nombre de périodes pour le calcul du RSI
    - **rf_ann**: Taux sans risque annualisé pour les calculs de performance

    Returns:
        JSON contenant tous les indicateurs calculés
    """
    try:
        # Appel de votre fonction
        indicators = ticker_indicators(
            ticker=ticker.upper(),
            p=p,
            n=n,
            rf_ann=rf_ann
        )

        # Conversion des types numpy pour la sérialisation JSON
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
    """
    Récupère une métrique spécifique pour un ticker

    Métriques disponibles: Price, ticker beta 1year, sharpe ratio, etc.
    """
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
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
# if __name__ == "__main__":
#     # Lancement du serveur
#     uvicorn.run(
#         "main:app",  # Remplacez "main" par le nom de votre fichier
#         host="0.0.0.0",
#         port=8000,
#         reload=True  # Active le rechargement automatique en développement
#     )
# uvicorn app.main:app --reload
