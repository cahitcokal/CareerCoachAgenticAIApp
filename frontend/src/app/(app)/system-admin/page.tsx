"use client";

import { useCallback, useEffect, useState } from "react";
import { API, api } from "../../../lib/api";
import { useLang } from "../../../lib/i18n";

interface Language { code: string; name: string; enabled: boolean; is_default: boolean; sort_order: number; }
interface Model { id: number; model: string; priority: number; enabled: boolean; }
interface Provider {
  provider: string; display_name: string; base_url: string | null;
  priority: number; enabled: boolean; has_api_key: boolean; models: Model[];
}
interface Agent {
  agent_name: string; display_name: string; enabled: boolean;
  provider_order: string[]; max_attempts: number; max_retry_delay: number; max_turns: number;
}
interface User { id: number; email: string; full_name: string | null; is_active: boolean; is_system_admin: boolean; }
interface Audit { id: number; entity: string; entity_key: string; action: string; created_at: string | null; }

export default function SystemAdminPage() {
  const { t } = useLang();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [error, setError] = useState("");
  const [newModel, setNewModel] = useState<Record<string, string>>({});
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    try {
      const [l, p, a, u] = await Promise.all([
        api<Language[]>(API.systemAdmin, "/languages"),
        api<Provider[]>(API.systemAdmin, "/providers"),
        api<Agent[]>(API.systemAdmin, "/agents"),
        api<User[]>(API.userManagement, "/admin/users"),
      ]);
      setLanguages(l); setProviders(p); setAgents(a); setUsers(u);
      try {
        const au = await api<Audit[]>(API.systemAdmin, "/internal/audit?limit=20");
        setAudit(au);
      } catch { /* audit is internal-key protected */ }
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const patchLanguage = async (code: string, patch: Partial<Language>) => {
    try {
      const current = languages.find((l) => l.code === code)!;
      await api(API.systemAdmin, `/languages/${code}`, {
        method: "PUT",
        body: JSON.stringify({ ...current, ...patch }),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const saveProvider = async (provider: string) => {
    try {
      const body: any = {};
      const key = apiKeyInputs[provider];
      if (key) body.api_key = key;
      if (Object.keys(body).length) {
        await api(API.systemAdmin, `/providers/${provider}`, { method: "PATCH", body: JSON.stringify(body) });
        setApiKeyInputs({ ...apiKeyInputs, [provider]: "" });
      }
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const toggleProvider = async (p: Provider) => {
    try {
      await api(API.systemAdmin, `/providers/${p.provider}`, {
        method: "PATCH", body: JSON.stringify({ enabled: !p.enabled }),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const addModel = async (provider: string) => {
    const model = (newModel[provider] || "").trim();
    if (!model) return;
    try {
      await api(API.systemAdmin, `/providers/${provider}/models`, {
        method: "POST", body: JSON.stringify({ model, priority: 100, enabled: true }),
      });
      setNewModel({ ...newModel, [provider]: "" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const removeModel = async (provider: string, modelId: number) => {
    try {
      await api(API.systemAdmin, `/providers/${provider}/models/${modelId}`, { method: "DELETE" });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const saveAgent = async (agent: Agent) => {
    try {
      await api(API.systemAdmin, `/agents/${agent.agent_name}`, {
        method: "PUT",
        body: JSON.stringify({
          enabled: agent.enabled,
          provider_order: agent.provider_order,
          max_attempts: agent.max_attempts,
          max_retry_delay: agent.max_retry_delay,
          max_turns: agent.max_turns,
        }),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const toggleUserAdmin = async (u: User) => {
    try {
      await api(API.userManagement, `/admin/users/${u.id}`, {
        method: "PATCH", body: JSON.stringify({ is_system_admin: !u.is_system_admin }),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const toggleAgentEnabled = async (agent: Agent) => {
    setAgents(agents.map((a) => a.agent_name === agent.agent_name ? { ...a, enabled: !a.enabled } : a));
    await saveAgent({ ...agent, enabled: !agent.enabled });
  };

  return (
    <div>
      <h1>{t("systemAdmin")}</h1>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>{t("systemLanguages")}</h3>
        <table>
          <thead><tr><th>Code</th><th>{t("name")}</th><th>{t("status")}</th><th>{t("defaultLanguage")}</th><th></th></tr></thead>
          <tbody>
            {languages.map((l) => (
              <tr key={l.code}>
                <td>{l.code}</td>
                <td>{l.name}</td>
                <td>
                  <input type="checkbox" checked={l.enabled}
                         onChange={(e) => patchLanguage(l.code, { enabled: e.target.checked })} />
                </td>
                <td>
                  <input type="radio" name="default-lang" checked={l.is_default}
                         onChange={() => patchLanguage(l.code, { is_default: true })} />
                </td>
                <td className="muted">{l.sort_order}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>{t("providers")}</h3>
        {providers.map((p) => (
          <div key={p.provider} style={{ borderTop: "1px solid #334155", paddingTop: "0.75rem", marginTop: "0.75rem" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{p.display_name} <span className="muted">({p.provider})</span></strong>
              <label className="row" style={{ gap: "0.4rem" }}>
                <input type="checkbox" checked={p.enabled} onChange={() => toggleProvider(p)} />
                {p.enabled ? t("active") : t("inactive")}
              </label>
            </div>
            <div className="row" style={{ marginTop: "0.5rem" }}>
              <input placeholder="base_url (optional)" defaultValue={p.base_url ?? ""}
                     onBlur={(e) => e.target.value !== (p.base_url ?? "") &&
                       api(API.systemAdmin, `/providers/${p.provider}`, {
                         method: "PATCH", body: JSON.stringify({ base_url: e.target.value || null }),
                       }).then(load)} />
              <input type="password" placeholder={p.has_api_key ? "API key (set)" : "API key"}
                     value={apiKeyInputs[p.provider] ?? ""}
                     onChange={(e) => setApiKeyInputs({ ...apiKeyInputs, [p.provider]: e.target.value })} />
              <button className="secondary" onClick={() => saveProvider(p.provider)}>{t("save")}</button>
            </div>
            <div style={{ marginTop: "0.5rem" }}>
              <strong className="muted">{t("models")}</strong>
              <ul>
                {p.models.map((m) => (
                  <li key={m.id} className="row" style={{ justifyContent: "space-between" }}>
                    <span>{m.model} <span className="muted">prio {m.priority}</span></span>
                    <span className="row">
                      <input type="checkbox" checked={m.enabled}
                             onChange={async (e) => {
                               await api(API.systemAdmin, `/providers/${p.provider}/models/${m.id}`, {
                                 method: "PATCH", body: JSON.stringify({ enabled: e.target.checked }),
                               });
                               load();
                             }} />
                      <button className="danger" onClick={() => removeModel(p.provider, m.id)}>{t("delete")}</button>
                    </span>
                  </li>
                ))}
              </ul>
              <div className="row">
                <input placeholder="model name" value={newModel[p.provider] ?? ""}
                       onChange={(e) => setNewModel({ ...newModel, [p.provider]: e.target.value })} />
                <button onClick={() => addModel(p.provider)}>{t("add")}</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("agentSettings")}</h3>
        {agents.map((a) => (
          <div key={a.agent_name} style={{ borderTop: "1px solid #334155", padding: "0.75rem 0" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <strong>{a.display_name}</strong>
              <label className="row" style={{ gap: "0.4rem" }}>
                <input type="checkbox" checked={a.enabled} onChange={() => toggleAgentEnabled(a)} />
                {a.enabled ? t("active") : t("inactive")}
              </label>
            </div>
            <div className="row" style={{ marginTop: "0.5rem" }}>
              <span className="muted">providers:</span>
              {providers.map((p) => (
                <label key={p.provider} className="row" style={{ gap: "0.25rem" }}>
                  <input type="checkbox" checked={a.provider_order.includes(p.provider)}
                         onChange={(e) => {
                           const order = e.target.checked
                             ? [...a.provider_order, p.provider]
                             : a.provider_order.filter((x) => x !== p.provider);
                           const updated = { ...a, provider_order: order };
                           setAgents(agents.map((x) => x.agent_name === a.agent_name ? updated : x));
                           saveAgent(updated);
                         }} />
                  {p.provider}
                </label>
              ))}
            </div>
            <div className="row" style={{ marginTop: "0.5rem" }}>
              <label className="muted">attempts
                <input type="number" min={1} max={10} value={a.max_attempts} style={{ width: 70 }}
                       onChange={(e) => setAgents(agents.map((x) => x.agent_name === a.agent_name
                         ? { ...x, max_attempts: Number(e.target.value) } : x))}
                       onBlur={() => saveAgent(agents.find((x) => x.agent_name === a.agent_name)!)} />
              </label>
              <label className="muted">delay(s)
                <input type="number" min={0} max={600} value={a.max_retry_delay} style={{ width: 80 }}
                       onChange={(e) => setAgents(agents.map((x) => x.agent_name === a.agent_name
                         ? { ...x, max_retry_delay: Number(e.target.value) } : x))}
                       onBlur={() => saveAgent(agents.find((x) => x.agent_name === a.agent_name)!)} />
              </label>
              <label className="muted">max results
                <input type="number" min={1} max={50} value={a.max_turns} style={{ width: 70 }}
                       onChange={(e) => setAgents(agents.map((x) => x.agent_name === a.agent_name
                         ? { ...x, max_turns: Number(e.target.value) } : x))}
                       onBlur={() => saveAgent(agents.find((x) => x.agent_name === a.agent_name)!)} />
              </label>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("users")}</h3>
        <table>
          <thead><tr><th>ID</th><th>Email</th><th>{t("fullName")}</th><th>{t("status")}</th><th>{t("systemAdminRole")}</th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.email}</td>
                <td>{u.full_name}</td>
                <td>{u.is_active ? t("active") : t("inactive")}</td>
                <td>
                  <input type="checkbox" checked={u.is_system_admin} onChange={() => toggleUserAdmin(u)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {audit.length > 0 && (
        <div className="card">
          <h3>Audit</h3>
          <table>
            <thead><tr><th>Time</th><th>Entity</th><th>Key</th><th>Action</th></tr></thead>
            <tbody>
              {audit.map((a) => (
                <tr key={a.id}>
                  <td className="muted">{a.created_at?.slice(0, 19).replace("T", " ")}</td>
                  <td>{a.entity}</td>
                  <td>{a.entity_key}</td>
                  <td>{a.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
