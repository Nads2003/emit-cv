"""Import de la liste officielle depuis Excel : aperçu, erreurs, doublons, confirmation, mise à jour, droits."""
import io
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import EtudiantAutorise
from tests.conftest import autoriser

API = "/api/v1/admin/etudiants-autorises"
ENTETE = ["Nom", "Prénom", "Email", "Matricule"]


def xlsx(lignes, entete=ENTETE) -> bytes:
    wb = Workbook()
    ws = wb.active
    if entete:
        ws.append(entete)
    for l in lignes:
        ws.append(l)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def envoyer(client, headers, data, nom="liste.xlsx"):
    return client.post(f"{API}/import", headers=headers, files={"file": (nom, data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})


def total():
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(EtudiantAutorise))


def test_apercu_n_applique_rien_puis_confirmation_applique(client, admin):
    r = envoyer(client, admin, xlsx([["Rakoto", "Hery", "hery@emit-test.mg", "e-001"], ["Rabe", "Lalaina", "lalaina@emit-test.mg", "E-002"]]))
    assert r.status_code == 201 and r.json()["nb_nouveaux"] == 2 and r.json()["nb_erreurs"] == 0 and r.json()["statut"] == "apercu"
    assert total() == 0  # rien d'appliqué avant confirmation
    c = client.post(f"{API}/import/{r.json()['id']}/confirmer", headers=admin)
    assert c.status_code == 200 and c.json()["statut"] == "confirme" and total() == 2
    with SessionLocal() as db:
        assert db.scalar(select(EtudiantAutorise.matricule).order_by(EtudiantAutorise.id)) == "E-001"  # normalisé en majuscules
    assert client.post(f"{API}/import/{r.json()['id']}/confirmer", headers=admin).status_code == 409  # une seule application
    assert client.get(API, headers=admin, params={"q": "lalaina"}).json()["total"] == 1


def test_erreurs_doublons_et_lignes_invalides(client, admin):
    lignes = [["A", "Un", "a@emit-test.mg", "M-1"], ["B", "Deux", "a@emit-test.mg", "M-2"],  # e-mail dupliqué
              ["C", "Trois", "c@emit-test.mg", "M-1"],                                         # matricule dupliqué
              ["", "Vide", "d@emit-test.mg", "M-4"], ["E", "Cinq", "pas-un-email", "M-5"], ["F", "Six", "f@emit-test.mg", "a b"],
              ["G", "Sept", "g@emit-test.mg", "M-7"], [None, None, None, None]]  # dernière : ligne vide ignorée
    r = envoyer(client, admin, xlsx(lignes)).json()
    assert r["nb_lignes"] == 7 and r["nb_nouveaux"] == 2 and r["nb_erreurs"] == 5
    messages = " | ".join(l["message"] for l in r["lignes"])
    assert "Doublon" in messages and "obligatoire" in messages and "e-mail invalide" in messages and "Matricule invalide" in messages
    # confirmer sans ignorer les erreurs est refusé ; en ignorant, seules les lignes valides sont appliquées
    assert client.post(f"{API}/import/{r['id']}/confirmer", headers=admin).status_code == 409 and total() == 0
    ok = client.post(f"{API}/import/{r['id']}/confirmer", headers=admin, json={"ignorer_erreurs": True})
    assert ok.status_code == 200 and total() == 2


def test_format_et_entetes_invalides(client, admin):
    assert envoyer(client, admin, b"ceci n'est pas un fichier excel").status_code == 422
    assert envoyer(client, admin, b"PK\x03\x04 faux zip").status_code == 422
    r = envoyer(client, admin, xlsx([["a", "b", "c@emit-test.mg", "M1"]], entete=["Nom", "Prénom", "Mail", "Numéro"]))
    assert r.status_code == 422 and "matricule" in r.json()["detail"].lower()
    assert envoyer(client, admin, xlsx([], entete=None)).status_code == 422
    assert envoyer(client, admin, xlsx([["a", "b", "c@emit-test.mg", "M1"]], entete=["email", "MATRICULE", "prenom", "NOM"])).status_code == 201  # ordre/casse libres
    assert envoyer(client, admin, b"PK\x03\x04" + b"0" * (3 * 1024 * 1024)).status_code == 413
    assert total() == 0


def test_mise_a_jour_conflits_et_entrees_liees_a_un_compte(client, admin, faire_etudiant):
    autoriser("Ancien", "Nom", "maj@emit-test.mg", "M-100")
    autoriser("Autre", "Pers", "autre@emit-test.mg", "M-200")
    faire_etudiant("Hery Rakoto")  # MAT-001 / etu1@test.mg : entrée liée à un compte
    r = envoyer(client, admin, xlsx([["Nouveau", "Nom", "maj@emit-test.mg", "M-100"],       # mise à jour d'une entrée libre
                                      ["X", "Y", "autre@emit-test.mg", "M-300"],             # e-mail d'un autre matricule
                                      ["Changé", "Hery", "etu1@test.mg", "MAT-001"],         # entrée liée à un compte : refusé
                                      ["Autre", "Pers", "autre@emit-test.mg", "M-200"]])).json()  # identique : inchangé
    assert (r["nb_maj"], r["nb_inchanges"], r["nb_erreurs"]) == (1, 1, 2)
    msgs = " | ".join(l["message"] for l in r["lignes"])
    assert "autre matricule" in msgs and "déjà liée à un compte" in msgs
    client.post(f"{API}/import/{r['id']}/confirmer", headers=admin, json={"ignorer_erreurs": True})
    with SessionLocal() as db:
        a = db.scalar(select(EtudiantAutorise).where(EtudiantAutorise.matricule == "M-100"))
        assert (a.nom, a.prenom) == ("Nouveau", "Nom")


def test_annulation_et_droits(client, admin, faire_etudiant):
    h, _ = faire_etudiant()
    data = xlsx([["A", "B", "ab@emit-test.mg", "M-1"]])
    assert envoyer(client, h, data).status_code == 403  # un étudiant ne peut pas importer
    r = envoyer(client, admin, data).json()
    assert client.post(f"{API}/import/{r['id']}/confirmer", headers=h).status_code == 403
    assert client.post(f"{API}/import/{r['id']}/annuler", headers=admin).status_code == 204
    assert client.post(f"{API}/import/{r['id']}/confirmer", headers=admin).status_code == 409
    assert client.get(f"{API}/imports", headers=admin).json()[0]["statut"] == "annule"


def test_fichier_de_test_fourni_100_etudiants(client, admin):
    chemin = Path(__file__).resolve().parents[2] / "docs" / "etudiants_test_100.xlsx"
    r = envoyer(client, admin, chemin.read_bytes(), "etudiants_test_100.xlsx").json()
    assert (r["nb_lignes"], r["nb_nouveaux"], r["nb_erreurs"]) == (100, 100, 0)
    assert client.post(f"{API}/import/{r['id']}/confirmer", headers=admin).json()["nb_nouveaux"] == 100 and total() == 100
    # réimport du même fichier : tout est « inchangé », idempotent
    r2 = envoyer(client, admin, chemin.read_bytes()).json()
    assert (r2["nb_nouveaux"], r2["nb_inchanges"]) == (0, 100)
    # et un étudiant du fichier peut s'inscrire
    ins = client.post("/api/v1/auth/inscription", json={"nom": "TEST007", "prenom": "Etudiant007", "email": "etudiant007@example.org", "matricule": "TEST-EMIT-0007",
                                                       "mot_de_passe": "Motdepasse1", "mention_id": 1})
    assert ins.status_code == 202
