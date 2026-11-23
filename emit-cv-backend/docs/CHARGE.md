# Test de charge : 4 000 CV

Mesures **réelles**, obtenues avec `backend/scripts/charge_test.py` (résultats bruts : `docs/charge_resultats.json`). Elles donnent un **ordre de grandeur** ; elles dépendent de la machine et de la nature des données.

## Conditions
- **Machine de test : 1 seul CPU** (conteneur de développement), PostgreSQL 16 sur la même machine, moteur TF-IDF. Les « 2 workers » se partageaient donc ce CPU : sur un serveur multi-cœurs, les temps d'analyse et de classement baisseront nettement.
- **4 000 CV synthétiques** (8 familles de profils, 3 à 7 compétences, 0 à 2 expériences, 0 à 2 projets), 4 001 comptes, 4 000 entrées autorisées. Schéma créé depuis `database/tables.sql`.
- Le test de charge part de CV **déjà structurés** (cas courant : CV créés en ligne). L'extraction de **fichiers** a été mesurée à part (ci-dessous).

## Résultats

| Étape | Résultat |
|---|---|
| Génération des 4 000 CV (18 365 compétences, 3 987 expériences, 4 006 projets) | 12 s |
| **Analyse des 4 000 CV** (file de tâches, **2 workers** en parallèle) | **80 s** (≈ 50 CV/s) · 4 000 terminées · **0 erreur** · chaque worker a exécuté 2 000 tâches (aucune tâche exécutée deux fois) · pic mémoire 200 Mo/worker |
| **Classement de 4 000 candidats par offre** (3 offres) | 5,3 à 5,8 s par offre · 12 000 recommandations · pic mémoire 265 Mo (traitement par blocs de 500) |
| **Modification d'un CV** (5 modifications rapprochées) | 5 modifications → **1** tâche en attente (coalescence) ; 1 analyse + 3 recalculs = 19 s |
| Taille de la base | 64 Mo (dont 34 Mo pour le détail explicable des 12 000 recommandations) ; 1 connexion ouverte |
| Extraction de fichiers, 200 fichiers simples d'une page | **PDF : 190 fichiers/s** (5 ms) · **DOCX : 71 fichiers/s** (14 ms) · 200/200 extraits correctement |

### Latence de l'API (40 requêtes par scénario, base de 4 000 CV, 0 erreur)

| Requête | p50 | p95 |
|---|---|---|
| Classement d'une offre, pages 1 à 40 (20/page) | 112 ms | 152 ms |
| Classement + filtres (compétence, score ≥ 60, hors éliminés) | 101 ms | 136 ms |
| Recherche de profils (compétence + disponibles) | 84 ms | 118 ms |
| Recherche de profils (texte) | 93 ms | 124 ms |
| Liste des offres | 27 ms | 39 ms |
| Statistiques administrateur | 19 ms | 25 ms |
| Étudiant : mes recommandations | 29 ms | 34 ms |

La recherche et le filtrage se font **en SQL, avec pagination** : aucun CV n'est chargé en mémoire pour répondre.

## Défaut trouvé par ce test, puis corrigé
La liste des offres et « mes recommandations » chargeaient **toutes les candidatures** de chaque offre uniquement pour les compter : **946 ms** et **984 ms** (p50). Remplacé par des comptages SQL groupés : **27 ms** et **29 ms**. Les tests automatisés ont été relancés après correction.

## Limites de cette mesure (à ne pas oublier)
- **Une seule machine à 1 CPU**, données synthétiques : la charge réelle (CV réels, PDF volumineux ou à mise en page complexe, utilisateurs simultanés) n'a **pas** été testée. Les 190 PDF/s concernent des fichiers d'une page, très simples ; comptez nettement moins sur de vrais CV (images, 2-3 pages).
- **Pas de test de charge d'utilisateurs simultanés** (type Locust/k6) ni de test d'endurance sur plusieurs jours. Procédure pour le faire : voir `DEPLOIEMENT.md`.
- **Coût d'un CV modifié** : chaque modification d'un CV publié déclenche le recalcul de **chaque offre ouverte** (≈ 5,5 s par offre à 4 000 candidats, ici sur 1 CPU). La coalescence évite les recalculs en rafale, mais avec beaucoup d'offres ouvertes et de modifications fréquentes, un **calcul incrémental par candidat** (non implémenté) deviendrait utile.
- **Volume de stockage** : ≈ 11 Mo de détails de scores par offre classée sur 4 000 candidats. Avec de nombreuses offres, prévoir une purge des classements des offres clôturées (non implémentée) et surveiller la taille de la base.
- Moteur d'embeddings transformers non mesuré.

## Rejouer le test
```bash
createdb emit_load && psql -d emit_load -f database/tables.sql
export DATABASE_URL=postgresql+psycopg://user:pw@localhost/emit_load TACHES_MODE=worker AI_BACKEND=tfidf
cd backend
python -m scripts.charge_test --cvs 4000 --workers 2                 # tout enchaîner (≈ 3 min sur 1 CPU)
python -m scripts.charge_test --cvs 4000 --phase generer             # ou phase par phase : generer, analyser, classer, lecture, incremental, base
python -m scripts.mesure_extraction --n 200                          # débit d'extraction PDF/DOCX
```
