"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

export interface User {
  id: string;
  name: string;
  email?: string;
}

type UserContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  login: (nextUser: User) => void;
  logout: () => void;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const stored = window.localStorage.getItem("stellcodex-user");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as User;
      if (parsed?.id && parsed?.name) {
        setUser(parsed);
      }
    } catch {
      window.localStorage.removeItem("stellcodex-user");
    }
  }, []);

  const login = (nextUser: User) => {
    setUser(nextUser);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("stellcodex-user", JSON.stringify(nextUser));
    }
  };

  const logout = () => {
    setUser(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("stellcodex-user");
    }
  };

  const value = useMemo(
    () => ({ user, isAuthenticated: Boolean(user), login, logout }),
    [user]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within UserProvider");
  }
  return context;
}
