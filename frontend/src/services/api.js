import { mockCurrentUser, mockPartners, mockConversations, mockMessages } from "@/data/mockData";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const delay = (value, ms = 200) => new Promise((resolve) => setTimeout(() => resolve(value), ms));

// ─── Helpers ────────────────────────────────────────────────────────────────

export const authHeaders = () => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const saveTokens = (data) => {
  if (typeof window === "undefined") return;
  if (data.access_token) localStorage.setItem("access_token", data.access_token);
  if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
};

export const clearTokens = () => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// Parse error detail from FastAPI response
export const parseError = async (response) => {
  try {
    const body = await response.json();
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
  return await response.json();
};

/**
 * Verify email with OTP.
 * Backend: POST /api/v1/auth/verify-email
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
  return await response.json();
};

/**
 * Resend OTP to email.
 * Backend: POST /api/v1/auth/resend-otp
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
 * Login with username/email + password.
 * Backend: POST /api/v1/auth/login
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
 * Logout current session.
 * Backend: POST /api/v1/auth/logout
 */
export const logout = async () => {
  if (typeof window !== "undefined") {
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
        // ignore network error on logout
      }
    }
  }
  clearTokens();
};

/**
 * Get the authenticated user identity.
 * Backend: GET /api/v1/auth/me
 */
export const fetchCurrentUser = async () => {
  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error("Not authenticated");
  return await response.json();
};

// ─── Profile APIs ────────────────────────────────────────────────────────────

export const fetchMyProfile = async () => {
  const response = await fetch(`${API_BASE}/api/v1/profiles/me`, {
    headers: authHeaders(),
  });
  if (!response.ok) return null;
  return await response.json();
};

export const updateMyProfile = async (profileData) => {
  const response = await fetch(`${API_BASE}/api/v1/profiles/me`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(profileData),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  return await response.json();
};

// ─── Languages APIs ──────────────────────────────────────────────────────────

export const fetchLanguages = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/languages`);
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
};

export const fetchMyLanguages = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/profiles/me/languages`, {
      headers: authHeaders(),
    });
    if (!response.ok) return [];
    const data = await response.json();
    return data.languages || [];
  } catch {
    return [];
  }
};

export const updateMyLanguages = async (languagesList) => {
  const response = await fetch(`${API_BASE}/api/v1/profiles/me/languages`, {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ languages: languagesList }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  return await response.json();
};

// ─── Interests APIs ──────────────────────────────────────────────────────────

export const getInterests = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/interests`);
    if (!response.ok) return [];
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
    if (!response.ok) return [];
    const data = await response.json();
    return data.interests || [];
  } catch (error) {
    console.error("Error fetching user interests:", error);
    return [];
  }
};

export const setMyInterests = async ({ interest_ids = [], custom_interests = [] } = {}) => {
  const response = await fetch(`${API_BASE}/api/v1/profiles/me/interests`, {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ interest_ids, custom_interests }),
  });
  if (!response.ok) {
    const msg = await parseError(response);
    throw new Error(msg);
  }
  const data = await response.json();
  return data.interests || [];
};

// ─── Unified Full User Profile ──────────────────────────────────────────────

export const getFullUserProfile = async () => {
  const authUser = await fetchCurrentUser();

  // Try to load profile, interests, languages in parallel
  const [profileRes, interestsRes, languagesRes] = await Promise.allSettled([
    fetchMyProfile(),
    getMyInterests(),
    fetchMyLanguages(),
  ]);

  const profile = profileRes.status === "fulfilled" ? profileRes.value || {} : {};
  const interestsList = interestsRes.status === "fulfilled" && Array.isArray(interestsRes.value) ? interestsRes.value : [];
  const languagesList = languagesRes.status === "fulfilled" && Array.isArray(languagesRes.value) ? languagesRes.value : [];

  const nativeLang = languagesList.find((l) => l.role === "NATIVE");
  const learningLang = languagesList.find((l) => l.role === "LEARNING");

  const interestNames = interestsList.map((i) => (typeof i === "object" ? i.name : i));

  return {
    ...authUser,
    name: authUser.full_name || authUser.username || "User",
    bio: profile.bio || "Language exchange enthusiast.",
    profession: profile.profession || "Language Learner",
    location: profile.location || "",
    avatar_url: profile.avatar_url || null,
    interests: interestNames.length > 0 ? interestNames : ["English Practice", "Culture", "Travel"],
    raw_interests: interestsList,
    languages: languagesList,
    nativeLanguage: nativeLang?.language_name || "Spanish",
    englishLevel: learningLang?.proficiency || "B2",
    learningLanguage: learningLang?.language_name || "English",
    profileCompletion: 80,
  };
};

export const getCurrentUser = async () => {
  try {
    return await getFullUserProfile();
  } catch {
    return delay(mockCurrentUser, 0);
  }
};

// ─── Matching / Partners APIs ───────────────────────────────────────────────

export const getMatches = async (limit = 20) => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/matches?limit=${limit}`, {
      headers: authHeaders(),
    });
    if (!response.ok) return null;
    const data = await response.json();
    return (data.items || []).map((m) => ({
      id: String(m.user_id),
      name: m.display_name || "Partner",
      profession: m.profession || "Language Learner",
      englishLevel: m.proficiency_level || "B2",
      nativeLanguage: "English",
      interests: m.shared_interests || [],
      bio: `Compatibility score: ${m.compatibility_score}%`,
      online: true,
      compatibility_score: m.compatibility_score,
    }));
  } catch {
    return null;
  }
};

