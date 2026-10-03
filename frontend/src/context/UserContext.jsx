import { createContext, useContext, useState } from "react";
import { mockCurrentUser } from "@/data/mockData";

// Mock session + profile held in memory. Replace with real auth later.
const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(mockCurrentUser);
  const updateUser = (patch) => setUser((u) => ({ ...u, ...patch }));
  const login = () => setUser(mockCurrentUser);
  const logout = () => {};
  return <UserContext.Provider value={{ user, updateUser, login, logout }}>{children}</UserContext.Provider>;
}

export function useUser() {
  return useContext(UserContext);
}
