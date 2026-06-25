import { create } from "zustand";
import { auth } from "@/api/endpoints";
import type { User } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("token"),
  user: null,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await auth.login(email, password);
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);
      set({ token: access_token, isLoading: false });
      // Fetch user profile after getting token
      await get().fetchUser();
    } catch (error: unknown) {
      const message =
        error instanceof Error
          ? error.message
          : "Login failed. Please check your credentials.";
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null });
    window.location.href = "/login";
  },

  fetchUser: async () => {
    try {
      set({ isLoading: true });
      const response = await auth.getMe();
      set({ user: response.data, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ token: null, user: null, isLoading: false });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
