"""Parseur heuristique : texte brut d'un CV -> compétences, formations, expériences, résumé.

Approche volontairement simple et robuste (sans dépendance lourde) :
  1. découpage en sections grâce aux titres usuels (FR/EN) ;
  2. compétences = référentiel (skills_taxonomy) appliqué à tout le texte ;
  3. formations / expériences = lignes contenant des motifs de diplômes / de périodes.
Le résultat est un PRÉ-REMPLISSAGE : l'étudiant relit et corrige son CV avant publication.
"""
import re
from datetime import date

from app.ai.skills_taxonomy import extract_skills, normalize

SECTION_TITLES = {
    "resume": ["profil", "resume", "a propos", "objectif", "summary", "about"],
    "competences": ["competences", "competence", "skills", "savoir faire", "outils", "langages", "technologies", "langues"],
    "formations": ["formation", "formations", "etudes", "parcours academique", "education", "diplomes", "cursus"],
    "experiences": ["experience", "experiences", "experience professionnelle", "experiences professionnelles", "stages", "parcours professionnel", "work experience"],
    "projets": ["projets", "projet", "projets academiques", "projets personnels", "realisations", "projects", "projets realises"],
}
DIPLOME_RE = re.compile(
    r"\b(licence|master|bts|dut|bac|baccalaureat|doctorat|ingenieur|dea|dess|mba|l[1-3]|m[1-2]|bachelor|diplome)\b", re.I
)
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
MONTHS = {
    "janvier": 1, "jan": 1, "january": 1, "fevrier": 2, "fev": 2, "february": 2, "mars": 3, "mar": 3, "march": 3,
    "avril": 4, "avr": 4, "april": 4, "mai": 5, "may": 5, "juin": 6, "jun": 6, "june": 6, "juillet": 7, "juil": 7,
    "july": 7, "aout": 8, "aug": 8, "august": 8, "septembre": 9, "sept": 9, "sep": 9, "september": 9, "octobre": 10,
    "oct": 10, "october": 10, "novembre": 11, "nov": 11, "november": 11, "decembre": 12, "dec": 12, "december": 12,
}
# ex: "Mars 2022 - Août 2022", "2021 – 2023", "03/2022 - présent"
_DATE = r"(?:(?:[A-Za-zéûô]+\.?\s+)?(?:0?[1-9]|1[0-2])/)?(?:[A-Za-zéûô]+\.?\s+)?(?:19|20)\d{2}"
PERIOD_RE = re.compile(rf"({_DATE})\s*(?:-|–|—|à|au|to)\s*({_DATE}|pr[ée]sent|aujourd'hui|en cours|now|actuel)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d[\d .-]{8,14}\d)")


def _parse_date(token: str) -> date | None:
    t = normalize(token)
    if any(w in t for w in ("present", "aujourd", "en cours", "now", "actuel")):
        return None
    year = YEAR_RE.search(t)
    if not year:
        return None
    month = 1
    m_num = re.search(r"\b(0?[1-9]|1[0-2])\b\s*(?=(?:19|20)\d{2})", t.replace("/", " "))
    if m_num:
        month = int(m_num.group(1))
    else:
        for word in t.split():
            if word in MONTHS:
                month = MONTHS[word]
                break
    return date(int(year.group(1)), month, 1)


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"entete": []}
    current = "entete"
    for line in lines:
        key = normalize(line)
        matched = None
        if 0 < len(key) <= 40:
            for name, titles in SECTION_TITLES.items():
                if key in titles or key.rstrip(" s") in titles:
                    matched = name
                    break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def _guess_level(text: str, skill: str) -> str:
    """Niveau de maîtrise déduit du contexte (ex. 'Python (avancé)'). Par défaut : intermédiaire."""
    norm = normalize(text)
    idx = norm.find(normalize(skill))
    window = norm[max(0, idx - 25): idx + len(skill) + 40] if idx >= 0 else ""
    if re.search(r"\b(expert|maitrise|excellent)\b", window):
        return "expert"
    if re.search(r"\b(avance|confirme|bon niveau)\b", window):
        return "avance"
    if re.search(r"\b(debutant|notions|basique|initiation)\b", window):
        return "debutant"
    return "intermediaire"


