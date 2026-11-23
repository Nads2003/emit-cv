"""Importer tous les modèles ici garantit qu'ils sont enregistrés sur Base.metadata (Alembic, create_all)."""
from app.models.acces import EtudiantAutorise, ImportLigne, ImportListe, InscriptionEnAttente, LimiteDebit  # noqa: F401
from app.models.cv import (CV, NIVEAUX_MAITRISE, Competence, CVAnalyse, CVInfos, Experience, ExperienceInfos, Formation,  # noqa: F401
                           ModelCV, Projet, formater_duree)
from app.models.tache import Tache  # noqa: F401
from app.models.misc import Historique, Notification  # noqa: F401
from app.models.offre import (STATUT_RECOMMANDEE, Candidature, CritereOffre, Offre, OffreInfos, Recommandation,  # noqa: F401
                              RecommandationDetail, ScoringRun, viser)
from app.models.user import (Administrateur, Disponibilite, Etudiant, EtudiantNiveau, Mention, NiveauEtude, Profile,  # noqa: F401
                             Utilisateur, en_utc, utcnow)
