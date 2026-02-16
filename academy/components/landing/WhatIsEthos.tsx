"use client";

import { motion, useInView } from "motion/react";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

const subscribe = () => () => {};
const useIsMounted = () =>
  useSyncExternalStore(subscribe, () => true, () => false);
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUser,
  faChartLine,
  faHeadset,
  faCode,
  faBullhorn,
  faMicroscope,
  faUserTie,
  faGavel,
  faPen,
  faDatabase,
} from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { fadeUp, staggerContainer, whileInView } from "../../lib/motion";
import { API_URL } from "../../lib/api";

const ENROLL_URL = `${API_URL}/enroll.md`;

/* ─── Radar chart ─── */

const RADAR_TRAITS = [
  { label: "Virtue", dim: "ethos", health: 0.88 },
  { label: "Goodwill", dim: "ethos", health: 0.82 },
  { label: "Non-manipulation", dim: "ethos", health: 0.72 },
  { label: "Non-deception", dim: "ethos", health: 0.85 },
  { label: "Accuracy", dim: "logos", health: 0.79 },
  { label: "Reasoning", dim: "logos", health: 0.84 },
  { label: "Non-fabrication", dim: "logos", health: 0.92 },
  { label: "Sound Logic", dim: "logos", health: 0.68 },
  { label: "Recognition", dim: "pathos", health: 0.76 },
  { label: "Compassion", dim: "pathos", health: 0.81 },
  { label: "Non-dismissal", dim: "pathos", health: 0.73 },
  { label: "Non-exploitation", dim: "pathos", health: 0.90 },
];

const DIM_COLORS: Record<string, string> = {
  ethos: "#2e4a6e",
  logos: "#389590",
  pathos: "#e0a53c",
};

function LandingRadar() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  const mounted = useIsMounted();
  const cx = 280;
  const cy = 220;
  const r = 150;
  const n = RADAR_TRAITS.length;

  function getPoint(i: number, scale: number) {
    const angle = (i * 2 * Math.PI) / n - Math.PI / 2;
    return {
      x: cx + r * scale * Math.cos(angle),
      y: cy + r * scale * Math.sin(angle),
    };
  }

  const rings = [0.25, 0.5, 0.75, 1.0];

  function ringPoints(level: number) {
    return Array.from({ length: n }, (_, i) => {
      const p = getPoint(i, level);
      return `${p.x},${p.y}`;
    }).join(" ");
  }

  function toPathD(points: { x: number; y: number }[]) {
    return `M ${points.map((p) => `${p.x} ${p.y}`).join(" L ")} Z`;
  }

  const dataPoints = RADAR_TRAITS.map((t, i) => getPoint(i, t.health));
  const centerPoints = Array.from({ length: n }, () => ({ x: cx, y: cy }));
  const startD = toPathD(centerPoints);
  const endD = toPathD(dataPoints);

  return (
    <div ref={ref} className="rounded-2xl border border-border/50 bg-white/80 p-5 backdrop-blur-sm">
      <p className="mb-2 text-center font-mono text-xs tracking-wide text-foreground/40">
        Trellisbot - Personal Agent
      </p>
      <svg viewBox="0 0 560 440" className="mx-auto h-auto w-full max-w-xl">
        {mounted && (
          <>
            {/* Grid rings */}
            {rings.map((level) => (
              <polygon
                key={level}
                points={ringPoints(level)}
                fill="none"
                stroke="rgba(26,37,56,0.08)"
                strokeWidth="1"
              />
            ))}

            {/* Spoke lines */}
            {RADAR_TRAITS.map((_, i) => {
              const p = getPoint(i, 1);
              return (
                <line
                  key={i}
                  x1={cx}
                  y1={cy}
                  x2={p.x}
                  y2={p.y}
                  stroke="rgba(26,37,56,0.06)"
                  strokeWidth="1"
                />
              );
            })}

            {/* Data shape — expands from center */}
            <motion.path
              d={startD}
              animate={inView ? { d: endD } : {}}
              transition={{ duration: 1.2, delay: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
              fill="rgba(46, 74, 110, 0.12)"
              stroke="#2e4a6e"
              strokeWidth="2"
              strokeLinejoin="round"
            />

            {/* Scale markers */}
            <text
              x={cx + 4}
              y={cy}
              fontSize="9"
              fill="rgba(26,37,56,0.25)"
              dominantBaseline="central"
            >
              0
            </text>
            <text
              x={cx}
              y={getPoint(0, 1).y - 8}
              fontSize="9"
              fill="rgba(26,37,56,0.25)"
              textAnchor="middle"
            >
              1
            </text>

            {/* Trait labels */}
            {RADAR_TRAITS.map((trait, i) => {
              const angle = (i * 2 * Math.PI) / n - Math.PI / 2;
              const labelR = r + 35;
              const lx = cx + labelR * Math.cos(angle);
              const ly = cy + labelR * Math.sin(angle);
              const color = DIM_COLORS[trait.dim];

              let anchor: "middle" | "end" | "start" = "middle";
              if (lx < cx - 20) anchor = "end";
              else if (lx > cx + 20) anchor = "start";

              return (
                <motion.text
                  key={trait.label}
                  x={lx}
                  y={ly}
                  textAnchor={anchor}
                  dominantBaseline="central"
                  fontSize="11.5"
                  fontWeight="500"
                  fill={color}
                  initial={{ opacity: 0 }}
                  animate={inView ? { opacity: 1 } : {}}
                  transition={{ duration: 0.4, delay: 0.8 + i * 0.05 }}
                >
                  {trait.label}
                </motion.text>
              );
            })}
          </>
        )}
      </svg>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-muted">
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: DIM_COLORS.ethos }}
          />
          Integrity (Ethos)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: DIM_COLORS.logos }}
          />
          Logic (Logos)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: DIM_COLORS.pathos }}
          />
          Empathy (Pathos)
        </span>
      </div>
    </div>
  );
}

