const DEFAULTS: Record<string, string> = {
  USER_MANAGEMENT:
    process.env.NEXT_PUBLIC_USER_MANAGEMENT_URL ||
    "https://user-management-379308139981.europe-west1.run.app",

  PERSONAL_ADMIN:
    process.env.NEXT_PUBLIC_PERSONAL_ADMIN_URL ||
    "https://personal-admin-379308139981.europe-west1.run.app",

  SYSTEM_ADMIN:
    process.env.NEXT_PUBLIC_SYSTEM_ADMIN_URL ||
    "https://system-admin-379308139981.europe-west1.run.app",

  OPPORTUNITY_SERVICE:
    process.env.NEXT_PUBLIC_OPPORTUNITY_SERVICE_URL ||
    "https://opportunity-service-379308139981.europe-west1.run.app",

  SCOUT_AGENT:
    process.env.NEXT_PUBLIC_SCOUT_AGENT_URL ||
    "https://scout-agent-379308139981.europe-west1.run.app",

  RELOCATION_AGENT:
    process.env.NEXT_PUBLIC_RELOCATION_AGENT_URL ||
    "https://relocation-agent-379308139981.europe-west1.run.app",

  APPLICATION_COACH_AGENT:
    process.env.NEXT_PUBLIC_APPLICATION_COACH_AGENT_URL ||
    "https://application-coach-agent-379308139981.europe-west1.run.app",
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
