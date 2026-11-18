"use client";

import Link from "next/link";
import { ArrowUpRight, ChevronDown, Menu, ShieldCheck, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/Button";

const links = [
  { href: "#capabilities", label: "Capabilities" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#use-cases", label: "Use cases" },
  { href: "#company", label: "Company" }
];

const explore = [
  { href: "#trust", label: "Trust infrastructure", note: "Why agents need verifiable authority" },
  { href: "#demo", label: "Product demonstration", note: "One request, five checks" },
  { href: "#capabilities", label: "Platform capabilities", note: "Identity, mandates, policy, audit" },
  { href: "/", label: "Decision Center", note: "Live monitoring and decisions" }
];

export function Brand({ small = false }: { small?: boolean }) {
  return (
    <Link className="k-brand" href="/home" aria-label="KYA-Shield home">
      <span className="k-brand-mark" aria-hidden="true"><ShieldCheck size={small ? 14 : 16} strokeWidth={2} /></span>
      <span className="k-brand-name">KYA<i>-</i>Shield</span>
    </Link>
  );
}

export function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [exploreOpen, setExploreOpen] = useState(false);
  const exploreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setExploreOpen(false);
        setMenuOpen(false);
      }
    };
    const onClick = (event: MouseEvent) => {
      if (exploreRef.current && !exploreRef.current.contains(event.target as Node)) setExploreOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, []);

  return (
    <header className="k-nav">
      <div className="k-container k-nav-inner">
        <Brand />
        <nav className="k-nav-links" aria-label="Primary">
          {links.map((link) => <a key={link.href} href={link.href}>{link.label}</a>)}
        </nav>
        <div className="k-nav-actions">
          <div className="k-dropdown" ref={exploreRef}>
            <button
              type="button"
              className="k-nav-link-button"
              aria-expanded={exploreOpen}
              aria-haspopup="true"
              aria-controls="k-explore-menu"
              onClick={() => setExploreOpen((open) => !open)}
            >
              Explore <ChevronDown size={14} className="k-chevron" data-open={exploreOpen} />
            </button>
            <div id="k-explore-menu" className="k-dropdown-menu" data-open={exploreOpen} hidden={!exploreOpen}>
              {explore.map((item) => (
                <Link key={item.label} href={item.href} onClick={() => setExploreOpen(false)}>
                  <b>{item.label}</b>
                  <span>{item.note}</span>
                </Link>
              ))}
            </div>
          </div>
          <Button href="/" variant="navigation" size="sm">Open Decision Center <ArrowUpRight size={14} /></Button>
        </div>
        <button
          type="button"
          className="k-menu-button"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="k-mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>
      <div id="k-mobile-menu" className="k-mobile-menu" hidden={!menuOpen}>
        <div className="k-container">
          {links.map((link) => <a key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>{link.label}</a>)}
          <Button href="/" variant="navigation" className="k-btn-block" onClick={() => setMenuOpen(false)}>Open Decision Center <ArrowUpRight size={15} /></Button>
        </div>
      </div>
    </header>
  );
}
