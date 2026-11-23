from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EtudiantMoiOut(BaseModel):
    id: int
    nom: str
    email: str
    matricule: str
    mention_id: int
    mention_nom: str | None
    niveau_id: int | None
    niveau_nom: str | None
    telephone: str | None
    adresse: str | None
    a_photo: bool
    disponible: bool
    dispo_debut: date | None
    dispo_fin: date | None
    dispo_type: str


class EtudiantMoiIn(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    matricule: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9/_.-]+$")
    mention_id: int
    niveau_id: int | None = None
    telephone: str | None = Field(default=None, max_length=30)
    adresse: str | None = Field(default=None, max_length=255)

    @field_validator("telephone")
    @classmethod
    def tel(cls, v):
        if v and not all(c.isdigit() or c in "+ .-()" for c in v):
            raise ValueError("Numéro de téléphone invalide.")
        return v or None


class DisponibiliteIn(BaseModel):
    disponible: bool
    dispo_debut: date | None = None
    dispo_fin: date | None = None
    dispo_type: Literal["stage", "emploi", "projet", "tous"] = "tous"

    @model_validator(mode="after")
    def dates(self):
        if self.dispo_debut and self.dispo_fin and self.dispo_fin < self.dispo_debut:
            raise ValueError("La date de fin de disponibilité doit être postérieure à la date de début.")
        return self


class EtudiantResume(BaseModel):
    id: int
    nom: str
    matricule: str
    email: str
    mention_nom: str | None
    niveau_nom: str | None
    disponible: bool
    dispo_type: str
    cv_id: int | None
    cv_titre: str | None
    competences: list[str]
    a_photo: bool


class EtudiantPage(BaseModel):
    total: int
    items: list[EtudiantResume]
