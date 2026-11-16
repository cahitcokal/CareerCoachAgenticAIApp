"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../lib/auth";
import { useLang } from "../lib/i18n";
import { Lang } from "../i18n/dictionaries";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { t, lang, setLang } = useLang();
  const pathname = usePathname();
  const router = useRouter();

  const link = (href: string, label: string) => (
    <Link href={href} style={{ color: pathname === href ? "#fff" : "#94a3b8", fontWeight: pathname === href ? 600 : 400 }}>
      {label}
    </Link>
  );

  return (
    <nav className="navbar">
      <strong>{t("appName")}</strong>
      {user && (
        <>
          {link("/", t("dashboard"))}
          {link("/admin", t("personalAdmin"))}
          {user.is_system_admin && link("/system-admin", t("systemAdmin"))}
        </>
      )}
      <span className="spacer" />
      <select value={lang} onChange={(e) => setLang(e.target.value as Lang)}
              style={{ width: "auto", padding: "0.25rem 0.5rem" }}>
        <option value="tr">TR</option>
        <option value="en">EN</option>
      </select>
      {user ? (
        <>
          <span className="muted">{user.full_name || user.email}</span>
          <button className="secondary" onClick={() => { logout(); router.push("/login"); }}>
            {t("logout")}
          </button>
        </>
      ) : (
        <Link href="/login">{t("login")}</Link>
      )}
    </nav>
  );
}
