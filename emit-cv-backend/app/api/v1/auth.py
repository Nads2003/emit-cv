"""Inscription (étudiants autorisés + e-mail vérifié), connexion, rafraîchissement du jeton, déconnexion."""
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_token, decode_token, verify_password
from app.db.session import get_db
from app.models import Utilisateur
from app.schemas.auth import ConnexionIn, InscriptionIn, MessageOut, TokenOut, UtilisateurOut, VerificationIn
from app.services import acces
from app.services.journal import journaliser

router = APIRouter(prefix="/auth", tags=["Authentification"])
COOKIE = "refresh_token"


def _ip(request: Request) -> str:
    return request.client.host if request.client else "?"


def _poser_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE, create_token(user_id, "refresh"), max_age=settings.refresh_token_days * 86400,
        httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite, path="/api/v1/auth",
    )


def _token_out(user: Utilisateur) -> TokenOut:
    return TokenOut(access_token=create_token(user.id, "access"), utilisateur=UtilisateurOut.model_validate(user))


@router.post("/inscription", response_model=MessageOut, status_code=202, summary="Demander la création d'un compte étudiant (liste autorisée)")
def inscription(data: InscriptionIn, request: Request, db: Session = Depends(get_db)):
    acces.demander_inscription(db, nom=data.nom, prenom=data.prenom, email=data.email, matricule=data.matricule, mot_de_passe=data.mot_de_passe,
                               mention_id=data.mention_id, niveau_id=data.niveau_id, ip=_ip(request))
    return MessageOut(message="Un e-mail de confirmation vient de vous être envoyé. Ouvrez le lien qu'il contient pour activer votre compte.")


@router.post("/verification", response_model=TokenOut, status_code=201, summary="Confirmer l'e-mail et créer le compte")
def verification(data: VerificationIn, request: Request, response: Response, db: Session = Depends(get_db)):
    etu = acces.confirmer_inscription(db, token=data.token, mot_de_passe=data.mot_de_passe, ip=_ip(request))
    _poser_cookie(response, etu.id)
    return _token_out(etu)


@router.post("/connexion", response_model=TokenOut, summary="Se connecter")
def connexion(data: ConnexionIn, request: Request, response: Response, db: Session = Depends(get_db)):
    email = data.email.lower()
    ratelimit.verifier(db, f"login:{_ip(request)}:{email}", settings.login_rate_limit, settings.login_rate_window_s)
    ratelimit.verifier(db, f"login-compte:{email}", settings.login_echecs_compte, 900, compter=False,
                       message="Compte temporairement verrouillé après trop d'échecs. Réessayez dans 15 minutes.")
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == email))
    # Même message que le compte existe ou non : on ne révèle pas quels e-mails sont inscrits
    if not user or not verify_password(data.mot_de_passe, user.mot_de_passe_hash):
        try:
            ratelimit.verifier(db, f"login-compte:{email}", settings.login_echecs_compte + 1, 900)  # compte uniquement les échecs
        except HTTPException:
            pass
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou mot de passe incorrect.")
    ratelimit.reinitialiser(db, f"login-compte:{email}")
    journaliser(db, user.id, "Connexion")
    db.commit()
    _poser_cookie(response, user.id)
    return _token_out(user)


@router.post("/refresh", response_model=TokenOut, summary="Obtenir un nouveau jeton d'accès")
def refresh(response: Response, refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    user_id = decode_token(refresh_token, "refresh") if refresh_token else None
    user = db.get(Utilisateur, user_id) if user_id else None
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée, veuillez vous reconnecter.")
    _poser_cookie(response, user.id)  # rotation du cookie
    return _token_out(user)


@router.post("/deconnexion", status_code=204, summary="Se déconnecter")
def deconnexion(response: Response):
    response.delete_cookie(COOKIE, path="/api/v1/auth")


@router.get("/moi", response_model=UtilisateurOut, summary="Utilisateur connecté")
def moi(user: Utilisateur = Depends(get_current_user)):
    return user
