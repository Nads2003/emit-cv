-- ============================================================================
-- EMIT · CV intelligent : schéma PostgreSQL
-- Généré automatiquement depuis les modèles (python -m scripts.export_sql). Ne pas modifier à la main.
--
-- 17 tables = les 17 classes du DIAGRAMME DE CLASSES du cahier des charges : mêmes noms de tables et de colonnes
--   (en minuscules : PostgreSQL ignore la casse des identifiants non guillemetés). Seules colonnes ajoutées : clés primaires/étrangères.
--   Noms conservés tels quels dans le diagramme : « scrore » (Recommandation) et « dure » (Experience).
-- + l'association « viser » + des tables COMPLÉMENTAIRES, séparées, pour ce que le diagramme ne couvre pas.
-- Mots de passe : la colonne utilisateur.mdp contient un HASH Argon2, jamais le mot de passe.
-- ============================================================================

-- COMPLÉMENT (hors diagramme) : Compteurs de limitation de débit (anti brute-force) partagés entre workers
CREATE TABLE limite_debit (
	cle VARCHAR(200) NOT NULL, 
	compteur INTEGER NOT NULL, 
	debut_fenetre TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (cle)
);

-- Classe du diagramme : Mention
CREATE TABLE mention (
	id SERIAL NOT NULL, 
	nom VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nom)
);

-- Classe du diagramme : ModelCV
CREATE TABLE modelcv (
	id SERIAL NOT NULL, 
	nom VARCHAR(80) NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	apercu VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id)
);

