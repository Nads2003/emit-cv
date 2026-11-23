"""Mesure le débit d'extraction + analyse sur de VRAIS fichiers PDF et DOCX générés (le test de charge principal part de CV déjà structurés).

    python -m scripts.mesure_extraction --n 200"""
import argparse
import io
import json
import random
import resource
import time

from docx import Document
from reportlab.pdfgen import canvas

from app.ai.extraction import extract_text_info
from app.ai.parser import parse_cv_text

LIGNES = ["Prenom NOM", "Développeur backend junior", "PROFIL", "Étudiant en Master 1 Informatique, passionné par les API REST et les bases de données.",
          "COMPÉTENCES", "Python (avancé), FastAPI, PostgreSQL, Docker, Git, Linux, travail en équipe", "FORMATION", "Master 1 Informatique - EMIT - 2025",
          "Licence 3 Informatique - EMIT - 2024", "EXPÉRIENCES PROFESSIONNELLES", "Stagiaire développeur - Orange Madagascar - Mars 2024 - Août 2024",
          "Développement d'une API interne et automatisation de déploiements.", "PROJETS", "Application de gestion de stock",
          "Application web de gestion pour une PME locale avec tableau de bord."]


def pdf(i):
    b = io.BytesIO(); c = canvas.Canvas(b); y = 800
    for l in LIGNES + [f"Référence {i}"]:
        c.drawString(50, y, l); y -= 18
    c.save(); return b.getvalue()


def docx(i):
    d = Document()
    for l in LIGNES + [f"Référence {i}"]:
        d.add_paragraph(l)
    b = io.BytesIO(); d.save(b); return b.getvalue()


def mesure(nom, fichiers):
    t = time.perf_counter(); ok = 0
    for f in fichiers:
        kind, texte, etat = extract_text_info(f)
        p = parse_cv_text(texte)
        ok += etat == "ok" and len(p["competences"]) >= 4 and len(p["formations"]) >= 1
    d = time.perf_counter() - t
    return {"format": nom, "fichiers": len(fichiers), "duree_s": round(d, 2), "fichiers_par_s": round(len(fichiers) / d, 1), "ms_par_fichier": round(1000 * d / len(fichiers), 1), "extraits_correctement": ok}


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--n", type=int, default=200); a = p.parse_args()
    res = [mesure("PDF", [pdf(i) for i in range(a.n)]), mesure("DOCX", [docx(i) for i in range(a.n)])]
    res.append({"pic_memoire_mo": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)})
    print(json.dumps(res, ensure_ascii=False, indent=1))
