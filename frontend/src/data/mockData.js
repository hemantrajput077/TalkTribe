// Local mock data. Replace via src/services/api.js when the backend is ready.

export const INTERESTS = [
  "Music", "Travel", "Technology", "Sports", "Movies", "Books", "Cooking",
  "Gaming", "Art", "Science", "Business", "Fashion", "Nature", "Fitness",
];

export const PROFICIENCY_LEVELS = ["Beginner", "Elementary", "Intermediate", "Upper Intermediate", "Advanced", "Fluent"];

export const LANGUAGES = ["English", "Hindi", "Spanish", "French", "German", "Japanese", "Portuguese", "Arabic", "Bengali", "Tamil", "Korean", "Mandarin"];

export const PROFESSIONS = ["Software Developer", "Designer", "Student", "Teacher", "Doctor", "Marketing", "Entrepreneur", "Engineer"];

export const mockCurrentUser = {
  id: "me",
  name: "Yogesh Goswami",
  email: "yogesh@talktribe.app",
  profession: "Software Developer",
  bio: "Developer from Jaipur. I want to speak English confidently in meetings and make friends around the world.",
  nativeLanguage: "Hindi",
  englishLevel: "Intermediate",
  learningLanguage: "English",
  interests: ["Technology", "Music", "Travel", "Gaming"],
  profileCompletion: 80,
};

export const mockPartners = [
  { id: "1", name: "Rahul Sharma", profession: "Software Developer", englishLevel: "Intermediate", nativeLanguage: "Hindi", learningLanguage: "English", interests: ["Technology", "Gaming", "Music", "Movies"], bio: "Building web apps by day, gaming by night. Let's practice tech talk and casual English together.", location: "Bengaluru, India", online: true },
  { id: "2", name: "Priya Nair", profession: "Designer", englishLevel: "Advanced", nativeLanguage: "Malayalam", learningLanguage: "English", interests: ["Art", "Travel", "Music", "Fashion"], bio: "Product designer who loves sketching and backpacking. Happy to help with pronunciation.", location: "Kochi, India", online: true },
  { id: "3", name: "Aman Verma", profession: "Student", englishLevel: "Beginner", nativeLanguage: "Hindi", learningLanguage: "English", interests: ["Sports", "Gaming", "Technology"], bio: "Engineering student preparing for interviews. Looking for patient partners to chat daily.", location: "Delhi, India", online: false },
  { id: "4", name: "Lucía Fernández", profession: "Teacher", englishLevel: "Upper Intermediate", nativeLanguage: "Spanish", learningLanguage: "English", interests: ["Books", "Travel", "Cooking", "Nature"], bio: "Primary school teacher from Valencia. I can help you with Spanish in return!", location: "Valencia, Spain", online: true },
  { id: "5", name: "Kenji Tanaka", profession: "Engineer", englishLevel: "Intermediate", nativeLanguage: "Japanese", learningLanguage: "English", interests: ["Technology", "Science", "Music", "Fitness"], bio: "Robotics engineer and amateur guitarist. Let's talk about gadgets and music.", location: "Osaka, Japan", online: false },
  { id: "6", name: "Fatima Khan", profession: "Doctor", englishLevel: "Advanced", nativeLanguage: "Urdu", learningLanguage: "English", interests: ["Science", "Books", "Fitness", "Nature"], bio: "Resident doctor who enjoys long reads and morning runs. Conversations over coffee, anyone?", location: "Lahore, Pakistan", online: true },
  { id: "7", name: "Marco Rossi", profession: "Entrepreneur", englishLevel: "Upper Intermediate", nativeLanguage: "Italian", learningLanguage: "English", interests: ["Business", "Cooking", "Travel", "Movies"], bio: "Running a small coffee brand. I want to pitch confidently to international clients.", location: "Milan, Italy", online: false },
  { id: "8", name: "Ananya Iyer", profession: "Marketing", englishLevel: "Fluent", nativeLanguage: "Tamil", learningLanguage: "English", interests: ["Music", "Movies", "Fashion", "Travel"], bio: "Brand marketer and playlist curator. I love helping people find their voice.", location: "Chennai, India", online: true },
];

export const mockConversations = [
  { id: "c1", partnerId: "1", lastMessage: "Sure, let's do a call at 7?", time: "10:24", unread: 2 },
  { id: "c2", partnerId: "2", lastMessage: "Your pronunciation is getting better!", time: "Yesterday", unread: 0 },
  { id: "c3", partnerId: "3", lastMessage: "Thanks for the interview tips", time: "Mon", unread: 0 },
  { id: "c4", partnerId: "4", lastMessage: "¡Hola! Ready for practice?", time: "Sun", unread: 1 },
];

export const mockMessages = {
  c1: [
    { id: "m1", from: "them", text: "Hi Yogesh! How are you?", time: "10:02" },
    { id: "m2", from: "me", text: "I'm good. How about you?", time: "10:05" },
    { id: "m3", from: "them", text: "Doing great. Want to practice talking about our projects today?", time: "10:12" },
    { id: "m4", from: "me", text: "Yes! I have a demo next week, so I'd love to rehearse.", time: "10:20" },
    { id: "m5", from: "them", text: "Sure, let's do a call at 7?", time: "10:24" },
  ],
  c2: [
    { id: "m1", from: "me", text: "Can you check how I say 'thoroughly'?", time: "18:40" },
    { id: "m2", from: "them", text: "Your pronunciation is getting better!", time: "18:52" },
  ],
  c3: [{ id: "m1", from: "them", text: "Thanks for the interview tips", time: "09:15" }],
  c4: [],
};
