import { createContext, useContext, useState, useCallback } from 'react';
import {
  createUser,
  verifyUser,
  getSession,
  setSession,
  clearSession,
} from '../utils/storage';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getSession());

  const login = useCallback((email, password) => {
    const verified = verifyUser(email, password);
    if (!verified) throw new Error('Incorrect email or password.');
    setSession(verified.email);
    setUser(verified);
    return verified;
  }, []);

  const signup = useCallback((name, email, password) => {
    const created = createUser({ name, email, password });
    setSession(created.email);
    setUser(created);
    return created;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
