"""Accès réservé aux étudiants autorisés : import de la liste officielle (Excel), inscription et vérification d'e-mail.

Règles de sécurité :
- l'autorisation est vérifiée CÔTÉ SERVEUR : (email, matricule, nom, prénom) doivent correspondre à une même entrée de la liste ;
- une entrée ne sert qu'une fois (colonne utilisateur_id UNIQUE) : impossible d'ouvrir deux comptes avec la même identité ;
- AUCUN compte n'est créé avant la confirmation de l'e-mail ; la confirmation exige le jeton reçu par e-mail ET le mot de passe choisi ;
- les réponses ne disent jamais si un e-mail/matricule existe, est déjà utilisé, ou si le nom diffère (message unique) ;
- jetons stockés hachés (SHA-256), à durée limitée, nombre d'essais limité ; compteurs de débit en base."""
import hashlib
import io
import re
import secrets
from datetime import timedelta

from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException
from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.skills_taxonomy import normalize
from app.core import ratelimit
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import (Administrateur, Etudiant, EtudiantAutorise, ImportLigne, ImportListe, InscriptionEnAttente, Mention, NiveauEtude, Profile,
                        Utilisateur, en_utc, utcnow)
from app.services import email as mail
from app.services.journal import journaliser

MATRICULE_RE = re.compile(r"^[A-Za-z0-9/_.-]{3,40}$")
MAX_XLSX = 2 * 1024 * 1024
MAX_LIGNES = 20000
MESSAGE_REFUS = "Inscription impossible : ces informations ne correspondent à aucun étudiant autorisé, ou ont déjà été utilisées. Vérifiez-les ou contactez l'administration."


def norm_email(e: str) -> str:
    return (e or "").strip().lower()


def norm_matricule(m: str) -> str:
    return (m or "").strip().upper()


def _cle_nom(s: str) -> str:
    return normalize(s)


