import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, getProfile } from '../services/api';

const AuthContext = createContext(null);

/* Role codes from backend UserProfile.ROLE_CHOICES */
export const ROLES = {
  MANAGER: 'MANAGER',
  WAITER: 'WAITER',
  CHEF: 'CHEF',
  HOST: 'HOST',
  CASHIER: 'CASHIER',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      getProfile()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const { data } = await apiLogin(username, password);
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    const profile = await getProfile();
    setUser(profile.data);
    return profile.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  /** Get the role string from the user profile */
  const role = user?.role || null;

  /** Check if current user has one of the given roles */
  const hasRole = (...roles) => roles.includes(role);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, role, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
