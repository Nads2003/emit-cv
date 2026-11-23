import io

from docx import Document
from reportlab.pdfgen import canvas

from app.core.config import settings

API = "/api/v1"


def faire_docx(lignes: list[str]) -> bytes:
    doc = Document()
    for l in lignes:
        doc.add_paragraph(l)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def faire_pdf(lignes: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for l in lignes:
        c.drawString(50, y, l)
        y -= 18
    c.save()
    return buf.getvalue()


CV_TEXTE = [
    "Hery Rakoto", "Développeur backend", "Profil",
    "Étudiant en Master 1 Informatique, passionné par les API REST, Python et FastAPI.",
    "Compétences", "Python (avancé), FastAPI, PostgreSQL, Docker, Git, travail en équipe",
    "Formation", "Master 1 Informatique - EMIT - 2025", "Licence 3 Informatique - EMIT - 2024",
    "Expériences professionnelles", "Stagiaire développeur - Orange Madagascar - Mars 2024 - Août 2024",
    "Développement d'une API interne avec FastAPI.",
]


def test_creation_modification_completude(client, faire_etudiant):
    h, _ = faire_etudiant()
    r = client.post(f"{API}/cvs", headers=h, json={"titre": "Mon CV", "competences": [{"nom": "postgres"}, {"nom": "Postgres"}, {"nom": "react js"}]})
    assert r.status_code == 201
    cv = r.json()
    assert [c["nom"] for c in cv["competences"]] == ["PostgreSQL", "React"]  # canonisées + dédoublonnées
    assert cv["statut"] == "brouillon" and cv["completude"] < 100
    r2 = client.put(f"{API}/cvs/{cv['id']}", headers=h, json={"titre": "Mon CV v2", "resume": "x" * 40, "model_cv_id": 1, "competences": [{"nom": "Python"}] * 3,
                    "formations": [{"diplome": "L3"}], "experiences": [{"poste": "Stage", "date_debut": "2024-01-01", "date_fin": "2024-07-01"}]})
    assert r2.status_code == 200 and r2.json()["titre"] == "Mon CV v2"
    assert r2.json()["experiences"][0]["duree_mois"] == 6


def test_validation_des_donnees(client, faire_etudiant):
    h, _ = faire_etudiant()
    mauvais = {"titre": "CV", "experiences": [{"poste": "X", "date_debut": "2024-05-01", "date_fin": "2024-01-01"}]}
    assert client.post(f"{API}/cvs", headers=h, json=mauvais).status_code == 422
    assert client.post(f"{API}/cvs", headers=h, json={"titre": "CV", "formations": [{"diplome": "X", "annee": 1800}]}).status_code == 422
    assert client.post(f"{API}/cvs", headers=h, json={"titre": "CV", "competences": [{"nom": "X", "niveau_maitrise": "dieu"}]}).status_code == 422
    assert client.post(f"{API}/cvs", headers=h, json={"titre": "CV", "model_cv_id": 999}).status_code == 422


def test_publication_exige_un_cv_complet(client, faire_etudiant):
    h, _ = faire_etudiant()
    cv_id = client.post(f"{API}/cvs", headers=h, json={"titre": "Vide"}).json()["id"]
    assert client.post(f"{API}/cvs/{cv_id}/publier", headers=h).status_code == 422


def test_isolation_entre_etudiants(client, faire_etudiant, publier_cv):
    h1, _ = faire_etudiant()
    h2, _ = faire_etudiant()
    cv_id = publier_cv(h1, "CV privé", [("Python", "avance")])
    for methode, url in [("get", f"{API}/cvs/{cv_id}"), ("delete", f"{API}/cvs/{cv_id}"), ("post", f"{API}/cvs/{cv_id}/depublier")]:
        assert getattr(client, methode)(url, headers=h2).status_code == 404
    assert client.get(f"{API}/cvs", headers=h2).json() == []


def test_admin_ne_voit_que_les_cv_publies(client, admin, faire_etudiant, publier_cv):
    h, _ = faire_etudiant()
    brouillon = client.post(f"{API}/cvs", headers=h, json={"titre": "Brouillon"}).json()["id"]
    publie = publier_cv(h, "Publié", [("Python", "avance")])
    assert client.get(f"{API}/cvs/{brouillon}", headers=admin).status_code == 403
    assert client.get(f"{API}/cvs/{publie}", headers=admin).status_code == 200


def test_import_docx_preremplit_le_cv(client, faire_etudiant):
    h, _ = faire_etudiant()
    r = client.post(f"{API}/cvs/import", headers=h, files={"file": ("cv.docx", faire_docx(CV_TEXTE), "application/octet-stream")})
    assert r.status_code == 201, r.text
    cv = r.json()
    noms = {c["nom"] for c in cv["competences"]}
    assert {"Python", "FastAPI", "PostgreSQL", "Docker", "Git"} <= noms
    assert next(c for c in cv["competences"] if c["nom"] == "Python")["niveau_maitrise"] == "avance"
    assert any("Master 1" in f["diplome"] for f in cv["formations"])
    assert cv["experiences"] and cv["experiences"][0]["date_debut"] == "2024-03-01" and cv["experiences"][0]["dure"] == "5 mois"
    assert cv["analyse"]["statut"] in ("ok", "en_attente")
    assert cv["source"] == "importe" and cv["statut"] == "brouillon" and cv["a_fichier"]
    dl = client.get(f"{API}/cvs/{cv['id']}/fichier", headers=h)
    assert dl.status_code == 200 and dl.content[:2] == b"PK"


def test_import_pdf(client, faire_etudiant):
    h, _ = faire_etudiant()
    pdf = faire_pdf(["Tiana Andrianina", "Competences", "React, JavaScript, Tailwind CSS, Python et Docker pour le web moderne", "Formation", "Licence 3 Informatique 2025"])
    r = client.post(f"{API}/cvs/import", headers=h, files={"file": ("cv.pdf", pdf, "application/pdf")})
    assert r.status_code == 201, r.text
    assert {"React", "JavaScript", "Tailwind CSS"} <= {c["nom"] for c in r.json()["competences"]}


def test_import_rejette_les_fichiers_dangereux(client, faire_etudiant, monkeypatch):
    h, _ = faire_etudiant()
    # faux PDF (contenu exécutable déguisé) : détecté par les octets magiques, pas par l'extension
    r = client.post(f"{API}/cvs/import", headers=h, files={"file": ("cv.pdf", b"MZ\x90\x00 malware", "application/pdf")})
    assert r.status_code == 422 and "PDF et DOCX" in r.json()["detail"]
    assert client.post(f"{API}/cvs/import", headers=h, files={"file": ("cv.pdf", b"%PDF-1.4 casse", "application/pdf")}).status_code == 422
    monkeypatch.setattr(settings, "max_cv_mb", 0)
    assert client.post(f"{API}/cvs/import", headers=h, files={"file": ("cv.docx", faire_docx(CV_TEXTE), "x")}).status_code == 413


def test_photo_validation_et_acces(client, faire_etudiant, admin):
    h, eid = faire_etudiant()
    h2, _ = faire_etudiant()
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 50
    assert client.post(f"{API}/etudiants/moi/photo", headers=h, files={"file": ("p.png", png, "image/png")}).status_code == 204
    assert client.post(f"{API}/etudiants/moi/photo", headers=h, files={"file": ("p.png", b"GIF89a....", "image/png")}).status_code == 422
    assert client.get(f"{API}/etudiants/{eid}/photo", headers=h).status_code == 200
    assert client.get(f"{API}/etudiants/{eid}/photo", headers=admin).status_code == 200
    assert client.get(f"{API}/etudiants/{eid}/photo", headers=h2).status_code == 403


def test_profil_et_disponibilite(client, faire_etudiant):
    h, _ = faire_etudiant()
    r = client.put(f"{API}/etudiants/moi/disponibilite", headers=h, json={"disponible": True, "dispo_debut": "2026-12-01", "dispo_fin": "2027-03-01", "dispo_type": "stage"})
    assert r.status_code == 200 and r.json()["dispo_type"] == "stage"
    assert client.put(f"{API}/etudiants/moi/disponibilite", headers=h, json={"disponible": True, "dispo_debut": "2027-03-01", "dispo_fin": "2026-12-01"}).status_code == 422
    r = client.put(f"{API}/etudiants/moi", headers=h, json={"nom": "Nouveau Nom", "matricule": "MAT-001", "mention_id": 1, "telephone": "+261 34 12 345 67"})
    assert r.status_code == 200 and r.json()["nom"] == "Nouveau Nom"
    assert client.put(f"{API}/etudiants/moi", headers=h, json={"nom": "N N", "matricule": "MAT-001", "mention_id": 1, "telephone": "abc"}).status_code == 422


# ------------------------------------------------------------------ extraction : fichiers scannés, vides, corrompus, malveillants
def pdf_image_seule() -> bytes:
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    img = io.BytesIO()
    Image.new("RGB", (60, 60), "white").save(img, "PNG")
    c.drawImage(ImageReader(io.BytesIO(img.getvalue())), 50, 600, 200, 200)  # une « page scannée » : une image, aucun texte
    c.save()
    return buf.getvalue()


def test_pdf_scanne_detecte_ocr_requis(client, faire_etudiant):
    h, _ = faire_etudiant()
    r = client.post(f"{API}/cvs/import", headers=h, files={"file": ("scan.pdf", pdf_image_seule(), "application/pdf")})
    assert r.status_code == 201, r.text
    cv = r.json()
    assert cv["analyse"]["statut"] == "ocr_requis" and "scanné" in cv["analyse"]["message"] and cv["competences"] == [] and cv["statut"] == "brouillon"
    # l'étudiant peut compléter son CV à la main : l'analyse repasse à « ok »
    put = client.put(f"{API}/cvs/{cv['id']}", headers=h, json={"titre": "Mon CV", "competences": [{"nom": "Python"}]})
    assert put.status_code == 200
    assert client.get(f"{API}/cvs/{cv['id']}", headers=h).json()["analyse"]["statut"] == "ok"


def test_pdf_sans_texte_ni_image_est_vide(client, faire_etudiant):
    h, _ = faire_etudiant()
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.showPage()
    c.save()
    r = client.post(f"{API}/cvs/import", headers=h, files={"file": ("vide.pdf", buf.getvalue(), "application/pdf")})
    assert r.status_code == 201 and r.json()["analyse"]["statut"] == "vide"


def test_fichiers_vides_corrompus_et_malveillants_refuses(client, faire_etudiant):
    import zipfile
    h, _ = faire_etudiant()
    post = lambda nom, data: client.post(f"{API}/cvs/import", headers=h, files={"file": (nom, data, "application/octet-stream")})
    assert post("v.pdf", b"").status_code == 422
    assert post("c.pdf", b"%PDF-1.4\n garbage garbage").status_code == 422
    assert post("c.docx", b"PK\x03\x04 pas un zip").status_code == 422
    assert post("x.exe", b"MZ\x90\x00").status_code == 422
    assert post("s.png", b"\x89PNG\r\n\x1a\n").status_code == 422
    base = faire_pdf(["Competences", "Python et Docker pour des projets web modernes"])
    assert post("ok.pdf", base).status_code == 201
    # PDF contenant du JavaScript / une action automatique / un fichier incorporé : refusé
    for marqueur in (b"/JavaScript", b"/JS (app.alert(1))", b"/OpenAction", b"/Launch", b"/EmbeddedFile"):
        r = post("piege.pdf", base + b"\n1 0 obj << " + marqueur + b" >> endobj")
        assert r.status_code == 422 and "contenu actif" in r.json()["detail"], marqueur
    # DOCX avec macros VBA, sans document.xml, ou « bombe de décompression »
    def zip_docx(extra=None, doc=True, gros=0):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
            if doc:
                z.writestr("word/document.xml", "<w:document/>")
            for k, v in (extra or {}).items():
                z.writestr(k, v)
            if gros:
                z.writestr("word/media/gros.bin", b"\0" * gros)
        return b.getvalue()
    assert "macros" in post("m.docx", zip_docx({"word/vbaProject.bin": b"x"})).json()["detail"]
    assert "Word valide" in post("n.docx", zip_docx({"docProps/app.xml": "x"}, doc=False)).json()["detail"]
    assert "volumineux" in post("b.docx", zip_docx(gros=70 * 1024 * 1024)).json()["detail"]


def test_taille_maximale_et_isolation_du_fichier(client, faire_etudiant, monkeypatch):
    h, _ = faire_etudiant()
    h2, _ = faire_etudiant()
    cv = client.post(f"{API}/cvs/import", headers=h, files={"file": ("a.pdf", faire_pdf(["Competences", "Python Docker Git et FastAPI pour le web"]), "application/pdf")}).json()
    assert client.get(f"{API}/cvs/{cv['id']}/fichier", headers=h).status_code == 200
    assert client.get(f"{API}/cvs/{cv['id']}/fichier", headers=h2).status_code == 404  # confidentialité : un autre étudiant ne peut pas le lire


def test_import_differe_puis_extraction_par_le_worker_et_cache(client, faire_etudiant):
    from app.db.session import SessionLocal
    from app.models import CV, Etudiant
    from app.services import cv_service, taches
    from app.services.analyse import analyser_cv
    from sqlalchemy import select
    h, eid = faire_etudiant()
    with SessionLocal() as db:
        etu = db.get(Etudiant, eid)
        cv = cv_service.creer_cv_depuis_octets(db, etu, faire_docx(CV_TEXTE), "lot.docx", differe=True)  # importation en LOT : extraction repoussée
        assert cv.competences == [] and cv.analyse.statut == "en_attente"
        taches.enqueue(db, "analyse_cv", cv.id, "lot")
        cv_id = cv.id
    assert taches.vider_la_file() >= 1
    with SessionLocal() as db:
        cv = db.scalar(select(CV).where(CV.id == cv_id))
        assert cv.analyse.statut == "ok" and {c.nom for c in cv.competences} >= {"Python", "FastAPI"} and cv.analyse.caracteristiques["competences"]
        premier = cv.analyse.analysee_le
        # CACHE : contenu inchangé => aucune réanalyse
        r = analyser_cv(db, cv_id)
        assert r["cache"] is True and r["change"] is False and db.get(CV, cv_id).analyse.analysee_le == premier
        # contenu modifié => réanalysé
        db.get(CV, cv_id).resume = "Résumé modifié avec Kubernetes."
        db.commit()
        r = analyser_cv(db, cv_id)
        assert r["change"] is True and r["cache"] is False
