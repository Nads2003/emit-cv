"""Jeu de données de DÉMONSTRATION (à ne jamais lancer en production).

Crée : 1 admin, 12 étudiants avec CV publiés, 3 offres publiées avec leur classement IA.
Comptes : admin@emit.mg / Admin12345   ·   etudiant1@emit.mg … etudiant12@emit.mg / Etudiant123
"""
from datetime import date

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app import models  # noqa: F401
from app.models import (CV, Administrateur, Competence, CritereOffre, Etudiant, EtudiantAutorise, Experience, Formation, Mention, ModelCV, NiveauEtude, Offre,
                        Profile, Projet, Utilisateur, formater_duree)
from app.services.analyse import analyser_cv
from app.services.catalogue import competence_catalogue
from app.services.recommandation import recompute_offer
from app.services.referentiels import seed_referentiels

# (nom, mention, niveau, titre CV, résumé, [(compétence, niveau)], (diplôme, année), (poste, entreprise, mois), dispo)
ETUDIANTS = [
    ("Hery Rakoto", "Informatique", "M1", "Développeur backend Python", "Passionné par les API et l'IA, j'ai réalisé plusieurs projets web avec FastAPI et PostgreSQL.", [("Python", "avance"), ("FastAPI", "avance"), ("PostgreSQL", "intermediaire"), ("Docker", "intermediaire"), ("Git", "avance")], ("Master 1 Informatique", 2025), ("Stagiaire développeur", "Orange Madagascar", 6), True),
    ("Tiana Andrianina", "Informatique", "L3", "Développeuse web front-end", "Je conçois des interfaces modernes et accessibles avec React et Tailwind CSS.", [("React", "avance"), ("JavaScript", "avance"), ("Tailwind CSS", "avance"), ("HTML/CSS", "expert"), ("UI/UX Design", "intermediaire")], ("Licence 3 Informatique", 2025), ("Stagiaire front-end", "Agence Digitale", 4), True),
    ("Fanja Razafy", "Informatique", "M2", "Data scientist junior", "Machine learning, NLP et analyse de données pour des projets à impact.", [("Python", "expert"), ("Machine Learning", "avance"), ("scikit-learn", "avance"), ("Pandas", "avance"), ("NLP", "intermediaire"), ("SQL", "intermediaire")], ("Master 2 Informatique", 2025), ("Stagiaire data", "Telma", 8), True),
    ("Mamy Randria", "Informatique", "M1", "Administrateur systèmes et réseaux", "Administration Linux, supervision et sécurité des réseaux d'entreprise.", [("Linux", "avance"), ("Réseaux", "avance"), ("Cybersécurité", "intermediaire"), ("Docker", "debutant")], ("Master 1 Informatique", 2025), ("Technicien réseau", "Airtel", 10), True),
    ("Lalaina Rabe", "Informatique", "L3", "Développeur full-stack", "Full-stack JavaScript et Python, goût pour le travail en équipe agile.", [("JavaScript", "avance"), ("Node.js", "intermediaire"), ("React", "intermediaire"), ("Python", "intermediaire"), ("MongoDB", "intermediaire"), ("Agile / Scrum", "intermediaire")], ("Licence 3 Informatique", 2025), ("Stagiaire développeur", "Startup Tana", 3), True),
    ("Voahangy Ravelo", "Gestion", "M1", "Assistante comptable et financière", "Rigueur et maîtrise de la comptabilité générale et analytique.", [("Comptabilité", "avance"), ("Excel", "expert"), ("Finance", "intermediaire"), ("ERP", "intermediaire")], ("Master 1 Gestion", 2025), ("Stagiaire comptabilité", "BNI Madagascar", 6), True),
    ("Nirina Rasolo", "Management", "M2", "Chef de projet junior", "Gestion de projet, méthodes agiles et pilotage d'équipes pluridisciplinaires.", [("Gestion de projet", "avance"), ("Agile / Scrum", "avance"), ("Management", "intermediaire"), ("Communication", "avance"), ("Excel", "avance")], ("Master 2 Management", 2025), ("Assistant chef de projet", "Ambatovy", 12), True),
    ("Solofo Andry", "Communication", "L3", "Community manager", "Stratégie de contenu, réseaux sociaux et création visuelle.", [("Marketing digital", "avance"), ("Photoshop", "intermediaire"), ("Communication", "avance"), ("Rédaction", "avance")], ("Licence 3 Communication", 2025), ("Stagiaire communication", "Radio Mada", 5), True),
    ("Aina Rakotomalala", "Informatique", "M2", "Ingénieur DevOps junior", "Automatisation, conteneurs et intégration continue.", [("Docker", "avance"), ("Kubernetes", "intermediaire"), ("CI/CD", "avance"), ("Linux", "avance"), ("Git", "expert"), ("Python", "intermediaire")], ("Master 2 Informatique", 2025), ("Stagiaire DevOps", "Axian", 9), False),
    ("Miora Rasoanaivo", "Informatique", "L2", "Étudiante en informatique", "Je débute en développement et souhaite progresser.", [("HTML/CSS", "intermediaire"), ("Python", "debutant")], ("Licence 2 Informatique", 2025), ("Stage d'observation", "EMIT", 1), True),
    ("Tojo Ramanana", "Gestion", "L3", "Gestionnaire logistique", "Supply chain, gestion des stocks et relation fournisseurs.", [("Logistique", "avance"), ("Excel", "avance"), ("ERP", "intermediaire")], ("Licence 3 Gestion", 2025), ("Stagiaire logistique", "Jirama", 4), True),
    ("Safidy Ratsimba", "Informatique", "M1", "Développeur mobile Flutter", "Applications mobiles multiplateformes avec Flutter et Firebase.", [("Flutter", "avance"), ("Dart", "avance"), ("API REST", "intermediaire"), ("Git", "intermediaire")], ("Master 1 Informatique", 2025), ("Développeur mobile", "Freelance", 8), True),
]

