const DEFAULTS: Record<string, string> = {
  USER_MANAGEMENT: "http://localhost:8001",
  PERSONAL_ADMIN: "http://localhost:8002",
  SYSTEM_ADMIN: "http://localhost:8003",
  OPPORTUNITY_SERVICE: "http://localhost:8004",
  SCOUT_AGENT: "http://localhost:8005",
  RELOCATION_AGENT: "http://localhost:8006",
  APPLICATION_COACH_AGENT: "http://localhost:8007",
};

const service = (name: keyof typeof DEFAULTS) =>
  process.env[`NEXT_PUBLIC_${name}_URL`] || DEFAULTS[name];

export const API = {
  userManagement: service("USER_MANAGEMENT"),
  personalAdmin: service("PERSONAL_ADMIN"),
  systemAdmin: service("SYSTEM_ADMIN"),
  opportunities: service("OPPORTUNITY_SERVICE"),
  scout: service("SCOUT_AGENT"),
  relocation: service("RELOCATION_AGENT"),
  coach: service("APPLICATION_COACH_AGENT"),
};

const TOKEN_KEY = "careercoach_token";
const LANG_KEY = "careercoach_lang";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getStoredLang(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LANG_KEY);
}

export function setStoredLang(lang: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(LANG_KEY, lang);
}

export async function api<T = any>(
  base: string,
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth = true, ...rest } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(rest.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(`${base}${path}`, { ...rest, headers });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : `HTTP ${response.status}`);
  }
  return data as T;
}
