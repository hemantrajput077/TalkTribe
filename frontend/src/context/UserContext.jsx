import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { login as apiLogin, logout as apiLogout, getFullUserProfile, updateMyProfile } from "@/services/api";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (typeof window === "undefined") {
      setLoading(false);
      return null;
    }
    const token = localStorage.getItem("access_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const data = await getFullUserProfile();
      setUser(data);
      return data;
    } catch (err) {
      console.warn("Session restore failed:", err);
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // On mount: try to restore session from stored access_token
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const updateUser = useCallback(async (patch) => {
    setUser((u) => (u ? { ...u, ...patch } : patch));

    // If profile fields are present, attempt background sync with backend
    const profileFields = {};
    if (patch.bio !== undefined) profileFields.bio = patch.bio;
    if (patch.profession !== undefined) profileFields.profession = patch.profession;
    if (patch.location !== undefined) profileFields.location = patch.location;
    if (patch.avatar_url !== undefined) profileFields.avatar_url = patch.avatar_url;

    if (Object.keys(profileFields).length > 0 && typeof window !== "undefined" && localStorage.getItem("access_token")) {
      try {
        await updateMyProfile(profileFields);
      } catch (err) {
        console.warn("Failed to sync profile update to backend:", err);
      }
    }
  }, []);

  /** Login via username/email + password. Stores tokens and sets user. */
  const login = async (username, password) => {
    // 1️⃣ Get JWT tokens (apiLogin saves them in localStorage)
    await apiLogin(username, password);

    // 2️⃣ Immediately fetch the full user profile (auth + profile + languages + interests)
    const profile = await getFullUserProfile();

    // 3️⃣ Store in context
    setUser(profile);

    return profile;
  };

  /** Logout: revoke tokens on backend, clear local state. */
  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, loading, updateUser, login, logout, refreshUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return ctx;
}
