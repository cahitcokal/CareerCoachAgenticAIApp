"use client";

import { useState } from "react";
import Link from "next/link";
import { API, api } from "../../lib/api";
import { useLang } from "../../lib/i18n";

export default function ForgotPasswordPage() {
  const { t } = useLang();
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const requestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await api(API.userManagement, "/auth/forgot-password", {
        method: "POST", body: JSON.stringify({ email }), auth: false,
      });
      setMessage("If the account exists, a reset token has been generated (check server logs in dev).");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const doReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(API.userManagement, "/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: newPassword }),
        auth: false,
      });
      setMessage("Password updated. You can now log in.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card auth-card">
        <h2>{t("forgotPassword")}</h2>
        <p className="muted">{t("noToken")}</p>
        <form onSubmit={requestReset} style={{ display: "grid", gap: "0.75rem" }}>
          <input type="email" placeholder={t("email")} value={email}
                 onChange={(e) => setEmail(e.target.value)} required />
          <button disabled={busy}>{t("forgotPassword")}</button>
        </form>
        <hr style={{ borderColor: "#334155", margin: "1rem 0" }} />
        <h3>{t("resetPassword")}</h3>
        <form onSubmit={doReset} style={{ display: "grid", gap: "0.75rem" }}>
          <input placeholder="Reset token" value={token}
                 onChange={(e) => setToken(e.target.value)} required />
          <input type="password" placeholder={t("password")} value={newPassword}
                 onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
          <button disabled={busy} className="secondary">{t("resetPassword")}</button>
        </form>
        {message && <div className="success" style={{ marginTop: "0.75rem" }}>{message}</div>}
        {error && <div className="error" style={{ marginTop: "0.75rem" }}>{error}</div>}
        <p className="muted" style={{ marginTop: "1rem" }}><Link href="/login">{t("login")}</Link></p>
      </div>
    </div>
  );
}
