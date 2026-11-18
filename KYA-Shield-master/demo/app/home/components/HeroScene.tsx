"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const InfiniteCoinEnvironment = dynamic(() => import("./InfiniteCoinEnvironment"), { ssr: false });

export function HeroScene() {
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const schedule = window.requestAnimationFrame(() => setShouldLoad(true));

    return () => {
      window.cancelAnimationFrame(schedule);
    };
  }, []);

  // The poster keeps the composition intact while the page becomes interactive.
  return shouldLoad
    ? <InfiniteCoinEnvironment className="k-hero-scene" />
    : <div className="k-hero-scene k-hero-poster" aria-hidden="true" />;
}
