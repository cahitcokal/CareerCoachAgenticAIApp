"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { API, api } from "../../lib/api";
import { useLang } from "../../lib/i18n";

interface Profile {
  id: number; name: string; is_active: boolean; deleted_at: string | null;
}
interface Opportunity {
  id: number; title: string; company: string | null; location: string | null;
  url: string | null; status: string; match_score: number | null;
  match_summary: string | null;
  profile_id: number | null; source: string | null; relocation_report: string | null;
  steps?: { id: number; title: string; completed: boolean }[];
  created_at: string | null;
}
interface AgentRun { id: number; status: string; started_at: string | null; }

const STATUSES = ["all", "new", "active", "archived", "applied", "rejected", "interview"];

export default function DashboardPage() {
  const { t } = useLang();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [runs, setRuns] = useState<Record<string, AgentRun[]>>({});
  const [statusFilter, setStatusFilter] = useState("all");
  const [profileFilter, setProfileFilter] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [companyFilter, setCompanyFilter] = useState("");
  const [minScore, setMinScore] = useState("");
  const [query, setQuery] = useState("");
  const [locations, setLocations] = useState("");
  const [profileId, setProfileId] = useState<number | "">("");
  const [jobUrl, setJobUrl] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (profileFilter) params.set("profile_id", profileFilter);
      if (countryFilter) params.set("country", countryFilter);
      if (companyFilter) params.set("company", companyFilter);
      if (minScore) params.set("min_score", minScore);
      const [opps, profs] = await Promise.all([
        api<Opportunity[]>(API.opportunities, `/opportunities?${params}`),
        api<Profile[]>(API.personalAdmin, "/profiles"),
      ]);
      setOpportunities(opps);
      setProfiles(profs.filter((p) => !p.deleted_at));
      const scoutRuns = await api<AgentRun[]>(API.scout, "/runs");
      const relocRuns = await api<AgentRun[]>(API.relocation, "/runs");
      const coachRuns = await api<AgentRun[]>(API.coach, "/runs");
      setRuns({ scout: scoutRuns, relocation: relocRuns, coach: coachRuns });
    } catch (err: any) {
      setError(err.message);
    }
  }, [statusFilter, profileFilter, countryFilter, companyFilter, minScore]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [load]);

  const scoutBusy = (runs.scout || []).length > 0;
  const anyAgentBusy = Object.values(runs).some((r) => (r || []).length > 0);

  const startSearch = async () => {
    setError(""); setNotice("");
    try {
      await api(API.scout, "/search", {
        method: "POST",
        body: JSON.stringify({
          profile_id: profileId === "" ? null : profileId,
          query: query || null,
          locations: locations ? locations.split(",").map((s) => s.trim()).filter(Boolean) : [],
          max_results: 10,
        }),
      });
      setNotice("Search started");
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const analyzeUrl = async () => {
    setError(""); setNotice("");
    try {
      await api(API.scout, "/analyze-url", {
        method: "POST",
        body: JSON.stringify({ url: jobUrl, profile_id: profileId === "" ? null : profileId }),
      });
      setNotice("URL analysis started");
      setJobUrl("");
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const trigger = async (kind: "relocation" | "coach", opportunityId: number) => {
    setError("");
    try {
      const base = kind === "relocation" ? API.relocation : API.coach;
      const path = kind === "relocation" ? "/relocation-report" : "/application-steps";
      await api(base, path, { method: "POST", body: JSON.stringify({ opportunity_id: opportunityId }) });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const profileName = useMemo(() => {
    const map = new Map(profiles.map((p) => [p.id, p.name]));
    return (id: number | null) => (id ? map.get(id) ?? `#${id}` : "—");
  }, [profiles]);

  const setOppStatus = async (id: number, status: string) => {
    try {
      await api(API.opportunities, `/opportunities/${id}`, {
        method: "PATCH", body: JSON.stringify({ status }),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h1>{t("dashboard")}</h1>
      {error && <div className="error">{error}</div>}
      {notice && <div className="success">{notice}</div>}

      <div className="card">
        <h3>{t("searchJobs")}</h3>
        <div className="row">
          <select value={profileId} onChange={(e) => setProfileId(e.target.value ? Number(e.target.value) : "")} style={{ width: "auto" }}>
            <option value="">{t("filterProfile")}: —</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.is_active ? t("active") : t("inactive")})</option>
            ))}
          </select>
          <input placeholder="Query" value={query} onChange={(e) => setQuery(e.target.value)} style={{ maxWidth: 220 }} />
          <input placeholder="Locations (comma separated)" value={locations} onChange={(e) => setLocations(e.target.value)} style={{ maxWidth: 240 }} />
          <button onClick={startSearch} disabled={scoutBusy}>
            {scoutBusy ? t("running") : t("startSearch")}
          </button>
        </div>
        <div className="row" style={{ marginTop: "0.5rem" }}>
          <input placeholder="Job posting URL" value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} style={{ maxWidth: 380 }} />
          <button className="secondary" onClick={analyzeUrl} disabled={!jobUrl || scoutBusy}>
            {t("analyzeUrl")}
          </button>
        </div>
        {scoutBusy && <p className="muted">{t("running")}</p>}
      </div>

      <div className="card">
        <div className="row">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ width: "auto" }}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === "all" ? t("all") : s}</option>)}
          </select>
          <select value={profileFilter} onChange={(e) => setProfileFilter(e.target.value)} style={{ width: "auto" }}>
            <option value="">{t("filterProfile")}: {t("all")}</option>
            {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input placeholder={t("filterCountry")} value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)} style={{ maxWidth: 160 }} />
          <input placeholder={t("filterCompany")} value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} style={{ maxWidth: 160 }} />
          <input placeholder={t("minScore")} value={minScore} onChange={(e) => setMinScore(e.target.value)} style={{ maxWidth: 100 }} />
        </div>
      </div>

      <div className="grid">
        {opportunities.map((opp) => {
          const relocBusy = (runs.relocation || []).some((r) => r.status === "running");
          const coachBusy = (runs.coach || []).some((r) => r.status === "running");
          return (
            <div className="card" key={opp.id}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <h3 style={{ margin: 0 }}>{opp.title}</h3>
                <span className={`badge ${opp.status === "active" ? "active" : ""}`}>{opp.status}</span>
              </div>
              <p className="muted">
                {opp.company || "—"} · {opp.location || "—"} · {t("matchScore")}: {opp.match_score ?? "—"} ·{" "}
                {t("filterProfile")}: {profileName(opp.profile_id)} · {opp.source}
              </p>
              {opp.url && <p><a href={opp.url} target="_blank" rel="noreferrer">{opp.url}</a></p>}
              {opp.match_summary && <p className="muted">{opp.match_summary}</p>}
              {opp.relocation_report && (
                <details>
                  <summary>{t("relocationReport")}</summary>
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8rem" }}>{opp.relocation_report}</pre>
                </details>
              )}
              {opp.steps && opp.steps.length > 0 && (
                <details>
                  <summary>{t("steps")} ({opp.steps.length})</summary>
                  <ul>
                    {opp.steps.map((s) => (
                      <li key={s.id}>
                        <label>
                          <input type="checkbox" checked={s.completed}
                                 onChange={async (e) => {
                                   await api(API.opportunities, `/opportunities/${opp.id}/steps/${s.id}`, {
                                     method: "PATCH", body: JSON.stringify({ completed: e.target.checked }),
                                   });
                                   load();
                                 }} />{" "}
                          {s.title}
                        </label>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              <div className="row" style={{ marginTop: "0.5rem" }}>
                <button className="secondary" disabled={relocBusy || anyAgentBusy}
                        onClick={() => trigger("relocation", opp.id)}>
                  {t("generateReport")}
                </button>
                <button className="secondary" disabled={coachBusy || anyAgentBusy}
                        onClick={() => trigger("coach", opp.id)}>
                  {t("generateSteps")}
                </button>
                <select value={opp.status} onChange={(e) => setOppStatus(opp.id, e.target.value)}
                        style={{ width: "auto" }}>
                  {STATUSES.filter((s) => s !== "all").map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          );
        })}
        {opportunities.length === 0 && <p className="muted">{t("opportunities")}: —</p>}
      </div>
    </div>
  );
}
