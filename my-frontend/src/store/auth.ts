// src/store/auth.ts
import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (a: string, r: string) => void;
  clear: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  setTokens: (accessToken, refreshToken) => {
    set({ accessToken, refreshToken });
    // persistance simple (dev)
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
  },
  clear: () => {
    set({ accessToken: null, refreshToken: null });
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
  },
}));

// re-hydrate au chargement
const a = localStorage.getItem("accessToken");
const r = localStorage.getItem("refreshToken");
if (a && r) useAuth.getState().setTokens(a, r);
