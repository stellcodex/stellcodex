"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type User = {
  name: string;
  role: "user" | "admin";
};

type UserContextValue = {
  user: User;
  setUser: (next: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
};

const UserContext = createContext<UserContextValue | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>({ name: "COSKUN", role: "user" });
  const logout = useCallback(() => setUser({ name: "Misafir", role: "user" }), []);
  const isAuthenticated = user.name !== "Misafir";
  const value = useMemo(
    () => ({ user, setUser, logout, isAuthenticated }),
    [isAuthenticated, logout, user]
  );
  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser, UserProvider içinde kullanılmalı.");
  return ctx;
}
