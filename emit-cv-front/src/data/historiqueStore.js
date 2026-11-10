const KEY = "emit_historique_demo";

const read = () => {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? [];
  } catch {
    return [];
  }
};

export const historiqueStore = {
  list: read,
  // Équivalent de enregistrerAction(action) du diagramme de classes
  log(key, params = {}) {
    const entry = { id: Date.now() + Math.random(), key, params, date: new Date().toISOString() };
    try {
      localStorage.setItem(KEY, JSON.stringify([entry, ...read()].slice(0, 100)));
    } catch {
      /* stockage indisponible */
    }
  },
};