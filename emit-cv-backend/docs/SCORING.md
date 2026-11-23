# Scoring et module d'IA (algorithme v2.0.0)

> **Statut des pondérations** : les poids ci-dessous sont une **proposition initiale** à tester et ajuster sur de vraies offres et de vrais CV (procédure en fin de document). Ils sont centralisés dans `backend/app/ai/scoring.py` (`POIDS`) ; un test vérifie qu'ils totalisent exactement 100.

## Formule

```
Score final = Σ ( poids_critère × note_critère / 100 )      note_critère ∈ [0, 100]      Σ poids = 100      score ∈ [0, 100]
```

| # | Critère | Poids | Ce qui est évalué | Sources dans le CV |
|---|---|---|---|---|
| 1 | Compétences | 40 | Compétences exigées par l'offre ↔ compétences **démontrées** | compétences déclarées ; à défaut, compétences retrouvées dans le texte du CV |
| 2 | Adéquation aux missions | 25 | Contenu des expériences/projets ↔ missions de l'offre | descriptions d'expériences et de projets |
| 3 | Expérience et projets | 10 | Ampleur de la pratique **pertinente** (durée, nombre) | expériences (dates) et projets |
| 4 | Spécialité | 10 | Spécialité du candidat ↔ spécialités visées | mention, intitulés de formation |
| 5 | Niveau d'études | 10 | Niveau du candidat ↔ niveau demandé | niveau d'études du profil |
| 6 | Disponibilité | 5 | Disponibilité déclarée ↔ dates/type de l'offre | disponibilité renseignée par l'étudiant |

Les six notes, leurs points (`poids × note / 100`), leur statut et leur justification sont renvoyés pour chaque candidat ; la somme des points est égale au score.

## Détail de chaque critère

**1. Compétences (40 %).** Chaque critère de l'offre a un poids (1 à 5), un niveau requis (débutant → expert) et un indicateur « obligatoire ». Crédit par critère : compétence **déclarée** = `min(1, niveau_déclaré / niveau_requis)` ; compétence **seulement mentionnée** dans le texte du CV = 0,6 (signalée « niveau non déclaré ») ; absente = 0. Note = somme pondérée des crédits ÷ somme des poids. Les **synonymes** et variantes (« Postgres » = « PostgreSQL », « fast api » = « FastAPI », accents, casse) sont reconnus via le référentiel `skills_taxonomy.py` (~90 compétences techniques **et comportementales** : communication, travail en équipe, gestion de projet, anglais…). Sans critères saisis, ils sont déduits de la description de l'offre.

**2. Adéquation aux missions (25 %).** Similarité entre le texte des missions de l'offre et chaque expérience/projet du candidat (TF-IDF par défaut, embeddings multilingues en option). Note = pondération 60/30/10 des trois meilleurs recoupements, normalisée sur les éléments présents. **Les compétences du référentiel sont retirées des deux textes avant comparaison** (elles sont déjà notées au critère 1), pour qu'un simple recoupement de mots-clés techniques ne compte pas deux fois.

**3. Expérience et projets (10 %).** Chaque élément reçoit une pertinence ∈ [0,1] fondée sur le **titre** du poste/projet comparé au titre de l'offre (le contenu, déjà noté au critère 2, n'intervient qu'à demi-poids et en secours, si le titre est trop vague). Expériences : mois × pertinence, cible 12 mois (emploi) ou 6 (stage/projet). Projets : somme des pertinences, cible 1,5. **Candidat débutant (< 6 mois d'expérience) : projets 60 % / expériences 40 %** ; sinon l'inverse. Un débutant avec des projets pertinents peut ainsi atteindre une note élevée.

**4. Spécialité (10 %).** Mention dans les spécialités visées = 100 ; spécialité visée citée dans les intitulés de formation = 60 (« partiel ») ; sinon 0. Aucune spécialité demandée = 100 (« non demandé »).

**5. Niveau d'études (10 %).** Niveau ≥ niveau demandé = 100 ; un cran en dessous = 60 ; deux = 30 ; au-delà 0. **Règle de l'offre** : l'administrateur indique si le niveau est **obligatoire** (éliminatoire) ou une **préférence**. La note est la même dans les deux cas ; seule l'éligibilité change (voir plus bas).

**6. Disponibilité (5 %).** Déclaré non disponible = 0 (information confirmée). Dates connues : début de disponibilité ≤ début de l'offre = 100 ; retard ≤ 30 j = 70 ; ≤ 90 j = 30 ; au-delà = 0 ; disponibilité terminée avant l'offre = 0 ; disponibilité plus courte que la période = ×0,7 ; type de disponibilité différent (stage/emploi/projet) = ×0,3.

## Informations absentes : « inconnu », jamais « échec »

