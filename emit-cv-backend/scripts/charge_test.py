"""Test de charge : N CV fictifs (4 000 par défaut) traités par la VRAIE chaîne (file de tâches, workers parallèles, scoring par blocs).

    createdb emit_load && psql -d emit_load -f ../database/tables.sql
    DATABASE_URL=postgresql+psycopg://user:pw@localhost/emit_load python -m scripts.charge_test --cvs 4000
Phases : generer -> analyser (2 workers en parallèle) -> classer (3 offres) -> lecture (latence API) -> incremental (1 CV modifié).
Les données sont synthétiques ; les mesures dépendent de la machine (voir docs/CHARGE.md pour le détail et les limites)."""
import argparse
import json
import os
import random
import resource
import statistics
import subprocess
import sys
import time
from datetime import date, timedelta

SEED = 42
FAMILLES = {  # (titre, compétences possibles, missions/expériences possibles, mention)
    "backend": ("Développeur backend", ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "Git", "API REST", "Linux", "SQL", "Redis"], ["conception d'api rest pour une plateforme interne", "développement de services web et intégration de bases de données", "automatisation de déploiements"], "Informatique"),
    "front": ("Développeur front-end", ["React", "JavaScript", "TypeScript", "Tailwind CSS", "HTML/CSS", "Git", "UI/UX Design", "Vue.js"], ["création d'interfaces web responsives", "intégration de maquettes et composants réutilisables", "optimisation de l'expérience utilisateur"], "Informatique"),
    "data": ("Data scientist junior", ["Python", "Machine Learning", "Pandas", "scikit-learn", "SQL", "NLP", "Statistiques", "Power BI"], ["analyse de données et construction de modèles prédictifs", "traitement automatique de textes", "tableaux de bord décisionnels"], "Informatique"),
    "reseaux": ("Administrateur systèmes et réseaux", ["Linux", "Réseaux", "Cybersécurité", "Administration système", "Docker", "Télécommunications"], ["supervision et sécurisation d'un réseau d'entreprise", "administration de serveurs", "support technique aux utilisateurs"], "Informatique"),
    "compta": ("Assistant comptable", ["Comptabilité", "Excel", "Finance", "ERP", "Audit", "Bureautique"], ["saisie des écritures comptables et rapprochements bancaires", "suivi des factures fournisseurs", "préparation des déclarations"], "Gestion"),
    "management": ("Chef de projet junior", ["Gestion de projet", "Agile / Scrum", "Management", "Communication", "Excel", "Travail en équipe"], ["pilotage d'un projet de transformation digitale", "animation d'équipes pluridisciplinaires", "reporting auprès de la direction"], "Management"),
    "marketing": ("Community manager", ["Marketing digital", "Communication", "Photoshop", "Rédaction", "Montage vidéo"], ["animation des réseaux sociaux et création de contenus", "campagnes de communication digitale", "veille concurrentielle"], "Communication"),
    "logistique": ("Gestionnaire logistique", ["Logistique", "Excel", "ERP", "Gestion de projet", "Vente et négociation"], ["gestion des stocks et approvisionnements", "relation avec les fournisseurs", "optimisation des flux"], "Gestion"),
}
OFFRES = [
    ("Stage Développeur Backend IA", "stage", "Conception d'API REST et intégration de modèles d'IA pour une plateforme interne de recommandation de candidats.", "Informatique", "M1", False,
     [("Python", 5, "avance", True), ("FastAPI", 4, "intermediaire", False), ("PostgreSQL", 3, "intermediaire", False), ("Docker", 2, "debutant", False)]),
    ("Assistant comptable (CDD)", "emploi", "Saisie des écritures comptables, rapprochements bancaires et suivi des factures fournisseurs.", "Gestion", "L3", True,
     [("Comptabilité", 5, "intermediaire", True), ("Excel", 3, "intermediaire", False), ("ERP", 2, "debutant", False)]),
    ("Projet application web étudiante", "projet", "Création d'une interface web moderne et responsive pour la vie étudiante.", None, None, False,
     [("React", 5, "intermediaire", True), ("Tailwind CSS", 3, "intermediaire", False), ("JavaScript", 3, "intermediaire", False)]),
]


