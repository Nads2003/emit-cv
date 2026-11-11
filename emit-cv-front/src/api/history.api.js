import api from "./axiosInstance";
import { historiqueStore } from "@/data/historiqueStore";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** GET /api/historique/  →  [{ id, action, date }]  (en démo : { id, key, params, date }) */
export const getHistorique = async () => {
  if (MOCK) {
    await wait(300);
    return historiqueStore.list();
  }
  const { data } = await api.get("/historique/");
  return data;
};