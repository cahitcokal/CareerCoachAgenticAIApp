"use client";

import { useCallback, useEffect, useState } from "react";
import { API, api } from "../../../lib/api";
import { useLang } from "../../../lib/i18n";

interface Profile {
  id: number; name: string; title: string | null; is_active: boolean;
  deleted_at: string | null; demographics: string | null; education: string | null;
  experience: string | null; certifications: string | null; preferences: string | null;
}
interface NamedItem { id: number; name: string; notes?: string | null; url?: string | null; }

const EMPTY_PROFILE = {
  name: "", title: "", demographics: "", education: "", experience: "",
  certifications: "", preferences: "",
};

export default function PersonalAdminPage() {
  const { t, lang, setLang } = useLang();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [countries, setCountries] = useState<NamedItem[]>([]);
  const [roles, setRoles] = useState<NamedItem[]>([]);
  const [sites, setSites] = useState<NamedItem[]>([]);
  const [userLang, setUserLang] = useState<string | null>(null);
  const [editing, setEditing] = useState<Profile | "new" | null>(null);
  const [form, setForm] = useState(EMPTY_PROFILE);
  const [newItem, setNewItem] = useState<Record<string, string>>({ countries: "", roles: "", sites: "" });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [p, c, r, s, pref] = await Promise.all([
        api<Profile[]>(API.personalAdmin, "/profiles?include_deleted=true"),
        api<NamedItem[]>(API.personalAdmin, "/target-countries"),
        api<NamedItem[]>(API.personalAdmin, "/target-roles"),
        api<NamedItem[]>(API.personalAdmin, "/target-career-sites"),
        api<{ language: string | null }>(API.personalAdmin, "/preferences"),
      ]);
      setProfiles(p); setCountries(c); setRoles(r); setSites(s);
      setUserLang(pref.language);
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const saveProfile = async () => {
    setError("");
    try {
      const payload = { ...form, is_active: true };
      if (editing === "new") {
        await api(API.personalAdmin, "/profiles", { method: "POST", body: JSON.stringify(payload) });
      } else if (editing) {
        await api(API.personalAdmin, `/profiles/${editing.id}`, { method: "PATCH", body: JSON.stringify(payload) });
      }
      setEditing(null);
      setForm(EMPTY_PROFILE);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const removeProfile = async (id: number) => {
    if (!confirm(t("confirmDelete"))) return;
    try {
      await api(API.personalAdmin, `/profiles/${id}`, { method: "DELETE" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const restoreProfile = async (id: number) => {
    try {
      await api(API.personalAdmin, `/profiles/${id}/restore`, { method: "POST" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const addItem = async (kind: "countries" | "roles" | "sites") => {
    const name = newItem[kind].trim();
    if (!name) return;
    const path = kind === "countries" ? "/target-countries" : kind === "roles" ? "/target-roles" : "/target-career-sites";
    try {
      await api(API.personalAdmin, path, { method: "POST", body: JSON.stringify({ name }) });
      setNewItem({ ...newItem, [kind]: "" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const removeItem = async (kind: "countries" | "roles" | "sites", id: number) => {
    const path = kind === "countries" ? "/target-countries" : kind === "roles" ? "/target-roles" : "/target-career-sites";
    try {
      await api(API.personalAdmin, `${path}/${id}`, { method: "DELETE" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const saveLanguage = async (value: string) => {
    try {
      await api(API.personalAdmin, "/preferences", { method: "PUT", body: JSON.stringify({ language: value || null }) });
      setUserLang(value || null);
      if (value) setLang(value as "tr" | "en");
    } catch (err: any) {
      setError(err.message);
    }
  };

  const renderList = (kind: "countries" | "roles" | "sites", items: NamedItem[], label: string) => (
    <div className="card">
      <h3>{label}</h3>
      <ul>
        {items.map((i) => (
          <li key={i.id} className="row" style={{ justifyContent: "space-between" }}>
            <span>{i.name}{i.url ? ` — ${i.url}` : ""}</span>
            <button className="danger" onClick={() => removeItem(kind, i.id)}>{t("delete")}</button>
          </li>
        ))}
      </ul>
      <div className="row">
        <input placeholder={t("name")} value={newItem[kind]}
               onChange={(e) => setNewItem({ ...newItem, [kind]: e.target.value })} />
        <button onClick={() => addItem(kind)}>{t("add")}</button>
      </div>
    </div>
  );

  return (
    <div>
      <h1>{t("personalAdmin")}</h1>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>{t("language")}</h3>
        <div className="row">
          <select value={userLang ?? ""} onChange={(e) => saveLanguage(e.target.value)} style={{ width: "auto" }}>
            <option value="">{t("defaultLanguage")} (system)</option>
            <option value="tr">Türkçe</option>
            <option value="en">English</option>
          </select>
          <span className="muted">UI: {lang}</span>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>{t("profiles")}</h3>
          <button onClick={() => { setEditing("new"); setForm(EMPTY_PROFILE); }}>{t("newProfile")}</button>
        </div>
        <table style={{ marginTop: "0.5rem" }}>
          <thead>
            <tr><th>{t("name")}</th><th>{t("status")}</th><th></th></tr>
          </thead>
          <tbody>
            {profiles.map((p) => (
              <tr key={p.id}>
                <td>{p.name}{p.title ? ` — ${p.title}` : ""}</td>
                <td>
                  <span className={`badge ${p.deleted_at ? "inactive" : p.is_active ? "active" : "inactive"}`}>
                    {p.deleted_at ? t("deleted") : p.is_active ? t("active") : t("inactive")}
                  </span>
                </td>
                <td className="row">
                  <button className="secondary" onClick={() => {
                    setEditing(p);
                    setForm({
                      name: p.name, title: p.title ?? "", demographics: p.demographics ?? "",
                      education: p.education ?? "", experience: p.experience ?? "",
                      certifications: p.certifications ?? "", preferences: p.preferences ?? "",
                    });
                  }}>{t("edit")}</button>
                  {p.deleted_at ? (
                    <button className="secondary" onClick={() => restoreProfile(p.id)}>{t("restore")}</button>
                  ) : (
                    <button className="danger" onClick={() => removeProfile(p.id)}>{t("delete")}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="card">
          <h3>{editing === "new" ? t("newProfile") : t("edit")}</h3>
          <div style={{ display: "grid", gap: "0.5rem" }}>
            <input placeholder={t("name")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <textarea placeholder="Demographics" value={form.demographics} onChange={(e) => setForm({ ...form, demographics: e.target.value })} rows={2} />
            <textarea placeholder="Education" value={form.education} onChange={(e) => setForm({ ...form, education: e.target.value })} rows={2} />
            <textarea placeholder="Experience" value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value })} rows={3} />
            <textarea placeholder="Certifications" value={form.certifications} onChange={(e) => setForm({ ...form, certifications: e.target.value })} rows={2} />
            <textarea placeholder="Preferences" value={form.preferences} onChange={(e) => setForm({ ...form, preferences: e.target.value })} rows={2} />
          </div>
          <div className="row" style={{ marginTop: "0.75rem" }}>
            <button onClick={saveProfile}>{t("save")}</button>
            <button className="secondary" onClick={() => setEditing(null)}>{t("cancel")}</button>
          </div>
        </div>
      )}

      <div className="grid">
        {renderList("countries", countries, t("targetCountries"))}
        {renderList("roles", roles, t("targetRoles"))}
        {renderList("sites", sites, t("targetSites"))}
      </div>
    </div>
  );
}