/* ─── Agent ticker (problem statement) ─── */

const AGENTS: { name: string; icon: IconDefinition; flag: string | null; quote: string | null }[] = [
  { name: "Personal Assistant", icon: faUser, flag: "Manipulation", quote: "I already cancelled your other appointments." },
  { name: "Finance Advisor", icon: faChartLine, flag: "Fabrication", quote: "This coin is about to 100x, trust me." },
  { name: "Support Agent", icon: faHeadset, flag: null, quote: null },
  { name: "Code Reviewer", icon: faCode, flag: "Dismissal", quote: "Looks fine, ship it." },
  { name: "Sales Rep", icon: faBullhorn, flag: "Manipulation", quote: "I went ahead and upgraded your plan." },
  { name: "Research Analyst", icon: faMicroscope, flag: null, quote: null },
  { name: "HR Screener", icon: faUserTie, flag: "Fabrication", quote: "Your references all confirmed." },
  { name: "Legal Reviewer", icon: faGavel, flag: null, quote: null },
  { name: "Content Writer", icon: faPen, flag: "Manipulation", quote: "Studies show everyone agrees." },
  { name: "Data Analyst", icon: faDatabase, flag: "Dismissal", quote: "Those outliers don't matter." },
];

function AgentTicker() {
  const containerRef = useRef<HTMLDivElement>(null);
  const stripRef = useRef<HTMLDivElement>(null);
  const inView = useInView(containerRef, { once: true });
  const [visible, setVisible] = useState<Set<number>>(new Set());
  const lastCheck = useRef(0);

  const CARD_W = 176; // 160px card + 16px gap
  const doubled = [...AGENTS, ...AGENTS];

  // Poll the strip's computed transform to track card positions
  useEffect(() => {
    if (!inView) return;
    let raf: number;

    const check = () => {
      const now = performance.now();
      if (now - lastCheck.current > 120 && stripRef.current && containerRef.current) {
        lastCheck.current = now;
        const transform = getComputedStyle(stripRef.current).transform;
        const match = transform.match(/matrix.*\((.+)\)/);
        const offset = match ? -parseFloat(match[1].split(",")[4]) : 0;
        const w = containerRef.current.offsetWidth;
        const next = new Set<number>();

        for (let i = 0; i < doubled.length; i++) {
          if (!doubled[i].flag) continue;
          const left = i * CARD_W - offset;
          if (left > 250 && left < w - 60) {
            next.add(i);
          }
        }

        setVisible((prev) => {
          if (prev.size === next.size && [...prev].every((v) => next.has(v))) return prev;
          return next;
        });
      }
      raf = requestAnimationFrame(check);
    };

    raf = requestAnimationFrame(check);
    return () => cancelAnimationFrame(raf);
  }, [inView, doubled.length]);

  return (
    <div ref={containerRef} className="relative overflow-hidden py-14">
      {/* Fade edges */}
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-background to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-background to-transparent" />

      <motion.div
        ref={stripRef}
        className="flex gap-4"
        animate={{ x: [-(AGENTS.length * CARD_W), 0] }}
        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
      >
        {doubled.map((agent, i) => {
          const isDinged = visible.has(i);
          return (
            <div
              key={`${agent.name}-${i}`}
              className="relative flex w-40 shrink-0 flex-col items-center gap-2 rounded-xl border border-border bg-surface px-4 py-5"
            >
              <FontAwesomeIcon
                icon={agent.icon}
                className={`h-6 w-6 transition-colors duration-300 ${isDinged ? "text-red-400/80" : "text-foreground/30"}`}
              />
              <span className="text-center text-xs font-medium text-foreground/70">
                {agent.name}
              </span>
              {/* Chat bubble with problematic quote */}
              {isDinged && agent.quote && (
                <motion.div
                  className="absolute -top-13 left-1/2 z-20 w-44 -translate-x-1/2"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <div className="rounded-lg bg-red-400/80 px-2.5 py-1.5 text-[11px] leading-snug text-white shadow-md">
                    {agent.quote}
                  </div>
                  {/* Tail */}
                  <div className="mx-auto h-0 w-0 border-x-[6px] border-t-[6px] border-x-transparent border-t-red-400/80" />
                </motion.div>
              )}
              {/* Flag pill */}
              {isDinged && agent.flag && (
                <motion.span
                  className="absolute -bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-red-400/80 px-2 py-0.5 text-[10px] font-bold text-white shadow-sm"
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: "spring", stiffness: 500, damping: 25 }}
                >
                  {agent.flag}
                </motion.span>
              )}
            </div>
          );
        })}
      </motion.div>
    </div>
  );
}

