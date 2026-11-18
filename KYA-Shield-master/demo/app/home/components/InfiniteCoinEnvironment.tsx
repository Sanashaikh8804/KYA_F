"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

/* ------------------------------------------------------------------ *
 *  KYA-Shield hero: a silver coin rolling along a wide satin-metal
 *  walkway through a dark architectural set.
 *  Physically based materials, softbox studio lighting, a glossy
 *  mirrored floor, a real reeded + bevelled coin with an embossed
 *  emblem (height-map -> normal map). The set is a treadmill: the
 *  ground, walkway seams and architecture scroll at exactly the coin's
 *  rolling speed, so there is no slip, reset or teleport.
 * ------------------------------------------------------------------ */

type Disposable = { dispose(): void };
type QualityProfile = {
  name: "high" | "medium" | "low";
  pixelRatio: number;
  shadowMap: number;
  coinMap: number;
  surfaceMap: number;
  coinSegments: number;
  anisotropy: number;
  shadows: boolean;
  reflection: boolean;
};

const COIN_R = 1.48;
const COIN_T = 0.3;
const FACE_R = COIN_R - 0.07;
const PATH_W = 6.4;
const PATH_TOP = 0.12;
const FLOOR_Y = -0.16;
const PANEL = 3.8;
const TILE = 6.4;
const SEG_PERIOD = 12;
const SEG_COUNT = 6;
const SEG_FAR = -62;
const ROLL_SPEED = 3.2;
const CAMERA_SMOOTHING = 3.8;

function getQualityProfile(mobile: boolean): QualityProfile {
  const device = navigator as Navigator & { deviceMemory?: number };
  const memory = device.deviceMemory ?? 8;
  const cores = navigator.hardwareConcurrency ?? 4;
  const constrained = mobile || memory <= 4 || cores <= 4;
  if (constrained) {
    return { name: "low", pixelRatio: 0.9, shadowMap: 768, coinMap: 384, surfaceMap: 320, coinSegments: 96, anisotropy: 2, shadows: false, reflection: false };
  }
  if (memory <= 8 || cores <= 6) {
    return { name: "medium", pixelRatio: 1.1, shadowMap: 1024, coinMap: 512, surfaceMap: 384, coinSegments: 144, anisotropy: 2, shadows: true, reflection: false };
  }
  return { name: "high", pixelRatio: 1.3, shadowMap: 1536, coinMap: 768, surfaceMap: 512, coinSegments: 192, anisotropy: 4, shadows: true, reflection: true };
}

function makeCanvas(w: number, h = w) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return [c, c.getContext("2d")!] as const;
}

/* ---------- coin face artwork (shared by height + roughness maps) ---------- */
type FacePalette = { field: string; lip: string; groove: string; text: string; shield: string; inset: string; mark: string };

function shieldPath(ctx: CanvasRenderingContext2D, cx: number, cy: number, s: number) {
  ctx.beginPath();
  ctx.moveTo(cx, cy - s * 0.62);
  ctx.bezierCurveTo(cx + s * 0.2, cy - s * 0.5, cx + s * 0.38, cy - s * 0.46, cx + s * 0.5, cy - s * 0.48);
  ctx.lineTo(cx + s * 0.5, cy + s * 0.02);
  ctx.bezierCurveTo(cx + s * 0.5, cy + s * 0.36, cx + s * 0.22, cy + s * 0.56, cx, cy + s * 0.7);
  ctx.bezierCurveTo(cx - s * 0.22, cy + s * 0.56, cx - s * 0.5, cy + s * 0.36, cx - s * 0.5, cy + s * 0.02);
  ctx.lineTo(cx - s * 0.5, cy - s * 0.48);
  ctx.bezierCurveTo(cx - s * 0.38, cy - s * 0.46, cx - s * 0.2, cy - s * 0.5, cx, cy - s * 0.62);
  ctx.closePath();
}

