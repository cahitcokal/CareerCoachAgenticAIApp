"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../lib/auth";
import { useLang } from "../../lib/i18n";

export default function LoginPage() {
  const { login } = useAuth();
  const { t } = useLang();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card auth-card">
        <h2>{t("login")}</h2>
        <p className="muted">{t("loginSubtitle")}</p>
        <form onSubmit={submit} style={{ display: "grid", gap: "0.75rem" }}>
          <input type="email" placeholder={t("email")} value={email}
                 onChange={(e) => setEmail(e.target.value)} required />
          <input type="password" placeholder={t("password")} value={password}
                 onChange={(e) => setPassword(e.target.value)} required />
          {error && <div className="error">{error}</div>}
          <button disabled={busy}>{busy ? "…" : t("login")}</button>
        </form>
        <p className="muted" style={{ marginTop: "1rem" }}>
          <Link href="/forgot-password">{t("forgotPassword")}</Link>
          {" · "}
          <Link href="/register">{t("register")}</Link>
        </p>
      </div>
    </div>
  );
}
