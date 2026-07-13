/*
 * Local persistence layer (no backend).
 * - Users are stored in `ss_users` keyed by email.
 * - The active session email is stored in `ss_session`.
 * - Per-user data (saved profile + last analysis) lives under `ss_user_data_<email>`.
 *
 * NOTE: This is intentionally simple client-side storage for a demo — passwords
 * are NOT securely hashed. Do not use this pattern for real authentication.
 */

const USERS_KEY = 'ss_users';
const SESSION_KEY = 'ss_session';
const userDataKey = (email) => `ss_user_data_${email.toLowerCase()}`;

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage full / unavailable — ignore for demo */
  }
}

// ── Users ────────────────────────────────────────────
export function getUsers() {
  return readJSON(USERS_KEY, {});
}

export function findUser(email) {
  if (!email) return null;
  return getUsers()[email.toLowerCase()] || null;
}

export function createUser({ name, email, password }) {
  const users = getUsers();
  const key = email.toLowerCase();
  if (users[key]) throw new Error('An account with this email already exists.');
  users[key] = { name: name.trim(), email: key, password };
  writeJSON(USERS_KEY, users);
  return { name: users[key].name, email: key };
}

export function verifyUser(email, password) {
  const user = findUser(email);
  if (!user || user.password !== password) return null;
  return { name: user.name, email: user.email };
}

// ── Session ──────────────────────────────────────────
export function getSession() {
  const email = readJSON(SESSION_KEY, null);
  if (!email) return null;
  const user = findUser(email);
  return user ? { name: user.name, email: user.email } : null;
}

export function setSession(email) {
  writeJSON(SESSION_KEY, email.toLowerCase());
}

export function clearSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}

// ── Per-user data (profile + last analysis) ──────────
export function getUserData(email) {
  if (!email) return { profile: null, lastResult: null, savedAt: null };
  return readJSON(userDataKey(email), { profile: null, lastResult: null, savedAt: null });
}

export function saveUserProfile(email, profile) {
  if (!email) return;
  const data = getUserData(email);
  data.profile = profile;
  data.savedAt = new Date().toISOString();
  writeJSON(userDataKey(email), data);
}

export function saveUserResult(email, result) {
  if (!email) return;
  const data = getUserData(email);
  data.lastResult = result;
  data.savedAt = new Date().toISOString();
  writeJSON(userDataKey(email), data);
}
