"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../lib/auth";
import { useLang } from "../../lib/i18n";

export default function RegisterPage() {
  const { register } = useAuth();
  const { t } = useLang();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(fullName, email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card auth-card">
        <h2>{t("register")}</h2>
        <p className="muted">{t("registerSubtitle")}</p>
        <form onSubmit={submit} style={{ display: "grid", gap: "0.75rem" }}>
          <input placeholder={t("fullName")} value={fullName}
                 onChange={(e) => setFullName(e.target.value)} required />
          <input type="email" placeholder={t("email")} value={email}
                 onChange={(e) => setEmail(e.target.value)} required />
          <input type="password" placeholder={t("password")} value={password}
                 onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          {error && <div className="error">{error}</div>}
          <button disabled={busy}>{busy ? "…" : t("register")}</button>
        </form>
        <p className="muted" style={{ marginTop: "1rem" }}>
          <Link href="/login">{t("login")}</Link>
        </p>
      </div>
    </div>
  );
}
