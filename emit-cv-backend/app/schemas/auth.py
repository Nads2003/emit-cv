import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def valider_mot_de_passe(v: str) -> str:
    if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères, dont une lettre et un chiffre.")
    if len(v) > 128:
        raise ValueError("Le mot de passe est trop long (128 caractères maximum).")
    return v


class InscriptionIn(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    prenom: str = Field(min_length=1, max_length=120)
    email: EmailStr
    mot_de_passe: str
    matricule: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9/_.-]+$")
    mention_id: int  # obligatoire : Mention 1 — regrouper — 1..* Etudiant
    niveau_id: int | None = None

    _mdp = field_validator("mot_de_passe")(valider_mot_de_passe)

    @field_validator("nom", "prenom", "matricule", mode="before")
    @classmethod
    def nettoyer(cls, v):
        return re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v

    @field_validator("nom")
    @classmethod
    def nom_propre(cls, v: str) -> str:
        return re.sub(r"\s+", " ", v).strip()

    @field_validator("email")
    @classmethod
    def email_min(cls, v: str) -> str:
        return v.lower()


class VerificationIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    mot_de_passe: str = Field(min_length=1, max_length=128)


class MessageOut(BaseModel):
    message: str


class ConnexionIn(BaseModel):
    email: EmailStr
    mot_de_passe: str = Field(min_length=1, max_length=128)


class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    email: str
    role: Literal["etudiant", "admin"]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurOut
