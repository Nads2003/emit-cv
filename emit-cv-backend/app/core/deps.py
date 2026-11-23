"""Dépendances FastAPI : utilisateur courant + contrôle d'accès par rôle (RBAC)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Administrateur, Etudiant, Utilisateur

bearer = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Utilisateur:
    erreur = HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise ou session expirée.", headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise erreur
    user_id = decode_token(creds.credentials, "access")
    if user_id is None:
        raise erreur
    user = db.get(Utilisateur, user_id)
    if user is None:
        raise erreur
    return user


def require_admin(user: Utilisateur = Depends(get_current_user)) -> Administrateur:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux administrateurs.")
    return user  # type: ignore[return-value]


def require_etudiant(user: Utilisateur = Depends(get_current_user)) -> Etudiant:
    if user.role != "etudiant":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux étudiants.")
    return user  # type: ignore[return-value]
