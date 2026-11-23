# Compte rendu des modifications

Statuts : **Testé** = exécuté avec succès dans cet environnement (résultats réels ci-dessous) · **Implémenté, non testé** = code écrit mais non exécuté ici · **À configurer** = nécessite une infrastructure ou un compte externe.

## 1. Scoring de l'IA — remplacé par six critères pondérés (v2.0.0)
- **Implémenté et testé** : compétences 40 · missions 25 · expérience et projets 10 · spécialité 10 · niveau d'études 10 · disponibilité 5 (= 100, vérifié par test). Formule `Σ poids × note / 100`, notes 0–100, score 0–100.
- **Testé** : détail par critère, points forts / à vérifier / informations manquantes ; informations absentes = « inconnu » (note neutre) ; niveau **obligatoire** (éliminatoire) distingué d'une **préférence** ; candidats éliminés conservés et visibles ; classement déterministe ; synonymes et compétences comportementales ; projets valorisés pour les débutants ; masquage des compétences pour limiter le double comptage ; aucune information inventée.
- **Testé** : traçabilité — chaque classement enregistre version de l'algorithme, pondérations et critères de l'offre (`scoring_run`), consultable par l'administrateur.
- **Limites** : pondérations **à calibrer sur données réelles** (procédure dans `SCORING.md`) ; recoupement partiel assumé entre critères 2 et 3 ; score absolu gonflé quand l'offre demande peu de choses (le classement n'est pas affecté).

## 2. Fichier Excel de 100 étudiants fictifs
- **Testé** : `docs/etudiants_test_100.xlsx` — 100 lignes, en-têtes `Nom, Prénom, Email, Matricule`, 100 matricules et 100 e-mails uniques, aucun champ vide, e-mails valides pour le validateur, feuille « LISEZ-MOI » précisant que ce sont des **données fictives à remplacer par la liste officielle autorisée par l'EMIT**. Importé avec succès (100 ajoutés, 0 erreur) et réimport idempotent. Regénérable : `python -m scripts.generer_etudiants_test`.

## 3. Accès réservé aux étudiants autorisés
- **Testé** : inscription refusée côté serveur si e-mail + matricule + nom/prénom ne correspondent pas à la même entrée ; matricule déjà utilisé refusé (message unique non révélateur) ; **aucun compte avant vérification de l'e-mail** ; jeton haché, expirant, à usage unique, limité en essais, et mot de passe exigé à la confirmation ; unicité en base (e-mail, matricule, entrée ↔ compte) ; mots de passe Argon2 ; rôles `admin`/`etudiant` strictement séparés (routes admin refusées aux étudiants et inversement, accès sans jeton refusé) ; rôle non modifiable par le client ; limitation de débit (IP, matricule, connexion) et verrouillage temporaire de compte, compteurs en base.
- **Testé** : import Excel avec aperçu, erreurs de format, doublons (dans le fichier et avec la base), lignes invalides, conflits, mises à jour, entrées liées à un compte, confirmation unique, annulation, droits.
- **À configurer** : envoi réel des e-mails (`EMAIL_BACKEND=smtp` + serveur SMTP). Le mode `console` écrit le lien dans les journaux. **Implémenté, non testé** : envoi SMTP réel.
- Les rôles sont stockés `admin` / `etudiant` (équivalents de `ADMIN` / `ETUDIANT`).

## 4. Analyse de 4 000 CV ou plus
- **Testé** (PostgreSQL) : 4 000 CV analysés en **80 s** (2 workers, **1 CPU**, 0 erreur) ; classement de 4 000 candidats ≈ **5,5 s** par offre ; pages d'API 30–150 ms ; base 64 Mo. Détail et limites : `CHARGE.md`.
- **Testé** : file de tâches (états en attente / en cours / terminé / échoué), coalescence, nouveaux essais avec délai croissant, relance **d'une** tâche ou des seules tâches échouées, reprise après worker interrompu, deux workers sans doublon ; mode `worker` vs `inline` ; cache d'analyse (CV inchangé = pas de réanalyse) ; extraction différée (import en lot).
- **Testé** : PDF scanné détecté (`ocr_requis`), PDF vide, fichiers vides/corrompus/trop gros/mauvais type refusés, PDF à contenu actif (JavaScript, lancement, fichier incorporé) refusés, DOCX avec macros / sans `document.xml` / bombe de décompression refusés ; fichier de CV non lisible par un autre étudiant.
- **Testé** : extraction 190 PDF/s et 71 DOCX/s (fichiers simples).
- **Défaut trouvé et corrigé** par le test de charge : comptage des candidatures par chargement (≈ 1 s → ≈ 30 ms).
- **Non fourni** : OCR (détection uniquement) ; calcul incrémental par candidat ; purge des classements d'offres clôturées ; antivirus (ClamAV recommandé en production) ; modèle externe d'IA (aucun appel externe : pas de quota ni de coût).

## 5. Disponibilité 24 h/24
- **Implémenté** : redémarrage automatique, healthchecks (base, API `/ready`, worker, frontend), journaux JSON avec rotation, identifiant de requête, pool de connexions borné, recyclage des workers, arrêt propre, limites de charge, migrations automatiques, refus de démarrer avec une clé secrète faible, HTTPS via Caddy, en-têtes de sécurité/CSP, sauvegardes avec somme de contrôle + rotation + archive des CV.
- **Testé** : sauvegarde, **restauration à l'identique** (7 tables comparées), application fonctionnelle sur la base restaurée, détection d'une sauvegarde corrompue, `tables.sql` chargé dans une base vierge, migration Alembic cohérente avec les modèles.
- **Non testé ici** : `docker compose up` (pas de Docker), émission de certificats, SMTP, utilisateurs simultanés, endurance. Procédures dans `DEPLOIEMENT.md`.
- **Aucune garantie de 100 %** : un serveur unique reste un point de défaillance ; voir les objectifs RPO/RTO réalistes et les coûts indicatifs (à vérifier) dans `DEPLOIEMENT.md`.

## 6. Schéma de base de données (demande précédente, menée à terme)
17 tables du diagramme conformes (noms et colonnes), association `viser`, 15 tables complémentaires nommées et justifiées dans `tables.sql`. Écarts assumés et signalés : colonnes en minuscules ; `scrore` et `dure` conservés tels quels ; `annee` sans accent ; `Competence.cv_id` nullable pour servir de catalogue aux `CritereOffre` (le diagramme relie un critère à une compétence appartenant pourtant à un CV) ; candidatures « recommandée » générées par l'IA pour rattacher les recommandations (le diagramme relie `Recommandation` à `Candidature`).

## 7. Reste à faire / à décider
1. Obtenir la **liste officielle** auprès de l'EMIT et l'importer ; supprimer toute donnée de test.
2. **Calibrer** les pondérations sur de vraies offres et CV.
3. Configurer **SMTP, domaine, serveur** ; tester `docker compose` ; planifier et **tester** les sauvegardes hors site.
4. Test de **charge utilisateurs** sur le serveur cible ; surveillance externe.
5. Décider d'un **OCR**, d'un antivirus, du calcul incrémental et de la purge des anciens classements selon le volume réel.
6. Mentions (Informatique, Gestion, Management, Communication) à remplacer par les mentions réelles de l'EMIT.
