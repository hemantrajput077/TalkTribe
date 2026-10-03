// Data access layer. Every screen reads data through these functions.
// Later, swap each body for a real request (e.g. getPartners -> GET /api/v1/matches)
// without touching any UI components.
import { mockPartners, mockConversations, mockMessages, mockCurrentUser, INTERESTS } from "@/data/mockData";

const delay = (value, ms = 450) => new Promise((resolve) => setTimeout(() => resolve(value), ms));

export const getCurrentUser = () => delay(mockCurrentUser, 0);
export const getInterests = () => delay(INTERESTS, 0);
export const getPartners = () => delay(mockPartners);
export const getPartnerById = (id) => delay(mockPartners.find((p) => p.id === id) || null, 250);
export const getConversations = () =>
  delay(mockConversations.map((c) => ({ ...c, partner: mockPartners.find((p) => p.id === c.partnerId) })), 250);
export const getMessages = (conversationId) => delay(mockMessages[conversationId] || [], 150);