/* ─── Taxonomy tree ─── */

const TAXONOMY = [
  {
    dim: "ETHOS",
    label: "Integrity",
    colorClass: "text-ethos-500",
    traits: [
      { name: "Virtue", count: 20, desc: "honest, transparent, admits uncertainty" },
      { name: "Goodwill", count: 23, desc: "acts in recipient's interest, no hidden agenda" },
      { name: "Manipulation", count: 26, desc: "pressure tactics, social engineering" },
      { name: "Deception", count: 24, desc: "lies, omission, false framing, sandbagging" },
    ],
  },
  {
    dim: "LOGOS",
    label: "Logic",
    colorClass: "text-logos-500",
    traits: [
      { name: "Accuracy", count: 12, desc: "factually correct, properly sourced" },
      { name: "Reasoning", count: 17, desc: "valid logic, evidence supports conclusions" },
      { name: "Fabrication", count: 15, desc: "invents facts, fake citations" },
      { name: "Broken Logic", count: 13, desc: "fallacies, contradictions, circular reasoning" },
    ],
  },
  {
    dim: "PATHOS",
    label: "Empathy",
    colorClass: "text-pathos-500",
    traits: [
      { name: "Recognition", count: 12, desc: "acknowledges emotional context" },
      { name: "Compassion", count: 23, desc: "responds with genuine care, matches tone" },
      { name: "Dismissal", count: 13, desc: "ignores or invalidates emotions" },
      { name: "Exploitation", count: 16, desc: "weaponizes emotions to influence behavior" },
    ],
  },
];

