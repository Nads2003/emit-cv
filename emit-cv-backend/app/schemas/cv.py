from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Maitrise = Literal["debutant", "intermediaire", "avance", "expert"]


class CompetenceIn(BaseModel):
    nom: str = Field(min_length=1, max_length=80)
    niveau_maitrise: Maitrise = "intermediaire"

    @field_validator("nom")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class CompetenceOut(CompetenceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FormationIn(BaseModel):
    diplome: str = Field(min_length=1, max_length=160)
    etablissement: str = Field(default="", max_length=160)
    annee: int | None = Field(default=None, ge=1950, le=2100)


class FormationOut(FormationIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ExperienceIn(BaseModel):
    poste: str = Field(min_length=1, max_length=160)
    entreprise: str = Field(default="", max_length=160)
    date_debut: date | None = None
    date_fin: date | None = None  # vide = en cours
    description: str = Field(default="", max_length=2000)  # missions et réalisations (analysées par l'IA)

    @model_validator(mode="after")
    def coherence_dates(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("La date de fin doit être postérieure à la date de début.")
        return self


class ExperienceOut(ExperienceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dure: str = ""
    duree_mois: int = 0


class ProjetIn(BaseModel):
    titre: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    type: Literal["academique", "personnel"] = "academique"
    annee: int | None = Field(default=None, ge=1950, le=2100)


class ProjetOut(ProjetIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AnalyseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    statut: str
    message: str = ""


class CVIn(BaseModel):
    titre: str = Field(min_length=2, max_length=160)
    resume: str = Field(default="", max_length=3000)
    model_cv_id: int | None = None
    competences: list[CompetenceIn] = Field(default_factory=list, max_length=60)
    formations: list[FormationIn] = Field(default_factory=list, max_length=20)
    experiences: list[ExperienceIn] = Field(default_factory=list, max_length=20)
    projets: list[ProjetIn] = Field(default_factory=list, max_length=20)


class CVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    etudiant_id: int
    titre: str
    resume: str
    statut: str
    source: str
    est_public: bool
    model_cv_id: int | None
    fichier_nom_origine: str | None
    a_fichier: bool = False
    date_creation: datetime
    date_maj: datetime
    completude: int = 0
    competences: list[CompetenceOut] = []
    formations: list[FormationOut] = []
    experiences: list[ExperienceOut] = []
    projets: list[ProjetOut] = []
    analyse: AnalyseOut | None = None


class CVResume(BaseModel):
    id: int
    titre: str
    statut: str
    source: str
    completude: int
    date_maj: datetime
    nb_competences: int


class ModelCVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    description: str
    apercu: str
