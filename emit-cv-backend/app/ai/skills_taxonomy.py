"""Référentiel de compétences : nom canonique -> synonymes.

Sert à (1) normaliser les compétences saisies, (2) détecter des compétences dans le texte brut d'un CV
ou d'une offre. Facile à enrichir : il suffit d'ajouter des lignes au dictionnaire.
"""
import re
import unicodedata


def normalize(text: str) -> str:
    """Minuscules, sans accents, ponctuation -> espaces (on garde + et # : c++, c#)."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^a-z0-9+#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


SKILLS: dict[str, list[str]] = {
    # --- Langages ---
    "Python": ["python", "python3", "py"],
    "Java": ["java", "j2ee", "jee"],
    "JavaScript": ["javascript", "js", "ecmascript", "es6"],
    "TypeScript": ["typescript", "ts"],
    "PHP": ["php"],
    "C": ["langage c"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", "c sharp"],
    "Kotlin": ["kotlin"],
    "Dart": ["dart"],
    "R": ["langage r", "r studio", "rstudio"],
    "SQL": ["sql", "t sql", "pl sql"],
    # --- Web ---
    "HTML/CSS": ["html", "css", "html5", "css3", "html css"],
    "React": ["react", "reactjs", "react js"],
    "Vue.js": ["vue", "vuejs", "vue js"],
    "Angular": ["angular", "angularjs"],
    "Node.js": ["node", "nodejs", "node js"],
    "Django": ["django"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "Laravel": ["laravel"],
    "Spring Boot": ["spring", "spring boot"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "Bootstrap": ["bootstrap"],
    "API REST": ["api rest", "rest api", "restful", "api"],
    "WordPress": ["wordpress"],
    # --- Mobile ---
    "Flutter": ["flutter"],
    "React Native": ["react native"],
    "Android": ["android"],
    # --- Données / IA ---
    "Machine Learning": ["machine learning", "apprentissage automatique", "ml"],
    "Deep Learning": ["deep learning", "apprentissage profond", "reseaux de neurones"],
    "NLP": ["nlp", "traitement du langage naturel", "traitement automatique des langues", "spacy"],
    "Data Science": ["data science", "science des donnees", "data scientist"],
    "Data Analysis": ["analyse de donnees", "data analysis", "data analyst", "analyse des donnees"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau software", "tableau"],
    "Excel": ["excel", "microsoft excel", "tableur"],
    "Statistiques": ["statistiques", "statistique", "statistics"],
    "Big Data": ["big data", "hadoop", "spark"],
    "ETL": ["etl", "talend"],
    # --- Bases de données ---
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql", "mariadb"],
    "MongoDB": ["mongodb", "mongo"],
    "Oracle": ["oracle"],
    "SQLite": ["sqlite"],
    "Redis": ["redis"],
    "Modélisation UML": ["uml", "merise", "modelisation uml", "modelisation de donnees"],
    # --- DevOps / systèmes / réseaux ---
    "Docker": ["docker", "conteneurisation"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "gitlab", "versionnement"],
    "CI/CD": ["ci cd", "cicd", "integration continue", "jenkins", "github actions"],
    "Linux": ["linux", "ubuntu", "debian", "bash", "shell"],
    "Cloud": ["cloud", "aws", "azure", "gcp", "google cloud"],
    "Réseaux": ["reseau", "reseaux", "cisco", "tcp ip", "routage", "networking", "ccna"],
    "Cybersécurité": ["cybersecurite", "securite informatique", "securite des systemes", "pentest", "cybersecurity"],
    "Administration système": ["administration systeme", "administration reseau", "windows server", "active directory"],
    "Télécommunications": ["telecommunications", "telecom", "telecoms", "fibre optique"],
    # --- Gestion de projet / métier ---
    "Gestion de projet": ["gestion de projet", "gestion des projets", "chef de projet", "project management", "pmp"],
    "Agile / Scrum": ["agile", "scrum", "kanban", "methode agile", "methodes agiles"],
    "Management": ["management", "encadrement d equipe", "gestion d equipe", "leadership"],
    "Comptabilité": ["comptabilite", "comptable", "comptabilite generale", "comptabilite analytique"],
    "Finance": ["finance", "analyse financiere", "gestion financiere", "controle de gestion"],
    "Marketing digital": ["marketing digital", "marketing", "seo", "community management", "reseaux sociaux"],
    "Gestion des ressources humaines": ["ressources humaines", "gestion des ressources humaines", "gestion rh", "rh", "recrutement"],
    "Logistique": ["logistique", "supply chain", "gestion de stock", "gestion des stocks"],
    "Entrepreneuriat": ["entrepreneuriat", "creation d entreprise", "business plan"],
    "Vente et négociation": ["vente", "negociation", "relation client", "prospection"],
    "ERP": ["erp", "sap", "odoo", "dolibarr", "sage"],
    "Audit": ["audit", "audit interne", "audit informatique"],
    # --- Design / bureautique ---
    "UI/UX Design": ["ui ux", "ux", "ui", "figma", "design d interface", "maquettage", "wireframe"],
    "Photoshop": ["photoshop", "adobe photoshop"],
    "Illustrator": ["illustrator", "adobe illustrator"],
    "Montage vidéo": ["montage video", "premiere pro", "after effects"],
    "Bureautique": ["bureautique", "word", "powerpoint", "microsoft office", "pack office", "ms office"],
    # --- Transversales ---
    "Communication": ["communication", "communication orale", "communication ecrite", "prise de parole"],
    "Travail en équipe": ["travail en equipe", "esprit d equipe", "team work", "teamwork", "collaboration"],
    "Anglais": ["anglais", "english", "toeic", "toefl"],
    "Français": ["francais"],
    "Malgache": ["malgache"],
    "Résolution de problèmes": ["resolution de problemes", "problem solving", "esprit d analyse"],
    "Gestion du temps": ["gestion du temps", "organisation", "rigueur"],
    "Pédagogie": ["pedagogie", "formation des utilisateurs", "enseignement", "tutorat"],
    "Rédaction": ["redaction", "redaction de rapports", "documentation technique"],
}

# Index inverse : synonyme normalisé -> nom canonique
_SYNONYM_TO_CANON: dict[str, str] = {}
for _canon, _syns in SKILLS.items():
    _SYNONYM_TO_CANON[normalize(_canon)] = _canon
    for _s in _syns:
        _SYNONYM_TO_CANON[normalize(_s)] = _canon

# Motifs précompilés (les synonymes les plus longs d'abord pour éviter les chevauchements)
_PATTERNS: list[tuple[re.Pattern, str]] = []
for _syn, _canon in sorted(_SYNONYM_TO_CANON.items(), key=lambda kv: -len(kv[0])):
    _PATTERNS.append((re.compile(r"(?<![a-z0-9+#])" + re.escape(_syn) + r"(?![a-z0-9+#])"), _canon))


def canonical(name: str) -> str:
    """Nom canonique d'une compétence saisie librement (ou le nom nettoyé si inconnue)."""
    n = normalize(name)
    return _SYNONYM_TO_CANON.get(n, (name or "").strip())