function paintFace(ctx: CanvasRenderingContext2D, size: number, p: FacePalette) {
  const c = size / 2;
  const R = c;
  ctx.fillStyle = p.field;
  ctx.fillRect(0, 0, size, size);
  // raised outer lip + inner groove
  ctx.fillStyle = p.lip;
  ctx.beginPath(); ctx.arc(c, c, R, 0, Math.PI * 2); ctx.arc(c, c, R * 0.905, 0, Math.PI * 2, true); ctx.fill();
  ctx.strokeStyle = p.groove; ctx.lineWidth = size * 0.006;
  ctx.beginPath(); ctx.arc(c, c, R * 0.892, 0, Math.PI * 2); ctx.stroke();
  // dentil beading
  ctx.fillStyle = p.lip;
  const beads = 96;
  for (let i = 0; i < beads; i += 1) {
    const a = (i / beads) * Math.PI * 2;
    ctx.beginPath(); ctx.arc(c + Math.cos(a) * R * 0.855, c + Math.sin(a) * R * 0.855, size * 0.0042, 0, Math.PI * 2); ctx.fill();
  }
  // legend around the field
  ctx.fillStyle = p.text;
  ctx.font = `700 ${size * 0.052}px "Helvetica Neue", Arial, sans-serif`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const arc = (text: string, mid: number, radius: number, flip: boolean) => {
    const chars = text.split("");
    const step = (size * 0.0385) / radius;
    const start = mid - ((chars.length - 1) * step * (flip ? -1 : 1)) / 2;
    chars.forEach((ch, i) => {
      const a = start + i * step * (flip ? -1 : 1);
      ctx.save();
      ctx.translate(c + Math.cos(a) * radius, c + Math.sin(a) * radius);
      ctx.rotate(a + (flip ? -Math.PI / 2 : Math.PI / 2));
      ctx.fillText(ch, 0, 0);
      ctx.restore();
    });
  };
  arc("KYA-SHIELD", -Math.PI / 2, R * 0.76, false);
  arc("VERIFIED AUTHORITY", Math.PI / 2, R * 0.76, true);
  ctx.beginPath(); ctx.arc(c - R * 0.76, c, size * 0.007, 0, Math.PI * 2); ctx.arc(c + R * 0.76, c, size * 0.007, 0, Math.PI * 2); ctx.fill();
  // fine ring
  ctx.strokeStyle = p.lip; ctx.lineWidth = size * 0.008;
  ctx.beginPath(); ctx.arc(c, c, R * 0.655, 0, Math.PI * 2); ctx.stroke();
  // shield emblem
  const s = size * 0.5;
  ctx.fillStyle = p.shield; shieldPath(ctx, c, c, s); ctx.fill();
  ctx.fillStyle = p.inset; shieldPath(ctx, c, c, s * 0.86); ctx.fill();
  ctx.fillStyle = p.shield; shieldPath(ctx, c, c, s * 0.8); ctx.fill();
  // check mark
  ctx.strokeStyle = p.mark; ctx.lineWidth = size * 0.04; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.beginPath(); ctx.moveTo(c - s * 0.2, c + s * 0.01); ctx.lineTo(c - s * 0.04, c + s * 0.18); ctx.lineTo(c + s * 0.24, c - s * 0.17); ctx.stroke();
}

function brushNoise(ctx: CanvasRenderingContext2D, size: number, count: number, dark: boolean) {
  const c = size / 2;
  for (let i = 0; i < count; i += 1) {
    const r = Math.sqrt(Math.random()) * size * 0.5;
    const a = Math.random() * Math.PI * 2;
    const len = 0.01 + Math.random() * 0.12;
    const v = dark ? 20 + Math.random() * 60 : 150 + Math.random() * 90;
    ctx.strokeStyle = `rgba(${v},${v},${v},${0.03 + Math.random() * 0.07})`;
    ctx.lineWidth = Math.random() > 0.92 ? 2 : 1;
    ctx.beginPath(); ctx.arc(c, c, r, a - len, a + len); ctx.stroke();
  }
}

