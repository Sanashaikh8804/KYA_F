import { Check } from "lucide-react";
import type { ReactNode } from "react";
import { Reveal } from "./Reveal";

function Copy({ index, title, children, points }: { index: string; title: string; children: ReactNode; points?: string[] }) {
  return (
    <div className="k-cap-copy">
      <span className="k-index">{index}</span>
      <h3>{title}</h3>
      <p>{children}</p>
      {points && <ul>{points.map((point) => <li key={point}><Check size={13} aria-hidden="true" /> {point}</li>)}</ul>}
    </div>
  );
}

function Bar({ label, value, tone = "mint" }: { label: string; value: number; tone?: "mint" | "muted" }) {
  return (
    <div className="k-bar">
      <span>{label}</span>
      <i><b data-tone={tone} style={{ width: `${Math.round(value * 100)}%` }} /></i>
      <span className="k-mono">{value.toFixed(2)}</span>
    </div>
  );
}

export function Capabilities() {
  return (
    <div className="k-caps">
      {/* 01 — wide split */}
      <Reveal className="k-cap k-cap-split">
        <Copy index="01" title="Agent identity verification" points={["Human, scripted bot, or LLM agent", "Durable session identity", "Trust score on every request"]}>
          Classify who is acting before anything else. Each request is tied to a session and an agent class, so a decision always starts from a known actor.
        </Copy>
        <div className="k-panel">
          <div className="k-panel-head"><span className="k-label">Classification</span><span className="k-status k-status-ok"><Check size={12} aria-hidden="true" /> Verified</span></div>
          <dl className="k-kv"><div><dt>Session</dt><dd className="k-mono">ses_91c4e2</dd></div><div><dt>Agent ID</dt><dd className="k-mono">agt_7f3a9c</dd></div><div><dt>Trust score</dt><dd className="k-mono">0.91</dd></div></dl>
          <div className="k-bars" aria-label="Agent class probabilities">
            <Bar label="LLM agent" value={0.91} />
            <Bar label="Scripted bot" value={0.07} tone="muted" />
            <Bar label="Human" value={0.02} tone="muted" />
          </div>
        </div>
      </Reveal>

      {/* 02 + 03 — pair */}
      <div className="k-cap-pair">
        <Reveal className="k-cap k-cap-stack">
          <Copy index="02" title="Verifiable credentials">Check the credential an agent presents, who issued it, and whether it is still valid, rather than trusting a name.</Copy>
          <div className="k-panel k-code" role="img" aria-label="Credential record">
            <p><span>credential</span>agent_mandate</p>
            <p><span>subject</span>agt_7f3a9c</p>
            <p><span>issuer</span>Acme Treasury</p>
            <p><span>issued</span>2026-11-01</p>
            <p><span>expires</span>2026-11-30</p>
            <p><span>status</span><em>valid</em></p>
          </div>
        </Reveal>
        <Reveal className="k-cap k-cap-stack" delay={80}>
          <Copy index="03" title="Delegated mandates">Keep every action inside what a customer or operator actually granted: scope, limit, and validity period.</Copy>
          <div className="k-panel">
            <div className="k-panel-head"><span className="k-label">mnd_0198</span><span className="k-mono k-muted">1 – 30 Nov 2026</span></div>
            <div className="k-chips"><span>payments.initiate</span><span>orders.create</span></div>
            <div className="k-limit" role="img" aria-label="INR 18,500 requested against a limit of INR 50,000">
              <div className="k-limit-track"><b style={{ width: "37%" }} /><i style={{ left: "37%" }} /></div>
              <div className="k-limit-scale k-mono"><span>0</span><span>Request 18,500</span><span>Limit 50,000</span></div>
            </div>
          </div>
        </Reveal>
      </div>

      {/* 04 — reversed split */}
      <Reveal className="k-cap k-cap-split k-cap-reverse">
        <Copy index="04" title="Policy enforcement" points={["Rules read the full session context", "Same rules for every agent", "Versioned policy sets"]}>
          Write rules once and apply them to every request. Amount, payee, content origin, and agent trust are evaluated together, not in isolation.
        </Copy>
        <div className="k-panel k-rules" role="table" aria-label="Example policy rules">
          <div role="row" className="k-rules-head"><span role="columnheader">Condition</span><span role="columnheader">Outcome</span></div>
          <div role="row"><span role="cell" className="k-mono">amount ≤ mandate.limit</span><span role="cell" className="k-out k-out-ok">allow</span></div>
          <div role="row"><span role="cell" className="k-mono">payee is new</span><span role="cell" className="k-out">step-up</span></div>
          <div role="row"><span role="cell" className="k-mono">content origin is external</span><span role="cell" className="k-out">hold</span></div>
          <div role="row"><span role="cell" className="k-mono">amount &gt; mandate.limit</span><span role="cell" className="k-out k-out-bad">block</span></div>
        </div>
      </Reveal>

      {/* 05 + 06 — pair */}
      <div className="k-cap-pair">
        <Reveal className="k-cap k-cap-stack">
          <Copy index="05" title="Risk evaluation">Estimate fraud probability and the expected cost of each action, then choose the lowest-risk outcome.</Copy>
          <div className="k-panel">
            <div className="k-panel-head"><span className="k-label">Expected cost by action</span><span className="k-mono k-muted">p_fraud 0.03</span></div>
            <div className="k-bars">
              <Bar label="Allow" value={0.12} />
              <Bar label="Step-up" value={0.34} tone="muted" />
              <Bar label="Hold" value={0.58} tone="muted" />
              <Bar label="Block" value={0.81} tone="muted" />
            </div>
          </div>
        </Reveal>
        <Reveal className="k-cap k-cap-stack" delay={80}>
          <Copy index="06" title="Decision audit trails">Every decision carries its reasons and an audit reference, so risk and compliance teams can reconstruct what happened.</Copy>
          <div className="k-panel k-log" role="img" aria-label="Audit log for decision DEC-28471">
            <p><span className="k-mono">09:41:07.112</span>request received</p>
            <p><span className="k-mono">09:41:07.118</span>identity verified</p>
            <p><span className="k-mono">09:41:07.122</span>mandate in scope</p>
            <p><span className="k-mono">09:41:07.148</span>policy passed</p>
            <p><span className="k-mono">09:41:07.150</span><b>APPROVED</b> AUD-20261109-28471</p>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