OFFRES = [
    ("Stage Développeur Backend IA", "stage", "Stage de 6 mois : conception d'API REST et intégration de modèles d'IA (NLP) pour une plateforme interne.", "Informatique", "M1",
     [("Python", 5, "avance", True), ("FastAPI", 4, "intermediaire", False), ("PostgreSQL", 3, "intermediaire", False), ("Machine Learning", 3, "intermediaire", False), ("Docker", 2, "debutant", False)]),
    ("Chef de projet digital (CDD)", "emploi", "Pilotage de projets de transformation digitale, animation d'équipes agiles et reporting.", None, "M1",
     [("Gestion de projet", 5, "avance", True), ("Agile / Scrum", 4, "intermediaire", False), ("Communication", 3, "avance", False), ("Excel", 2, "intermediaire", False)]),
    ("Projet application web étudiante", "projet", "Création d'une interface web moderne pour la vie étudiante.", "Informatique", "L3",
     [("React", 5, "intermediaire", True), ("Tailwind CSS", 3, "intermediaire", False), ("JavaScript", 3, "intermediaire", False), ("UI/UX Design", 2, "debutant", False)]),
]


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_referentiels(db)
        if db.scalar(select(Utilisateur.id).where(Utilisateur.email == "admin@emit.mg")):
            print("Données de démo déjà présentes.")
            return
        admin = Administrateur(nom="Admin EMIT", email="admin@emit.mg", mot_de_passe_hash=hash_password("Admin12345"))
        db.add(admin)
        modele = db.scalar(select(ModelCV))
        h = hash_password("Etudiant123")
        mentions = {m.nom: m for m in db.scalars(select(Mention))}
        for i, (nom, mention, niv, titre, resume, comps, (dip, an), (poste, ent, mois), dispo) in enumerate(ETUDIANTS, 1):
            niveau = db.scalar(select(NiveauEtude).where(NiveauEtude.mention_id == mentions[mention].id, NiveauEtude.nom == niv))
            e = Etudiant(nom=nom, email=f"etudiant{i}@emit.mg", mot_de_passe_hash=h, matricule=f"EMIT-{2020 + i % 4}-{i:03d}",
                         mention_id=mentions[mention].id, niveau_id=niveau.id, disponible=dispo,
                         dispo_debut=date(2026, 11, 1), dispo_fin=date(2027, 5, 31), dispo_type="tous")
            e.profil = Profile(telephone=f"+261 34 00 000 {i:02d}")
            prenom, _, nom_famille = nom.partition(" ")
            db.add(EtudiantAutorise(nom=nom_famille, prenom=prenom, email=e.email, matricule=e.matricule, compte_cree_le=None))
            cv = CV(titre=titre, resume=resume, statut="publie", est_public=True, model_cv_id=modele.id if modele else None)
            cv.competences = [Competence(nom=n, niveau_maitrise=l) for n, l in comps]
            cv.formations = [Formation(diplome=dip, etablissement="EMIT", annee=an)]
            fin = date(2024 + mois // 12, 1 + (mois % 12), 1)
            exp = Experience(poste=poste, entreprise=ent, date_debut=date(2024, 1, 1), date_fin=fin, dure=formater_duree(date(2024, 1, 1), fin))
            exp.description = resume
            cv.experiences = [exp]
            cv.projets = [Projet(titre=f"Projet de fin d'études : {titre.lower()}", description=resume, type="academique", annee=an)]
            e.cvs.append(cv)
            db.add(e)
        db.commit()
        for u in db.scalars(select(Etudiant)):
            a = db.scalar(select(EtudiantAutorise).where(EtudiantAutorise.matricule == u.matricule))
            if a:
                a.utilisateur_id = u.id
        db.commit()
        for cv_id in db.scalars(select(CV.id)).all():
            analyser_cv(db, cv_id)
        for titre, typ, desc, mention, niv, criteres in OFFRES:
            o = Offre(admin_id=admin.id, titre=titre, type=typ, description=desc, statut="publiee",
                      periode_debut=date(2026, 12, 1), periode_fin=date(2027, 5, 31), date_limite=date(2027, 12, 31))
            if mention:
                o.mentions = [mentions[mention]]
                o.niveau_min = db.scalar(select(NiveauEtude).where(NiveauEtude.mention_id == mentions[mention].id, NiveauEtude.nom == niv))
            o.niveau_obligatoire = False
            o.criteres = [CritereOffre(competence_id=competence_catalogue(db, c).id, poids=p, niveau_requis=n, obligatoire=ob) for c, p, n, ob in criteres]
            db.add(o)
            db.commit()
            recompute_offer(db, o.id, declencheur="seed-demo")
        print("Démo prête.  admin@emit.mg / Admin12345  ·  etudiant1@emit.mg / Etudiant123")


if __name__ == "__main__":
    main()
