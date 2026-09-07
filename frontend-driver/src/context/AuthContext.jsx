import React, { createContext, useContext, useState, useEffect } from 'react';
import { driverApi } from '../api/client';

const DriverAuthContext = createContext(null);

export function DriverAuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = sessionStorage.getItem('driver_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => sessionStorage.getItem('driver_token') || null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleExpired = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('driver_auth_expired', handleExpired);
    return () => window.removeEventListener('driver_auth_expired', handleExpired);
  }, []);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const data = await driverApi.login(username, password);
      sessionStorage.setItem('driver_token', data.access_token);
      sessionStorage.setItem('driver_user', JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
      return { success: true, user: data.user };
    } catch (err) {
      return { success: false, error: err.message || 'Driver login failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem('driver_token');
    sessionStorage.removeItem('driver_user');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = Boolean(token && user);
  const isDriver = user?.role === 'driver';

  return (
    <DriverAuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated,
        isDriver,
      }}
    >
      {children}
    </DriverAuthContext.Provider>
  );
}

export function useDriverAuth() {
  const ctx = useContext(DriverAuthContext);
  if (!ctx) {
    throw new Error('useDriverAuth must be used within a DriverAuthProvider');
  }
  return ctx;
}