function coinMaps(size: number) {
  const density = size / 1024;
  const [hc, h] = makeCanvas(size);
  paintFace(h, size, { field: "#6a6a6a", lip: "#d2d2d2", groove: "#202020", text: "#e6e6e6", shield: "#b4b4b4", inset: "#4c4c4c", mark: "#f0f0f0" });
  brushNoise(h, size, Math.round(2600 * density * density), true);
  // soften the height field so edges read as bevels rather than cut-outs
  const [sc, s] = makeCanvas(size);
  s.filter = "blur(1.4px)";
  s.drawImage(hc, 0, 0);
  const src = s.getImageData(0, 0, size, size).data;
  const [nc, n] = makeCanvas(size);
  const out = n.createImageData(size, size);
  const k = 2.1;
  const at = (x: number, y: number) => src[((Math.min(size - 1, Math.max(0, y)) * size) + Math.min(size - 1, Math.max(0, x))) * 4] / 255;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const dx = (at(x + 1, y) - at(x - 1, y)) * k;
      const dy = (at(x, y + 1) - at(x, y - 1)) * k;
      const len = Math.hypot(dx, dy, 1);
      const i = (y * size + x) * 4;
      out.data[i] = (-dx / len * 0.5 + 0.5) * 255;
      out.data[i + 1] = (dy / len * 0.5 + 0.5) * 255;
      out.data[i + 2] = (1 / len * 0.5 + 0.5) * 255;
      out.data[i + 3] = 255;
    }
  }
  n.putImageData(out, 0, 0);
  // roughness: brushed field, polished relief
  const [rc, r] = makeCanvas(size);
  paintFace(r, size, { field: "#5c5c5c", lip: "#363636", groove: "#8a8a8a", text: "#323232", shield: "#363636", inset: "#7c7c7c", mark: "#2c2c2c" });
  brushNoise(r, size, Math.round(5200 * density * density), false);
  brushNoise(r, size, Math.round(2400 * density * density), true);
  for (let i = 0; i < Math.round(900 * density * density); i += 1) { // fine nicks and wear
    r.fillStyle = `rgba(${170 + Math.random() * 60},${170 + Math.random() * 60},${170 + Math.random() * 60},${0.15 + Math.random() * 0.3})`;
    r.fillRect(Math.random() * size, Math.random() * size, 1 + Math.random() * 3, 1);
  }
  return { normal: nc, rough: rc, sc };
}

/* ---------- walkway: satin brushed panels with machined seams ---------- */
function pathMaps(size: number) {
  const w = size, h = size;
  const density = size / 1024;
  const [rc, r] = makeCanvas(w, h);
  r.fillStyle = "#6a6a6a"; r.fillRect(0, 0, w, h);
  for (let i = 0; i < Math.round(2600 * density * density); i += 1) { // streaks run along the walkway
    const v = 60 + Math.random() * 90;
    r.strokeStyle = `rgba(${v},${v},${v},${0.04 + Math.random() * 0.09})`;
    r.lineWidth = 1 + Math.random() * 1.4;
    const x = Math.random() * w, y = Math.random() * h, l = 40 + Math.random() * 380;
    r.beginPath(); r.moveTo(x, y); r.lineTo(x + (Math.random() - 0.5) * 3, y + l); r.stroke();
  }
  const [bc, b] = makeCanvas(w, h);
  b.fillStyle = "#808080"; b.fillRect(0, 0, w, h);
  for (let i = 0; i < Math.round(2200 * density * density); i += 1) {
    const v = 90 + Math.random() * 90;
    b.strokeStyle = `rgba(${v},${v},${v},${0.03 + Math.random() * 0.07})`;
    b.lineWidth = 1;
    const x = Math.random() * w, y = Math.random() * h;
    b.beginPath(); b.moveTo(x, y); b.lineTo(x, y + 60 + Math.random() * 300); b.stroke();
  }
  // seam groove at the panel boundary (wraps seamlessly), plus soft edge rails
  const seam = Math.max(2, Math.round(5 * density));
  const rail = Math.max(1, Math.round(2 * density));
  b.fillStyle = "#1a1a1a"; b.fillRect(0, 0, w, seam); b.fillRect(0, h - seam, w, seam);
  b.fillStyle = "#c8c8c8"; b.fillRect(0, seam, w, rail); b.fillRect(0, h - seam - rail, w, rail);
  r.fillStyle = "#b0b0b0"; r.fillRect(0, 0, w, seam + rail); r.fillRect(0, h - seam - rail, w, seam + rail);
  return { rough: rc, bump: bc };
}

