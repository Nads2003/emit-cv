import { offresMock } from "./offres.mock";

const KEY = "emit_offres_demo";

const read = () => {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* stockage indisponible */
  }
  return structuredClone(offresMock);
};

const write = (list) => {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* stockage indisponible */
  }
};

export const offresStore = {
  all: read,
  get: (id) => read().find((o) => o.id === Number(id)) ?? null,
  save(offre) {
    const list = read();
    let saved = offre;
    if (offre.id) {
      const i = list.findIndex((o) => o.id === offre.id);
      if (i >= 0) list[i] = offre;
      else list.unshift(offre);
    } else {
      saved = { ...offre, id: Date.now(), datecreation: new Date().toISOString().slice(0, 10) };
      list.unshift(saved);
    }
    write(list);
    return saved;
  },
  remove(id) {
    write(read().filter((o) => o.id !== Number(id)));
  },
};