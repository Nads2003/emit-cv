"""Scoring v2 : six critères pondérés, formule vérifiable, justifications, aucune information inventée.

    Score final = Σ ( poids_critère × note_critère / 100 )        note_critère ∈ [0, 100]   Σ poids = 100

| # | Critère                    | Poids | Ce qui est mesuré                                                              |
|---|----------------------------|-------|--------------------------------------------------------------------------------|
| 1 | Compétences                | 40    | compétences exigées ↔ compétences démontrées (déclarées ou retrouvées dans le CV) |
| 2 | Adéquation aux missions    | 25    | contenu des expériences/projets ↔ missions de l'offre (compétences masquées)     |
| 3 | Expérience et projets      | 10    | ampleur (durée, nombre) de la pratique pertinente ; projets valorisés si débutant |
| 4 | Spécialité                 | 10    | mention / formation ↔ spécialités visées par l'offre                              |
| 5 | Niveau d'études            | 10    | niveau du candidat ↔ niveau demandé (obligatoire = éliminatoire, sinon préférence) |
| 6 | Disponibilité              | 5     | disponibilité déclarée ↔ date de début / contraintes de l'offre                   |

Principes :
- information ABSENTE du CV ou non renseignée => « inconnu » (note neutre NOTE_INCONNU), jamais « ne satisfait pas » (critères 4, 5, 6) ;
- critère NON DEMANDÉ par l'offre => note 100 (il ne départage personne) et statut « non_demande » ;
- exigence obligatoire non respectée => candidat marqué « éliminé » (règle de l'offre) mais son score reste calculé et visible : l'administrateur décide ;
- tout est tracé : version de l'algorithme, poids, critères de l'offre (voir ScoringRun).
Ce module est pur (aucun accès base de données) : il se teste et se calibre isolément.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.ai.skills_taxonomy import canonical_key, extract_skills, is_soft, normalize

VERSION_ALGORITHME = "2.0.0"
CRITERES = ["competences", "missions", "experience_projets", "specialite", "niveau_etudes", "disponibilite"]
POIDS = {"competences": 40, "missions": 25, "experience_projets": 10, "specialite": 10, "niveau_etudes": 10, "disponibilite": 5}
assert set(POIDS) == set(CRITERES) and sum(POIDS.values()) == 100, "Les pondérations doivent totaliser exactement 100 %."
LIBELLES = {"competences": "Compétences", "missions": "Adéquation aux missions", "experience_projets": "Expérience et projets",
            "specialite": "Spécialité", "niveau_etudes": "Niveau d'études", "disponibilite": "Disponibilité"}

NOTE_INCONNU = 50.0        # information absente : ni favorable ni défavorable
CREDIT_TEXTE = 0.6         # compétence retrouvée dans le texte du CV mais sans niveau déclaré
NIVEAUX = {"debutant": 1, "intermediaire": 2, "avance": 3, "expert": 4}
POIDS_TOP_MISSIONS = (0.6, 0.3, 0.1)   # critère 2 : meilleur, 2e, 3e recoupement
SEUIL_PERTINENCE = 0.15
MOIS_CIBLE = {"emploi": 12, "stage": 6, "projet": 6}
SEUIL_DEBUTANT_MOIS = 6


@dataclass
class OfferData:
    id: int
    type: str = "stage"
    titre: str = ""
    missions: str = ""                     # description / missions de l'offre
    criteres: list[dict] = field(default_factory=list)   # {competence, poids, niveau_requis, obligatoire}
    specialites_ids: set[int] = field(default_factory=set)
    specialites_noms: list[str] = field(default_factory=list)
    niveau_min_rang: int | None = None
    niveau_min_nom: str | None = None
    niveau_obligatoire: bool = False
    periode_debut: date | None = None
    periode_fin: date | None = None


@dataclass
class CandidateData:
    etudiant_id: int
    cv_id: int
    competences: list[dict] = field(default_factory=list)  # {nom, niveau, source: declaree|texte}
    items: list[dict] = field(default_factory=list)        # {genre: experience|projet, titre, texte, mois, type?}
    formations_texte: str = ""
    mention_id: int | None = None
    mention_nom: str | None = None
    niveau_rang: int | None = None
    niveau_nom: str | None = None
    disponible: bool = True
    dispo_debut: date | None = None
    dispo_fin: date | None = None
    dispo_type: str = "tous"


@dataclass
class ItemSims:
    """Similarités [0,1] de chaque élément (expérience/projet) : avec les missions (critère 2) et avec le titre de l'offre (critère 3)."""
    missions: list[float] = field(default_factory=list)
    titres: list[float] = field(default_factory=list)


