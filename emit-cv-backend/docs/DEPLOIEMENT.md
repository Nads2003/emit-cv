# Déploiement en production et disponibilité

> **Honnêteté sur la disponibilité** : aucun logiciel ne garantit « 24 h/24, 7 j/7 à 100 % ». La disponibilité réelle dépend de l'hébergeur, du réseau, du fournisseur de base de données et de votre surveillance. Ce projet fournit les **mécanismes** (redémarrage automatique, sondes de santé, journaux, sauvegardes testées, reprise) ; **une seule machine reste un point de défaillance unique**. Visez un objectif réaliste (par ex. 99 % à 99,5 % = 4 à 7 h d'indisponibilité par mois) et mesurez-le.

## 1. Architecture de production recommandée (budget maîtrisé)

```
Internet ──HTTPS──▶ Caddy (certificats automatiques) ──▶ nginx + frontend (React)
                                                          └─▶ /api ─▶ backend FastAPI (Gunicorn ×3) ──▶ PostgreSQL
                                                                      worker ×2 (analyses, classements) ──┘      │
                                                                      volume « uploads » (CV)             sauvegardes quotidiennes
```
Tout tient sur **un serveur Linux** (Docker Compose) : `db`, `backend`, `worker` (×2, extensible), `frontend`, `caddy`. Le frontend peut aussi être servi par Vercel/Netlify (`VITE_API_URL=https://api.votre-domaine/api/v1`, `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`).

## 2. Mise en production pas à pas

1. **Serveur** : Linux (Ubuntu LTS), 2 à 4 vCPU, 4 à 8 Go de RAM, disque SSD ≥ 40 Go ; pare-feu : seuls 22 (SSH par clé), 80 et 443 ouverts. Installer Docker + Docker Compose **≥ 2.24**.
2. **DNS** : enregistrement A `cv.votre-domaine.mg` → IP du serveur.
3. **Configuration** : `cp .env.example .env` puis renseigner `POSTGRES_PASSWORD` (long), `SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(64))"`), `PUBLIC_ORIGIN=https://cv.votre-domaine.mg`, `COOKIE_SECURE=true`, `DOMAINE`, `ADMIN_EMAIL`/`ADMIN_PASSWORD`, et **`EMAIL_BACKEND=smtp` + SMTP_*** (sans cela, aucun e-mail de confirmation n'est envoyé). `chmod 600 .env`, ne jamais le committer.
4. **Lancement** : `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`. Les **migrations** sont appliquées automatiquement (`alembic upgrade head`) avant le démarrage des workers ; le backend **refuse de démarrer** en production avec une `SECRET_KEY` faible.
5. **Liste des étudiants** : importer la liste officielle (voir `IMPORT_ETUDIANTS.md`).
6. **Sauvegardes** : ajouter au cron `30 2 * * * cd /opt/emit-cv-ia && COMPOSE=1 ./deploy/backup_db.sh >> backups/backup.log 2>&1` ; **copier `backups/` hors du serveur** (stockage objet S3, autre machine : `rclone`/`rsync`).
7. **Surveillance** (section 4) puis **répétition d'incident** (section 6) avant l'ouverture.

## 3. Variables d'environnement et secrets

| Variable | Rôle |
|---|---|
| `SECRET_KEY` | signature des jetons JWT (≥ 32 caractères en production, vérifié au démarrage) |
| `POSTGRES_PASSWORD`, `DATABASE_URL` | accès base |
| `COOKIE_SECURE`, `COOKIE_SAMESITE`, `CORS_ORIGINS`, `PUBLIC_URL` | sécurité des cookies, origine autorisée, liens d'e-mail |
| `EMAIL_BACKEND`, `SMTP_*`, `EMAIL_FROM` | envoi des e-mails de vérification |
| `TACHES_MODE` | `worker` (production) ou `inline` (dev) |
| `WEB_CONCURRENCY`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `WORKER_BATCH`, `SCORING_CHUNK` | dimensionnement (voir 5) |
| `LOG_JSON` | journaux JSON pour agrégation |

Les secrets ne sont jamais dans le code ni dans l'image : uniquement `.env` (droits 600) ou, mieux, les secrets de votre plateforme (Docker secrets, gestionnaire de secrets de l'hébergeur). Aucun secret réel n'est fourni dans `.env.example`.

