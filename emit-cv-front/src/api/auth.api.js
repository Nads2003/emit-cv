import api from "./axiosInstance";

const MOCK = import.meta.env.VITE_AUTH_MOCK === "true";

/**
 * Attendu côté Django : POST /api/auth/login/
 * Corps    : { email, password }
 * Réponse  : { access, refresh, user: { id, nom, email, role } }
 */
export const loginRequest = async (email, password) => {
  if (MOCK) {
    // Simulation temporaire : "admin..." => administrateur, sinon étudiant
    await new Promise((r) => setTimeout(r, 600));
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