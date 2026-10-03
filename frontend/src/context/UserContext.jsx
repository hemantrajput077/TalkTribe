import { createContext, useContext, useState, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, fetchCurrentUser } from "@/services/api";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount: try to restore session from stored access_token
  useEffect(() => {
    (async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await fetchCurrentUser();
        setUser(data);
      } catch {
        // Token expired or invalid — clear it
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const updateUser = (patch) => setUser((u) => ({ ...u, ...patch }));

  /** Login via username + password. Stores tokens and sets user. */
  const login = async (username, password) => {
    // 1️⃣ Get JWT tokens (apiLogin also saves them)
    await apiLogin(username, password);

    // 2️⃣ Immediately fetch the logged‑in user profile
    const profile = await fetchCurrentUser();

    // 3️⃣ Store the profile in context
    setUser(profile);

    // 4️⃣ Return the profile for the caller (LoginPage)
    return profile;
  };

  /** Logout: revoke tokens on backend, clear local state. */
  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, loading, updateUser, login, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