def parse_cv_text(text: str) -> dict:
    lines = [l.strip(" \t•-*▪●·") for l in text.replace("\r", "\n").split("\n")]
    lines = [l for l in lines if l]
    sections = _split_sections(lines)

    competences = [{"nom": s, "niveau_maitrise": _guess_level(text, s)} for s in extract_skills(text)]

    # --- Formations
    formations = []
    for line in sections.get("formations", []) or []:
        if DIPLOME_RE.search(normalize(line)) or YEAR_RE.search(line):
            annee = YEAR_RE.findall(line)
            parts = [p.strip() for p in re.split(r"\s[-–—|,]\s|\s\|\s", line) if p.strip()]
            diplome = next((p for p in parts if DIPLOME_RE.search(normalize(p))), parts[0] if parts else line)
            etab = next((p for p in parts if p != diplome and not YEAR_RE.fullmatch(p.strip())), "")
            formations.append({"diplome": diplome[:160], "etablissement": etab[:160], "annee": int(annee[-1]) if annee else None})
    # Si aucune section "Formation" claire : on cherche des diplômes dans tout le texte
    if not formations:
        for line in lines:
            if DIPLOME_RE.search(normalize(line)) and len(line) < 140:
                annee = YEAR_RE.findall(line)
                formations.append({"diplome": line[:160], "etablissement": "", "annee": int(annee[-1]) if annee else None})
    formations = formations[:8]

    # --- Expériences : une période de dates sert d'ancre ; le poste/entreprise sont autour
    experiences = []
    exp_lines = sections.get("experiences", []) or []
    i = 0
    while i < len(exp_lines):
        m = PERIOD_RE.search(exp_lines[i])
        if m:
            reste = (exp_lines[i][: m.start()] + " " + exp_lines[i][m.end():]).strip(" -–—|,:()")
            if not reste and i > 0:
                reste = exp_lines[i - 1]
            parts = [p.strip() for p in re.split(r"\s[-–—|@,]\s|\s(?:chez|at)\s", reste) if p.strip()]
            desc_lines = []
            j = i + 1
            while j < len(exp_lines) and not PERIOD_RE.search(exp_lines[j]) and len(desc_lines) < 4:
                desc_lines.append(exp_lines[j])
                j += 1
            experiences.append({
                "poste": (parts[0] if parts else "Expérience")[:160],
                "entreprise": (parts[1] if len(parts) > 1 else "")[:160],
                "date_debut": _parse_date(m.group(1)),
                "date_fin": _parse_date(m.group(2)),
                "description": " ".join(desc_lines)[:600],
            })
            i = j
        else:
            i += 1
    experiences = experiences[:8]

    # --- Projets : une ligne courte sans point final = titre ; les lignes suivantes = description
    projets, courant = [], None
    for ligne in sections.get("projets", []) or []:
        if EMAIL_RE.search(ligne) or PHONE_RE.search(ligne):  # coordonnées : ce n'est pas un projet
            continue
        if len(ligne) <= 90 and not ligne.endswith("."):
            courant = {"titre": ligne[:160], "description": "", "type": "personnel" if "perso" in normalize(ligne) else "academique",
                       "annee": int(YEAR_RE.findall(ligne)[-1]) if YEAR_RE.search(ligne) else None}
            projets.append(courant)
        elif courant is not None:
            courant["description"] = (courant["description"] + " " + ligne).strip()[:600]
    projets = projets[:8]

    resume = " ".join(sections.get("resume", []))[:600]
    if not resume:
        # à défaut : début du texte (hors coordonnées)
        resume = " ".join(l for l in sections.get("entete", [])[1:6] if "@" not in l and len(l) > 25)[:400]

    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    return {
        "titre": (sections.get("entete") or ["CV importé"])[0][:160] if sections.get("entete") else "CV importé",
        "resume": resume,
        "competences": competences,
        "formations": formations,
        "experiences": experiences,
        "projets": projets,
        "email_detecte": email.group(0) if email else None,
        "telephone_detecte": phone.group(0).strip() if phone else None,
    }