/* ---------- graphite tiled floor ---------- */
function floorMaps(size: number) {
  const density = size / 1024;
  const [cc, c] = makeCanvas(size);
  const [rc, r] = makeCanvas(size);
  const [bc, b] = makeCanvas(size);
  const half = size / 2;
  c.fillStyle = "#050607"; c.fillRect(0, 0, size, size);
  r.fillStyle = "#808080"; r.fillRect(0, 0, size, size);
  b.fillStyle = "#101010"; b.fillRect(0, 0, size, size);
  for (let ty = 0; ty < 2; ty += 1) {
    for (let tx = 0; tx < 2; tx += 1) {
      const x0 = tx * half + 4, y0 = ty * half + 4, w = half - 8;
      const t = 30 + Math.floor(Math.random() * 10);
      const g = c.createLinearGradient(x0, y0, x0 + w, y0 + w);
      g.addColorStop(0, `rgb(${t + 8},${t + 11},${t + 13})`);
      g.addColorStop(1, `rgb(${t - 4},${t - 1},${t + 1})`);
      c.fillStyle = g; c.fillRect(x0, y0, w, w);
      r.fillStyle = `rgb(${95 + Math.random() * 30},${95 + Math.random() * 30},${95 + Math.random() * 30})`; r.fillRect(x0, y0, w, w);
      b.fillStyle = "#9a9a9a"; b.fillRect(x0, y0, w, w);
    }
  }
  for (let i = 0; i < Math.round(9000 * density * density); i += 1) {
    const x = Math.random() * size, y = Math.random() * size, v = Math.random() * 255;
    c.fillStyle = `rgba(${v},${v},${v},${Math.random() * 0.035})`; c.fillRect(x, y, 1 + Math.random() * 2, 1 + Math.random() * 2);
    r.fillStyle = `rgba(${v},${v},${v},${Math.random() * 0.25})`; r.fillRect(x, y, 2, 2);
  }
  return { color: cc, rough: rc, bump: bc };
}

/* ---------- soft contact shadow ---------- */
function contactTexture() {
  const [c, x] = makeCanvas(256);
  const g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  g.addColorStop(0, "rgba(0,0,0,0.85)");
  g.addColorStop(0.35, "rgba(0,0,0,0.42)");
  g.addColorStop(1, "rgba(0,0,0,0)");
  x.fillStyle = g; x.fillRect(0, 0, 256, 256);
  return c;
}

/* ---------- studio lighting captured to an environment map ---------- */
function createStudioEnvironment(renderer: THREE.WebGLRenderer) {
  const studio = new THREE.Scene();
  const bg = new THREE.Color(0x0c1012);
  studio.background = bg;
  studio.add(new THREE.Mesh(new THREE.BoxGeometry(70, 40, 70), new THREE.MeshBasicMaterial({ color: bg, side: THREE.BackSide })));
  const card = (w: number, h: number, i: number, pos: [number, number, number], at: [number, number, number]) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(i, i * 0.995, i * 0.985), side: THREE.DoubleSide }));
    m.position.set(...pos); m.lookAt(...at); studio.add(m);
  };
  card(12, 7, 7.5, [-7, 14, 3], [0, 0, -5]);      // overhead key softbox
  card(5, 22, 7.2, [14, 5, 2], [0, 1, -6]);         // tall strip, right
  card(5, 18, 4.4, [-15, 4, 4], [0, 1, -6]);        // strip, left
  card(26, 3, 2.6, [0, 2, 17], [0, 0, -5]);         // low front bounce
  card(9, 14, 2.4, [-8, 4, -20], [0, 0, -4]);       // back kicker
  card(30, 8, 0.9, [0, 9, -24], [0, 0, 0]);         // dim back wall glow
  const gen = new THREE.PMREMGenerator(renderer);
  const target = gen.fromScene(studio, 0.035);
  studio.traverse((o) => {
    const m = o as THREE.Mesh;
    m.geometry?.dispose();
    if (m.material) (m.material as THREE.Material).dispose();
  });
  gen.dispose();
  return target;
}

