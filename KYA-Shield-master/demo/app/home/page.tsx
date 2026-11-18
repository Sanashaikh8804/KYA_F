import Link from "next/link";
import { ArrowRight, Check, X } from "lucide-react";
import { Brand, NavBar } from "./components/NavBar";
import { HeroScene } from "./components/HeroScene";
import { Capabilities } from "./components/Capabilities";
import { Demo } from "./components/Demo";
import { Reveal } from "./components/Reveal";
import { Button } from "../components/Button";

const facts = [
  ["4", "decision outcomes", "Allow, step-up, hold, or block."],
  ["5", "checks per request", "Identity to final decision, in order."],
  ["3", "agent classes", "Human, scripted bot, LLM agent."],
  ["1", "audit reference", "Attached to every decision."]
];

const problems = [
  ["Unknown agent identity", "Requests arrive from software no one can name or tell apart from a person.", "Every actor is classified and tied to a durable session identity."],
  ["Unbounded permissions", "An agent holds broad access, and nothing says what it may not do.", "Actions, limits, and validity are fixed in a mandate."],
  ["Unverified delegated authority", "No proof that a customer or operator actually granted the authority claimed.", "Credentials are verified against their issuer before a mandate is honored."],
  ["Uncontrolled transactions", "Money moves on the strength of a prompt, with no limit check at the moment of action.", "Amount, payee, and context are evaluated against policy first."],
  ["Missing accountability", "When something goes wrong, no one can show why it was allowed.", "Each decision stores its reasons and an audit reference."]
];

const steps = [
  ["01", "Agent identity", "Classify the actor and establish a durable session identity."],
  ["02", "Credential verification", "Verify the credential, its issuer, and its validity."],
  ["03", "Mandate validation", "Check scope, limit, expiry, and payee against the mandate."],
  ["04", "Policy evaluation", "Apply your rules to the full session context."],
  ["05", "Final decision", "Return an explainable allow, step-up, hold, or block."]
];

const useCases = [
  ["Payments", "Verify intent and authority before a transfer is initiated.", "A procurement agent pays a supplier within a per-transaction cap. A larger transfer to a new payee is blocked."],
  ["Customer support", "Keep account changes inside the authority a customer approved.", "A support agent updates contact details on request, but a payout change is held for step-up."],
  ["Commerce", "Let agents buy on a customer's behalf within precise limits.", "A shopping agent completes an order inside budget and category, and stops at the limit."],
  ["Internal operations", "Make automation accountable across sensitive tools.", "An operations agent runs routine jobs. Each action is logged with the mandate that allowed it."]
];

const footer = [
  ["Product", [["Capabilities", "#capabilities"], ["How it works", "#how-it-works"], ["Demonstration", "#demo"], ["Decision Center", "/"]]],
  ["Company", [["About", "#company"], ["Use cases", "#use-cases"], ["Trust infrastructure", "#trust"]]],
  ["Documentation", [["Overview", "#trust"], ["Decision model", "#how-it-works"], ["Policy rules", "#capabilities"]]],
  ["Contact", [["contact@kya-shield.com", "mailto:contact@kya-shield.com"]]],
  ["Legal", [["Privacy", "#"], ["Terms", "#"], ["Security", "#"]]]
] as const;