## 4. Surveillance, journaux, redémarrage

- **Redémarrage** : `restart: unless-stopped` sur chaque service ; **healthchecks Docker** : base (`pg_isready`), backend (`/ready` = base joignable), worker (fichier de vie rafraîchi, alerte si > 2 min), frontend (`/nginx-health`). Un conteneur *unhealthy* est visible via `docker compose ps`.
- **Sondes HTTP** : `GET /health` (le processus répond) et `GET /ready` (base OK + état de la file ; **503** sinon). Branchez un service externe (UptimeRobot, Better Stack, Uptime Kuma auto-hébergé) sur `https://…/ready` avec alerte e-mail/SMS : c'est la seule façon de détecter une panne **du serveur entier**.
- **Journaux** : JSON, rotation Docker (10 Mo × 5 fichiers par service) ; chaque requête porte un `X-Request-ID` ; les requêtes lentes (> 1,5 s) ou en erreur 5xx sont journalisées ; PostgreSQL journalise les requêtes > 1 s. Pour centraliser : Loki/Grafana, ou Sentry (optionnel, non intégré).
- **Alertes métier** : l'écran **Traitements** et `GET /admin/stats` exposent les tâches échouées et les analyses à vérifier ; relancer **une** tâche ou toutes les échouées sans retraiter les autres.
- **Disque** : surveiller l'espace (base, `uploads`, `backups`) — alerte à 80 %.

## 5. Capacité, ressources et limites de charge

Mesures réelles (détail et limites : `CHARGE.md`) : 4 000 CV analysés en 80 s avec 2 workers sur **1 CPU** ; classement de 4 000 candidats ≈ 5,5 s par offre ; pages d'API ≈ 30 à 150 ms ; base 64 Mo ; mémoire 200–265 Mo par worker.

- **Connexions PostgreSQL** : `(WEB_CONCURRENCY + nb workers) × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` doit rester **< `max_connections`** (100). Réglages fournis : (3 + 2) × 10 = 50.
- **Risques de saturation** : (1) pics de calculs de classement (mettre plus de workers, ou les limiter pour protéger l'API) ; (2) croissance de `recommandation_detail` (≈ 11 Mo par offre à 4 000 candidats) ; (3) téléversements simultanés (5 Mo max par CV, 8 Mo côté nginx) ; (4) enchaînement de modifications de CV avec beaucoup d'offres ouvertes.
- **Limites en place** : taille de fichier, nombre de lignes d'import, limitation de débit (API + nginx 20 req/s/IP), pool de connexions borné, `--max-requests` (recyclage des workers), coalescence des tâches, traitement par blocs.
- **À faire avant l'ouverture** : un test d'utilisateurs simultanés (k6 ou Locust) sur **votre** serveur, p. ex. 200 utilisateurs sur le scénario « connexion → liste des offres → postuler », et suivre CPU, RAM, connexions (`pg_stat_activity`), latences.

## 6. Sauvegardes et reprise après incident

**Sauvegarde** (`deploy/backup_db.sh`) : `pg_dump` au format compressé + somme de contrôle SHA-256 + archive des fichiers de CV ; vérification que la sauvegarde est lisible ; rotation (14 jours + 8 dimanches).
**Restauration** (`deploy/restore_db.sh fichier.dump [base]`) : contrôle la somme de contrôle (refus si corrompue) puis restaure. **Vérification** (`deploy/verifier_sauvegarde.sh`) : restaure dans une base jetable et contrôle les données — **à planifier chaque semaine**.

*Testé ici* : sauvegarde de la base de charge (4 001 comptes, 4 000 CV, 12 000 recommandations), restauration **à l'identique** (comptages égaux sur 7 tables), application fonctionnelle sur la base restaurée, corruption volontaire détectée. *Non testé ici* : exécution dans les conteneurs Docker (mode `COMPOSE=1`), copie hors serveur.

| Objectif (à valider par vous) | Valeur avec la configuration fournie |
|---|---|
| **RPO** (données perdues au pire) | jusqu'à 24 h (sauvegarde quotidienne). Pour moins : archivage WAL / base managée avec restauration à un instant donné |
| **RTO** (durée de remise en service) | ≈ 30 min à 2 h : nouveau serveur + Docker + `.env` + restauration (temps de restauration de 64 Mo : quelques secondes ; le reste est manuel) |

**Procédure — serveur perdu** : 1) nouveau serveur, Docker, DNS ; 2) récupérer le dépôt et le `.env` (sauvegardé à part, dans un coffre de mots de passe) ; 3) `docker compose up -d db` ; 4) `COMPOSE=1 ./deploy/restore_db.sh backups/<dernier>.dump` ; 5) restaurer `uploads_*.tar.gz` dans le volume ; 6) `docker compose up -d` (les migrations se rejouent sans effet si déjà à jour) ; 7) vérifier `/ready`, se connecter, contrôler un classement.
**Procédure — mauvaise mise à jour** : `git checkout <version précédente>` puis `docker compose up -d --build` ; si une migration est en cause, restaurer la sauvegarde faite **avant** la mise à jour (toujours en faire une).
**Procédure — tâches bloquées** : écran *Traitements* ; un worker tombé libère ses tâches après `WORKER_VERROU_S` (15 min), elles sont reprises automatiquement.