export default function InfiniteCoinEnvironment({ className }: { className?: string }) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = host.current;
    if (!mount) return;
    const mobile = window.matchMedia("(max-width: 760px)").matches;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const quality = getQualityProfile(mobile);
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: quality.name !== "low", powerPreference: "high-performance" });
    } catch {
      return;
    }
    let pixelRatio = Math.min(window.devicePixelRatio || 1, quality.pixelRatio, 1.35);
    renderer.setPixelRatio(pixelRatio);
    renderer.setClearColor(0x0b0d0f, 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.92;
    renderer.shadowMap.enabled = quality.shadows;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.domElement.style.cssText = "display:block;width:100%;height:100%";
    mount.appendChild(renderer.domElement);

    const disposables: Disposable[] = [];
    const own = <T extends Disposable>(r: T) => (disposables.push(r), r);
    const aniso = Math.min(renderer.capabilities.getMaxAnisotropy(), quality.anisotropy);
    const tex = (canvas: HTMLCanvasElement, srgb: boolean, repeat = false) => {
      const t = own(new THREE.CanvasTexture(canvas));
      t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      t.anisotropy = aniso;
      if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
      return t;
    };

    const scene = new THREE.Scene();
    const fogColor = 0x0f1316;
    scene.background = new THREE.Color(fogColor);
    scene.fog = new THREE.FogExp2(fogColor, 0.031);
    const environment = own(createStudioEnvironment(renderer));
    // r163+ ignores material.envMapIntensity for scene.environment, so bind the map per material instead
    const envMap = environment.texture;

    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 140);
    const world = new THREE.Group();
    world.rotation.y = THREE.MathUtils.degToRad(-30);
    scene.add(world);

    const key = new THREE.DirectionalLight(0xfffcf6, 0.22);
    key.position.set(-7, 12, 8);
    key.target.position.set(0, 0, -6);
    key.castShadow = quality.shadows;
    key.shadow.mapSize.set(quality.shadowMap, quality.shadowMap);
    key.shadow.bias = -0.0004;
    key.shadow.normalBias = 0.035;
    key.shadow.radius = 4;
    Object.assign(key.shadow.camera, { left: -11, right: 11, top: 12, bottom: -9, near: 1, far: 50 });
    world.add(key, key.target);
    const fill = new THREE.DirectionalLight(0xdfe6e6, 0.7);
    fill.position.set(8, 5, 8);
    fill.target.position.set(0, 1, -6);
    world.add(fill, fill.target);
    const rim = new THREE.SpotLight(0xffffff, 40, 40, THREE.MathUtils.degToRad(28), 0.8, 1.2);
    rim.position.set(9, 8, -3);
    rim.target.position.set(0.5, 0.5, -8);
    world.add(rim, rim.target);
    scene.add(new THREE.HemisphereLight(0x8f9a9a, 0x050606, 0.3));

    /* ---------------- shared materials ---------------- */
    const floorSet = floorMaps(quality.surfaceMap);
    const floorColor = tex(floorSet.color, true, true);
    const floorRough = tex(floorSet.rough, false, true);
    const floorBump = tex(floorSet.bump, false, true);
    const floorRepeatY = 110 / TILE;
    [floorColor, floorRough, floorBump].forEach((t) => t.repeat.set(46 / TILE, floorRepeatY));
    const floorMaterial = own(new THREE.MeshPhysicalMaterial({
      color: 0x9aa0a2, map: floorColor, metalness: 0.7, roughness: 1, roughnessMap: floorRough,
      bumpMap: floorBump, bumpScale: 0.6, clearcoat: 0.6, clearcoatRoughness: 0.14, envMapIntensity: 0.7,
      transparent: true, opacity: 0.8, depthWrite: true,
    }));

    const pathSet = pathMaps(quality.surfaceMap);
    const pathRough = tex(pathSet.rough, false, true);
    const pathBump = tex(pathSet.bump, false, true);
    [pathRough, pathBump].forEach((t) => t.repeat.set(1, 96 / PANEL));
    const pathMaterial = own(new THREE.MeshPhysicalMaterial({
      color: 0x9aa2a3, metalness: 1, roughness: 1, roughnessMap: pathRough, bumpMap: pathBump, bumpScale: 0.9,
      anisotropy: 0.5, envMapIntensity: 1.25,
    }));
    const plinthMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0x2a3032, metalness: 0.8, roughness: 0.4, envMapIntensity: 0.9 }));
    const kerbMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0xb0b7b8, metalness: 1, roughness: 0.24, envMapIntensity: 1.0 }));
    const darkMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0x12171a, metalness: 0.7, roughness: 0.3, clearcoat: 0.4, clearcoatRoughness: 0.2, envMapIntensity: 0.9 }));
    const lightMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0xb9c0c1, metalness: 1, roughness: 0.2, envMapIntensity: 1.1 }));
    const contactMap = tex(contactTexture(), true);
    const contactMaterial = own(new THREE.MeshBasicMaterial({ map: contactMap, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, fog: false, color: 0x000000 }));

    /* ---------------- coin ---------------- */
    const maps = coinMaps(quality.coinMap);
    const normalMap = tex(maps.normal, false);
    const roughMap = tex(maps.rough, false);
    const faceMaterial = own(new THREE.MeshPhysicalMaterial({
      color: 0xffffff, metalness: 1, roughness: 1, roughnessMap: roughMap, normalMap, normalScale: new THREE.Vector2(1.5, 1.5),
      anisotropy: 0.35, clearcoat: 0.08, clearcoatRoughness: 0.3, envMapIntensity: 1.8,
    }));
    const rimMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0xcfd5d5, metalness: 1, roughness: 0.22, envMapIntensity: 1.6 }));
    const bevelMaterial = own(new THREE.MeshPhysicalMaterial({ color: 0xf2f5f5, metalness: 1, roughness: 0.12, envMapIntensity: 1.8 }));

    const seg = quality.coinSegments;
    const reeds = quality.name === "low" ? 84 : 112;
    const edgeGeo = own(new THREE.CylinderGeometry(COIN_R, COIN_R, COIN_T - 0.12, seg, 1, true));
    {
      const p = edgeGeo.attributes.position;
      for (let i = 0; i < p.count; i += 1) {
        const x = p.getX(i), z = p.getZ(i);
        const a = Math.atan2(z, x);
        const w = Math.pow(0.5 + 0.5 * Math.cos(a * reeds), 0.7);
        const rr = COIN_R - 0.016 * (1 - w);
        p.setXYZ(i, Math.cos(a) * rr, p.getY(i), Math.sin(a) * rr);
      }
      edgeGeo.computeVertexNormals();
      edgeGeo.rotateX(Math.PI / 2);
    }
    const chamferGeo = own(new THREE.CylinderGeometry(FACE_R, COIN_R - 0.006, 0.06, seg, 1, true));
    chamferGeo.rotateX(Math.PI / 2);
    chamferGeo.translate(0, 0, COIN_T / 2 - 0.03);
    const faceGeo = own(new THREE.CircleGeometry(FACE_R, seg));
    const lipGeo = own(new THREE.TorusGeometry(FACE_R, 0.012, 8, seg));

    const coin = new THREE.Group();
    coin.add(new THREE.Mesh(edgeGeo, rimMaterial));
    [1, -1].forEach((dir) => {
      const side = new THREE.Group();
      if (dir < 0) side.rotation.y = Math.PI;
      const face = new THREE.Mesh(faceGeo, faceMaterial); face.position.z = COIN_T / 2; side.add(face);
      side.add(new THREE.Mesh(chamferGeo, bevelMaterial));
      const lip = new THREE.Mesh(lipGeo, bevelMaterial); lip.position.z = COIN_T / 2; side.add(lip);
      coin.add(side);
    });
    [faceMaterial, rimMaterial, bevelMaterial].forEach((m) => { m.shadowSide = THREE.DoubleSide; });
    coin.rotation.y = Math.PI / 2;
    coin.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh) m.castShadow = true; });

    [floorMaterial, pathMaterial, plinthMaterial, kerbMaterial, darkMaterial, lightMaterial, faceMaterial, rimMaterial, bevelMaterial].forEach((m) => { m.envMap = envMap; });

    /* ---------------- stage (built twice: real + mirrored reflection) ---------------- */
    const box = (w: number, h: number, d: number) => own(new RoundedBoxGeometry(w, h, d, 2, 0.028));
    const geo = {
      plinth: box(PATH_W + 0.55, 0.14, 110),
      slab: box(PATH_W, 0.14, 110),
      kerb: box(1.7, 0.5, 110),
      trim: box(0.09, 0.05, 110),
      floor: own(new THREE.PlaneGeometry(46, 110)),
      contact: own(new THREE.PlaneGeometry(1.5, 3.4)),
    };
    const variants = [
      { a: [5.4, 0.9, 5.6], b: [2.8, 2.4, 2.4], c: [1.8, 4.7, 1.8], d: [2.2, 1.3, 2.4] },
      { a: [5.4, 0.9, 5.6], b: [2.8, 3.4, 2.4], c: [1.8, 3.6, 1.8], d: [2.2, 0.8, 2.4] },
      { a: [5.4, 0.9, 5.6], b: [2.8, 1.5, 2.4], c: [1.8, 5.6, 1.8], d: [2.2, 1.9, 2.4] },
    ];
    const blocks = variants.map((v) => ({
      a: box(v.a[0], v.a[1], v.a[2]), b: box(v.b[0], v.b[1], v.b[2]), c: box(v.c[0], v.c[1], v.c[2]), d: box(v.d[0], v.d[1], v.d[2]), v,
    }));

    const buildStage = (primary: boolean) => {
      const group = new THREE.Group();
      const add = (g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, parent: THREE.Object3D = group) => {
        const mesh = new THREE.Mesh(g, m);
        mesh.position.set(x, y, z);
        if (primary) { mesh.castShadow = true; mesh.receiveShadow = true; }
        parent.add(mesh);
        return mesh;
      };
      const floor = new THREE.Mesh(geo.floor, floorMaterial);
      floor.rotation.x = -Math.PI / 2; floor.position.set(0, FLOOR_Y, -26);
      floor.receiveShadow = primary;
      if (primary) group.add(floor);
      add(geo.plinth, plinthMaterial, 0, FLOOR_Y + 0.07, -26);
      add(geo.slab, pathMaterial, 0, PATH_TOP - 0.07, -26);
      [-1, 1].forEach((s) => add(geo.trim, kerbMaterial, s * (PATH_W / 2 - 0.05), PATH_TOP + 0.015, -26));
      add(geo.kerb, kerbMaterial, PATH_W / 2 + 0.55 + 0.85 - 0.02, FLOOR_Y + 0.25, -26);
      const segments: THREE.Group[] = [];
      for (let i = 0; i < SEG_COUNT; i += 1) {
        const s = new THREE.Group();
        const { a, b, c, d, v } = blocks[i % blocks.length];
        const x0 = 6.9;
        add(a, darkMaterial, x0 + 1.2, FLOOR_Y + v.a[1] / 2, 0, s);
        add(b, lightMaterial, x0 - 0.2, FLOOR_Y + v.a[1] + v.b[1] / 2, -1.2, s);
        add(c, darkMaterial, x0 + 2.4, FLOOR_Y + v.a[1] + v.c[1] / 2, -1.5, s);
        add(d, lightMaterial, x0 - 2.4, FLOOR_Y + v.d[1] / 2, 1.5, s);
        group.add(s);
        segments.push(s);
      }
      return { group, segments };
    };

    const main = buildStage(true);
    world.add(main.group);
    const mirror = quality.reflection ? buildStage(false) : null;
    if (mirror) {
      const mirrorRoot = new THREE.Group();
      mirrorRoot.position.y = FLOOR_Y * 2;
      mirrorRoot.scale.y = -1;
      mirrorRoot.add(mirror.group);
      world.add(mirrorRoot);
    }

    const spin = new THREE.Group();
    spin.add(coin);
    spin.position.set(0, PATH_TOP + COIN_R, 0);
    world.add(spin);
    let mirrorSpin: THREE.Group | null = null;
    if (mirror) {
      mirrorSpin = new THREE.Group();
      mirrorSpin.add(coin.clone());
      mirrorSpin.position.copy(spin.position);
      mirror.group.add(mirrorSpin);
    }
    const contact = new THREE.Mesh(geo.contact, contactMaterial);
    contact.rotation.x = -Math.PI / 2;
    contact.rotation.z = Math.PI / 2;
    contact.position.set(0, PATH_TOP + 0.004, 0);
    world.add(contact);

    /* ---------------- camera ---------------- */
    const camPos = new THREE.Vector3();
    const camTarget = new THREE.Vector3();
    const resize = () => {
      const bounds = mount.getBoundingClientRect();
      const w = Math.max(1, Math.round(bounds.width));
      const h = Math.max(1, Math.round(bounds.height));
      renderer.setSize(w, h, false);
      renderer.setViewport(0, 0, w, h);
      renderer.setScissorTest(false);
      camera.aspect = w / h;
      const narrow = camera.aspect < 0.95;
      const compact = camera.aspect < 1.3;
      camPos.set(narrow ? -1.2 : -1.8, narrow ? 5.6 : 4.4, narrow ? 15 : compact ? 12.8 : 11);
      camTarget.set(narrow ? 0.3 : 3.4, 1.3, -3);
      camera.fov = narrow ? 40 : 32;
      camera.setViewOffset(w, h, narrow ? 0 : -w * 0.22, narrow ? -h * 0.1 : 0, w, h);
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(mount);

    const pointer = new THREE.Vector2();
    const eased = new THREE.Vector2();
    const onMove = (e: PointerEvent) => pointer.set(e.clientX / window.innerWidth * 2 - 1, e.clientY / window.innerHeight * 2 - 1);
    if (!mobile && !reducedMotion) window.addEventListener("pointermove", onMove, { passive: true });

    /* ---------------- animation: ground scrolls at the coin's rolling speed ---------------- */
    const clock = new THREE.Clock();
    let raf: number | null = null;
    let travel = 0;
    let running = true;
    let frameCount = 0;
    let frameTimeTotal = 0;
    let shadowRendered = false;
    const updateSegments = (segments: THREE.Group[]) => {
      const span = SEG_COUNT * SEG_PERIOD;
      for (let i = 0; i < segments.length; i += 1) {
        segments[i].position.z = SEG_FAR + ((i * SEG_PERIOD + travel) % span);
      }
    };
    const apply = () => {
      const t1 = (travel / PANEL) % 1;
      pathRough.offset.y = t1; pathBump.offset.y = t1;
      const t2 = (travel / TILE) % 1;
      floorColor.offset.y = t2; floorRough.offset.y = t2; floorBump.offset.y = t2;
      updateSegments(main.segments);
      if (mirror) updateSegments(mirror.segments);
      const rot = -travel / COIN_R;
      spin.rotation.x = rot;
      if (mirrorSpin) mirrorSpin.rotation.x = rot;
    };
    const render = () => {
      if (quality.shadows && !shadowRendered) {
        renderer.shadowMap.needsUpdate = true;
      }
      renderer.render(scene, camera);
      if (quality.shadows && !shadowRendered) {
        renderer.shadowMap.autoUpdate = false;
        shadowRendered = true;
      }
    };
    const lowerPixelRatio = () => {
      const next = Math.max(0.85, Math.round((pixelRatio - 0.15) * 20) / 20);
      if (next === pixelRatio) return;
      pixelRatio = next;
      renderer.setPixelRatio(pixelRatio);
      resize();
    };
    const frame = () => {
      raf = null;
      if (!running || document.hidden || reducedMotion) return;
      const dt = Math.min(clock.getDelta(), 0.05);
      travel += ROLL_SPEED * dt;
      apply();
      const px = mobile || reducedMotion ? 0 : 1;
      eased.lerp(pointer, 1 - Math.exp(-dt * CAMERA_SMOOTHING));
      camera.position.set(camPos.x + eased.x * 0.3 * px, camPos.y - eased.y * 0.16 * px, camPos.z);
      camera.lookAt(camTarget);
      render();
      frameTimeTotal += dt;
      frameCount += 1;
      if (frameCount === 90) {
        // RAF cadence is an inexpensive proxy for frame pressure. Scale only down,
        // never above the profile selected for this device.
        if (frameTimeTotal / frameCount > 0.021) lowerPixelRatio();
        frameCount = 0;
        frameTimeTotal = 0;
      }
      raf = requestAnimationFrame(frame);
    };
    const resume = () => {
      if (!running || document.hidden || reducedMotion || raf !== null) return;
      clock.getDelta();
      raf = requestAnimationFrame(frame);
    };
    const pause = () => {
      if (raf !== null) cancelAnimationFrame(raf);
      raf = null;
      clock.getDelta();
      render();
    };
    apply();
    render();
    resume();
    const io = new IntersectionObserver(([e]) => {
      running = e.isIntersecting;
      if (running) resume(); else pause();
    }, { threshold: 0.01 });
    io.observe(mount);
    const onVisibilityChange = () => {
      if (document.hidden) pause(); else resume();
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      pause();
      io.disconnect();
      ro.disconnect();
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener("pointermove", onMove);
      disposables.forEach((r) => r.dispose());
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    };
  }, []);

  return <div ref={host} className={className} aria-hidden="true" />;
}
