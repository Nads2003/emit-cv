const skills = (list) => list.map(([nom, niveau], i) => ({ id: `s${i}`, nom, niveau }));

const make = ({ id, nom, matricule, mention, niveau, dispo, poste, competences, diplome, annee, exps = [], publie = true }) => ({
  id,
  matricule,
  mention,
  niveau,
  cvPublie: publie,
  cv: {
    titre: `CV ${poste}`,
    statut: publie ? "publie" : "brouillon",
    source: "cree",
    modele: "moderne",
    profil: {
      nom,
      poste,
      email: `${nom.split(" ")[0].toLowerCase()}@emit.mg`,
      telephone: `+261 34 00 000 0${id}`,
      adresse: "Antananarivo, Madagascar",
      resume: `Étudiant(e) en ${niveau} ${mention}, motivé(e), rigoureux(se) et à la recherche d'une opportunité pour mettre en pratique ses compétences.`,
      disponibilite: dispo,
    },
    competences: skills(competences),
    formations: [{ id: "f1", diplome, etablissement: "EMIT", annee }],
    experiences: exps.map((e, i) => ({ id: `e${i}`, ...e })),
  },
});

export const candidatsMock = [
  make({
    id: 1, nom: "Rakoto Jean", matricule: "EMIT-2024-001", mention: "Informatique", niveau: "L3",
    dispo: "immediate", poste: "Développeur web Full Stack", diplome: "Licence en Informatique", annee: "2026",
    competences: [["React", "avance"], ["Django", "intermediaire"], ["PostgreSQL", "intermediaire"], ["Git", "avance"], ["Tailwind CSS", "avance"]],
    exps: [{ poste: "Stagiaire développeur", entreprise: "Startup Mada Tech", dateDebut: "2025-07", dateFin: "2025-09", description: "Modules React et API Django REST." }],
  }),
  make({
    id: 2, nom: "Rasoanaivo Miora", matricule: "EMIT-2023-014", mention: "Informatique", niveau: "M1",
    dispo: "oneMonth", poste: "Data analyst", diplome: "Master 1 en Informatique", annee: "2026",
    competences: [["Python", "avance"], ["SQL", "avance"], ["Power BI", "intermediaire"], ["Statistiques", "intermediaire"]],
    exps: [{ poste: "Stagiaire data", entreprise: "Orange Madagascar", dateDebut: "2025-06", dateFin: "2025-08", description: "Tableaux de bord Power BI et requêtes SQL." }],
  }),
  make({
    id: 3, nom: "Andrianarisoa Tahina", matricule: "EMIT-2024-022", mention: "Réseaux et Télécoms", niveau: "L2",
    dispo: "immediate", poste: "Technicien réseau", diplome: "Licence 2 Réseaux et Télécoms", annee: "2027",
    competences: [["Cisco", "intermediaire"], ["TCP/IP", "avance"], ["Linux", "intermediaire"]],
  }),
  make({
    id: 4, nom: "Razafindrakoto Hery", matricule: "EMIT-2023-031", mention: "Informatique", niveau: "L3",
    dispo: "threeMonths", poste: "Développeur mobile", diplome: "Licence en Informatique", annee: "2026",
    competences: [["React Native", "intermediaire"], ["API REST", "avance"], ["UI / UX", "intermediaire"], ["Git", "intermediaire"]],
  }),
  make({
    id: 5, nom: "Randrianasolo Fanja", matricule: "EMIT-2022-009", mention: "Gestion", niveau: "M1",
    dispo: "immediate", poste: "Assistante gestion de projet", diplome: "Master 1 en Gestion", annee: "2026",
    competences: [["Gestion de projet", "avance"], ["Excel", "avance"], ["Communication", "expert"]],
    exps: [{ poste: "Assistante administrative", entreprise: "Banque partenaire", dateDebut: "2025-01", dateFin: "2025-04", description: "Suivi de planning et comptes rendus." }],
  }),
  make({
    id: 6, nom: "Rakotomalala Lova", matricule: "EMIT-2021-005", mention: "Réseaux et Télécoms", niveau: "M2",
    dispo: "oneMonth", poste: "Analyste sécurité", diplome: "Master 2 Réseaux et Télécoms", annee: "2026",
    competences: [["Sécurité réseau", "avance"], ["Linux", "avance"], ["Cisco", "intermediaire"], ["TCP/IP", "intermediaire"]],
  }),
  make({
    id: 7, nom: "Ravelomanana Soa", matricule: "EMIT-2024-037", mention: "Informatique", niveau: "L3",
    dispo: "immediate", poste: "Développeuse web", diplome: "Licence en Informatique", annee: "2026",
    competences: [["React", "intermediaire"], ["Django", "avance"], ["PostgreSQL", "avance"], ["Python", "intermediaire"], ["Git", "intermediaire"]],
    exps: [{ poste: "Stagiaire backend", entreprise: "EMIT", dateDebut: "2025-08", dateFin: "2025-10", description: "API Django REST et base PostgreSQL." }],
  }),
  make({
    id: 8, nom: "Rabemananjara Tojo", matricule: "EMIT-2021-018", mention: "Informatique", niveau: "M2",
    dispo: "notAvailable", poste: "Ingénieur logiciel", diplome: "Master 2 en Informatique", annee: "2026",
    competences: [["React", "expert"], ["Django", "avance"], ["PostgreSQL", "avance"], ["Python", "avance"], ["Git", "expert"]],
  }),
  // CV non publié : exclu des recommandations et de la recherche
  make({
    id: 9, nom: "Ramanantsoa Fy", matricule: "EMIT-2025-040", mention: "Informatique", niveau: "L2",
    dispo: "immediate", poste: "Débutant web", diplome: "Licence 2 en Informatique", annee: "2027",
    competences: [["HTML / CSS", "debutant"]], publie: false,
  }),
];