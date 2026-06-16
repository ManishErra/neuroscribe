"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isTokenExpired } from "../lib/auth";
import { apiRequest } from "../lib/api";

interface User {
  id: string;
  email: string;
  name: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem("ns_access_token");
      if (!token || isTokenExpired(token)) {
        throw new Error("No token or token expired");
      }
      const userData = await apiRequest("/auth/me");
      setUser(userData);
    } catch (e) {
      localStorage.removeItem("ns_access_token");
      setUser(null);
    }
  };

  const refreshUser = async () => {
    setLoading(true);
    await fetchUser();
    setLoading(false);
  };

  useEffect(() => {
    const initAuth = async () => {
      await fetchUser();
      setLoading(false);
    };
    initAuth();
  }, []);

  useEffect(() => {
    if (loading) return;

    const publicPaths = ["/login"];
    const isPublicPath = publicPaths.includes(pathname);

    if (!user && !isPublicPath) {
      router.push("/login");
    } else if (user && isPublicPath) {
      router.push("/patients");
    }
  }, [user, loading, pathname, router]);

  const login = async (token: string) => {
    localStorage.setItem("ns_access_token", token);
    setLoading(true);
    await fetchUser();
    setLoading(false);
  };

  const logout = () => {
    localStorage.removeItem("ns_access_token");
    setUser(null);
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-black text-zinc-400">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-t-blue-500 border-zinc-800 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm font-medium tracking-wide">Loading NeuroScribe...</p>
        </div>
      </div>
    );
  }

  const publicPaths = ["/login"];
  const isPublicPath = publicPaths.includes(pathname);

  if (!user && !isPublicPath) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-black text-zinc-400">
        <p className="text-sm font-medium tracking-wide">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