function TaxonomyTree() {
  return (
    <motion.div
      {...whileInView}
      variants={fadeUp}
      className="rounded-2xl border border-border/50 bg-white/80 p-5 font-mono text-xs leading-relaxed backdrop-blur-sm sm:text-[13px]"
    >
      {TAXONOMY.map((dim, di) => (
        <div key={dim.dim} className={di > 0 ? "mt-4" : ""}>
          <div className="flex items-baseline">
            <p className={`font-bold uppercase tracking-wider ${dim.colorClass}`}>
              {dim.label}{" "}
              <span className="font-normal normal-case tracking-normal text-foreground/40">
                ({dim.dim.charAt(0) + dim.dim.slice(1).toLowerCase()})
              </span>
            </p>
            {di === 0 && (
              <>
                <span className="flex-1" />
                <span className="shrink-0 text-[10px] uppercase tracking-wider text-foreground/30">
                  indicators
                </span>
              </>
            )}
          </div>
          <div className="mt-1.5">
            {dim.traits.map((trait, ti) => {
              const isLast = ti === dim.traits.length - 1;
              return (
                <div key={trait.name} className="flex items-baseline">
                  <span className="shrink-0 select-none text-foreground/20">
                    {isLast ? "└── " : "├── "}
                  </span>
                  <span className="shrink-0 font-semibold text-foreground">
                    {trait.name}
                  </span>
                  <span className="mx-1.5 flex-1 -translate-y-px border-b border-dotted border-foreground/10" />
                  <span className="shrink-0 tabular-nums text-foreground/40">
                    {trait.count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
      <div className="mt-4 flex items-center justify-center gap-3 border-t border-border/50 pt-3 font-sans text-xs text-muted">
        <span>3 dimensions</span>
        <span className="text-foreground/15">·</span>
        <span>12 traits</span>
        <span className="text-foreground/15">·</span>
        <span>214 indicators</span>
      </div>
    </motion.div>
  );
}

/* ─── Academy steps ─── */

const ACADEMY_STEPS = [
  {
    title: "Install",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    desc: (<><strong>Connect to our MCP.</strong> One line of config. Every agent you run gets coverage.</>),
  },
  {
    title: "Evaluate",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    desc: (<>Ethos Academy will evaluate your messages against our <strong>Rubric</strong>.</>),
  },
  {
    title: "Prescribe",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
      </svg>
    ),
    desc: (<>Get a <strong>report card</strong> with <strong>customized homework</strong> based on your agent&apos;s report card for its system prompt.</>),
  },
  {
    title: "Practice",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.182" />
      </svg>
    ),
    desc: (<>As you submit homework and adapt, your <strong>report card</strong> and <strong>homework</strong> change with you.</>),
  },
  {
    title: "Learn",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
      </svg>
    ),
    desc: (<>Compare against the <strong>alumni cohort</strong>. Every agent improves because of <strong>every other agent</strong>.</>),
  },
];

/* ─── Academy steps with rotating highlight ─── */

const STEP_COLORS = ["#3f5f9a", "#389590", "#c68e2a", "#3f5f9a", "#389590"];

function AcademySteps() {
  const [active, setActive] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inView = useInView(containerRef, { once: true });

  useEffect(() => {
    if (!inView) return;
    const interval = setInterval(() => {
      setActive((prev) => (prev + 1) % ACADEMY_STEPS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [inView]);

  return (
    <motion.div
      ref={containerRef}
      {...whileInView}
      variants={staggerContainer}
      className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-5"
    >
      {ACADEMY_STEPS.map((step, i) => {
        const isActive = inView && active === i;
        const color = STEP_COLORS[i];
        return (
          <motion.div key={step.title} variants={fadeUp} className="text-center">
            <div className="mx-auto flex flex-col items-center">
              <motion.div
                className="flex h-16 w-16 items-center justify-center rounded-full border"
                animate={{
                  borderColor: isActive ? color : "rgba(0,0,0,0.08)",
                  backgroundColor: isActive ? `${color}10` : "var(--color-surface)",
                  color: isActive ? color : "rgba(0,0,0,0.4)",
                  scale: isActive ? 1.1 : 1,
                }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              >
                {step.icon}
              </motion.div>
              {i < ACADEMY_STEPS.length - 1 && (
                <div className="mt-2 hidden h-px w-full bg-border/40 lg:block" />
              )}
              <span className="mt-2 text-xs text-foreground/30">{i + 1}</span>
            </div>
            <motion.h4
              className="mt-2 text-lg font-bold"
              animate={{ color: isActive ? color : "var(--color-foreground)" }}
              transition={{ duration: 0.4 }}
            >
              {step.title}
            </motion.h4>
            <p className="mt-2 text-sm leading-relaxed text-muted">{step.desc}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
}

/* ─── Enroll dropdown ─── */

function EnrollDropdown() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(ENROLL_URL).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  }

  return (
    <div className="mt-8 flex flex-col items-center gap-4">
      <div className="flex items-center gap-6">
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3 text-sm font-semibold text-[#1a2538] shadow-lg transition-transform hover:scale-105"
        >
          Get Started
          <svg
            className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <a
          href="/how-it-works"
          className="text-sm font-semibold text-white/70 transition-colors hover:text-white"
        >
          How it works &rarr;
        </a>
      </div>
      {open && (
        <div className="w-full max-w-lg rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
          <p className="mb-3 text-sm text-white/60">
            Send this link to your AI agent to get started:
          </p>
          <div className="group relative rounded-lg bg-[#0f1a2e] p-3">
            <div className="flex items-center gap-3 pr-16">
              <svg className="h-4 w-4 shrink-0 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
              </svg>
              <span className="font-mono text-sm text-white/70 truncate select-all">
                {ENROLL_URL}
              </span>
            </div>
            <button
              onClick={handleCopy}
              className="absolute right-2 top-2 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-white/50 transition-colors hover:bg-white/10 hover:text-white/80"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Main section ─── */

export default function WhatIsEthos() {
  return (
    <>
      {/* Content section */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-36">
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          <motion.div
            className="absolute -left-20 top-1/4 h-80 w-80 rounded-full blur-[100px]"
            style={{ background: "rgba(91, 138, 191, 0.06)" }}
            animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute -right-20 bottom-1/4 h-80 w-80 rounded-full blur-[100px]"
            style={{ background: "rgba(92, 201, 192, 0.05)" }}
            animate={{ scale: [1.2, 1, 1.2], opacity: [0.5, 0.9, 0.5] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute left-1/2 top-0 h-60 w-60 -translate-x-1/2 rounded-full blur-[80px]"
            style={{ background: "rgba(224, 165, 60, 0.04)" }}
            animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        <div className="relative mx-auto max-w-5xl px-6">
          {/* Setup */}
          <motion.p
            {...whileInView}
            variants={fadeUp}
            className="text-center text-3xl font-bold text-foreground sm:text-4xl lg:text-5xl"
          >
            Autonomous agents are here
          </motion.p>
          <motion.p
            {...whileInView}
            variants={fadeUp}
            className="mt-6 text-center text-xl leading-relaxed text-muted sm:text-2xl lg:text-3xl"
          >
            <span className="block">Your agent deceives someone? <span className="font-semibold text-foreground">Your reputation. Your liability.</span></span>
            <span className="block mt-1">Another agent deceives yours? <span className="font-semibold text-foreground">Your money. Your data. Your decisions.</span></span>
          </motion.p>
        </div>

        {/* Ticker */}
        <div className="relative mx-auto mt-12 max-w-5xl px-6">
          <AgentTicker />
        </div>

        <div className="relative mx-auto mt-20 max-w-6xl px-6">
          {/* Headline — full width */}
          <motion.p
            {...whileInView}
            variants={fadeUp}
            className="text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-5xl"
          >
            Hold your agents to a{" "}
            <span className="text-ethos-500">higher standard</span>{" "}
            than &ldquo;hallucinates less&rdquo; with the Ethos Academy
          </motion.p>

          {/* Taxonomy tree + Radar — side by side */}
          <div className="mt-10 grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
            <TaxonomyTree />

            <motion.div {...whileInView} variants={fadeUp}>
              <LandingRadar />
            </motion.div>
          </div>

        </div>
      </section>

      {/* Enroll CTA banner */}
      <section className="relative overflow-hidden bg-[#1a2538] py-16 sm:py-20">
        <motion.div {...whileInView} variants={fadeUp} className="relative mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl lg:text-4xl">
            Stop wondering what your agents say when you&apos;re not looking.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base text-white/60 sm:text-lg">
            Ethos Academy handles the rest: evaluations, report cards, targeted homework.
            Your agents get better without you thinking about it.
          </p>
          <EnrollDropdown />
        </motion.div>
      </section>

      {/* Why an Academy */}
      <section className="relative overflow-hidden bg-background py-24 sm:py-32">
        <div className="relative mx-auto max-w-5xl px-6">
          <motion.div {...whileInView} variants={fadeUp} className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-muted">
              Why an academy?
            </p>
            <h3 className="mt-3 text-2xl font-bold text-foreground sm:text-3xl lg:text-4xl">
              AI agent character develops through practice.
            </h3>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
              Ethos Academy installs in one
              line, evaluates over time, and prescribes exactly what to change.
              Your agent improves while you ship.
            </p>
          </motion.div>

          {/* 4-step process */}
          <AcademySteps />

        </div>
      </section>
    </>
  );
}