@dataclass
class ScoreResult:
    etudiant_id: int
    cv_id: int
    score: float
    elimine: bool
    detail: dict


def effective_criteria(offer: OfferData) -> tuple[list[dict], bool]:
    """Critères saisis par l'administrateur ; à défaut, compétences reconnues dans le texte de l'offre (poids égaux, non obligatoires)."""
    if offer.criteres:
        return offer.criteres, False
    deduits = [{"competence": s, "poids": 1.0, "niveau_requis": "intermediaire", "obligatoire": False}
               for s in extract_skills(f"{offer.titre} {offer.missions}")]
    return deduits, True


def _bloc(cle: str, note: float, statut: str, resume: str, **elements) -> dict:
    note = round(max(0.0, min(100.0, note)), 1)
    return {"cle": cle, "libelle": LIBELLES[cle], "poids": POIDS[cle], "note": note, "points": round(POIDS[cle] * note / 100, 2),
            "statut": statut, "resume": resume, "elements": elements}


# ----------------------------------------------------------------------------------------------- 1. Compétences
def note_competences(criteres: list[dict], cand: CandidateData, deduits: bool) -> tuple[dict, list[str], list[str]]:
    """Retourne (bloc, points_forts, points_à_vérifier) ; `elements` contient trouvées / insuffisantes / manquantes / obligatoires_manquantes."""
    if not criteres:
        return (_bloc("competences", NOTE_INCONNU, "inconnu", "L'offre ne précise aucune compétence exploitable : critère non évaluable.",
                      trouvees=[], insuffisantes=[], manquantes=[], obligatoires_manquantes=[]), [], [])
    connues = {canonical_key(c["nom"]): c for c in cand.competences}
    total = gagne = 0.0
    trouvees, insuffisantes, manquantes, oblig_manq = [], [], [], []
    for c in criteres:
        w = max(0.1, float(c.get("poids", 1.0)))
        requis = NIVEAUX.get(c.get("niveau_requis", "intermediaire"), 2)
        found = connues.get(canonical_key(c["competence"]))
        if found and found["source"] == "declaree":
            niveau = NIVEAUX.get(found.get("niveau") or "intermediaire", 2)
            credit = min(1.0, niveau / requis)
            entree = {"nom": c["competence"], "niveau": found.get("niveau"), "requis": c.get("niveau_requis"), "source": "declaree", "type": "comportementale" if is_soft(c["competence"]) else "technique"}
            (trouvees if credit >= 1.0 else insuffisantes).append(entree)
        elif found:  # mentionnée dans le CV, niveau non déclaré
            credit = CREDIT_TEXTE
            trouvees.append({"nom": c["competence"], "niveau": None, "requis": c.get("niveau_requis"), "source": "texte", "type": "comportementale" if is_soft(c["competence"]) else "technique"})
        else:
            credit = 0.0
        if credit < 0.5:
            manquantes.append(c["competence"])
            if c.get("obligatoire"):
                oblig_manq.append(c["competence"])
        total += w
        gagne += w * credit
    note = 100 * gagne / total
    declarees = [t for t in trouvees if t["source"] == "declaree"]
    if not cand.competences:
        statut, resume = "absent", "Aucune compétence renseignée ni détectée dans le CV."
    elif note >= 99.9 and all(t["source"] == "declaree" for t in trouvees):
        statut, resume = "confirme", f"{len(trouvees)} compétence(s) demandée(s) confirmée(s) sur {len(criteres)}."
    else:
        statut = "partiel"
        resume = f"{len(trouvees) + len(insuffisantes)} compétence(s) sur {len(criteres)} retrouvée(s) ; {len(manquantes)} non retrouvée(s)."
    forts = [f"Compétence confirmée : {t['nom']}" + (f" (niveau {t['niveau']})" if t['niveau'] else "") for t in declarees]
    verifier = [f"{t['nom']} apparaît dans le CV mais son niveau n'est pas déclaré" for t in trouvees if t["source"] == "texte"]
    verifier += [f"Niveau de {t['nom']} inférieur à celui demandé ({t['niveau']} au lieu de {t['requis']})" for t in insuffisantes]
    if manquantes:
        verifier.append("Compétences demandées non retrouvées dans le CV : " + ", ".join(manquantes))
    bloc = _bloc("competences", note, statut, resume, trouvees=trouvees, insuffisantes=insuffisantes, manquantes=manquantes, obligatoires_manquantes=oblig_manq)
    if deduits:
        bloc["elements"]["criteres_deduits"] = True
    return bloc, forts, verifier


