// Anonymous per-device identity: no login, just a UUID generated once and
// kept in localStorage, sent as X-User-Id on every API request. This is a
// conscious design choice (not a half-built login) so anyone can try the
// demo without signing up, while per-device data (like quiz history) still
// persists across visits. It intentionally does NOT use the reactive
// local-store helpers used elsewhere -- this value is generated once and
// never changes, so it doesn't need to drive re-renders.

const USER_ID_KEY = "study_ai_user_id";

// In-memory fallback for when localStorage is blocked (private browsing,
// locked-down settings). Cached at module scope so every call during the
// session still returns the SAME id -- otherwise each API request would
// look like a different anonymous user.
let inMemoryFallbackId: string | null = null;

export function getUserId(): string {
  if (typeof window === "undefined") return "";

  try {
    let userId = window.localStorage.getItem(USER_ID_KEY);
    if (!userId) {
      userId = crypto.randomUUID();
      window.localStorage.setItem(USER_ID_KEY, userId);
    }
    return userId;
  } catch {
    if (!inMemoryFallbackId) {
      inMemoryFallbackId = crypto.randomUUID();
    }
    return inMemoryFallbackId;
  }
}
