# EMIT-CV-IA

**Plateforme de gestion de CV et de recommandation de candidats à l'EMIT, assistée par IA.**

Lorsqu'une opportunité (stage, emploi ou projet) est disponible, il est difficile d'identifier rapidement les étudiants les plus qualifiés. EMIT-CV-IA centralise les CV des étudiants et utilise un module d'intelligence artificielle pour classer automatiquement les candidats les plus pertinents pour chaque offre.

> Ce dépôt contient le **front-end** (React). Le back-end est développé séparément avec **FastAPI**.

---

## Sommaire

- [Acteurs et fonctionnalités](#acteurs-et-fonctionnalités)
- [Stack technique](#stack-technique)
- [Démarrage rapide](#démarrage-rapide)
- [Variables d'environnement](#variables-denvironnement)
- [Mode démo (sans back-end)](#mode-démo-sans-back-end)
- [Structure du projet](#structure-du-projet)
- [Pages et routes](#pages-et-routes)
- [Contrat d'API pour le back-end FastAPI](#contrat-dapi-pour-le-back-end-fastapi)
- [Déploiement](#déploiement)
- [État d'avancement](#état-davancement)

---

## Acteurs et fonctionnalités

### Étudiant

- Créer un compte et se connecter (authentification JWT).
- Créer ou modifier son CV, importer un CV existant (PDF ou Word), ajouter compétences, formations et expériences, indiquer sa disponibilité. Aperçu en direct avec 3 modèles et export PDF.
- Consulter les offres disponibles (recherche, filtres) et postuler.
- Recevoir des recommandations d'offres avec un score de compatibilité.
- S'entraîner à l'entretien d'embauche avec un recruteur IA (retour et score par réponse, bilan final).
- Gérer son profil (photo, informations, mot de passe) et consulter ses notifications.

### Administrateur EMIT

- Publier, modifier, clôturer, republier ou supprimer une offre.
- Définir les critères d'une offre : compétence, niveau requis, poids (1 à 5), caractère obligatoire.
- Consulter les candidats recommandés par l'IA, voir leur classement, valider ou refuser un candidat.
- Filtrer et rechercher des profils (spécialité, niveau, disponibilité, compétence).
- Consulter l'historique de ses actions et ses notifications.

### Système IA

- Analyse des CV, calcul d'un score par candidat et par offre, classement des candidats.
- Simulation d'entretiens et évaluation des réponses.

---

## Stack technique

| Couche | Technologie |
| --- | --- |
| Front-end | React 19, Vite, React Router 7 |
| UI | Tailwind CSS 4, lucide-react, police Poppins |
| Requêtes HTTP | Axios (intercepteur JWT) |
| Back-end | FastAPI (Python) |
| Base de données | PostgreSQL (recommandé) |
| Authentification | JWT (access + refresh) |
| Module IA | Python : scikit-learn / spaCy / transformers |
| Déploiement | Front : Vercel ou Netlify — Back : Linux + Uvicorn/Gunicorn |

Fonctionnalités transverses du front : mode sombre / clair, interface en français et en anglais, responsive (mobile, tablette, desktop).

---

## Démarrage rapide

**Prérequis :** Node.js 20.19 ou plus récent (ou 22.12+) et npm.

```bash
# 1. Installer les dépendances
npm install

# 2. Créer le fichier d'environnement
cp .env.example .env

# 3. Lancer le serveur de développement
npm run dev
```

L'application est disponible sur http://localhost:5173.

### Scripts

| Commande | Rôle |
| --- | --- |
| `npm run dev` | Serveur de développement avec rechargement à chaud |
| `npm run build` | Build de production dans `dist/` |
| `npm run preview` | Prévisualise le build de production |
| `npm run lint` | Analyse du code (oxlint) |

---

## Variables d'environnement

Fichier `.env` à la racine (ne pas le versionner ; `.env.example` sert de modèle).
**Redémarrer `npm run dev` après toute modification.**

| Variable | Valeur par défaut | Description |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000/api` | URL de base de l'API FastAPI |
| `VITE_AUTH_MOCK` | *(non défini = démo active)* | `false` pour appeler le vrai back-end ; toute autre valeur utilise les données fictives |

---

## Mode démo (sans back-end)

Tant que `VITE_AUTH_MOCK` n'est pas égal à `false`, le front fonctionne seul avec des données fictives conservées dans le `localStorage` du navigateur.

**Comptes de test**

| Rôle | Identifiants |
| --- | --- |
| Administrateur | un email commençant par `admin` (ex. `admin@emit.mg`) + mot de passe de 4 caractères ou plus |
| Étudiant | tout autre email (ex. `etudiant@emit.mg`) + mot de passe de 4 caractères ou plus |

Pour tester l'erreur « email déjà utilisé » à l'inscription : utiliser un email commençant par `exist`.

Les offres créées côté administrateur apparaissent côté étudiant, les décisions de l'administrateur génèrent des notifications pour l'étudiant, etc. Pour repartir de zéro : vider le stockage local du site dans les outils de développement du navigateur.

**Passer au vrai back-end :** mettre `VITE_AUTH_MOCK=false` dans `.env` et redémarrer. Toute la communication réseau passe par les fichiers de `src/api/`.

---

## Structure du projet

```
emit-cv-front/
├── public/images/          → hero.jpg, logo-emit.png, services-*.jpg
├── .env / .env.example
├── vite.config.js          → plugins React + Tailwind, alias "@" → src/
└── src/
    ├── api/                → appels HTTP (un fichier par domaine) + mode démo
    ├── components/
    │   ├── admin/          → ProfileModal
    │   ├── common/         → Avatar, Logo, ScoreBadge, SectionTitle, ImageWithFallback
    │   ├── cv/             → CvEditor, CvPreview, Field, EditorSection
    │   ├── entretien/      → SetupForm, InterviewSession, InterviewResult
    │   ├── home/           → sections de la page d'accueil
    │   ├── layout/         → Navbar, Footer, Sidebar, NotificationBell
    │   └── offres/         → OffreCard, OffreFilters, OffreModal
    ├── constants/          → routes, rôles, listes académiques
    ├── context/            → AuthContext, ThemeContext, LanguageContext
    ├── data/               → données fictives et stockage de démonstration
    ├── hooks/              → useAuth, useTheme, useLanguage, useCv
    ├── i18n/               → translations.js (fr / en)
    ├── layouts/            → PublicLayout, SidebarLayout, EtudiantLayout, AdminLayout
    ├── pages/
    │   ├── public/         → Accueil, Offres, Contact, NotFound
    │   ├── auth/           → Login, Register
    │   ├── etudiant/       → Dashboard, MonCV, Entretien
    │   ├── admin/          → Dashboard, GestionOffres, OffreForm,
    │   │                     CandidatsRecommandes, RechercheProfils, Historique
    │   └── shared/         → Profil (étudiant et administrateur)
    ├── routes/             → AppRoutes, ProtectedRoute
    ├── styles/             → index.css (Tailwind, thème, impression du CV)
    └── utils/              → token, scoring, redirect, formatDate, image
```

### Conventions

- Alias d'import : `@/` pointe vers `src/`.
- Tous les textes passent par `t("cle.sous.cle")` (`useLanguage`) ; ajouter chaque nouvelle clé en **français et en anglais** dans `src/i18n/translations.js`.
- Les couleurs de marque sont définies dans `src/styles/index.css` (`brand`, `night`, `night-card`, `night-line`).
- Le mode sombre repose sur la classe `dark` placée sur `<html>`.

---

## Pages et routes

| Route | Accès | Page |
| --- | --- | --- |
| `/` | Public | Accueil |
| `/offres` | Public | Liste des offres, recherche, filtres, détail et candidature |
| `/contact` | Public | Formulaire de contact |
| `/login`, `/register` | Public | Connexion, inscription étudiant |
| `/etudiant` | Étudiant | Tableau de bord, offres recommandées avec score |
| `/etudiant/cv` | Ouvert (démo) | Mon CV : édition, import, aperçu, export PDF |
| `/etudiant/entretien` | Étudiant | Entretien avec l'IA |
| `/etudiant/profil` | Étudiant | Profil |
| `/admin` | Administrateur | Tableau de bord |
| `/admin/offres` | Administrateur | Gestion des offres |
| `/admin/offres/nouvelle`, `/admin/offres/:id/modifier` | Administrateur | Formulaire d'offre et de ses critères |
| `/admin/candidats` | Administrateur | Candidats recommandés et classement |
| `/admin/profils` | Administrateur | Recherche de profils |
| `/admin/historique` | Administrateur | Historique des actions |
| `/admin/profil` | Administrateur | Profil |

`ProtectedRoute` vérifie la connexion et le rôle : un visiteur est renvoyé vers `/login` (puis ramené à la page demandée), un utilisateur au mauvais rôle est renvoyé vers son propre espace.
> La protection du front ne remplace pas celle du back-end : **chaque endpoint doit contrôler le rôle côté serveur.**

---

## Contrat d'API pour le back-end FastAPI

Base : `VITE_API_URL` (par défaut `http://localhost:8000/api`). Format JSON, sauf mention contraire.
Authentification : en-tête `Authorization: Bearer <access_token>` ajouté automatiquement par le front.

### Points d'attention FastAPI

- **CORS** : autoriser l'origine du front (`http://localhost:5173` en développement) via `CORSMiddleware`, avec les en-têtes `Authorization` et `Content-Type`.
- **Slash final** : le front appelle les routes **avec** un `/` final (`/offres/`). Déclarer les routes ainsi côté FastAPI, ou supprimer le slash dans `src/api/*.js`. Une redirection 307 automatique peut casser les requêtes cross-origin.
- **Fichiers** : `python-multipart` est nécessaire pour `/cv/import/` et `PATCH /auth/me/`.
- **Rôles** : valeurs `"admin"` et `"etudiant"` (champ `role` de l'utilisateur).
- **Mots de passe** : stockés hachés (bcrypt/argon2) ; HTTPS en production.

### Authentification et profil

| Méthode | Route | Corps | Réponse |
| --- | --- | --- | --- |
| POST | `/auth/login/` | `{ email, password }` | `{ access, refresh, user }` — 400/401 si identifiants invalides |
| POST | `/auth/register/` | `{ nom, email, matricule, password }` | 201 — 400/409 si email ou matricule déjà utilisé |
| GET | `/auth/me/` | — | `user` |
| PATCH | `/auth/me/` | `multipart/form-data` : `nom`, `telephone`, `adresse`, `mention`, `niveau`, `poste`, `photo` (fichier), `supprimer_photo` (`"true"`) | `user` mis à jour |
| POST | `/auth/change-password/` | `{ ancien_mot_de_passe, nouveau_mot_de_passe }` | 200 — 400 si l'ancien est incorrect |

Objet `user` :

```json
{
  "id": 1,
  "nom": "Rakoto Jean",
  "email": "jean@emit.mg",
  "role": "etudiant",
  "telephone": "+261 34 00 000 00",
  "adresse": "Antananarivo",
  "photo": "https://.../photo.jpg",
  "matricule": "EMIT-2024-001",
  "mention": "Informatique",
  "niveau": "L3"
}
```

L'administrateur a `poste` à la place de `matricule`, `mention` et `niveau`.
Le refresh automatique du token n'est pas encore branché côté front (voir [État d'avancement](#état-davancement)).

### Offres et candidatures

| Méthode | Route | Corps | Réponse |
| --- | --- | --- | --- |
| GET | `/offres/` | — | tableau d'offres |
| GET | `/offres/{id}/` | — | offre |
| POST | `/offres/` | offre (admin) | offre créée |
| PUT | `/offres/{id}/` | offre (admin) | offre modifiée |
| PATCH | `/offres/{id}/` | `{ statut }` (admin) | offre — clôturer / republier |
| DELETE | `/offres/{id}/` | — (admin) | 204 |
| POST | `/candidatures/` | `{ offre: id }` (étudiant) | candidature créée |

Objet `offre` :

```json
{
  "id": 1,
  "titre": "Stage développeur web React / FastAPI",
  "type": "stage",
  "entreprise": "EMIT",
  "lieu": "Antananarivo",
  "description": "...",
  "datecreation": "2026-10-28",
  "statut": "ouverte",
  "mention": "Informatique",
  "niveau": "L3",
  "competences": [
    { "nom": "React", "niveauRequis": "avance", "poids": 4, "obligatoire": true }
  ]
}
```

Valeurs : `type` ∈ `stage | emploi | projet` — `statut` ∈ `ouverte | fermee | pourvue` — `niveauRequis` ∈ `debutant | intermediaire | avance | expert` — `poids` de 1 à 5 — `niveau` ∈ `L1 | L2 | L3 | M1 | M2`.

### CV

| Méthode | Route | Corps | Réponse |
| --- | --- | --- | --- |
| POST | `/cv/import/` | `multipart/form-data` : `file` (PDF/Word, 5 Mo max) | CV extrait par le module IA |

Structure du CV (utilisée par l'éditeur, l'aperçu et l'import) :

```json
{
  "titre": "CV Développeur web",
  "profil": {
    "nom": "", "poste": "", "email": "", "telephone": "",
    "adresse": "", "resume": "",
    "disponibilite": "immediate"
  },
  "competences": [{ "id": "c1", "nom": "React", "niveau": "avance" }],
  "formations": [{ "id": "f1", "diplome": "", "etablissement": "", "annee": "2026" }],
  "experiences": [
    { "id": "e1", "poste": "", "entreprise": "", "dateDebut": "2025-07", "dateFin": "2025-09", "description": "" }
  ]
}
```

`disponibilite` ∈ `immediate | oneMonth | threeMonths | notAvailable`.
La **sauvegarde** et la **publication** du CV (aujourd'hui stockées dans le navigateur) nécessiteront des routes dédiées, par exemple `GET/PUT /cv/` et `PATCH /cv/` pour le statut `brouillon | publie`.

### Recommandations et administration

| Méthode | Route | Réponse |
| --- | --- | --- |
| GET | `/recommandations/` | **Étudiant** : offres recommandées, triées par score décroissant |
| GET | `/offres/{id}/candidats-recommandes/` | **Admin** : classement des candidats pour une offre |
| POST | `/offres/{id}/candidats/{candidatId}/decision/` | `{ decision }` avec `decision` ∈ `attente | selectionne | refuse` |
| GET | `/profils/` | **Admin** : étudiants dont le CV est publié |
| GET | `/admin/overview/` | **Admin** : statistiques du tableau de bord |

Élément de `/recommandations/` : l'offre complète plus `score` (0 à 100), `communes` (compétences en commun) et `manquantes` (compétences à développer).

```json
{ "id": 1, "titre": "...", "score": 92, "communes": ["React", "Django"], "manquantes": ["Git"] }
```

Élément de `/offres/{id}/candidats-recommandes/` :

```json
{
  "id": 7,
  "matricule": "EMIT-2024-037",
  "mention": "Informatique",
  "niveau": "L3",
  "score": 88,
  "communes": ["React", "PostgreSQL"],
  "manquantes": ["Git"],
  "decision": "attente",
  "cv": { "profil": { "nom": "", "poste": "", "disponibilite": "" }, "competences": [], "formations": [], "experiences": [] }
}
```

Réponse de `/admin/overview/` :

```json
{
  "stats": { "offresOuvertes": 3, "offresTotal": 6, "cvPublies": 8, "selectionnes": 2 },
  "dernieresOffres": [ /* 4 offres */ ],
  "topOffre": { /* offre ou null */ },
  "top": [ /* 3 meilleurs candidats de topOffre, avec score */ ]
}
```

### Entretien IA

| Méthode | Route | Corps | Réponse |
| --- | --- | --- | --- |
| POST | `/entretiens/` | `{ poste, type, nombre_questions, langue }` — `type` ∈ `rh | technique | mixte`, `langue` ∈ `fr | en` | `{ id, questions: [{ id, texte }] }` |
| POST | `/entretiens/{id}/reponses/` | `{ question: id, reponse }` | `{ score, good, improve }` |

`good` et `improve` sont des listes de **clés** de conseils traduites par le front :
`good` ∈ `detailed | example | result | structure` — `improve` ∈ `short | noExample | noResult | long`.

### Notifications et historique

| Méthode | Route | Réponse |
| --- | --- | --- |
| GET | `/notifications/` | `[{ id, message, date, lu }]` de l'utilisateur connecté |
| PATCH | `/notifications/{id}/` | corps `{ lu: true }` |
| POST | `/notifications/tout-lire/` | marque toutes les notifications comme lues |
| GET | `/historique/` | `[{ id, action, date }]` (administrateur) |

Les notifications et lignes d'historique doivent être **créées par le serveur** lors des actions concernées (nouvelle offre, candidat sélectionné, nouvelle candidature, etc.). Le front relit les notifications toutes les 30 secondes.

---

## Déploiement

Le front est une application monopage (SPA) : toutes les routes doivent renvoyer `index.html`.

**Vercel** — fichier `vercel.json` à la racine :

```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

**Netlify** — fichier `public/_redirects` :

```
/*    /index.html   200
```

Définir `VITE_API_URL` (URL publique de l'API, en HTTPS) et `VITE_AUTH_MOCK=false` dans les variables d'environnement de l'hébergeur, puis autoriser le domaine du front dans le CORS du back-end.

---

## État d'avancement

**Réalisé (front-end, mode démo)**
- Navbar, page d'accueil, thème sombre/clair, FR/EN
- Connexion, inscription, routes protégées par rôle
- Offres publiques avec recherche, filtres et candidature
- Espace étudiant : tableau de bord et recommandations, Mon CV, entretien IA, profil, notifications
- Espace administrateur : tableau de bord, gestion des offres et critères, classement des candidats, recherche de profils, historique, profil, notifications

**À faire**
- Branchement au back-end FastAPI (authentification JWT, refresh automatique du token, déconnexion sur réponse 401)
- Sauvegarde et publication du CV via l'API
- Page « Analyse de CV »
- Envoi réel du formulaire de contact
- Réponse orale pour l'entretien IA (reconnaissance vocale)
- Tests automatisés et mise en ligne (Vercel / Netlify)