export default function HomePage() {
  return (
    <div className="k-site">
      <a className="k-skip" href="#main">Skip to content</a>
      <NavBar />

      <main id="main">
        {/* HERO */}
        <section className="k-hero">
          <HeroScene />
          <div className="k-hero-shade" aria-hidden="true" />
          <div className="k-container k-hero-grid">
            <div className="k-hero-copy">
              <p className="k-eyebrow">Trust infrastructure for agentic commerce</p>
              <h1>Move fast.<br /><span>Know why.</span></h1>
              <p className="k-lede">KYA-Shield gives every AI agent a verifiable identity, a bounded mandate, and a decision your risk team can stand behind.</p>
              <div className="k-actions">
                <Button href="/" variant="primary">Start with a live decision <ArrowRight size={16} /></Button>
                <Button href="#capabilities" variant="secondary">Explore the platform <ArrowRight size={16} /></Button>
              </div>
              <ul className="k-hero-notes" aria-label="What every decision includes">
                <li><Check size={13} aria-hidden="true" /> Explainable reasons</li>
                <li><Check size={13} aria-hidden="true" /> Audit reference</li>
                <li><Check size={13} aria-hidden="true" /> Allow, step-up, hold, block</li>
              </ul>
            </div>
          </div>
        </section>

        {/* A — TRUST INFRASTRUCTURE */}
        <section className="k-section k-section-ruled" id="trust">
          <div className="k-container">
            <Reveal className="k-editorial">
              <div>
                <p className="k-eyebrow">Trust infrastructure</p>
                <h2>Agents are starting to act for customers. Authority has to be provable.</h2>
              </div>
              <div className="k-prose">
                <p>An agent that can move money or change an account needs more than an API key. It needs an identity others can verify, and a limit on what it may do on someone&apos;s behalf.</p>
                <p>KYA-Shield sits at the moment of action. It checks who is acting, what they were authorized to do, and whether this request fits, then records why it said yes or no.</p>
              </div>
            </Reveal>
            <Reveal className="k-facts" delay={60}>
              {facts.map(([value, label, note]) => (
                <div key={label}><b className="k-mono">{value}</b><span>{label}</span><p>{note}</p></div>
              ))}
            </Reveal>
          </div>
        </section>

        {/* B — THE PROBLEM */}
        <section className="k-section">
          <div className="k-container">
            <Reveal className="k-head">
              <p className="k-eyebrow">The problem</p>
              <h2>Autonomous agents break the assumptions access controls were built on.</h2>
            </Reveal>
            <Reveal className="k-compare" delay={60}>
              <div className="k-compare-head" aria-hidden="true"><span>Risk</span><span>Without KYA-Shield</span><span>With KYA-Shield</span></div>
              <ul>
                {problems.map(([title, bad, good]) => (
                  <li key={title}>
                    <h3>{title}</h3>
                    <p className="k-bad"><X size={14} aria-hidden="true" /><span><em className="k-sr">Without KYA-Shield: </em>{bad}</span></p>
                    <p className="k-good"><Check size={14} aria-hidden="true" /><span><em className="k-sr">With KYA-Shield: </em>{good}</span></p>
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </section>

        {/* C — HOW IT WORKS */}
        <section className="k-section k-section-surface" id="how-it-works">
          <div className="k-container">
            <Reveal className="k-head">
              <p className="k-eyebrow">How KYA-Shield works</p>
              <h2>Five checks, in order. One clear answer.</h2>
            </Reveal>
            <Reveal className="k-steps-wrap" delay={60}>
              <ol className="k-steps">
                {steps.map(([n, title, copy]) => (
                  <li key={n}><span className="k-step-node k-mono">{n}</span><h3>{title}</h3><p>{copy}</p></li>
                ))}
              </ol>
            </Reveal>
          </div>
        </section>

        {/* D — CAPABILITIES */}
        <section className="k-section" id="capabilities">
          <div className="k-container">
            <Reveal className="k-head">
              <p className="k-eyebrow">Product capabilities</p>
              <h2>Everything a decision depends on, in one control plane.</h2>
            </Reveal>
            <Capabilities />
          </div>
        </section>

        {/* E — DEMO */}
        <section className="k-section k-section-surface" id="demo">
          <div className="k-container">
            <Reveal className="k-head">
              <p className="k-eyebrow">Product demonstration</p>
              <h2>An agent asks to pay. Watch the request resolve.</h2>
              <p className="k-sub">Run the same agent against two requests. One stays within its mandate. One does not.</p>
            </Reveal>
            <Reveal delay={60}><Demo /></Reveal>
          </div>
        </section>

        {/* F — USE CASES */}
        <section className="k-section" id="use-cases">
          <div className="k-container">
            <Reveal className="k-head">
              <p className="k-eyebrow">Use cases</p>
              <h2>Built for the places risk becomes real.</h2>
            </Reveal>
            <Reveal className="k-usecases" delay={60}>
              <ul>
                {useCases.map(([title, copy, example], i) => (
                  <li key={title}>
                    <span className="k-index">0{i + 1}</span>
                    <h3>{title}</h3>
                    <p>{copy}</p>
                    <p className="k-example"><span className="k-label">Example</span>{example}</p>
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </section>

        {/* G — FINAL CTA */}
        <section className="k-final" id="company">
          <div className="k-container">
            <Reveal className="k-final-inner">
              <h2>Trust every agent.<br /><span>Control every decision.</span></h2>
              <p>Give your agents real authority with limits you set, and a record you can show. KYA-Shield lets your organization deploy AI agents with confidence.</p>
              <Button href="/" variant="primary">Open Decision Center <ArrowRight size={16} /></Button>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="k-footer">
        <div className="k-container">
          <div className="k-footer-grid">
            <div className="k-footer-brand">
              <Brand small />
              <p>Trust infrastructure for agentic commerce.</p>
            </div>
            {footer.map(([heading, items]) => (
              <nav key={heading} aria-label={heading}>
                <h3 className="k-label">{heading}</h3>
                <ul>{items.map(([label, href]) => <li key={label}><a href={href}>{label}</a></li>)}</ul>
              </nav>
            ))}
          </div>
          <div className="k-footer-base"><span>© 2026 KYA-Shield. All rights reserved.</span><span>Agent trust infrastructure</span></div>
        </div>
      </footer>
    </div>
  );
}
