import { createContext, useState, useCallback, useMemo } from "react";
import { loginRequest } from "@/api/auth.api";
import { tokenStorage } from "@/utils/token";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStorage.getUser());

  const login = useCallback(async (email, password) => {
    const data = await loginRequest(email, password);
    tokenStorage.set(data.access, data.refresh);
    tokenStorage.setUser(data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isAuthenticated: !!user, login, logout }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}