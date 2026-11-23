from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.cv import Maitrise
from app.schemas.etudiant import EtudiantResume

TypeOffre = Literal["stage", "emploi", "projet"]


class CritereIn(BaseModel):
    competence: str = Field(min_length=1, max_length=80)
    poids: float = Field(default=3, ge=1, le=5)
    niveau_requis: Maitrise = "intermediaire"
    obligatoire: bool = False

    @field_validator("competence")
    @classmethod
    def strip(cls, v):
        return v.strip()


class CritereOut(CritereIn):
    id: int

    model_config = {"from_attributes": True}


class OffreIn(BaseModel):
    titre: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=8000)
    type: TypeOffre = "stage"
    date_limite: date | None = None
    periode_debut: date | None = None
    periode_fin: date | None = None
    niveau_min_id: int | None = None
    niveau_obligatoire: bool = False  # True : le niveau minimal est une exigence éliminatoire ; False : simple préférence
    mention_ids: list[int] = Field(default_factory=list, max_length=20)
    criteres: list[CritereIn] = Field(default_factory=list, max_length=30)
    publier: bool = False  # True : publie immédiatement

    @model_validator(mode="after")
    def coherence(self):
        if self.periode_debut and self.periode_fin and self.periode_fin < self.periode_debut:
            raise ValueError("La fin de la période doit être postérieure à son début.")
        if self.publier and not self.criteres and len(self.description.strip()) < 20:
            raise ValueError("Pour publier, ajoutez des critères ou une description détaillée (20 caractères minimum).")
        return self


class OffreOut(BaseModel):
    id: int
    titre: str
    description: str
    type: str
    statut: str
    est_ouverte: bool
    date_creation: datetime
    date_limite: date | None
    periode_debut: date | None
    periode_fin: date | None
    niveau_min_id: int | None
    niveau_min_nom: str | None
    niveau_obligatoire: bool = False
    mention_ids: list[int]
    mentions_noms: list[str]
    criteres: list[CritereOut]
    nb_candidatures: int = 0
    nb_recommandes: int = 0


class OffreEtudiantOut(OffreOut):
    """Vue d'une offre pour un étudiant : + score de recommandation et état de sa candidature."""
    score: float | None = None
    rang: int | None = None
    detail: dict | None = None
    a_postule: bool = False
    statut_candidature: str | None = None


class RecommandationOut(BaseModel):
    rang: int
    elimine: bool = False
    score: float
    detail: dict
    etudiant: EtudiantResume
    statut_candidature: str | None = None
    a_postule: bool = False


class ClassementOut(BaseModel):
    total: int
    moteur_ia: str | None
    version_algorithme: str | None = None
    run_id: int | None = None
    calcule_le: datetime | None = None
    items: list[RecommandationOut]


class StatutCandidatureIn(BaseModel):
    statut: Literal["valide", "selectionne", "refuse"]


class CandidatureOut(BaseModel):
    id: int
    offre_id: int
    offre_titre: str
    offre_statut: str
    statut: str
    date: datetime
    a_postule: bool