| Situation | Traitement |
|---|---|
| Niveau d'études, dates de disponibilité ou spécialité **non renseignés** | statut `inconnu`, note neutre `NOTE_INCONNU = 50`, signalé dans « informations manquantes » ; si le niveau est obligatoire : éligibilité « à vérifier » (pas d'élimination) |
| Critère **non demandé** par l'offre | statut `non_demande`, note 100 (ne départage personne) |
| Aucune expérience ni projet dans le CV | statut `absent`, note 0 pour les critères 2 et 3 (absence de preuve, pas d'invention) |
| Offre sans description des missions / sans compétences exploitables | critère `inconnu` (50), non évaluable |

Le champ `fiabilite` indique la part du score (en %) qui repose sur des informations connues. **L'IA n'invente jamais** une compétence, expérience, diplôme ou disponibilité : tout provient du CV et du profil ; chaque compétence indique sa source (`declaree` / `texte`).

> **Limite à connaître** : comme un critère « non demandé » vaut 100, le score **absolu** est gonflé pour les offres qui demandent peu de choses (ex. 25 points « offerts » si ni spécialité, ni niveau, ni dates). Le **classement** n'est pas affecté (tous les candidats reçoivent les mêmes points) ; ne comparez pas des scores absolus entre offres de natures différentes.

## Éligibilité : exigences obligatoires ≠ préférences

- Un **critère de compétence « obligatoire »** non retrouvé, ou un **niveau obligatoire** non atteint → candidat marqué **`elimine`** (« exigence obligatoire non respectée »). Il **n'est pas supprimé** : son score reste calculé et visible, il est classé après les candidats conformes, et filtrable (« Masquer les éliminés »). L'administrateur décide.
- Niveau **préféré** non atteint → simple écart : note réduite, mention « préférence, non éliminatoire », aucun marquage.
- Niveau obligatoire **inconnu** → `a_verifier`, pas d'élimination.
- Aucune pénalité cachée : à exigence égale, le score n'est pas modifié (testé).

## Explications fournies à l'administrateur

Pour chaque candidat : score global ; les 6 notes ; **points forts**, **points à vérifier**, **informations manquantes** ; compétences trouvées (avec source et niveau) / insuffisantes / manquantes ; meilleurs recoupements d'expériences ; version de l'algorithme et moteur ; fiabilité. L'interface rappelle que *la recommandation éclaire la décision, elle ne la remplace pas* : valider / sélectionner / refuser reste une action manuelle de l'administrateur.

## Classement et traçabilité

Tri : conformes d'abord, puis éliminés ; score décroissant ; départage par nombre de compétences trouvées puis identifiant (résultat **déterministe**). Chaque calcul crée un enregistrement `scoring_run` qui conserve : **version de l'algorithme, pondérations, instantané des critères de l'offre** (compétences, niveau, spécialités, dates), moteur d'IA, déclencheur, durée, statut/erreur. Chaque score pointe vers son `run_id` ; l'historique est consultable (`GET /offres/{id}/runs`, bouton « Traçabilité »).

## Moteurs de similarité

| Moteur | Usage | Remarques |
|---|---|---|
| **TF-IDF** (scikit-learn) | par défaut, 100 % local | ajusté en flux sur tout le corpus pour des poids IDF cohérents d'un bloc de CV à l'autre ; calibrage `ETIREMENT = 0.30` |
| **sentence-transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) | `pip install -r requirements-ml.txt`, `AI_BACKEND=auto\|transformers` | meilleur sur les paraphrases ; **non testé dans cet environnement** (pas de téléchargement du modèle) ; repli automatique sur TF-IDF |

**Aucun fournisseur d'IA externe n'est utilisé** : pas d'appel réseau, pas de coût par requête, pas de quota, les CV ne quittent pas le serveur. Si un modèle externe était ajouté un jour, il faudrait le placer **derrière la file de tâches** (déjà en place : workers configurables, `WORKER_BATCH`) avec un limiteur de débit et un plafond de coût ; cette partie n'est volontairement pas implémentée.

## Calibrer les pondérations (à faire avant la mise en production)

1. Réunir 5 à 10 offres réelles variées et, pour chacune, 30 à 50 CV réels (anonymisés ou avec accord).
2. Faire classer ces CV « à la main » par 2 ou 3 responsables (classement de référence, ou au minimum « retenu / à discuter / écarté »).
3. Comparer au classement de l'IA : corrélation de rang (Spearman), et « parmi les 10 premiers de l'IA, combien figurent dans les retenus ? ».
4. Ajuster `POIDS`, `ETIREMENT`, `SEUIL_PERTINENCE`, `NOTE_INCONNU` ; relancer `python -m pytest tests/test_scoring_v2.py` (le test des 100 % garantit la cohérence) ; recalculer les classements. Chaque ajustement est tracé par un nouveau `VERSION_ALGORITHME`.
5. Examiner les cas où l'IA se trompe : ils indiquent souvent un synonyme manquant dans `skills_taxonomy.py`, facile à enrichir.

## Limites connues

- Recoupement partiel assumé entre les critères 2 et 3 (même corpus de texte, agrégations et champs différents) ; mesuré par les tests mais à valider sur données réelles.
- Compétences non listées dans le référentiel : reconnues seulement par correspondance exacte.
- Le parseur de CV importé est heuristique (titres de sections usuels FR/EN) : un CV à la mise en page atypique donne un pré-remplissage incomplet, que l'étudiant corrige.
- Pas d'OCR : les PDF scannés sont **détectés** et signalés (`ocr_requis`), pas lus.
- Pas de mesure d'équité/biais sur données réelles : à faire avant usage décisionnel.