def phase_generer(n: int) -> dict:
    from sqlalchemy import select
    from app import models  # noqa: F401
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models import (CV, Competence, CVInfos, Etudiant, EtudiantAutorise, Experience, ExperienceInfos, Formation, Mention, NiveauEtude, Profile, Projet)
    from app.services.referentiels import seed_referentiels
    rnd = random.Random(SEED)
    t0 = time.perf_counter()
    mdp = hash_password("Etudiant123")  # un seul hash réutilisé (Argon2 volontairement lent)
    with SessionLocal() as db:
        seed_referentiels(db)
        mentions = {m.nom: m for m in db.scalars(select(Mention))}
        niveaux = {(n_.mention_id, n_.nom): n_.id for n_ in db.scalars(select(NiveauEtude))}
        for debut in range(0, n, 250):
            for i in range(debut, min(n, debut + 250)):
                fam = rnd.choice(list(FAMILLES))
                titre, skills, missions, mention = FAMILLES[fam]
                m = mentions[mention]
                e = Etudiant(nom=f"Prenom{i:05d} NOM{i:05d}", email=f"charge{i:05d}@example.org", mot_de_passe_hash=mdp, matricule=f"CHG-{i:05d}", mention_id=m.id)
                e.niveau_id = niveaux[(m.id, rnd.choice(["L2", "L3", "L3", "M1", "M1", "M2"]))]
                e.profil = Profile()
                e.disponible = rnd.random() > 0.08
                if rnd.random() < 0.7:
                    e.dispo_debut = date(2026, 11, 1) + timedelta(days=rnd.randint(0, 120))
                    e.dispo_fin = e.dispo_debut + timedelta(days=rnd.randint(120, 300))
                cv = CV(titre=titre, statut="publie", est_public=True, model_cv_id=1, resume=f"Étudiant en {mention}, profil {titre.lower()}, motivé par les projets concrets et le travail en équipe.")
                for s in rnd.sample(skills, k=rnd.randint(3, min(7, len(skills)))):
                    cv.competences.append(Competence(nom=s, niveau_maitrise=rnd.choice(["debutant", "intermediaire", "intermediaire", "avance", "expert"])))
                cv.formations.append(Formation(diplome=f"Licence {mention}", etablissement="EMIT", annee=2024))
                for _ in range(rnd.choice([0, 1, 1, 2])):
                    deb = date(2024, 1, 1) + timedelta(days=rnd.randint(0, 400))
                    fin = deb + timedelta(days=rnd.randint(60, 300))
                    x = Experience(poste=f"Stagiaire {titre.lower()}", entreprise=f"Entreprise{rnd.randint(1, 80)}", date_debut=deb, date_fin=fin, dure="")
                    x.description = rnd.choice(missions) + ". " + rnd.choice(missions)
                    cv.experiences.append(x)
                for _ in range(rnd.choice([0, 1, 2])):
                    genre = rnd.choice(["de fin d'études", "personnel", "de groupe"])
                    cv.projets.append(Projet(titre=f"Projet {genre} : {rnd.choice(missions)[:60]}", description=rnd.choice(missions), type=rnd.choice(["academique", "personnel"])))
                cv.infos = CVInfos(resume=cv.resume)
                e.cvs.append(cv)
                db.add(e)
                db.add(EtudiantAutorise(nom=f"NOM{i:05d}", prenom=f"Prenom{i:05d}", email=e.email, matricule=e.matricule))
            db.commit()
    return {"cvs_generes": n, "duree_s": round(time.perf_counter() - t0, 1)}


def _worker(duree_max: int) -> None:
    from app.services import taches
    fin = time.time() + duree_max
    n = 0
    while time.time() < fin:
        k = taches.traiter_lot(20, worker_id=f"charge-{os.getpid()}")
        n += k
        if k == 0:
            break
    print(json.dumps({"worker": os.getpid(), "taches": n, "ru_maxrss_mo": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}))


def _file_vide(db) -> bool:
    from sqlalchemy import func, select
    from app.models import Tache
    return (db.scalar(select(func.count()).select_from(Tache).where(Tache.statut.in_(("en_attente", "en_cours")))) or 0) == 0