# ----------------------------------------------------------------------------------------------- 2. Missions
def note_missions(offer: OfferData, cand: CandidateData, sims: ItemSims) -> tuple[dict, list[str], list[str], list[str]]:
    if len(offer.missions.strip()) < 20:
        return (_bloc("missions", NOTE_INCONNU, "inconnu", "L'offre ne décrit pas assez ses missions : critère non évaluable."),
                [], [], [])
    if not cand.items:
        return (_bloc("missions", 0, "absent", "Aucune expérience ni aucun projet décrit dans le CV."), [], [],
                ["Aucune expérience ni projet renseigné : impossible d'évaluer l'adéquation aux missions."])
    classes = sorted(zip(sims.missions, cand.items), key=lambda x: -x[0])[:3]
    # pondération normalisée sur les éléments réellement présents : un seul excellent élément peut atteindre 100
    p = POIDS_TOP_MISSIONS[:len(classes)]
    note = 100 * sum(w * s for w, (s, _) in zip(p, classes)) / sum(p)
    meilleurs = [{"titre": it["titre"], "genre": it["genre"], "similarite": round(100 * s)} for s, it in classes]
    forts = [f"{'Expérience' if m['genre'] == 'experience' else 'Projet'} proche des missions : {m['titre']} ({m['similarite']} %)" for m in meilleurs if m["similarite"] >= 45]
    verifier = [] if forts else ["Peu de recoupement entre les missions de l'offre et les expériences/projets décrits."]
    resume = f"Meilleur recoupement : {meilleurs[0]['titre']} ({meilleurs[0]['similarite']} %)."
    return _bloc("missions", note, "confirme", resume, meilleurs=meilleurs), forts, verifier, []


# ----------------------------------------------------------------------------------------------- 3. Expérience et projets
def note_experience_projets(offer: OfferData, cand: CandidateData, sims: ItemSims) -> tuple[dict, list[str], list[str], list[str]]:
    if not cand.items:
        return (_bloc("experience_projets", 0, "absent", "Aucun stage, expérience ou projet renseigné."), [], [],
                ["Aucun stage, expérience ni projet renseigné."])
    exp_mois, proj_rel, details = 0.0, 0.0, []
    for it, s_titre, s_miss in zip(cand.items, sims.titres, sims.missions):
        # pertinence au niveau du TITRE du poste/projet ; le contenu (déjà noté au critère 2) n'intervient qu'à demi-poids, en secours
        rel = s_titre if s_titre >= SEUIL_PERTINENCE else 0.5 * s_miss
        rel = rel if rel >= SEUIL_PERTINENCE else 0.0
        if it["genre"] == "experience":
            exp_mois += it["mois"] * rel
        else:
            proj_rel += rel
        if rel > 0:
            details.append({"titre": it["titre"], "genre": it["genre"], "pertinence": round(100 * rel), "mois": it["mois"]})
    mois_total = sum(i["mois"] for i in cand.items if i["genre"] == "experience")
    debutant = mois_total < SEUIL_DEBUTANT_MOIS
    n_exp = min(1.0, exp_mois / MOIS_CIBLE.get(offer.type, 6))
    n_proj = min(1.0, proj_rel / 1.5)
    w_exp, w_proj = (0.4, 0.6) if debutant else (0.6, 0.4)  # débutant : les projets pèsent davantage
    note = 100 * (w_exp * n_exp + w_proj * n_proj)
    forts = [f"{'Expérience' if d['genre'] == 'experience' else 'Projet'} pertinent(e) : {d['titre']}" + (f" ({d['mois']} mois)" if d['genre'] == 'experience' and d['mois'] else "") for d in details][:4]
    verifier = [] if details else ["Les expériences et projets renseignés semblent éloignés du poste proposé."]
    resume = (f"Profil débutant : projets pondérés à {int(w_proj * 100)} %. " if debutant else "") + f"{round(exp_mois, 1)} mois d'expérience pertinente, {len(details)} élément(s) pertinent(s)."
    return _bloc("experience_projets", note, "confirme", resume, pertinents=details, mois_experience_totale=mois_total, debutant=debutant), forts, verifier, []


