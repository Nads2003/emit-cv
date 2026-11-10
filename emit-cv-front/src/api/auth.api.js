import api from "./axiosInstance";

// Simulation active tant que VITE_AUTH_MOCK n'est pas "false"
const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * POST /api/auth/login/
 * Corps    : { email, password }
 * Réponse  : { access, refresh, user: { id, nom, email, role } }
 */
export const loginRequest = async (email, password) => {
  if (MOCK) {
    // "admin..." => administrateur, sinon étudiant
    await wait(600);
    if (!email || password.length < 4) {
      const err = new Error("invalid");
      err.response = { status: 401 };
      throw err;
    }
    const role = email.toLowerCase().startsWith("admin") ? "admin" : "etudiant";
    return {
      access: "mock-access",
      refresh: "mock-refresh",
      user: { id: 1, nom: role === "admin" ? "Administrateur EMIT" : "Étudiant EMIT", email, role },
    };
  }

  const { data } = await api.post("/auth/login/", { email, password });
  return data;
};

/**
 * POST /api/auth/register/
 * Corps    : { nom, email, matricule, password }
 * Réponse  : 201 (compte créé) ou 400/409 si email ou matricule déjà utilisé
 */
export const registerRequest = async ({ nom, email, matricule, password }) => {
  if (MOCK) {
    await wait(700);
    // Pour tester l'erreur : un email qui commence par "exist"
    if (email.toLowerCase().startsWith("exist")) {
      const err = new Error("conflict");
      err.response = { status: 409 };
      throw err;
    }
    return { ok: true };
  }

  const { data } = await api.post("/auth/register/", { nom, email, matricule, password });
  return data;
};