def _hash_token(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


# ===================================================================================== Inscription
def _envoyer_lien(autorise: EtudiantAutorise, token: str) -> None:
    lien = f"{settings.public_url.rstrip('/')}/verification?token={token}"
    mail.envoyer(autorise.email, "Confirmez votre inscription à EMIT CV",
                 f"Bonjour {autorise.prenom},\n\nPour finaliser la création de votre compte, ouvrez ce lien puis saisissez le mot de passe choisi à l'inscription "
                 f"(valable {settings.verif_token_minutes} minutes) :\n\n{lien}\n\nSi vous n'êtes pas à l'origine de cette demande, ignorez ce message : aucun compte ne sera créé.")


def demander_inscription(db: Session, *, nom: str, prenom: str, email: str, matricule: str, mot_de_passe: str, mention_id: int, niveau_id: int | None, ip: str) -> None:
    ratelimit.verifier(db, f"inscription:ip:{ip}", settings.inscription_limit, 3600)
    ratelimit.verifier(db, f"inscription:mat:{norm_matricule(matricule)}", settings.inscription_limit_matricule, 3600)
    if not db.get(Mention, mention_id):
        raise HTTPException(422, "Mention inconnue.")
    if niveau_id:
        niv = db.get(NiveauEtude, niveau_id)
        if not niv or niv.mention_id != mention_id:
            raise HTTPException(422, "Niveau d'études invalide pour cette mention.")
    a = db.scalar(select(EtudiantAutorise).where(EtudiantAutorise.email == norm_email(email), EtudiantAutorise.matricule == norm_matricule(matricule)))
    ok = (a is not None and a.utilisateur_id is None and _cle_nom(a.nom) == _cle_nom(nom) and _cle_nom(a.prenom) == _cle_nom(prenom)
          and db.scalar(select(Utilisateur.id).where(Utilisateur.email == a.email)) is None
          and db.scalar(select(Etudiant.id).where(Etudiant.matricule == a.matricule)) is None)
    if not ok:
        raise HTTPException(403, MESSAGE_REFUS)
    ancienne = db.scalar(select(InscriptionEnAttente).where(InscriptionEnAttente.autorise_id == a.id))
    if ancienne:
        db.delete(ancienne)
        db.flush()
    token = secrets.token_urlsafe(32)
    db.add(InscriptionEnAttente(autorise_id=a.id, mdp_hash=hash_password(mot_de_passe), mention_id=mention_id, niveau_id=niveau_id,
                                token_hash=_hash_token(token), expire_le=utcnow() + timedelta(minutes=settings.verif_token_minutes)))
    db.commit()
    _envoyer_lien(a, token)


def confirmer_inscription(db: Session, *, token: str, mot_de_passe: str, ip: str) -> Utilisateur:
    ratelimit.verifier(db, f"verif:ip:{ip}", settings.verif_limit, 600)
    refus = HTTPException(400, "Lien invalide ou expiré, ou mot de passe incorrect. Refaites votre inscription pour recevoir un nouveau lien.")
    p = db.scalar(select(InscriptionEnAttente).where(InscriptionEnAttente.token_hash == _hash_token(token or "")))
    if p is None or en_utc(p.expire_le) < utcnow():
        if p is not None:
            db.delete(p)
            db.commit()
        raise refus
    if not verify_password(mot_de_passe, p.mdp_hash):
        p.tentatives += 1
        if p.tentatives >= settings.verif_max_tentatives:
            db.delete(p)
        db.commit()
        raise refus
    a = db.get(EtudiantAutorise, p.autorise_id, with_for_update=True)
    if a is None or a.utilisateur_id is not None:
        raise refus
    nom_complet = f"{a.prenom} {a.nom}".strip()
    etu = Etudiant(nom=nom_complet, email=a.email, mot_de_passe_hash=p.mdp_hash, matricule=a.matricule, mention_id=p.mention_id)
    etu.niveau_id = p.niveau_id
    etu.profil = Profile()
    etu.disponible = True
    try:
        db.add(etu)
        db.flush()
        a.utilisateur_id, a.compte_cree_le = etu.id, utcnow()
        db.delete(p)
        journaliser(db, etu.id, "Création du compte étudiant (e-mail vérifié)")
        db.commit()
    except IntegrityError:  # filet de sécurité : les contraintes d'unicité en base ont le dernier mot
        db.rollback()
        raise HTTPException(409, "Un compte existe déjà pour cette identité.")
    return etu


# ===================================================================================== Import Excel
ENTETES = {"nom": "nom", "prenom": "prenom", "email": "email", "e mail": "email", "courriel": "email", "matricule": "matricule"}


def _lire_xlsx(data: bytes) -> list[dict]:
    if len(data) > MAX_XLSX:
        raise HTTPException(413, "Fichier Excel trop volumineux (2 Mo maximum).")
    if data[:4] != b"PK\x03\x04":
        raise HTTPException(422, "Format invalide : un fichier Excel .xlsx est attendu.")
    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        lignes = list(ws.iter_rows(values_only=True, max_row=MAX_LIGNES + 2))
    except Exception:
        raise HTTPException(422, "Le fichier Excel est illisible ou corrompu.")
    if not lignes:
        raise HTTPException(422, "Le fichier Excel est vide.")
    cols = {}
    for i, h in enumerate(lignes[0]):
        cle = ENTETES.get(normalize(str(h or "")))
        if cle and cle not in cols:
            cols[cle] = i
    manquantes = {"nom", "prenom", "email", "matricule"} - set(cols)
    if manquantes:
        raise HTTPException(422, "En-têtes manquants dans la première ligne : " + ", ".join(sorted(manquantes)) + ". Attendu : Nom, Prénom, Email, Matricule.")
    if len(lignes) - 1 > MAX_LIGNES:
        raise HTTPException(413, f"Trop de lignes (maximum {MAX_LIGNES}).")
    out = []
    for n, row in enumerate(lignes[1:], start=2):
        vals = {k: ("" if row[i] is None else str(row[i]).strip()) for k, i in cols.items() if i < len(row)}
        if any(vals.values()):
            out.append({"numero": n, **{k: vals.get(k, "") for k in ("nom", "prenom", "email", "matricule")}})
    return out


def _valider_ligne(l: dict) -> str | None:
    if not (l["nom"] and l["prenom"] and l["email"] and l["matricule"]):
        return "Champ obligatoire manquant (nom, prénom, e-mail et matricule sont requis)."
    if len(l["nom"]) > 120 or len(l["prenom"]) > 120:
        return "Nom ou prénom trop long (120 caractères maximum)."
    if not MATRICULE_RE.match(l["matricule"]):
        return "Matricule invalide (3 à 40 caractères : lettres, chiffres, / _ . -)."
    try:
        validate_email(l["email"], check_deliverability=False)
    except EmailNotValidError:
        return "Adresse e-mail invalide."
    return None


def _classer(db: Session, lignes: list[dict]) -> list[dict]:
    """Ajoute à chaque ligne : action (nouveau|maj|inchange|erreur) et message. Détecte invalides, doublons dans le fichier, conflits avec la base."""
    par_mat = {a.matricule: a for a in db.scalars(select(EtudiantAutorise))}
    par_email = {a.email: a for a in par_mat.values()}
    vus_mat, vus_email = {}, {}
    for l in lignes:
        l["matricule"], l["email"] = norm_matricule(l["matricule"]), norm_email(l["email"])
        err = _valider_ligne(l)
        if not err:
            if l["matricule"] in vus_mat:
                err = f"Doublon dans le fichier : matricule déjà présent à la ligne {vus_mat[l['matricule']]}."
            elif l["email"] in vus_email:
                err = f"Doublon dans le fichier : e-mail déjà présent à la ligne {vus_email[l['email']]}."
        if not err:
            ex_m, ex_e = par_mat.get(l["matricule"]), par_email.get(l["email"])
            if ex_e is not None and (ex_m is None or ex_e.id != ex_m.id):
                err = f"Cet e-mail est déjà associé à un autre matricule ({ex_e.matricule})."
            elif ex_m is None:
                l["action"], l["message"] = "nouveau", ""
            elif (ex_m.nom, ex_m.prenom, ex_m.email) == (l["nom"], l["prenom"], l["email"]):
                l["action"], l["message"] = "inchange", ""
            elif ex_m.utilisateur_id is not None:
                err = "Entrée déjà liée à un compte étudiant : modification refusée."
            else:
                l["action"], l["message"] = "maj", "Les informations de cette entrée seront mises à jour."
        if err:
            l["action"], l["message"] = "erreur", err
        else:
            vus_mat[l["matricule"]] = l["numero"]
            vus_email[l["email"]] = l["numero"]
    return lignes


def apercu_import(db: Session, admin: Administrateur, nom_fichier: str, data: bytes) -> ImportListe:
    lignes = _classer(db, _lire_xlsx(data))
    cnt = {a: sum(1 for l in lignes if l["action"] == a) for a in ("nouveau", "maj", "inchange", "erreur")}
    imp = ImportListe(admin_id=admin.id, nom_fichier=(nom_fichier or "liste.xlsx")[:255], hash_fichier=hashlib.sha256(data).hexdigest(),
                      nb_lignes=len(lignes), nb_nouveaux=cnt["nouveau"], nb_maj=cnt["maj"], nb_inchanges=cnt["inchange"], nb_erreurs=cnt["erreur"])
    db.add(imp)
    db.flush()
    db.add_all(ImportLigne(import_id=imp.id, numero=l["numero"], nom=l["nom"][:255], prenom=l["prenom"][:255], email=l["email"][:255],
                           matricule=l["matricule"][:255], action=l["action"], message=l["message"]) for l in lignes)
    journaliser(db, admin.id, f"Aperçu d'import de la liste des étudiants : {imp.nom_fichier} ({len(lignes)} lignes, {cnt['erreur']} erreur(s))")
    db.commit()
    return imp


def confirmer_import(db: Session, admin: Administrateur, import_id: int, ignorer_erreurs: bool) -> ImportListe:
    imp = db.get(ImportListe, import_id, with_for_update=True)
    if imp is None:
        raise HTTPException(404, "Import introuvable.")
    if imp.statut != "apercu":
        raise HTTPException(409, "Cet import a déjà été traité.")
    if imp.nb_erreurs and not ignorer_erreurs:
        raise HTTPException(409, f"{imp.nb_erreurs} ligne(s) en erreur : corrigez le fichier, ou confirmez en ignorant ces lignes.")
    lignes = [{"numero": l.numero, "nom": l.nom, "prenom": l.prenom, "email": l.email, "matricule": l.matricule}
              for l in db.scalars(select(ImportLigne).where(ImportLigne.import_id == imp.id).order_by(ImportLigne.numero))]
    lignes = _classer(db, lignes)  # on re-vérifie : la base a pu changer depuis l'aperçu
    nouveaux = maj = 0
    for l in lignes:
        if l["action"] == "nouveau":
            db.add(EtudiantAutorise(nom=l["nom"], prenom=l["prenom"], email=l["email"], matricule=l["matricule"], import_id=imp.id))
            nouveaux += 1
        elif l["action"] == "maj":
            a = db.scalar(select(EtudiantAutorise).where(EtudiantAutorise.matricule == l["matricule"]))
            a.nom, a.prenom, a.email = l["nom"], l["prenom"], l["email"]
            maj += 1
    imp.statut, imp.confirme_le, imp.nb_nouveaux, imp.nb_maj = "confirme", utcnow(), nouveaux, maj
    journaliser(db, admin.id, f"Import confirmé de la liste des étudiants : {nouveaux} ajouté(s), {maj} mis à jour")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Conflit détecté pendant l'import (doublon). Relancez l'aperçu.")
    return imp
