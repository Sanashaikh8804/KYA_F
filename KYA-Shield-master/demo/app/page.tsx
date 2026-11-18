"use client";

import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Ban,
  Bell,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
  Clock3,
  CreditCard,
  FileCheck2,
  FileWarning,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  UserRound,
  Users,
  X,
  XCircle
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

type EventItem = {
  session_id: string;
  ts_ms: number;
  event_type: string;
  page?: string;
  api_endpoint?: string;
  target?: string;
  amount?: number;
  payee?: string;
  new_payee?: boolean;
  merchant_category?: string;
  content_origin?: string;
  device?: { webdriver?: boolean; user_agent?: string };
};
type Decision = {
  session_id?: string;
  agent_class: "human" | "scripted_bot" | "llm_agent";
  agent_class_probs?: Record<string, number>;
  agent_trust_score: number;
  p_fraud: number;
  action: "allow" | "step_up" | "hold" | "block";
  expected_cost_by_action?: Record<string, number>;
  reason_codes: { code: string; text: string; weight?: number }[];
  latency_ms: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const scenarios = [
  { key: "human", label: "Human customer", detail: "Natural browser interaction", icon: UserRound },
  { key: "legitimate-agent", label: "Authorised agent", detail: "Mandate stays in scope", icon: ShieldCheck },
  { key: "prompt-injected-agent", label: "Prompt-injected agent", detail: "New payee after external content", icon: AlertTriangle }
];
const navItems = [
  ["Overview", LayoutDashboard],
  ["Live monitoring", Activity],
  ["Agent registry", Users],
  ["Trust intelligence", ShieldCheck],
  ["Mandates", FileCheck2],
  ["Investigations", Search],
  ["Audit logs", Clock3]
] as const;
const emptyDecision: Decision = { agent_class: "human", agent_trust_score: 0, p_fraud: 0, action: "allow", reason_codes: [], latency_ms: 0 };

function eventText(event: EventItem) {
  if (event.event_type === "transaction") return `${event.payee} · INR ${event.amount?.toLocaleString("en-IN")}`;
  if (event.event_type === "api_call") return event.api_endpoint ?? "API request";
  if (event.event_type === "page_view") return `${event.page ?? "Page viewed"}${event.content_origin === "external" ? " · external content" : ""}`;
  return event.target ?? "Interaction";
}
function actionIcon(action: Decision["action"]) {
  return action === "allow" ? <CheckCircle2 size={16} /> : action === "block" ? <Ban size={16} /> : <AlertTriangle size={16} />;
}

export default function Dashboard() {
  const [scenario, setScenario] = useState("prompt-injected-agent");
  const [events, setEvents] = useState<EventItem[]>([]);
  const [decision, setDecision] = useState<Decision>(emptyDecision);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [eventFilter, setEventFilter] = useState("all");
  const [eventSearch, setEventSearch] = useState("");
  const [paused, setPaused] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [liveSessionId, setLiveSessionId] = useState("");
  const [liveMode, setLiveMode] = useState(false);

  const loadScenario = useCallback(async (scenarioKey: string) => {
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API_URL}/demo/scenarios/${scenarioKey}`);
      if (!response.ok) throw new Error(`Scenario request failed (${response.status})`);
      const nextEvents = (await response.json()) as EventItem[];
      setEvents(nextEvents);
      const scoreResponse = await fetch(`${API_URL}/score`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(nextEvents) });
      if (!scoreResponse.ok) throw new Error(`Scoring request failed (${scoreResponse.status})`);
      setDecision((await scoreResponse.json()) as Decision); setLastUpdated(new Date());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to connect to the scoring API");
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { void loadScenario(scenario); }, [loadScenario, scenario]);
  useEffect(() => {
    if (!liveMode || paused || !liveSessionId.trim()) return;
    let active = true;
    const refresh = async () => {
      try {
        const response = await fetch(`${API_URL}/sessions/${encodeURIComponent(liveSessionId.trim())}/decision`);
        if (!response.ok) throw new Error(`Live session request failed (${response.status})`);
        const payload = await response.json() as { events: EventItem[]; decision: Decision };
        if (!active) return;
        setEvents(payload.events);
        setDecision(payload.decision);
        setLastUpdated(new Date());
        setError("");
      } catch (requestError) {
        if (active && requestError instanceof Error && !requestError.message.includes("(404)")) {
          setError(requestError.message);
        }
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => { active = false; window.clearInterval(timer); };
  }, [liveMode, liveSessionId, paused]);

  const filteredEvents = useMemo(() => events.filter((event) => {
    const matchesType = eventFilter === "all" || event.event_type === eventFilter;
    return matchesType && `${event.event_type} ${eventText(event)}`.toLowerCase().includes(eventSearch.toLowerCase());
  }), [events, eventFilter, eventSearch]);
  const transaction = useMemo(() => [...events].reverse().find((event) => event.event_type === "transaction"), [events]);
  const trustLevel = decision.agent_trust_score >= 70 ? "good" : decision.agent_trust_score >= 40 ? "warn" : "bad";
  const trustLabel = decision.agent_trust_score >= 70 ? "Trusted" : decision.agent_trust_score >= 40 ? "Review required" : "High risk";
  const trustSignals = [
    ["Agent identity", decision.agent_class === "human" ? 92 : 72],
    ["Mandate compliance", decision.reason_codes.some((reason) => ["R100", "R101", "R102", "R103", "R109"].includes(reason.code)) ? 18 : 96],
    ["Behavioural consistency", Math.max(12, Math.round((1 - decision.p_fraud) * 100))],
    ["Transaction safety", Math.max(10, Math.round((1 - decision.p_fraud) * 100))]
  ];

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="sidebar-brand"><div className="brand-mark"><ShieldCheck size={18} /></div><div><b>KYA-Shield</b><span>Trust infrastructure</span></div><button className="mobile-close" onClick={() => setMobileNav(false)}><X size={17} /></button></div>
        <div className="workspace-switch"><span className="workspace-avatar">F</span><span><b>Fintrust Bank</b><small>Risk operations</small></span><ChevronDown size={14} /></div>
        <nav>{navItems.map(([label, Icon], index) => <button className={index === 0 ? "active" : ""} key={label} onClick={() => setMobileNav(false)}><Icon size={16} /><span>{label}</span>{label === "Live monitoring" && <i className="nav-live" />}</button>)}</nav>
        <div className="sidebar-bottom"><button><Settings size={16} /><span>Settings</span></button><div className="operator"><span className="operator-avatar">AK</span><span><b>Alex Kim</b><small>Security analyst</small></span><ChevronDown size={13} /></div></div>
      </aside>

      <section className="main-area">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMobileNav(true)}><Menu size={19} /></button><div className="breadcrumbs"><span>Risk operations</span><b>/</b><strong>Decision center</strong></div><div className="top-actions"><span className="environment"><i /> Sandbox environment</span><span className="live-status"><i /> Live scoring</span><Bell size={17} /><span className="header-avatar">AK</span></div></header>
        <div className="page-content">
          <div className="page-heading"><div><p className="eyebrow">Session review · Agent Trust</p><h1>Agent decision center</h1><p className="lede">A precise view of what happened, what changed, and why the bank should act.</p></div><div className="heading-meta"><span><Clock3 size={14} /> {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Waiting for API"}</span><button className="outline-button" onClick={() => void loadScenario(scenario)}>Refresh decision <ArrowUpRight size={14} /></button></div></div>

          <section className="scenario-section"><div className="section-top"><div><p className="eyebrow">Evaluation scenarios</p><h2>Choose a session to inspect</h2></div><span className="data-note">Synthetic demo data · local only</span></div><div className="scenario-grid">{scenarios.map(({ key, label, detail, icon: Icon }) => <button className={`scenario-card ${scenario === key && !liveMode ? "selected" : ""}`} key={key} onClick={() => { setLiveMode(false); setScenario(key); }}><span className="scenario-icon"><Icon size={17} /></span><span className="scenario-copy"><b>{label}</b><small>{detail}</small></span>{scenario === key && !liveMode && <CheckCircle2 className="selected-icon" size={16} />}</button>)}</div><div className="live-session-bar"><div><p className="eyebrow">Live session monitor</p><span>Poll an active mock-bank or Ollama session every 2 seconds.</span></div><input value={liveSessionId} onChange={(event) => setLiveSessionId(event.target.value)} placeholder="Session ID, e.g. ollama-d2fedcbb1484" /><button className="outline-button" onClick={() => { setLiveMode(Boolean(liveSessionId.trim())); setPaused(false); }}>{liveMode ? "Monitoring" : "Monitor session"}</button></div></section>

          {error && <div className="error-banner"><XCircle size={17} /> {error}. Start FastAPI on port 8000, then refresh.</div>}

          <section className="metric-grid">
            <article className="metric-card trust-card"><div className="card-heading"><span>Agent trust score</span><ShieldCheck size={16} /></div><div className="trust-body"><div className={`gauge ${trustLevel}`} style={{ "--score": `${decision.agent_trust_score * 3.6}deg` } as React.CSSProperties}><div><strong>{decision.agent_trust_score}</strong><small>/ 100</small></div></div><div className="trust-copy"><b>{trustLabel}</b><span>{decision.agent_class.replace("_", " ")} · confidence {Math.round((decision.agent_class_probs?.[decision.agent_class] ?? 0) * 100)}%</span><div className="mini-bar"><i className={trustLevel} style={{ width: `${decision.agent_trust_score}%` }} /></div></div></div></article>
            <article className="metric-card"><div className="card-heading"><span>Recommended action</span>{actionIcon(decision.action)}</div><div className={`action-value ${decision.action}`}>{decision.action.replace("_", "-")}</div><p className="metric-note">Lowest expected cost for this session</p></article>
            <article className="metric-card"><div className="card-heading"><span>Fraud probability</span><FileWarning size={16} /></div><div className="number-value">{Math.round(decision.p_fraud * 100)}<small>%</small></div><p className="metric-note">{transaction ? `Exposure · INR ${transaction.amount?.toLocaleString("en-IN")}` : "No transaction detected"}</p></article>
            <article className="metric-card"><div className="card-heading"><span>Scoring latency</span><Clock3 size={16} /></div><div className="number-value">{decision.latency_ms.toFixed(2)}<small> ms</small></div><p className="metric-note">p95 budget · under 100 ms</p></article>
          </section>

          <section className="content-grid">
            <article className="panel event-panel"><div className="panel-header"><div><p className="eyebrow">Observable activity</p><h2>Session event timeline</h2></div><div className="panel-tools"><span className="count-pill">{filteredEvents.length} / {events.length}</span><button className={`pause-button ${paused ? "paused" : ""}`} onClick={() => setPaused(!paused)}>{paused ? "Resume" : "Pause"}</button></div></div><div className="filter-row"><div className="search-field"><Search size={14} /><input value={eventSearch} onChange={(event) => setEventSearch(event.target.value)} placeholder="Search events" /></div><select value={eventFilter} onChange={(event) => setEventFilter(event.target.value)}><option value="all">All events</option><option value="transaction">Transactions</option><option value="api_call">API calls</option><option value="page_view">Page views</option><option value="click">Clicks</option></select></div><div className="event-list">{filteredEvents.map((event, index) => <div className="event-row" key={`${event.ts_ms}-${index}`}><div className={`event-icon ${event.event_type}`}><Activity size={14} /></div><div className="event-main"><b>{event.event_type.replace("_", " ")}</b><span>{eventText(event)}</span></div>{event.event_type === "transaction" && <span className={`severity ${event.new_payee ? "danger" : "safe"}`}>{event.new_payee ? "New payee" : "In scope"}</span>}<time>{new Date(event.ts_ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time></div>)}</div></article>
            <div className="right-stack"><article className="panel"><div className="panel-header"><div><p className="eyebrow">Decision explanation</p><h2>Reason codes</h2></div><span className="coverage"><CheckCircle2 size={14} /> 100% coverage</span></div><div className="reason-list">{decision.reason_codes.map((reason) => <div className="reason-row" key={reason.code}><span className={`reason-code ${reason.code.startsWith("R1") ? "hard" : "signal"}`}>{reason.code}</span><span className="reason-text"><b>{reason.text}</b><small>{reason.code.startsWith("R1") ? "Security control" : "Behavioural signal"} · contribution {Math.round((reason.weight ?? 0) * 100)}%</small></span></div>)}</div></article><article className="panel"><div className="panel-header"><div><p className="eyebrow">Policy economics</p><h2>Expected cost comparison</h2></div><CircleDollarSign size={16} /></div><div className="cost-chart">{Object.entries(decision.expected_cost_by_action ?? {}).map(([action, cost]) => { const max = Math.max(...Object.values(decision.expected_cost_by_action ?? {}).map(Number), 1); return <div className={`cost-row ${action === decision.action ? "active" : ""}`} key={action}><span>{action.replace("_", "-")}</span><div className="cost-track"><i style={{ width: `${Math.max(3, Number(cost) / max * 100)}%` }} /></div><b>INR {Number(cost).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</b></div>; })}</div></article></div>
          </section>

          <section className="intelligence-grid"><article className="panel"><div className="panel-header"><div><p className="eyebrow">Trust intelligence</p><h2>Signal breakdown</h2></div><span className="muted">Derived from this session</span></div><div className="signal-list">{trustSignals.map(([label, value]) => <div className="signal-row" key={label as string}><span>{label}</span><div className="signal-track"><i className={Number(value) < 40 ? "low" : ""} style={{ width: `${value}%` }} /></div><b>{value}%</b></div>)}</div></article><article className="panel mandate-card"><div className="panel-header"><div><p className="eyebrow">Intent firewall</p><h2>Mandate status</h2></div><FileCheck2 size={16} /></div><div className="mandate-status"><span className={decision.reason_codes.some((reason) => reason.code === "R101") ? "mandate-icon bad" : "mandate-icon"}>{decision.reason_codes.some((reason) => reason.code === "R101") ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}</span><div><b>{decision.reason_codes.some((reason) => reason.code === "R101") ? "Scope violation detected" : "Mandate verified"}</b><small>Independent customer authorization check</small></div></div><div className="mandate-meta"><span>Principal <b>cust-001</b></span><span>Agent <b>{decision.agent_class.replace("_", " ")}</b></span></div></article></section>

          <footer className="footer"><span><CreditCard size={14} /> Session <code>{decision.session_id ?? "—"}</code></span><span>{loading ? "Refreshing decision…" : "Scored locally · no external calls"}</span></footer>
        </div>
      </section>
    </main>
  );
}