def phase_analyser(workers: int) -> dict:
    from sqlalchemy import func, select
    from app.db.session import SessionLocal
    from app.models import CV, CVAnalyse, Tache
    from app.services import taches
    with SessionLocal() as db:
        ids = db.scalars(select(CV.id)).all()
        for cid in ids:
            db.add(Tache(type="analyse_cv", cible_id=cid, declencheur="charge", priorite=4))
        db.commit()
    t0 = time.perf_counter()
    procs = [subprocess.Popen([sys.executable, "-m", "scripts.charge_test", "--phase", "worker"], stdout=subprocess.PIPE, text=True) for _ in range(workers)]
    sorties = [json.loads(p.communicate()[0].strip().splitlines()[-1]) for p in procs]
    duree = time.perf_counter() - t0
    with SessionLocal() as db:
        statuts = dict(db.execute(select(Tache.statut, func.count()).where(Tache.type == "analyse_cv").group_by(Tache.statut)).all())
        analyses = dict(db.execute(select(CVAnalyse.statut, func.count()).group_by(CVAnalyse.statut)).all())
    return {"cvs": len(ids), "workers": workers, "duree_s": round(duree, 1), "cv_par_seconde": round(len(ids) / duree, 1), "taches": statuts, "analyses": analyses, "par_worker": sorties}


def phase_classer() -> dict:
    from sqlalchemy import func, select
    from app.db.session import SessionLocal
    from app.models import Administrateur, CritereOffre, Mention, NiveauEtude, Offre, Recommandation, ScoringRun, Tache
    from app.core.security import hash_password
    from app.services.catalogue import competence_catalogue
    from app.services import taches
    with SessionLocal() as db:
        admin = Administrateur(nom="Admin charge", email="admin-charge@example.org", mot_de_passe_hash=hash_password("Admin12345"))
        db.add(admin)
        db.commit()
        mentions = {m.nom: m for m in db.scalars(select(Mention))}
        for titre, typ, desc, mention, niv, oblig, criteres in OFFRES:
            o = Offre(admin_id=admin.id, titre=titre, description=desc, statut="publiee")
            o.type, o.periode_debut, o.periode_fin = typ, date(2026, 12, 1), date(2027, 5, 31)
            if mention:
                o.mentions = [mentions[mention]]
                o.niveau_min_id = db.scalar(select(NiveauEtude.id).where(NiveauEtude.mention_id == mentions[mention].id, NiveauEtude.nom == niv))
                o.niveau_obligatoire = oblig
            o.criteres = [CritereOffre(competence_id=competence_catalogue(db, c).id, poids=p, niveau_requis=n, obligatoire=ob) for c, p, n, ob in criteres]
            db.add(o)
            db.commit()
            taches.enqueue(db, "calcul_offre", o.id, "publication-offre")
    t0 = time.perf_counter()
    out = subprocess.run([sys.executable, "-m", "scripts.charge_test", "--phase", "worker"], capture_output=True, text=True)
    duree = time.perf_counter() - t0
    w = json.loads(out.stdout.strip().splitlines()[-1])
    with SessionLocal() as db:
        runs = [{"offre": r.offre_id, "statut": r.statut, "candidats": r.nb_candidats, "duree_ms": r.duree_ms, "erreur": r.erreur} for r in db.scalars(select(ScoringRun).order_by(ScoringRun.id))]
        nb_reco = db.scalar(select(func.count()).select_from(Recommandation))
    return {"offres": len(OFFRES), "duree_totale_s": round(duree, 1), "runs": runs, "recommandations_en_base": nb_reco, "pic_memoire_worker_mo": w["ru_maxrss_mo"], "stderr": out.stderr[-300:] if out.returncode else ""}


