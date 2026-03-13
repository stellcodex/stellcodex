"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type User = {
  name: string;
  role: "user" | "admin";
};

type UserContextValue = {
  user: User;
  setUser: (next: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
};

const GUEST: User = { name: "Guest", role: "user" };

const UserContext = createContext<UserContextValue | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(GUEST);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== "undefined" ? window.localStorage.getItem("scx_token") : null;
    if (!token) {
      setLoading(false);
      return;
    }
    fetch("/api/v1/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.email) {
          setUser({
            name: data.email.split("@")[0],
            role: data.role === "admin" ? "admin" : "user",
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem("scx_token");
    document.cookie = "scx_token=; path=/; max-age=0";
    setUser(GUEST);
  }, []);

  const isAuthenticated = user.name !== "Guest";

  const value = useMemo(
    () => ({ user, setUser, logout, isAuthenticated, loading }),
    [isAuthenticated, loading, logout, user]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside UserProvider.");
  return ctx;
}
