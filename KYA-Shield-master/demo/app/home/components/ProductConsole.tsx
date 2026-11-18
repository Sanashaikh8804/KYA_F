import { Check, ShieldCheck } from "lucide-react";

const policy = [
  ["Identity verification", "credential vc_7f3a · signature valid", "6 ms"],
  ["Mandate validation", "payments.initiate in scope · not expired", "4 ms"],
  ["Transaction limit", "INR 18,500 ≤ INR 50,000 per transaction", "2 ms"],
  ["Risk assessment", "p_fraud 0.03 · known payee · trusted origin", "26 ms"]
];

/** Static, realistic rendering of a KYA-Shield authorization decision. */
export function ProductConsole() {
  return (
    <figure className="k-console" aria-label="KYA-Shield authorization decision for agent agt_7f3a9c">
      <div className="k-console-top">
        <span className="k-console-crumb"><ShieldCheck size={13} aria-hidden="true" /> <span className="k-crumb-extra">Decision Center <i>/</i> Authorizations <i>/</i> </span><b>DEC-28471</b></span>
        <span className="k-mono k-muted">38 ms</span>
      </div>

      <div className="k-console-split">
        <section aria-labelledby="c-id">
          <h3 id="c-id" className="k-label">Agent identity</h3>
          <dl className="k-kv">
            <div><dt>Agent ID</dt><dd className="k-mono">agt_7f3a9c</dd></div>
            <div><dt>Status</dt><dd><span className="k-status k-status-ok"><Check size={12} aria-hidden="true" /> Verified</span></dd></div>
            <div><dt>Class</dt><dd>LLM agent</dd></div>
            <div><dt>Credential</dt><dd className="k-mono">vc_7f3a · Acme Treasury</dd></div>
          </dl>
        </section>
        <section aria-labelledby="c-mandate">
          <h3 id="c-mandate" className="k-label">Mandate</h3>
          <dl className="k-kv">
            <div><dt>Mandate</dt><dd className="k-mono">mnd_0198</dd></div>
            <div><dt>Actions</dt><dd className="k-mono">payments.initiate</dd></div>
            <div><dt>Limit</dt><dd>INR 50,000 / transaction</dd></div>
            <div><dt>Valid</dt><dd>1 Nov – 30 Nov 2026</dd></div>
          </dl>
        </section>
      </div>

      <section className="k-console-policy" aria-labelledby="c-policy">
        <h3 id="c-policy" className="k-label">Policy evaluation</h3>
        <ul>
          {policy.map(([name, detail, time]) => (
            <li key={name}>
              <span className="k-tick" aria-hidden="true"><Check size={11} strokeWidth={2.5} /></span>
              <span className="k-policy-name">{name}</span>
              <span className="k-policy-detail k-mono">{detail}</span>
              <span className="k-policy-time k-mono">{time}</span>
              <span className="k-sr">passed</span>
            </li>
          ))}
        </ul>
      </section>

      <div className="k-console-decision">
        <div>
          <span className="k-label">Final decision</span>
          <strong className="k-verdict k-verdict-ok"><Check size={18} strokeWidth={2.5} aria-hidden="true" /> APPROVED</strong>
          <p>All four checks passed. Payment to Northwind Supplies is within delegated authority.</p>
        </div>
        <dl className="k-kv k-kv-stack">
          <div><dt>Audit reference</dt><dd className="k-mono">AUD-20261109-28471</dd></div>
          <div><dt>Policy set</dt><dd className="k-mono">commerce_default v4</dd></div>
        </dl>
      </div>
    </figure>
  );
}
