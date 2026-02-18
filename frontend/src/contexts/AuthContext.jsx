import { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const login = async (username, password, totpCode = '') => {
    const res = await client.post('/accounts/login/', {
      username, password, totp_code: totpCode,
    });
    if (res.data.requires_2fa) {
      return { requires2fa: true };
    }
    localStorage.setItem('tokens', JSON.stringify(res.data.tokens));
    localStorage.setItem('user', JSON.stringify(res.data.user));
    setUser(res.data.user);
    return { success: true };
  };

  const register = async (data) => {
    const res = await client.post('/accounts/register/', data);
    localStorage.setItem('tokens', JSON.stringify(res.data.tokens));
    localStorage.setItem('user', JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('tokens');
    localStorage.removeItem('user');
    setUser(null);
  };

  const refreshProfile = async () => {
    try {
      const res = await client.get('/accounts/profile/');
      localStorage.setItem('user', JSON.stringify(res.data));
      setUser(res.data);
    } catch {
      // ignore
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, refreshProfile, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
