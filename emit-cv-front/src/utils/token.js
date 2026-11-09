const ACCESS = "access_token";
const REFRESH = "refresh_token";
const USER = "user";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS),
  getRefresh: () => localStorage.getItem(REFRESH),
  set(access, refresh) {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem(USER));
    } catch {
      return null;
    }
  },
  setUser: (user) => localStorage.setItem(USER, JSON.stringify(user)),
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
    localStorage.removeItem(USER);
  },
};