def phase_lecture() -> dict:
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    tok = c.post("/api/v1/auth/connexion", json={"email": "admin-charge@example.org", "mot_de_passe": "Admin12345"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    def mesure(nom, fn, n=40):
        ts = []
        erreurs = 0
        for i in range(n):
            t = time.perf_counter()
            r = fn(i)
            ts.append((time.perf_counter() - t) * 1000)
            erreurs += r.status_code >= 400
        ts.sort()
        return {"requete": nom, "n": n, "p50_ms": round(statistics.median(ts)), "p95_ms": round(ts[int(0.95 * len(ts)) - 1]), "max_ms": round(ts[-1]), "erreurs": erreurs}
    base = "/api/v1"
    res = [
        mesure("classement page 1..40 (20/page)", lambda i: c.get(f"{base}/offres/1/recommandations", headers=h, params={"page": i + 1, "taille": 20})),
        mesure("classement + filtres (compétence, score ≥ 60, hors éliminés)", lambda i: c.get(f"{base}/offres/1/recommandations", headers=h, params={"competence": "Python", "min_score": 60, "masquer_elimines": True, "page": 1 + i % 5})),
        mesure("recherche de profils (compétence + disponibles)", lambda i: c.get(f"{base}/etudiants", headers=h, params={"competence": ["Python"], "disponible": True, "page": 1 + i % 20, "taille": 20})),
        mesure("recherche de profils (texte)", lambda i: c.get(f"{base}/etudiants", headers=h, params={"q": f"NOM0{i:03d}"})),
        mesure("liste des offres", lambda i: c.get(f"{base}/offres", headers=h)),
        mesure("statistiques admin", lambda i: c.get(f"{base}/admin/stats", headers=h), 20),
    ]
    etu = c.post(f"{base}/auth/connexion", json={"email": "charge00007@example.org", "mot_de_passe": "Etudiant123"}).json()["access_token"]
    he = {"Authorization": f"Bearer {etu}"}
    res.append(mesure("étudiant : mes recommandations", lambda i: c.get(f"{base}/recommandations/moi", headers=he), 30))
    return {"latences": res}


def phase_incremental() -> dict:
    """Un étudiant modifie son CV : l'analyse est refaite pour CE CV seul, puis une seule recalcul par offre."""
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import CV, Tache
    from app.services import taches
    with SessionLocal() as db:
        cv = db.scalar(select(CV).where(CV.etudiant_id == 7))
        cv.resume = cv.resume + " Nouvelle compétence : Kubernetes."
        db.commit()
        cid = cv.id
        for _ in range(5):  # 5 modifications rapprochées : coalescées en UNE tâche
            taches.enqueue(db, "analyse_cv", cid, "modification", priorite=4)
        nb = len(db.scalars(select(Tache).where(Tache.statut == "en_attente")).all())
    t0 = time.perf_counter()
    total = 0
    while True:
        k = taches.traiter_lot(20)
        total += k
        if k == 0:
            break
    return {"taches_en_attente_apres_5_modifications": nb, "taches_executees": total, "duree_s": round(time.perf_counter() - t0, 1)}


def taille_base() -> dict:
    from sqlalchemy import text
    from app.db.session import SessionLocal
    with SessionLocal() as db:
        taille = db.scalar(text("select pg_size_pretty(pg_database_size(current_database()))"))
        gros = db.execute(text("select relname, pg_size_pretty(pg_total_relation_size(relid)) from pg_catalog.pg_statio_user_tables order by pg_total_relation_size(relid) desc limit 5")).all()
        conns = db.scalar(text("select count(*) from pg_stat_activity where datname=current_database()"))
    return {"taille_base": taille, "plus_grosses_tables": {k: v for k, v in gros}, "connexions_ouvertes": conns}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cvs", type=int, default=4000)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--phase", default="tout")
    a = p.parse_args()
    if a.phase == "worker":
        return _worker(3600)
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    phases = {"generer": lambda: phase_generer(a.cvs), "analyser": lambda: phase_analyser(a.workers), "classer": phase_classer, "lecture": phase_lecture,
              "incremental": phase_incremental, "base": taille_base}
    if a.phase in phases:  # une seule phase (utile quand l'environnement limite la durée d'une commande)
        t = time.perf_counter()
        r = phases[a.phase]()
        r["_duree_phase_s"] = round(time.perf_counter() - t, 1)
        r["_pic_memoire_processus_mo"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        return
    out = {"machine": {"cpu": os.cpu_count()}, "cvs": a.cvs}
    for nom, fn in [("generation", lambda: phase_generer(a.cvs)), ("analyse", lambda: phase_analyser(a.workers)), ("classement", phase_classer),
                    ("lecture", phase_lecture), ("incremental", phase_incremental), ("base", taille_base)]:
        t = time.perf_counter()
        out[nom] = fn()
        print(f"[{nom}] {time.perf_counter() - t:.1f}s", file=sys.stderr, flush=True)
    out["pic_memoire_orchestrateur_mo"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
