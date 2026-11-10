import api from "./axiosInstance";
import { notifStore } from "@/data/notifStore";

const MOCK = import.meta.env.VITE_AUTH_MOCK !== "false";

/**
 * GET /api/notifications/
 * Réponse : [{ id, message, date, lu }]  (en démo : { id, key, params, date, lu })
 */
export const getNotifications = async (role) => {
  if (MOCK) return notifStore.list(role);
  const { data } = await api.get("/notifications/");
  return data;
};

/** PATCH /api/notifications/{id}/  { lu: true } */
export const markNotificationRead = async (role, id) => {
  if (MOCK) return notifStore.markRead(role, id);
  await api.patch(`/notifications/${id}/`, { lu: true });
};

/** POST /api/notifications/tout-lire/ */
export const markAllNotificationsRead = async (role) => {
  if (MOCK) return notifStore.markAll(role);
  await api.post("/notifications/tout-lire/");
};