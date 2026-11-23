# Importer la liste officielle des étudiants autorisés

Seuls les étudiants figurant dans cette liste peuvent créer un compte. La vérification est faite **côté serveur** (le frontend n'est qu'une commodité).

> ⚠️ Le fichier `docs/etudiants_test_100.xlsx` contient **100 étudiants fictifs** (Nom `TEST001`, matricule `TEST-EMIT-0001`, e-mail `@example.org`). Il sert uniquement aux essais. **Avant la mise en production**, remplacez-le par la liste officielle **obtenue auprès de l'EMIT, avec son autorisation et dans le respect de la protection des données personnelles**, puis ne conservez aucune donnée de test en production.

## Format du fichier

Fichier `.xlsx` (2 Mo max, 20 000 lignes max). **Première feuille**, **en-têtes en première ligne** (ordre et casse libres, accents facultatifs) :

| Nom | Prénom | Email | Matricule |
|---|---|---|---|

- tous les champs sont obligatoires ; e-mail valide ; matricule de 3 à 40 caractères (lettres, chiffres, `/ _ . -`) ;
- le matricule est normalisé en majuscules, l'e-mail en minuscules ;
- les lignes entièrement vides sont ignorées.

## Procédure (interface)

1. Connectez-vous en administrateur → **Étudiants autorisés** → **Importer un fichier Excel**.
2. Un **aperçu** s'affiche : nouvelles entrées, mises à jour, inchangées, **erreurs** (ligne, matricule, e-mail, cause). **Rien n'est appliqué.**
3. Corrigez le fichier et réimportez, ou confirmez : si des erreurs subsistent, la confirmation indique qu'elles seront **ignorées** (seules les lignes valides sont appliquées).
4. **Confirmer** applique les changements (re-vérifiés au moment de la confirmation, car la base peut avoir changé depuis l'aperçu). Un import ne s'applique qu'**une fois**.

## Procédure (ligne de commande)

```bash
cd backend
python -m scripts.import_etudiants ../docs/etudiants_test_100.xlsx --admin-email admin@emit.mg              # aperçu seul
python -m scripts.import_etudiants liste_officielle.xlsx --admin-email admin@emit.mg --confirmer           # applique
```

## Règles de contrôle (aperçu et confirmation)

| Cas | Résultat |
|---|---|
| Champ manquant, e-mail invalide, matricule invalide | erreur |
| Matricule ou e-mail **dupliqué dans le fichier** | erreur sur la 2ᵉ occurrence |
| E-mail déjà associé à **un autre matricule** en base | erreur |
| Matricule déjà en base, informations identiques | « inchangé » |
| Matricule en base, informations différentes, **pas encore de compte** | « mise à jour » |
| Entrée **déjà liée à un compte** et informations différentes | erreur (modification refusée) |
| Colonne manquante / fichier non Excel / corrompu / trop gros | refus de tout le fichier |

Réimporter le même fichier est **idempotent** (tout est « inchangé »). Les entrées absentes d'un nouvel import ne sont **jamais supprimées** automatiquement.

## Parcours d'inscription d'un étudiant

1. Il saisit nom, prénom, e-mail, matricule, mention/niveau et mot de passe. Le serveur exige que **les quatre informations d'identité correspondent à la même entrée** de la liste, non encore utilisée.
2. Il reçoit un e-mail avec un lien (valable 1 h, usage unique). **Aucun compte n'existe à ce stade.**
3. Il ouvre le lien et saisit son mot de passe : le compte est alors créé et activé (jeton **et** mot de passe requis, pour qu'un tiers ne puisse pas finaliser une inscription forgée).
4. Une entrée ne sert qu'**une fois** (contrainte d'unicité en base) : impossible d'ouvrir un second compte avec le même matricule.

Les refus (non listé, déjà utilisé, nom différent…) renvoient **un message unique** qui ne révèle ni l'existence ni l'état d'une entrée. Limites de débit : 5 tentatives/heure par IP et par matricule ; 10 confirmations/10 min par IP ; verrouillage temporaire d'un compte après 8 échecs de connexion en 15 min (compteurs stockés en base, valables avec plusieurs workers).

> L'e-mail réel n'est envoyé qu'avec `EMAIL_BACKEND=smtp` et un serveur SMTP configuré (voir `DEPLOIEMENT.md`). En développement (`console`), le lien apparaît dans les journaux du backend.
