"use client";

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { API, api, getToken, setToken } from "./api";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_system_admin: boolean;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api<User>(API.userManagement, "/auth/me");
      setUser(me);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api<{ access_token: string; user: User }>(
      API.userManagement, "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }), auth: false });
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const register = useCallback(async (fullName: string, email: string, password: string) => {
    const res = await api<{ access_token: string; user: User }>(
      API.userManagement, "/auth/register",
      { method: "POST", body: JSON.stringify({ full_name: fullName, email, password }), auth: false });
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
