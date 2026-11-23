"""Offres : publication/gestion (admin), consultation (étudiant), classement IA des candidats, candidatures."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.scoring import VERSION_ALGORITHME
from app.core.deps import get_current_user, require_admin, require_etudiant
from app.db.session import get_db
from app.models import (CV, STATUT_RECOMMANDEE, Administrateur, Candidature, Competence, CritereOffre, Disponibilite, Etudiant, EtudiantNiveau,
                        Mention, NiveauEtude, Offre, Recommandation, RecommandationDetail, ScoringRun, Utilisateur)
from app.schemas.offre import ClassementOut, OffreEtudiantOut, OffreIn, OffreOut, RecommandationOut, StatutCandidatureIn
from app.services import taches
from app.services.catalogue import competence_catalogue
from app.services.journal import journaliser, notifier
from app.services.presenters import etudiant_resume
from app.services.recommandation import cv_publie_recent
from app.ai.skills_taxonomy import canonical

router = APIRouter(prefix="/offres", tags=["Offres"])

# On ne charge JAMAIS les candidatures d'une offre (des milliers) : seuls des comptages SQL sont utilisés.
_OPTS = (selectinload(Offre.criteres).selectinload(CritereOffre.competence_ref), selectinload(Offre.mentions), selectinload(Offre.infos))


def comptes(db: Session, offre_ids: list[int]) -> dict[int, tuple[int, int]]:
    """{offre_id: (nb candidatures, nb candidats recommandés)} en deux requêtes groupées."""
    if not offre_ids:
        return {}
    cand = dict(db.execute(select(Candidature.offre_id, func.count()).where(Candidature.offre_id.in_(offre_ids), Candidature.statut != STATUT_RECOMMANDEE)
                           .group_by(Candidature.offre_id)).all())
    reco = dict(db.execute(select(Candidature.offre_id, func.count()).join(Recommandation, Recommandation.candidature_id == Candidature.id)
                           .where(Candidature.offre_id.in_(offre_ids)).group_by(Candidature.offre_id)).all())
    return {i: (cand.get(i, 0), reco.get(i, 0)) for i in offre_ids}


def offre_out(o: Offre, nb: tuple[int, int] = (0, 0)) -> OffreOut:
    return OffreOut(
        id=o.id, titre=o.titre, description=o.description, type=o.type, statut=o.statut, est_ouverte=o.est_ouverte,
        date_creation=o.date_creation, date_limite=o.date_limite, periode_debut=o.periode_debut, periode_fin=o.periode_fin,
        niveau_min_id=o.niveau_min_id, niveau_min_nom=o.niveau_min.nom if o.niveau_min else None, niveau_obligatoire=o.niveau_obligatoire,
        mention_ids=[m.id for m in o.mentions], mentions_noms=[m.nom for m in o.mentions],
        criteres=[{"id": c.id, "competence": c.competence, "poids": c.poids, "niveau_requis": c.niveau_requis, "obligatoire": c.obligatoire} for c in o.criteres],
        nb_candidatures=nb[0], nb_recommandes=nb[1],
    )


def _get_offre(db: Session, offre_id: int) -> Offre:
    o = db.scalar(select(Offre).where(Offre.id == offre_id).options(*_OPTS))
    if o is None:
        raise HTTPException(404, "Offre introuvable.")
    return o


def _appliquer(db: Session, o: Offre, data: OffreIn) -> None:
    if data.niveau_min_id and not db.get(NiveauEtude, data.niveau_min_id):
        raise HTTPException(422, "Niveau d'études minimal inconnu.")
    mentions = list(db.scalars(select(Mention).where(Mention.id.in_(data.mention_ids)))) if data.mention_ids else []
    if len(mentions) != len(set(data.mention_ids)):
        raise HTTPException(422, "Une des mentions ciblées est inconnue.")
    o.titre, o.description, o.type = data.titre.strip(), data.description.strip(), data.type
    o.date_limite, o.periode_debut, o.periode_fin, o.niveau_min_id = data.date_limite, data.periode_debut, data.periode_fin, data.niveau_min_id
    o.niveau_obligatoire = bool(data.niveau_obligatoire and data.niveau_min_id)
    o.mentions = mentions
    o.criteres.clear()
    vus = set()
    for c in data.criteres:
        ref = competence_catalogue(db, c.competence)
        if ref.nom.lower() in vus:
            continue
        vus.add(ref.nom.lower())
        o.criteres.append(CritereOffre(competence_id=ref.id, poids=c.poids, niveau_requis=c.niveau_requis, obligatoire=c.obligatoire))


def _planifier(db: Session, bg: BackgroundTasks, offre_id: int, declencheur: str) -> None:
    taches.enqueue(db, "calcul_offre", offre_id, declencheur, priorite=2)
    bg.add_task(taches.declencher_inline)


# ------------------------------------------------------------------ Administrateur : gestion des offres
@router.post("", response_model=OffreOut, status_code=201, summary="Publier une offre (ou l'enregistrer en brouillon)")
def creer(data: OffreIn, bg: BackgroundTasks, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = Offre(admin_id=admin.id, titre=data.titre)
    _appliquer(db, o, data)
    o.statut = "publiee" if data.publier else "brouillon"
    db.add(o)
    journaliser(db, admin.id, f"{'Publication' if data.publier else 'Création (brouillon)'} de l'offre « {o.titre} »")
    db.commit()
    if o.statut == "publiee":
        _planifier(db, bg, o.id, "publication-offre")
    return offre_out(_get_offre(db, o.id), comptes(db, [o.id])[o.id])


@router.put("/{offre_id}", response_model=OffreOut, summary="Modifier une offre et ses critères")
def modifier(offre_id: int, data: OffreIn, bg: BackgroundTasks, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    if o.statut == "cloturee":
        raise HTTPException(409, "Une offre clôturée ne peut plus être modifiée.")
    nouvelle_pub = o.statut == "brouillon" and data.publier
    _appliquer(db, o, data)
    if nouvelle_pub:
        o.statut = "publiee"
    journaliser(db, admin.id, f"Modification de l'offre « {o.titre} »")
    db.commit()
    if o.statut == "publiee":
        _planifier(db, bg, o.id, "publication-offre" if nouvelle_pub else "modification-offre")
    return offre_out(_get_offre(db, o.id), comptes(db, [o.id])[o.id])


@router.post("/{offre_id}/publier", response_model=OffreOut, summary="Publier un brouillon")
def publier(offre_id: int, bg: BackgroundTasks, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    if o.statut != "brouillon":
        raise HTTPException(409, "Seul un brouillon peut être publié.")
    if not o.criteres and len(o.description.strip()) < 20:
        raise HTTPException(422, "Ajoutez des critères ou une description détaillée avant de publier.")
    o.statut = "publiee"
    journaliser(db, admin.id, f"Publication de l'offre « {o.titre} »")
    db.commit()
    _planifier(db, bg, o.id, "publication-offre")
    return offre_out(_get_offre(db, o.id), comptes(db, [o.id])[o.id])


@router.post("/{offre_id}/cloturer", response_model=OffreOut, summary="Clôturer une offre")
def cloturer(offre_id: int, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    if o.statut == "cloturee":
        raise HTTPException(409, "Cette offre est déjà clôturée.")
    o.statut = "cloturee"
    for (etu_id,) in db.execute(select(CV.etudiant_id).join(Candidature, Candidature.cv_id == CV.id)
                                .where(Candidature.offre_id == o.id, Candidature.statut != STATUT_RECOMMANDEE)):
        notifier(db, etu_id, f"L'offre « {o.titre} » est clôturée.")
    journaliser(db, admin.id, f"Clôture de l'offre « {o.titre} »")
    db.commit()
    return offre_out(_get_offre(db, o.id), comptes(db, [o.id])[o.id])


@router.delete("/{offre_id}", status_code=204, summary="Supprimer un brouillon")
def supprimer(offre_id: int, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    if o.statut != "brouillon":
        raise HTTPException(409, "Seul un brouillon peut être supprimé : clôturez plutôt l'offre.")
    journaliser(db, admin.id, f"Suppression du brouillon « {o.titre} »")
    db.delete(o)
    db.commit()


@router.post("/{offre_id}/recalculer", summary="Relancer le calcul IA (score + classement)")
def recalculer(offre_id: int, bg: BackgroundTasks, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    t = taches.enqueue(db, "calcul_offre", o.id, "recalcul-manuel", priorite=1)
    journaliser(db, admin.id, f"Recalcul du classement de l'offre « {o.titre} »")
    db.commit()
    bg.add_task(taches.declencher_inline)
    return {"tache_id": t.id, "statut": t.statut}


@router.get("/{offre_id}/runs", summary="Historique des calculs de classement (traçabilité : version, poids, critères)")
def runs(offre_id: int, _: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(ScoringRun).where(ScoringRun.offre_id == offre_id).order_by(ScoringRun.id.desc()).limit(30)).all()
    return [{"id": r.id, "version_algorithme": r.version_algorithme, "poids": r.poids, "criteres_offre": r.criteres_offre, "moteur_ia": r.moteur_ia,
             "statut": r.statut, "nb_candidats": r.nb_candidats, "duree_ms": r.duree_ms, "declencheur": r.declencheur, "erreur": r.erreur, "cree_le": r.cree_le} for r in rows]


@router.get("/{offre_id}/recommandations", response_model=ClassementOut, summary="Classement IA des candidats (admin)")
def classement(
    offre_id: int,
    q: str | None = Query(None, max_length=100),
    competence: list[str] = Query(default=[]),
    mention_id: int | None = None,
    niveau_id: int | None = None,
    disponible: bool | None = None,
    min_score: float = Query(0, ge=0, le=100),
    seulement_candidats: bool = False,
    masquer_elimines: bool = False,
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    _: Administrateur = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.get(Offre, offre_id) is None:
        raise HTTPException(404, "Offre introuvable.")
    cond = [Candidature.offre_id == offre_id, Recommandation.score >= min_score]
    if q:
        like = f"%{q.strip()}%"
        cond.append(or_(Etudiant.nom.ilike(like), Etudiant.matricule.ilike(like)))
    for comp in competence:
        cond.append(CV.competences.any(func.lower(Competence.nom) == canonical(comp).lower()))
    if mention_id:
        cond.append(Etudiant.mention_id == mention_id)
    if niveau_id:
        cond.append(Etudiant.niveau_info.has(EtudiantNiveau.niveauetude_id == niveau_id))
    if disponible is not None:
        cond.append(Etudiant.dispo.has(Disponibilite.disponible.is_(disponible)))
    if seulement_candidats:
        cond.append(Candidature.statut != STATUT_RECOMMANDEE)
    if masquer_elimines:
        cond.append(RecommandationDetail.elimine.is_(False))
    base = (select(Recommandation).join(Candidature, Candidature.id == Recommandation.candidature_id).join(CV, CV.id == Candidature.cv_id)
            .join(Etudiant, Etudiant.id == CV.etudiant_id).join(RecommandationDetail, RecommandationDetail.recommandation_id == Recommandation.id).where(*cond))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(RecommandationDetail.rang).offset((page - 1) * taille).limit(taille)
                      .options(selectinload(Recommandation.info), selectinload(Recommandation.candidature).selectinload(Candidature.cv).selectinload(CV.etudiant).selectinload(Etudiant.cvs).selectinload(CV.competences))).all()
    items = []
    for r in rows:
        cand = r.candidature
        items.append(RecommandationOut(rang=r.rang, elimine=r.elimine, score=r.score, detail=r.detail, etudiant=etudiant_resume(cand.cv.etudiant),
                                       statut_candidature=cand.statut if cand.a_postule else None, a_postule=cand.a_postule))
    run = None
    if rows and rows[0].info and rows[0].info.run_id:
        run = db.get(ScoringRun, rows[0].info.run_id)
    return ClassementOut(total=total, moteur_ia=run.moteur_ia if run else None, version_algorithme=run.version_algorithme if run else VERSION_ALGORITHME,
                         run_id=run.id if run else None, calcule_le=run.cree_le if run else None, items=items)


def _candidature(db: Session, offre_id: int, etudiant_id: int) -> Candidature | None:
    return db.scalar(select(Candidature).join(CV, CV.id == Candidature.cv_id).where(Candidature.offre_id == offre_id, CV.etudiant_id == etudiant_id)
                     .options(selectinload(Candidature.recommandation).selectinload(Recommandation.info)))


@router.put("/{offre_id}/candidats/{etudiant_id}/statut", summary="Valider, sélectionner ou refuser un candidat (décision de l'administrateur)")
def changer_statut(offre_id: int, etudiant_id: int, data: StatutCandidatureIn, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    o = db.get(Offre, offre_id)
    if o is None:
        raise HTTPException(404, "Offre introuvable.")
    cand = _candidature(db, offre_id, etudiant_id)
    if cand is None:
        raise HTTPException(404, "Ce candidat ne figure pas dans le classement de cette offre.")
    cand.statut = data.statut
    etu = db.get(Etudiant, etudiant_id)
    libelle = {"valide": "validée", "selectionne": "retenue : vous êtes sélectionné(e)", "refuse": "refusée"}[data.statut]
    notifier(db, etudiant_id, f"Votre candidature pour « {o.titre} » est {libelle}.")
    journaliser(db, admin.id, f"Candidat {etu.nom if etu else etudiant_id} -> {data.statut} pour « {o.titre} »")
    db.commit()
    return {"statut": cand.statut}


# ------------------------------------------------------------------ Liste / détail (admin et étudiants)
@router.get("", response_model=list[OffreEtudiantOut], summary="Lister les offres (étudiant : offres ouvertes)")
def lister(
    type: str | None = Query(None, pattern="^(stage|emploi|projet)$"),
    statut: str | None = Query(None, pattern="^(brouillon|publiee|cloturee)$"),
    q: str | None = Query(None, max_length=100),
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Offre).options(*_OPTS).order_by(Offre.date_creation.desc())
    if q:
        stmt = stmt.where(or_(Offre.titre.ilike(f"%{q.strip()}%"), Offre.description.ilike(f"%{q.strip()}%")))
    if user.role == "admin":
        if statut:
            stmt = stmt.where(Offre.statut == statut)
    else:
        stmt = stmt.where(Offre.statut == "publiee")
    offres = [o for o in db.scalars(stmt).unique() if (not type or o.type == type) and (user.role == "admin" or o.est_ouverte)]
    cands = {}
    if user.role == "etudiant":
        cands = {c.offre_id: c for c in db.scalars(select(Candidature).join(CV, CV.id == Candidature.cv_id).where(CV.etudiant_id == user.id)
                                                   .options(selectinload(Candidature.recommandation).selectinload(Recommandation.info)))}
    nb = comptes(db, [o.id for o in offres]) if user.role == "admin" else {}
    return [_vue_etudiant(o, cands.get(o.id), user.role == "etudiant", nb.get(o.id, (0, 0))) for o in offres]


def _vue_etudiant(o: Offre, cand: Candidature | None, avec_detail: bool, nb: tuple[int, int] = (0, 0)) -> OffreEtudiantOut:
    """Les effectifs de candidats ne sont jamais montrés aux étudiants (nb = (0, 0) pour eux)."""
    reco = cand.recommandation if cand else None
    return OffreEtudiantOut(**offre_out(o, nb).model_dump(), score=reco.score if reco else None, rang=reco.rang if reco else None,
                            detail=reco.detail if (reco and avec_detail) else None,
                            a_postule=bool(cand and cand.a_postule), statut_candidature=cand.statut if cand and cand.a_postule else None)


@router.get("/{offre_id}", response_model=OffreEtudiantOut, summary="Détail d'une offre")
def detail(offre_id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    o = _get_offre(db, offre_id)
    if user.role == "etudiant":
        if o.statut == "brouillon":
            raise HTTPException(404, "Offre introuvable.")
        return _vue_etudiant(o, _candidature(db, o.id, user.id), True)
    return _vue_etudiant(o, None, False, comptes(db, [o.id])[o.id])


# ------------------------------------------------------------------ Étudiant : postuler / retirer
@router.post("/{offre_id}/postuler", status_code=201, summary="Postuler à une offre avec mon CV publié")
def postuler(offre_id: int, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    o = db.get(Offre, offre_id)
    if o is None or o.statut == "brouillon":
        raise HTTPException(404, "Offre introuvable.")
    if not o.est_ouverte:
        raise HTTPException(409, "Cette offre n'accepte plus de candidatures.")
    cv = cv_publie_recent(etu)
    if cv is None:
        raise HTTPException(422, "Publiez d'abord un CV pour pouvoir postuler.")
    cand = _candidature(db, offre_id, etu.id)
    if cand and cand.a_postule:
        raise HTTPException(409, "Vous avez déjà postulé à cette offre.")
    if cand:
        cand.statut, cand.cv_id = "postule", cv.id
    else:
        db.add(Candidature(offre_id=offre_id, cv_id=cv.id, statut="postule"))
    notifier(db, o.admin_id, f"{etu.nom} a postulé à « {o.titre} ».")
    journaliser(db, etu.id, f"Candidature à l'offre « {o.titre} »")
    db.commit()
    return {"message": "Candidature envoyée."}


@router.delete("/{offre_id}/postuler", status_code=204, summary="Retirer ma candidature")
def retirer(offre_id: int, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cand = _candidature(db, offre_id, etu.id)
    if cand is None or not cand.a_postule:
        raise HTTPException(404, "Aucune candidature à retirer.")
    if cand.statut != "postule":
        raise HTTPException(409, "Votre candidature a déjà été traitée, elle ne peut plus être retirée.")
    if cand.recommandation:
        cand.statut = STATUT_RECOMMANDEE  # on retire seulement la candidature ; la recommandation de l'IA reste
    else:
        db.delete(cand)
    db.commit()
