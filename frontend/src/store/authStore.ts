import { create } from 'zustand';
import { api } from '../utils/api';

interface User {
  id: number;
  email: string;
  is_admin: boolean;
  avatar_url?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      set({ token: access_token, loading: false });
      
      // Fetch user profile info
      const userResponse = await api.get('/auth/me');
      set({ user: userResponse.data });
      return true;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication failed';
      set({ error: msg, loading: false });
      return false;
    }
  },

  register: async (email, password) => {
    set({ loading: true, error: null });
    try {
      await api.post('/auth/register', { email, password });
      set({ loading: false });
      return true;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed';
      set({ error: msg, loading: false });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, error: null });
  },

  fetchMe: async () => {
    if (!localStorage.getItem('token')) return;
    set({ loading: true });
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, loading: false });
    } catch (err) {
      localStorage.removeItem('token');
      set({ user: null, token: null, loading: false });
    }
  }
}));