## 7. Migrations de base de données

`alembic upgrade head` (automatique au démarrage du backend). Le schéma complet est aussi fourni en SQL pur : `database/tables.sql` (généré depuis les modèles : `python -m scripts.export_sql`). Avant une migration en production : **sauvegarde**, puis essai sur une copie restaurée.

## 8. HTTPS

Caddy (`docker-compose.prod.yml`) obtient et renouvelle les certificats Let's Encrypt ; HSTS activé ; cookies `Secure` + `HttpOnly` ; le backend écrit un avertissement au démarrage si `COOKIE_SECURE=false` en production (il ne s'arrête pas : pensez à le vérifier). *Non testé ici* : l'émission du certificat (nécessite un vrai domaine public).

## 9. Coûts indicatifs (à vérifier au moment de l'achat)

> Les tarifs d'hébergement ont **changé en 2026** (hausses annoncées chez plusieurs fournisseurs, offres renommées) et les sources consultées divergent : les montants ci-dessous sont des **ordres de grandeur**, à confirmer sur le site du fournisseur (hors taxes, hors devise locale).

| Poste | Option économique | Option plus robuste |
|---|---|---|
| Serveur (2–4 vCPU, 4–8 Go) | quelques € à une vingtaine d'€ / mois (VPS d'un hébergeur européen à bas coût) | 20 à 60 €/mois (plus de ressources, 2ᵉ serveur, sauvegardes de l'hébergeur) |
| Base PostgreSQL | incluse dans le serveur (Docker) | **managée** (sauvegardes/restauration à un instant donné, réplica) : en général plusieurs fois le prix d'un petit VPS |
| Nom de domaine | ≈ 10 à 20 €/an | idem |
| Certificat HTTPS | 0 (Let's Encrypt) | 0 |
| E-mails transactionnels (SMTP) | offres gratuites limitées (quelques centaines de mails/jour) | quelques € à dizaines d'€/mois |
| Surveillance de disponibilité | gratuite (UptimeRobot, Uptime Kuma auto-hébergé) | quelques €/mois |
| Stockage des sauvegardes hors site | quelques centimes à quelques € / mois (stockage objet) | idem |
| **Total indicatif** | **≈ 10 à 30 €/mois** | **≈ 50 à 150 €/mois** |

Pas de coût d'IA par requête (calcul local). Le surcoût principal d'une disponibilité élevée est **humain** (astreinte, mises à jour de sécurité, tests de restauration).

## 10. Pour viser une disponibilité plus élevée (au-delà du budget minimal)
Deux serveurs applicatifs derrière un répartiteur de charge ; base managée avec réplica et bascule ; stockage objet partagé pour les CV (au lieu d'un volume local) ; limiteur de débit et file de tâches déjà compatibles multi-serveurs (compteurs et file en base). Ces éléments **ne sont pas déployés ici**.

## 11. Ce qui n'a pas pu être testé dans cet environnement
`docker compose up` (pas de Docker disponible) · émission de certificats HTTPS · envoi d'e-mails SMTP réels · charge d'utilisateurs simultanés · exécution prolongée · moteur d'embeddings transformers · OCR (non fourni). Chacun a une procédure ci-dessus ou dans `CHARGE.md`.