-- COMPLÉMENT (hors diagramme) : File de tâches asynchrones (analyses de CV, calculs de classement) avec suivi d'état
CREATE TABLE tache (
	id SERIAL NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	cible_id INTEGER NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	priorite INTEGER NOT NULL, 
	tentatives INTEGER NOT NULL, 
	max_tentatives INTEGER NOT NULL, 
	erreur TEXT NOT NULL, 
	resultat JSON NOT NULL, 
	declencheur VARCHAR(60) NOT NULL, 
	cree_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	disponible_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	demarre_le TIMESTAMP WITH TIME ZONE, 
	termine_le TIMESTAMP WITH TIME ZONE, 
	verrouille_par VARCHAR(80), 
	verrou_expire_le TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_tache_cible_id ON tache (cible_id);
CREATE INDEX ix_tache_file ON tache (statut, priorite, id);
CREATE INDEX ix_tache_type ON tache (type);

-- Classe du diagramme : Utilisateur
CREATE TABLE utilisateur (
	id SERIAL NOT NULL, 
	nom VARCHAR(120) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	mdp VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_utilisateur_email ON utilisateur (email);
CREATE INDEX ix_utilisateur_role ON utilisateur (role);

-- Classe du diagramme : Administrateur
CREATE TABLE administrateur (
	id INTEGER NOT NULL, 
	poste VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES utilisateur (id) ON DELETE CASCADE
);

-- Classe du diagramme : Etudiant
CREATE TABLE etudiant (
	id INTEGER NOT NULL, 
	matricule VARCHAR(40) NOT NULL, 
	mention_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES utilisateur (id) ON DELETE CASCADE, 
	FOREIGN KEY(mention_id) REFERENCES mention (id)
);
CREATE UNIQUE INDEX ix_etudiant_matricule ON etudiant (matricule);

-- Classe du diagramme : Historique
CREATE TABLE historique (
	id SERIAL NOT NULL, 
	utilisateur_id INTEGER NOT NULL, 
	action VARCHAR(300) NOT NULL, 
	date TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(utilisateur_id) REFERENCES utilisateur (id) ON DELETE CASCADE
);
CREATE INDEX ix_historique_utilisateur_id ON historique (utilisateur_id);

-- Classe du diagramme : NiveauEtude
CREATE TABLE niveauetude (
	id SERIAL NOT NULL, 
	nom VARCHAR(20) NOT NULL, 
	mention_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(mention_id) REFERENCES mention (id) ON DELETE CASCADE
);

-- Classe du diagramme : Notification
CREATE TABLE notification (
	id SERIAL NOT NULL, 
	utilisateur_id INTEGER NOT NULL, 
	message VARCHAR(400) NOT NULL, 
	date TIMESTAMP WITH TIME ZONE NOT NULL, 
	lu BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(utilisateur_id) REFERENCES utilisateur (id) ON DELETE CASCADE
);
CREATE INDEX ix_notification_utilisateur_id ON notification (utilisateur_id);

-- Classe du diagramme : CV
CREATE TABLE cv (
	id SERIAL NOT NULL, 
	etudiant_id INTEGER NOT NULL, 
	modelcv_id INTEGER NOT NULL, 
	titre VARCHAR(160) NOT NULL, 
	datecreation TIMESTAMP WITH TIME ZONE NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	source VARCHAR(20) NOT NULL, 
	fichierpdf VARCHAR(255), 
	estpublic BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE, 
	FOREIGN KEY(modelcv_id) REFERENCES modelcv (id)
);
CREATE INDEX ix_cv_etudiant_id ON cv (etudiant_id);
CREATE INDEX ix_cv_statut ON cv (statut);

-- COMPLÉMENT (hors diagramme) : Disponibilité de l'étudiant (cahier des charges, section 4 : « Ajouter sa disponibilité »)
CREATE TABLE disponibilite (
	id SERIAL NOT NULL, 
	etudiant_id INTEGER NOT NULL, 
	disponible BOOLEAN NOT NULL, 
	datedebut DATE, 
	datefin DATE, 
	type VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (etudiant_id), 
	FOREIGN KEY(etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE
);

-- COMPLÉMENT (hors diagramme) : Niveau d'études de l'étudiant (le diagramme relie NiveauEtude à Mention, pas à Etudiant)
CREATE TABLE etudiant_niveau (
	etudiant_id INTEGER NOT NULL, 
	niveauetude_id INTEGER NOT NULL, 
	PRIMARY KEY (etudiant_id), 
	FOREIGN KEY(etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE, 
	FOREIGN KEY(niveauetude_id) REFERENCES niveauetude (id)
);

-- COMPLÉMENT (hors diagramme) : Imports Excel de la liste officielle (aperçu puis confirmation)
CREATE TABLE import_liste (
	id SERIAL NOT NULL, 
	admin_id INTEGER NOT NULL, 
	nom_fichier VARCHAR(255) NOT NULL, 
	hash_fichier VARCHAR(64) NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	nb_lignes INTEGER NOT NULL, 
	nb_nouveaux INTEGER NOT NULL, 
	nb_maj INTEGER NOT NULL, 
	nb_inchanges INTEGER NOT NULL, 
	nb_erreurs INTEGER NOT NULL, 
	cree_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	confirme_le TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(admin_id) REFERENCES administrateur (id)
);

-- Classe du diagramme : Offre
CREATE TABLE offre (
	id SERIAL NOT NULL, 
	administrateur_id INTEGER NOT NULL, 
	titre VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	datecreation TIMESTAMP WITH TIME ZONE NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(administrateur_id) REFERENCES administrateur (id)
);
CREATE INDEX ix_offre_statut ON offre (statut);

-- Classe du diagramme : Profile
CREATE TABLE profile (
	id SERIAL NOT NULL, 
	etudiant_id INTEGER NOT NULL, 
	photo VARCHAR(255), 
	telephone VARCHAR(30), 
	adresse VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (etudiant_id), 
	FOREIGN KEY(etudiant_id) REFERENCES etudiant (id) ON DELETE CASCADE
);

-- Classe du diagramme : Candidature
CREATE TABLE candidature (
	id SERIAL NOT NULL, 
	offre_id INTEGER NOT NULL, 
	cv_id INTEGER NOT NULL, 
	date TIMESTAMP WITH TIME ZONE NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_candidature_offre_cv UNIQUE (offre_id, cv_id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE CASCADE, 
	FOREIGN KEY(cv_id) REFERENCES cv (id)
);
CREATE INDEX ix_candidature_cv_id ON candidature (cv_id);
CREATE INDEX ix_candidature_offre_id ON candidature (offre_id);

-- Classe du diagramme : Competence
CREATE TABLE competence (
	id SERIAL NOT NULL, 
	cv_id INTEGER, 
	nom VARCHAR(80) NOT NULL, 
	niveaumaitrise VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);
CREATE INDEX ix_competence_cv_id ON competence (cv_id);
CREATE INDEX ix_competence_nom_lower ON competence (lower(nom));

-- COMPLÉMENT (hors diagramme) : Résultat mis en cache de l'analyse d'un CV (statut : en_attente, en_cours, ok, ocr_requis, vide, echec)
CREATE TABLE cv_analyse (
	cv_id INTEGER NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	message TEXT NOT NULL, 
	version_extracteur VARCHAR(20) NOT NULL, 
	hash_contenu VARCHAR(64) NOT NULL, 
	texte_scoring TEXT NOT NULL, 
	caracteristiques JSON NOT NULL, 
	analysee_le TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (cv_id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);
CREATE INDEX ix_cv_analyse_statut ON cv_analyse (statut);

-- COMPLÉMENT (hors diagramme) : Résumé, texte extrait du fichier importé, nom d'origine, date de mise à jour du CV
CREATE TABLE cv_infos (
	cv_id INTEGER NOT NULL, 
	resume TEXT NOT NULL, 
	texte_extrait TEXT NOT NULL, 
	fichier_nom_origine VARCHAR(255), 
	date_maj TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (cv_id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);

-- COMPLÉMENT (hors diagramme) : Liste officielle des étudiants autorisés à créer un compte (e-mail et matricule uniques)
CREATE TABLE etudiant_autorise (
	id SERIAL NOT NULL, 
	nom VARCHAR(120) NOT NULL, 
	prenom VARCHAR(120) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	matricule VARCHAR(40) NOT NULL, 
	import_id INTEGER, 
	cree_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	utilisateur_id INTEGER, 
	compte_cree_le TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(import_id) REFERENCES import_liste (id) ON DELETE SET NULL, 
	UNIQUE (utilisateur_id), 
	FOREIGN KEY(utilisateur_id) REFERENCES utilisateur (id) ON DELETE SET NULL
);
CREATE UNIQUE INDEX ix_etudiant_autorise_email ON etudiant_autorise (email);
CREATE UNIQUE INDEX ix_etudiant_autorise_matricule ON etudiant_autorise (matricule);

-- Classe du diagramme : Experience
CREATE TABLE experience (
	id SERIAL NOT NULL, 
	cv_id INTEGER NOT NULL, 
	poste VARCHAR(160) NOT NULL, 
	entreprise VARCHAR(160) NOT NULL, 
	dure VARCHAR(50) NOT NULL, 
	datedebut DATE, 
	datefin DATE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);
CREATE INDEX ix_experience_cv_id ON experience (cv_id);

-- Classe du diagramme : Formation
CREATE TABLE formation (
	id SERIAL NOT NULL, 
	cv_id INTEGER NOT NULL, 
	diplome VARCHAR(160) NOT NULL, 
	etablissement VARCHAR(160) NOT NULL, 
	annee INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);
CREATE INDEX ix_formation_cv_id ON formation (cv_id);

-- COMPLÉMENT (hors diagramme) : Lignes d'un import Excel et leur diagnostic
CREATE TABLE import_ligne (
	id SERIAL NOT NULL, 
	import_id INTEGER NOT NULL, 
	numero INTEGER NOT NULL, 
	nom VARCHAR(255) NOT NULL, 
	prenom VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	matricule VARCHAR(255) NOT NULL, 
	action VARCHAR(20) NOT NULL, 
	message TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(import_id) REFERENCES import_liste (id) ON DELETE CASCADE
);
CREATE INDEX ix_import_ligne_import_id ON import_ligne (import_id);

-- COMPLÉMENT (hors diagramme) : Type d'opportunité, échéances, niveau d'études minimal et son caractère obligatoire
CREATE TABLE offre_infos (
	offre_id INTEGER NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	date_limite DATE, 
	periode_debut DATE, 
	periode_fin DATE, 
	niveauetude_min_id INTEGER, 
	niveau_obligatoire BOOLEAN NOT NULL, 
	PRIMARY KEY (offre_id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE CASCADE, 
	FOREIGN KEY(niveauetude_min_id) REFERENCES niveauetude (id)
);

-- COMPLÉMENT (hors diagramme) : Projets académiques et personnels (critère d'IA « Expérience et projets »)
CREATE TABLE projet (
	id SERIAL NOT NULL, 
	cv_id INTEGER NOT NULL, 
	titre VARCHAR(160) NOT NULL, 
	description TEXT NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	annee INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cv_id) REFERENCES cv (id) ON DELETE CASCADE
);
CREATE INDEX ix_projet_cv_id ON projet (cv_id);

-- COMPLÉMENT (hors diagramme) : Traçabilité de chaque classement : version de l'algorithme, pondérations, critères de l'offre
CREATE TABLE scoring_run (
	id SERIAL NOT NULL, 
	offre_id INTEGER NOT NULL, 
	version_algorithme VARCHAR(20) NOT NULL, 
	poids JSON NOT NULL, 
	criteres_offre JSON NOT NULL, 
	moteur_ia VARCHAR(30) NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	nb_candidats INTEGER NOT NULL, 
	duree_ms INTEGER NOT NULL, 
	erreur TEXT NOT NULL, 
	declencheur VARCHAR(60) NOT NULL, 
	cree_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE CASCADE
);
CREATE INDEX ix_scoring_run_offre_id ON scoring_run (offre_id);

-- Classe du diagramme : association « viser » (Mention 0..* — Offre 0..*)
CREATE TABLE viser (
	offre_id INTEGER NOT NULL, 
	mention_id INTEGER NOT NULL, 
	PRIMARY KEY (offre_id, mention_id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE CASCADE, 
	FOREIGN KEY(mention_id) REFERENCES mention (id) ON DELETE CASCADE
);

-- Classe du diagramme : CritereOffre
CREATE TABLE critereoffre (
	id SERIAL NOT NULL, 
	offre_id INTEGER NOT NULL, 
	competence_id INTEGER NOT NULL, 
	poids FLOAT NOT NULL, 
	niveaurequis VARCHAR(20) NOT NULL, 
	obligatoire BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE CASCADE, 
	FOREIGN KEY(competence_id) REFERENCES competence (id)
);
CREATE INDEX ix_critereoffre_offre_id ON critereoffre (offre_id);

-- COMPLÉMENT (hors diagramme) : Missions et réalisations d'une expérience (critère d'IA « Adéquation aux missions »)
CREATE TABLE experience_infos (
	experience_id INTEGER NOT NULL, 
	description TEXT NOT NULL, 
	PRIMARY KEY (experience_id), 
	FOREIGN KEY(experience_id) REFERENCES experience (id) ON DELETE CASCADE
);

-- COMPLÉMENT (hors diagramme) : Inscription en attente de vérification d'e-mail (aucun compte tant que non confirmée)
CREATE TABLE inscription_en_attente (
	id SERIAL NOT NULL, 
	autorise_id INTEGER NOT NULL, 
	mdp_hash VARCHAR(255) NOT NULL, 
	mention_id INTEGER NOT NULL, 
	niveau_id INTEGER, 
	token_hash VARCHAR(64) NOT NULL, 
	expire_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	tentatives INTEGER NOT NULL, 
	cree_le TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (autorise_id), 
	FOREIGN KEY(autorise_id) REFERENCES etudiant_autorise (id) ON DELETE CASCADE, 
	FOREIGN KEY(mention_id) REFERENCES mention (id), 
	FOREIGN KEY(niveau_id) REFERENCES niveauetude (id)
);
CREATE UNIQUE INDEX ix_inscription_en_attente_token_hash ON inscription_en_attente (token_hash);

-- Classe du diagramme : Recommandation
CREATE TABLE recommandation (
	id SERIAL NOT NULL, 
	candidature_id INTEGER NOT NULL, 
	scrore INTEGER NOT NULL, 
	statut VARCHAR(20) NOT NULL, 
	date TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (candidature_id), 
	FOREIGN KEY(candidature_id) REFERENCES candidature (id) ON DELETE CASCADE
);
CREATE INDEX ix_recommandation_scrore ON recommandation (scrore);

-- COMPLÉMENT (hors diagramme) : Rang, détail explicable du score, statut éliminatoire et calcul d'origine
CREATE TABLE recommandation_detail (
	recommandation_id INTEGER NOT NULL, 
	rang INTEGER NOT NULL, 
	elimine BOOLEAN NOT NULL, 
	run_id INTEGER, 
	detail JSON NOT NULL, 
	PRIMARY KEY (recommandation_id), 
	FOREIGN KEY(recommandation_id) REFERENCES recommandation (id) ON DELETE CASCADE, 
	FOREIGN KEY(run_id) REFERENCES scoring_run (id) ON DELETE SET NULL
);
CREATE INDEX ix_recommandation_detail_elimine ON recommandation_detail (elimine);
CREATE INDEX ix_recommandation_detail_rang ON recommandation_detail (rang);