def canonical_key(name: str) -> str:
    """Clé de comparaison : canonique normalisé. 'Postgres' et 'PostgreSQL' donnent la même clé."""
    return normalize(canonical(name))


def extract_skills(text: str) -> list[str]:
    """Détecte les compétences connues dans un texte libre. Retourne des noms canoniques, sans doublon."""
    norm = normalize(text)
    found: dict[str, None] = {}
    for pattern, canon in _PATTERNS:
        if canon in found:
            continue
        if pattern.search(norm):
            found[canon] = None
            # on masque le motif trouvé pour que "react native" ne déclenche pas aussi "react"
            norm = pattern.sub(" ", norm)
    return list(found)


def all_skill_names() -> list[str]:
    return sorted(SKILLS)


SOFT_SKILLS = {"Communication", "Travail en équipe", "Résolution de problèmes", "Gestion du temps", "Management", "Pédagogie", "Rédaction",
               "Entrepreneuriat", "Vente et négociation"}


def is_soft(skill: str) -> bool:
    return canonical(skill) in SOFT_SKILLS


def mask_skills(text: str) -> str:
    """Texte normalisé dont les compétences du référentiel sont retirées.
    Sert au critère « Adéquation aux missions » pour ne pas compter une seconde fois les compétences (déjà notées par le critère 1)."""
    norm = normalize(text)
    for pattern, _ in _PATTERNS:
        norm = pattern.sub(" ", norm)
    return re.sub(r"\s+", " ", norm).strip()
