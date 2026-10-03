import { mockCurrentUser, mockPartners, mockConversations, mockMessages } from "@/data/mockData";

const API_BASE = import.meta.env.VITE_API_URL || "";

const delay = (value, ms = 450) => new Promise((resolve) => setTimeout(() => resolve(value), ms));

// ─── Helpers ────────────────────────────────────────────────────────────────

const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const saveTokens = (data) => {
  if (data.access_token) localStorage.setItem("access_token", data.access_token);
  if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
};

const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// Parse error detail from FastAPI response
const parseError = async (response) => {
  try {
    const body = await response.json();
    // FastAPI validation errors come as { detail: [...] } or { detail: "string" }
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((e) => e.msg || e.message || JSON.stringify(e)).join(", ");
    }
    return JSON.stringify(body);
  } catch {
    return `Request failed with status ${response.status}`;
  }
};

// ─── Auth APIs ───────────────────────────────────────────────────────────────

/**
 * Register a new user.
 * Backend: POST /api/v1/auth/register
 * Body: { username, email, phone_number, password, full_name }
 * Returns: OTPResponse → { message: string }
 */
export const register = async ({ username, email, phone_number, password, full_name }) => {
  const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, phone_number, password, full_name }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  return await response.json(); // { message: "..." }
};

/**
 * Verify email with OTP.
 * Backend: POST /api/v1/auth/verify-email
 * Body: { email, otp }
 * Returns: OTPResponse → { message: string }
 */
export const verifyEmail = async (email, otp) => {
  const response = await fetch(`${API_BASE}/api/v1/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  return await response.json(); // { message: "Email verified successfully! You can now login." }
};

/**
 * Resend OTP to the given email.
 * Backend: POST /api/v1/auth/resend-otp
 * Body: { email }
 * Returns: OTPResponse → { message: string }
 */
export const resendOtp = async (email) => {
  const response = await fetch(`${API_BASE}/api/v1/auth/resend-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  return await response.json();
};

/**
 * Login with username + password.
 * Backend: POST /api/v1/auth/login
 * Body: { username, password }    ← NOTE: backend uses "username", NOT email
 * Returns: Token → { access_token, refresh_token, token_type }
 */
export const login = async (username, password) => {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  const data = await response.json();
  saveTokens(data);
  return data;
};

/**
 * Logout current session (single device).
 * Backend: POST /api/v1/auth/logout
 * Body: { refresh_token, access_token }
 */
export const logout = async () => {
  const access_token = localStorage.getItem("access_token");
  const refresh_token = localStorage.getItem("refresh_token");
  if (refresh_token && access_token) {
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token, access_token }),
      });
    } catch {
      // ignore network errors on logout
    }
  }
  clearTokens();
};

/**
 * Get the currently authenticated user.
 * Backend: GET /api/v1/auth/me  (requires Bearer token)
 * Returns: RegisterResponse → { id, username, full_name, email, phone_number, is_active, role, account_status, created_at }
 */
export const fetchCurrentUser = async () => {
  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error("Not authenticated");
  return await response.json();
};

/**
 * Alias used by UserContext; falls back to mock data if not authenticated.
 */
export const getCurrentUser = async () => {
  try {
    return await fetchCurrentUser();
  } catch {
    return await delay(mockCurrentUser, 0);
  }
};

// ─── Interests APIs ──────────────────────────────────────────────────────────

export const getInterests = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/interests`);
    if (!response.ok) throw new Error("Failed to fetch interests");
    const data = await response.json();
    return data.interests || data || [];
  } catch (error) {
    console.error("Error fetching interests:", error);
    return [];
  }
};

export const getMyInterests = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/profiles/me/interests`, {
      headers: authHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch user interests");
    const data = await response.json();
    return data.interests || data || [];
  } catch (error) {
    console.error("Error fetching user interests:", error);
    return [];
  }
};

export const setMyInterests = async ({ interest_ids = [], custom_interests = [] } = {}) => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/profiles/me/interests`, {
      method: "PUT",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ interest_ids, custom_interests }),
    });
    if (!response.ok) throw new Error("Failed to update user interests");
    const data = await response.json();
    return data.interests || data || [];
  } catch (error) {
    console.error("Error updating user interests:", error);
    return [];
  }
};

// ─── Mock APIs (to be replaced with real calls later) ────────────────────────

export const getPartners = async () => delay(mockPartners);

export const getPartnerById = async (id) => {
  const partner = mockPartners.find((p) => p.id === id) || null;
  return delay(partner, 250);
};

export const getConversations = async () => {
  const conversations = mockConversations.map((c) => ({
    ...c,
    partner: mockPartners.find((p) => p.id === c.partnerId),
  }));
  return delay(conversations, 250);
};

export const getMessages = async (conversationId) => {
  const msgs = mockMessages[conversationId] || [];
  return delay(msgs, 150);
};