# ----------------------------------------------------------------------------------------------- 4. Spécialité
def note_specialite(offer: OfferData, cand: CandidateData) -> tuple[dict, list[str], list[str], list[str]]:
    if not offer.specialites_ids:
        return _bloc("specialite", 100, "non_demande", "Aucune spécialité exigée par l'offre."), [], [], []
    visees = ", ".join(offer.specialites_noms)
    if cand.mention_id is None:
        return _bloc("specialite", NOTE_INCONNU, "inconnu", "Spécialité du candidat inconnue."), [], [], ["Spécialité de formation non renseignée."]
    if cand.mention_id in offer.specialites_ids:
        return _bloc("specialite", 100, "confirme", f"Mention « {cand.mention_nom} » conforme aux spécialités visées."), [f"Spécialité conforme : {cand.mention_nom}"], [], []
    ft = normalize(cand.formations_texte)
    for nom in offer.specialites_noms:
        if normalize(nom) and normalize(nom) in ft:
            return (_bloc("specialite", 60, "partiel", f"Spécialité « {nom} » mentionnée dans la formation, mention différente ({cand.mention_nom})."), [],
                    [f"Mention « {cand.mention_nom} » différente des spécialités visées ({visees}), mais « {nom} » figure dans la formation"], [])
    return (_bloc("specialite", 0, "confirme", f"Mention « {cand.mention_nom} » différente des spécialités visées ({visees})."), [],
            [f"Spécialité « {cand.mention_nom} » différente de celle visée : {visees}"], [])


# ----------------------------------------------------------------------------------------------- 5. Niveau d'études
def note_niveau(offer: OfferData, cand: CandidateData) -> tuple[dict, list[str], list[str], list[str], str | None]:
    """Retourne (bloc, forts, à_vérifier, manquantes, problème_éliminatoire)."""
    if offer.niveau_min_rang is None:
        return _bloc("niveau_etudes", 100, "non_demande", "Aucun niveau d'études exigé par l'offre."), [], [], [], None
    exige = "exigé (obligatoire)" if offer.niveau_obligatoire else "souhaité"
    if cand.niveau_rang is None:
        elim = None
        verifier = ["Niveau d'études inconnu : à vérifier" + (" (exigence obligatoire de l'offre)" if offer.niveau_obligatoire else "")]
        return (_bloc("niveau_etudes", NOTE_INCONNU, "inconnu", f"Niveau du candidat non renseigné (niveau {exige} : {offer.niveau_min_nom})."),
                [], verifier if offer.niveau_obligatoire else [], ["Niveau d'études non renseigné."], elim)
    ecart = offer.niveau_min_rang - cand.niveau_rang
    if ecart <= 0:
        return _bloc("niveau_etudes", 100, "confirme", f"Niveau {cand.niveau_nom} conforme au niveau {exige} ({offer.niveau_min_nom})."), [f"Niveau d'études conforme : {cand.niveau_nom}"], [], [], None
    note = {1: 60, 2: 30}.get(ecart, 0)
    if offer.niveau_obligatoire:
        msg = f"Exigence éliminatoire non respectée : niveau {offer.niveau_min_nom} obligatoire, candidat en {cand.niveau_nom}"
        return _bloc("niveau_etudes", note, "confirme", msg), [], [msg], [], msg
    return (_bloc("niveau_etudes", note, "partiel", f"Écart de préférence : niveau {offer.niveau_min_nom} souhaité, candidat en {cand.niveau_nom}."), [],
            [f"Niveau {cand.niveau_nom} inférieur au niveau souhaité ({offer.niveau_min_nom}) : simple préférence, non éliminatoire"], [], None)


