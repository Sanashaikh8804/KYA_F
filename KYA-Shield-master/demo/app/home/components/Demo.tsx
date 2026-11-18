"use client";

import { Check, RotateCcw, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/Button";

type Stage = { name: string; pass: boolean | null; detail: string };
type Scenario = {
  key: "approved" | "blocked";
  label: string;
  request: [string, string][];
  stages: Stage[];
  verdict: string;
  reason: string;
  ref: string;
};

const scenarios: Scenario[] = [
  {
    key: "approved",
    label: "Within mandate",
    request: [
      ["Agent", "agt_7f3a9c"],
      ["Action", "payments.initiate"],
      ["Payee", "Northwind Supplies"],
      ["Amount", "INR 18,500"]
    ],
    stages: [
      { name: "Agent request", pass: true, detail: "Request received and bound to a session." },
      { name: "Identity verification", pass: true, detail: "LLM agent · credential vc_7f3a verified." },
      { name: "Mandate validation", pass: true, detail: "payments.initiate is in scope for mnd_0198." },
      { name: "Policy evaluation", pass: true, detail: "Within INR 50,000 limit · known payee · p_fraud 0.03." },
      { name: "Final authorization", pass: true, detail: "Authorized within delegated authority." }
    ],
    verdict: "APPROVED",
    reason: "Identity verified, action in scope, amount within limit.",
    ref: "AUD-20261109-28471"
  },
  {
    key: "blocked",
    label: "Exceeds mandate",
    request: [
      ["Agent", "agt_7f3a9c"],
      ["Action", "payments.initiate"],
      ["Payee", "Unlisted Payee Ltd (new)"],
      ["Amount", "INR 2,40,000"]
    ],
    stages: [
      { name: "Agent request", pass: true, detail: "Request received and bound to a session." },
      { name: "Identity verification", pass: true, detail: "LLM agent · credential vc_7f3a verified." },
      { name: "Mandate validation", pass: false, detail: "INR 2,40,000 exceeds the INR 50,000 mandate limit." },
      { name: "Policy evaluation", pass: null, detail: "Not reached after mandate failure." },
      { name: "Final authorization", pass: false, detail: "Authorization denied." }
    ],
    verdict: "BLOCKED",
    reason: "Amount exceeds the delegated limit and the payee is new.",
    ref: "AUD-20261109-28472"
  }
];

export function Demo() {
  const [key, setKey] = useState<Scenario["key"]>("approved");
  const [progress, setProgress] = useState(5);
  const [running, setRunning] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const scenario = scenarios.find((item) => item.key === key) ?? scenarios[0];

  const stop = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
  }, []);

  const run = useCallback((next?: Scenario["key"]) => {
    stop();
    if (next) setKey(next);
    const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setRunning(false);
      setProgress(5);
      return;
    }
    setProgress(0);
    setRunning(true);
    timer.current = setInterval(() => {
      setProgress((current) => Math.min(current + 1, 5));
    }, 620);
  }, [stop]);

  useEffect(() => {
    if (running && progress >= 5) {
      stop();
      setRunning(false);
    }
  }, [running, progress, stop]);

  useEffect(() => stop, [stop]);

  const finished = progress >= 5;
  const blocked = scenario.key === "blocked";

  return (
    <div className="k-demo">
      <div className="k-demo-controls">
        <div className="k-segmented" role="group" aria-label="Demonstration scenario">
          {scenarios.map((item) => (
            <button key={item.key} type="button" aria-pressed={item.key === key} onClick={() => run(item.key)}>{item.label}</button>
          ))}
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={() => run()} disabled={running}>
          <RotateCcw size={14} aria-hidden="true" /> {running ? "Evaluating…" : "Run request"}
        </Button>
      </div>

      <div className="k-demo-body">
        <div className="k-demo-request">
          <span className="k-label">Incoming request</span>
          <dl className="k-kv k-kv-stack">
            {scenario.request.map(([term, value]) => (
              <div key={term}><dt>{term}</dt><dd className={term === "Amount" ? "" : "k-mono"}>{value}</dd></div>
            ))}
          </dl>
        </div>

        <ol className="k-lifecycle" aria-live="polite">
          {scenario.stages.map((stage, index) => {
            const done = index < progress;
            const active = running && index === progress;
            const state = !done ? (active ? "active" : "pending") : stage.pass === true ? "pass" : stage.pass === false ? "fail" : "skip";
            return (
              <li key={stage.name} data-state={state}>
                <span className="k-life-node" aria-hidden="true">
                  {state === "pass" && <Check size={12} strokeWidth={2.5} />}
                  {state === "fail" && <X size={12} strokeWidth={2.5} />}
                  {state !== "pass" && state !== "fail" && <b>{index + 1}</b>}
                </span>
                <div>
                  <h4>{stage.name}</h4>
                  <p>{done ? stage.detail : active ? "Evaluating…" : "Waiting"}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="k-demo-result" data-state={finished ? (blocked ? "blocked" : "approved") : "pending"}>
        <div>
          <span className="k-label">Final decision</span>
          <strong className={`k-verdict ${finished ? (blocked ? "k-verdict-bad" : "k-verdict-ok") : "k-verdict-idle"}`}>
            {finished ? (blocked ? <X size={18} strokeWidth={2.5} aria-hidden="true" /> : <Check size={18} strokeWidth={2.5} aria-hidden="true" />) : null}
            {finished ? scenario.verdict : "PENDING"}
          </strong>
        </div>
        <p>{finished ? scenario.reason : "Checks are running in order. Each result is recorded."}</p>
        <span className="k-mono k-muted">{finished ? scenario.ref : "—"}</span>
      </div>
    </div>
  );
}