// ─── Matching & Partner Profiles from Database ─────────────────────────────

export const fetchCommunityProfiles = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/profiles`);
    if (!response.ok) return [];
    const profiles = await response.json();
    return profiles.map((p) => ({
      id: String(p.user_id),
      name: p.name || "Partner",
      profession: p.profession || "Language Learner",
      englishLevel: p.english_level || "Intermediate",
      nativeLanguage: p.native_language || "English",
      learningLanguage: p.learning_language || "English",
      interests: Array.isArray(p.interests) ? p.interests : [],
      bio: p.bio || "Practicing English on TalkTribe.",
      location: p.location || "",
      avatar_url: p.avatar_url || null,
      online: true,
    }));
  } catch (err) {
    console.warn("fetchCommunityProfiles error:", err);
    return [];
  }
};

export const getMatches = async (limit = 20) => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/matches?limit=${limit}`, {
      headers: authHeaders(),
    });
    if (!response.ok) return null;
    const data = await response.json();
    return (data.items || []).map((m) => ({
      id: String(m.user_id),
      name: m.display_name || "Partner",
      profession: m.profession || "Language Learner",
      englishLevel: m.proficiency_level || "B2",
      nativeLanguage: "English",
      interests: m.shared_interests || [],
      bio: `Compatibility score: ${m.compatibility_score}%`,
      online: true,
      compatibility_score: m.compatibility_score,
    }));
  } catch {
    return null;
  }
};

export const getPartners = async () => {
  // 1. If user is logged in, try fetching tailored matches
  const matches = await getMatches(20);
  if (matches && matches.length > 0) {
    return matches;
  }
  // 2. Fetch real active community learners from PostgreSQL database
  const community = await fetchCommunityProfiles();
  if (community && community.length > 0) {
    return community;
  }
  return [];
};

export const getPartnerById = async (id) => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/profiles/${id}`);
    if (response.ok) {
      const p = await response.json();
      return {
        id: String(p.user_id),
        name: p.name || "Partner",
        profession: p.profession || "Language Learner",
        englishLevel: p.english_level || "Intermediate",
        nativeLanguage: p.native_language || "English",
        learningLanguage: p.learning_language || "English",
        interests: Array.isArray(p.interests) ? p.interests : [],
        bio: p.bio || "Practicing English on TalkTribe.",
        location: p.location || "",
        avatar_url: p.avatar_url || null,
        online: true,
      };
    }
  } catch (err) {
    console.warn("getPartnerById error:", err);
  }
  const partners = await getPartners();
  return partners.find((p) => String(p.id) === String(id)) || null;
};

// ─── Conversations & Messages ───────────────────────────────────────────────

export const getConversations = async () => {
  const partners = await getPartners();
  if (partners.length === 0) return [];

  return partners.slice(0, 5).map((p, idx) => ({
    id: `conv-${p.id}`,
    partnerId: p.id,
    partner: p,
    unread: idx === 0 ? 1 : 0,
    lastMessage: {
      text:
        idx === 0
          ? `Hey! Would love to practice English and discuss ${p.interests[0] || "our goals"}.`
          : `Great speaking with you earlier! Catch you soon.`,
      time: idx === 0 ? "10:42 AM" : "Yesterday",
    },
  }));
};

export const getMessages = async (conversationId) => {
  const partners = await getPartners();
  const partnerId = conversationId.replace("conv-", "");
  const partner = partners.find((p) => String(p.id) === String(partnerId)) || partners[0];
  const partnerName = partner ? partner.name.split(" ")[0] : "Partner";
  const interest = partner?.interests?.[0] || "language exchange";

  return [
    {
      id: "1",
      from: "partner",
      text: `Hi there! I saw your profile and noticed you are also interested in ${interest}. How is your English practice going?`,
      time: "10:30 AM",
    },
    {
      id: "2",
      from: "me",
      text: `Hello ${partnerName}! Thanks for reaching out. Yes, I practice speaking every week. Where are you joining from?`,
      time: "10:35 AM",
    },
    {
      id: "3",
      from: "partner",
      text: `I'm based in ${partner?.location || "our international community"}. Let's do a voice call soon!`,
      time: "10:42 AM",
    },
  ];
};