# ----------------------------------------------------------------------------------------------- 6. Disponibilité
def note_disponibilite(offer: OfferData, cand: CandidateData) -> tuple[dict, list[str], list[str], list[str]]:
    if not cand.disponible:
        return _bloc("disponibilite", 0, "confirme", "Le candidat s'est déclaré non disponible."), [], ["Candidat déclaré non disponible"], []
    facteur_type = 0.3 if cand.dispo_type not in ("tous", offer.type) else 1.0
    notes_type = [f"Disponibilité déclarée pour un autre type d'opportunité ({cand.dispo_type})"] if facteur_type < 1 else []
    if offer.periode_debut is None:
        return _bloc("disponibilite", 100 * facteur_type, "non_demande", "Aucune date de début exigée par l'offre."), [], notes_type, []
    d0, d1 = cand.dispo_debut, cand.dispo_fin
    if d0 is None and d1 is None:
        return (_bloc("disponibilite", NOTE_INCONNU, "inconnu", "Dates de disponibilité non renseignées : à vérifier avec le candidat."),
                [], notes_type + ["Disponibilité : dates à vérifier"], ["Dates de disponibilité non renseignées."])
    if d1 is not None and d1 < offer.periode_debut:
        return _bloc("disponibilite", 0, "confirme", f"Disponibilité terminée avant le début de l'offre ({offer.periode_debut:%d/%m/%Y})."), [], notes_type + ["Disponibilité terminée avant le début de l'offre"], []
    if d0 is None:
        return _bloc("disponibilite", NOTE_INCONNU, "inconnu", "Date de début de disponibilité non renseignée."), [], notes_type, ["Date de début de disponibilité non renseignée."]
    retard = (d0 - offer.periode_debut).days
    note = 100 if retard <= 0 else 70 if retard <= 30 else 30 if retard <= 90 else 0
    verifier = list(notes_type)
    if retard > 0:
        verifier.append(f"Disponible {retard} jour(s) après le début prévu de l'offre")
    if offer.periode_fin and d1 and d1 < offer.periode_fin - timedelta(days=30):
        note *= 0.7
        verifier.append("Disponibilité plus courte que la période de l'offre")
    note *= facteur_type
    forts = ["Disponible dès le début de l'offre"] if retard <= 0 and note >= 99 else []
    return _bloc("disponibilite", note, "confirme", f"Disponible à partir du {d0:%d/%m/%Y}."), forts, verifier, []


# ----------------------------------------------------------------------------------------------- Assemblage
def score_candidate(offer: OfferData, cand: CandidateData, sims: ItemSims, criteres: list[dict] | None = None, deduits: bool = False) -> ScoreResult:
    if criteres is None:
        criteres, deduits = effective_criteria(offer)
    if len(sims.missions) != len(cand.items) or len(sims.titres) != len(cand.items):
        sims = ItemSims([0.0] * len(cand.items), [0.0] * len(cand.items))
    b1, f1, v1 = note_competences(criteres, cand, deduits)
    b2, f2, v2, m2 = note_missions(offer, cand, sims)
    b3, f3, v3, m3 = note_experience_projets(offer, cand, sims)
    b4, f4, v4, m4 = note_specialite(offer, cand)
    b5, f5, v5, m5, elim_niveau = note_niveau(offer, cand)
    b6, f6, v6, m6 = note_disponibilite(offer, cand)
    blocs = {b["cle"]: b for b in (b1, b2, b3, b4, b5, b6)}

    score = round(sum(POIDS[k] * blocs[k]["note"] / 100 for k in CRITERES), 1)
    non_respectees = []
    if b1["elements"]["obligatoires_manquantes"]:
        non_respectees.append("Compétence(s) obligatoire(s) absente(s) du CV : " + ", ".join(b1["elements"]["obligatoires_manquantes"]))
    if elim_niveau:
        non_respectees.append(elim_niveau)
    elimine = bool(non_respectees)
    a_verifier_oblig = offer.niveau_obligatoire and b5["statut"] == "inconnu"
    eligibilite = "elimine" if elimine else "a_verifier" if a_verifier_oblig else "conforme"
    poids_inconnus = sum(b["poids"] for b in blocs.values() if b["statut"] == "inconnu")
    detail = {
        "version_algorithme": VERSION_ALGORITHME, "formule": "Σ (poids × note / 100)", "poids": dict(POIDS),
        "score": score, "criteres": blocs, "eligibilite": eligibilite, "exigences_non_respectees": non_respectees,
        "points_forts": f1 + f2 + f3 + f4 + f5 + f6,
        "points_a_verifier": v1 + v2 + v3 + v4 + v5 + v6,
        "informations_manquantes": m2 + m3 + m4 + m5 + m6 + (["Aucune compétence renseignée."] if b1["statut"] == "absent" else []),
        "fiabilite": 100 - poids_inconnus,  # % du score reposant sur des informations connues
        "criteres_deduits": deduits, "non_disponible": not cand.disponible,
    }
    return ScoreResult(cand.etudiant_id, cand.cv_id, score, elimine, detail)


def classer(results: list[ScoreResult]) -> list[tuple[int, ScoreResult]]:
    """Tri déterministe : candidats conformes d'abord, puis éliminés ; par score décroissant ; départage par nb de compétences, puis id."""
    ordre = sorted(results, key=lambda r: (r.elimine, -r.score, -len(r.detail["criteres"]["competences"]["elements"]["trouvees"]), r.etudiant_id))
    return [(i + 1, r) for i, r in enumerate(ordre)]
