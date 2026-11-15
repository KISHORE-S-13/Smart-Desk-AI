import React, { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("smartdesk_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("smartdesk_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleAuthExpired = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener("smartdesk_auth_expired", handleAuthExpired);
    return () => window.removeEventListener("smartdesk_auth_expired", handleAuthExpired);
  }, []);

  useEffect(() => {
    const verifyUser = async () => {
      if (token) {
        try {
          const res = await authApi.getMe();
          setUser(res.data.user);
          localStorage.setItem("smartdesk_user", JSON.stringify(res.data.user));
        } catch {
          setUser(null);
          setToken(null);
          localStorage.removeItem("smartdesk_token");
          localStorage.removeItem("smartdesk_user");
        }
      }
      setLoading(false);
    };
    verifyUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await authApi.login(email, password);
    const { token: newToken, user: newUser } = res.data;
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("smartdesk_token", newToken);
    localStorage.setItem("smartdesk_user", JSON.stringify(newUser));
    return newUser;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("smartdesk_token");
    localStorage.removeItem("smartdesk_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.role === "admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
