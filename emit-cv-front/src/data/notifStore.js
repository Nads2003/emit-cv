const KEY = (role) => `emit_notifs_${role}`;

const seed = (role) => [
  {
    id: 1,
    key: role === "admin" ? "notif.welcomeAdmin" : "notif.welcomeStudent",
    params: {},
    date: new Date().toISOString(),
    lu: false,
  },
];

const read = (role) => {
  try {
    const raw = localStorage.getItem(KEY(role));
    if (raw) return JSON.parse(raw);
  } catch {
    /* stockage indisponible */
  }
  const initial = seed(role);
  try {
    localStorage.setItem(KEY(role), JSON.stringify(initial));
  } catch {
    /* stockage indisponible */
  }
  return initial;
};

const write = (role, list) => {
  try {
    localStorage.setItem(KEY(role), JSON.stringify(list));
  } catch {
    /* stockage indisponible */
  }
  window.dispatchEvent(new Event("emit:notifs")); // met la cloche à jour dans cet onglet
};

export const notifStore = {
  list: (role) => read(role).sort((a, b) => new Date(b.date) - new Date(a.date)),
  push(role, key, params = {}) {
    const n = { id: Date.now() + Math.random(), key, params, date: new Date().toISOString(), lu: false };
    write(role, [n, ...read(role)].slice(0, 50));
  },
  markRead: (role, id) => write(role, read(role).map((n) => (n.id === id ? { ...n, lu: true } : n))),
  markAll: (role) => write(role, read(role).map((n) => ({ ...n, lu: true }))),
};