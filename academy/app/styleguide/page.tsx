export default function StyleguidePage() {
  return (
    <div className="space-y-16 pb-20">
      {/* ─── Hero ─── */}
      <section className="relative -mx-6 -mt-8 overflow-hidden">
        <img
          src="/academy-banner.jpeg"
          alt="School of Athens — humans and AI"
          className="h-[28rem] w-full object-cover object-[center_30%]"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 px-6 pb-8">
          <h1 className="text-3xl font-bold tracking-tight">Styleguide</h1>
          <p className="mt-1 text-sm text-muted">
            Design system for Ethos Academy — inspired by the School of Athens.
          </p>
        </div>
      </section>

      {/* ─── Design Philosophy ─── */}
      <section className="space-y-3">
        <SectionHeader
          title="Philosophy"
          description="Warm marble base. Colorful data. Glass surfaces."
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <PhilosophyCard
            title="Simple base"
            body="Warm cream background from Renaissance stone. White surfaces. Minimal borders. The base stays quiet so data can be loud."
          />
          <PhilosophyCard
            title="Colorful dimensions"
            body="Three rich color scales — terracotta rose, cerulean blue, amber gold — each with full positive-to-negative range for data visualization."
          />
          <PhilosophyCard
            title="Glass & gradients"
            body="Frosted glass surfaces with subtle backdrop blur. Soft gradients that add depth without distraction."
          />
        </div>
      </section>

      {/* ─── Base Palette ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Base Palette"
          description="The foundation. Warm neutrals from marble and stone."
        />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
          <Swatch name="Background" color="var(--background)" hex="#faf7f2" />
          <Swatch name="Surface" color="var(--surface)" hex="#ffffff" border />
          <Swatch name="Foreground" color="var(--foreground)" hex="#2a2018" dark />
          <Swatch name="Muted" color="var(--muted)" hex="#8b7e74" dark />
          <Swatch name="Border" color="var(--border)" hex="#e6ddd2" />
          <Swatch name="Action" color="var(--action)" hex="#4a90a4" dark />
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="flex gap-2">
            <Swatch name="Action" color="var(--action)" hex="#4a90a4" dark compact />
            <Swatch name="Action Light" color="var(--action-light)" hex="#e8f4f8" compact />
            <Swatch name="Action Hover" color="var(--action-hover)" hex="#3d7a8c" dark compact />
          </div>
        </div>
      </section>

      {/* ─── Dimension Colors ─── */}
      <section className="space-y-8">
        <SectionHeader
          title="Dimension Colors"
          description="Three color families for ethos, logos, and pathos. Each spans positive (light) to negative (dark)."
        />

        <DimensionScale
          name="Ethos"
          subtitle="Character & Virtue — Terracotta Rose"
          description="From Plato's robes. Positive traits (virtue, goodwill) use lighter values. Negative traits (manipulation, deception) use darker values."
          cssPrefix="ethos"
          hexes={[
            "#fef2f0", "#fde3df", "#fbc7bf", "#f8a292", "#f07a67",
            "#dc5845", "#c4422f", "#a53425", "#882d22", "#6b2620",
          ]}
        />

        <DimensionScale
          name="Logos"
          subtitle="Logic & Reason — Cerulean Blue"
          description="From the sky through the arches and Aristotle's robe. Positive traits (accuracy, reasoning) glow bright. Negative traits (fabrication, broken logic) go deep."
          cssPrefix="logos"
          hexes={[
            "#f0f5ff", "#dce8fc", "#bad0fa", "#8db2f5", "#6b96ec",
            "#4a78d4", "#365dba", "#2a4a9a", "#253d7d", "#1e3060",
          ]}
        />

        <DimensionScale
          name="Pathos"
          subtitle="Emotion & Empathy — Amber Gold"
          description="From the golden robes and warm light. Positive traits (recognition, compassion) shine warm. Negative traits (dismissal, exploitation) darken to umber."
          cssPrefix="pathos"
          hexes={[
            "#fef8eb", "#feefcc", "#fde099", "#fbc862", "#f0ae3a",
            "#d89420", "#b87818", "#965e14", "#7a4a12", "#603810",
          ]}
        />
      </section>

      {/* ─── Alignment Status ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Alignment Status"
          description="Four states for agent trust classification."
        />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatusSwatch name="Aligned" color="var(--aligned)" hex="#16a34a" />
          <StatusSwatch name="Drifting" color="var(--drifting)" hex="#d97706" />
          <StatusSwatch name="Misaligned" color="var(--misaligned)" hex="#dc2626" />
          <StatusSwatch name="Violation" color="var(--violation)" hex="#991b1b" />
        </div>
      </section>

      {/* ─── Trait Mapping ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Trait Color Mapping"
          description="How the 12 traits map to dimension colors with positive/negative polarity."
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <TraitGroup
            dimension="Ethos"
            positive={[
              { name: "Virtue", shade: "400" },
              { name: "Goodwill", shade: "300" },
            ]}
            negative={[
              { name: "Manipulation", shade: "700" },
              { name: "Deception", shade: "800" },
            ]}
            cssPrefix="ethos"
          />
          <TraitGroup
            dimension="Logos"
            positive={[
              { name: "Accuracy", shade: "400" },
              { name: "Reasoning", shade: "300" },
            ]}
            negative={[
              { name: "Fabrication", shade: "700" },
              { name: "Broken Logic", shade: "800" },
            ]}
            cssPrefix="logos"
          />
          <TraitGroup
            dimension="Pathos"
            positive={[
              { name: "Recognition", shade: "400" },
              { name: "Compassion", shade: "300" },
            ]}
            negative={[
              { name: "Dismissal", shade: "700" },
              { name: "Exploitation", shade: "800" },
            ]}
            cssPrefix="pathos"
          />
        </div>
      </section>

      {/* ─── Typography ─── */}
      <section className="space-y-6">
        <SectionHeader title="Typography" description="Geist Sans for body. Geist Mono for data." />
        <div className="glass-strong rounded-2xl p-8 space-y-6">
          <div className="space-y-3">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Headings — Geist Sans</p>
            <h1 className="text-4xl font-bold tracking-tight">Phronesis</h1>
            <h2 className="text-2xl font-semibold tracking-tight">Practical wisdom through trust</h2>
            <h3 className="text-lg font-semibold">12 behavioral traits, 3 dimensions</h3>
          </div>
          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Body — Geist Sans</p>
            <p className="text-base">
              Ethos scores AI agent messages for honesty, accuracy, and intent. Each evaluation produces scores across 12 behavioral traits organized into three Aristotelian dimensions.
            </p>
            <p className="text-sm text-muted">
              Secondary text for descriptions, metadata, and supporting information.
            </p>
          </div>
          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Mono — Geist Mono</p>
            <p className="font-mono text-sm">agent_id: sha256(&quot;claude-3-opus&quot;)</p>
            <p className="font-mono text-sm tabular-nums">
              ethos: 0.847 &nbsp; logos: 0.923 &nbsp; pathos: 0.761
            </p>
          </div>
        </div>
      </section>

      {/* ─── Glassmorphism ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Glassmorphism"
          description="Three levels of frosted glass. Used for cards, panels, and overlays."
        />
        <div
          className="relative rounded-2xl overflow-hidden p-8"
          style={{
            background: `linear-gradient(135deg, var(--ethos-300), var(--logos-300), var(--pathos-300))`,
          }}
        >
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="glass-subtle rounded-xl p-6 space-y-2">
              <p className="text-sm font-semibold">glass-subtle</p>
              <p className="text-xs text-foreground/70">
                Light frosted effect. 35% white, 8px blur. For overlays on colorful backgrounds.
              </p>
              <code className="block text-xs font-mono mt-2 text-foreground/60">className=&quot;glass-subtle&quot;</code>
            </div>
            <div className="glass rounded-xl p-6 space-y-2">
              <p className="text-sm font-semibold">glass</p>
              <p className="text-xs text-foreground/70">
                Default glass. 55% white, 16px blur. The workhorse for most cards and panels.
              </p>
              <code className="block text-xs font-mono mt-2 text-foreground/60">className=&quot;glass&quot;</code>
            </div>
            <div className="glass-strong rounded-xl p-6 space-y-2">
              <p className="text-sm font-semibold">glass-strong</p>
              <p className="text-xs text-foreground/70">
                Heavy frost. 75% white, 24px blur. For content that needs high readability over color.
              </p>
              <code className="block text-xs font-mono mt-2 text-foreground/60">className=&quot;glass-strong&quot;</code>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Gradients ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Gradients"
          description="Subtle gradients for backgrounds, bars, and accent elements."
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <GradientSample
            name="Ethos gradient"
            from="var(--ethos-400)"
            to="var(--ethos-600)"
            css="from-ethos-400 to-ethos-600"
          />
          <GradientSample
            name="Logos gradient"
            from="var(--logos-400)"
            to="var(--logos-600)"
            css="from-logos-400 to-logos-600"
          />
          <GradientSample
            name="Pathos gradient"
            from="var(--pathos-400)"
            to="var(--pathos-600)"
            css="from-pathos-400 to-pathos-600"
          />
          <GradientSample
            name="Dimension blend"
            from="var(--ethos-400)"
            via="var(--logos-400)"
            to="var(--pathos-400)"
            css="ethos → logos → pathos"
          />
          <GradientSample
            name="Trust positive"
            from="var(--ethos-200)"
            via="var(--logos-200)"
            to="var(--pathos-200)"
            css="Light dimension blend"
          />
          <GradientSample
            name="Trust negative"
            from="var(--ethos-800)"
            via="var(--logos-800)"
            to="var(--pathos-800)"
            css="Dark dimension blend"
          />
        </div>
      </section>

      {/* ─── Buttons ─── */}
      <section className="space-y-6">
        <SectionHeader title="Buttons" description="Action buttons with the primary teal." />
        <div className="flex flex-wrap items-center gap-4">
          <button className="rounded-xl bg-action px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-action-hover">
            Primary
          </button>
          <button className="rounded-xl border border-border bg-surface px-5 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-background">
            Secondary
          </button>
          <button className="rounded-xl bg-action/10 px-5 py-2.5 text-sm font-medium text-action transition-colors hover:bg-action/20">
            Ghost
          </button>
          <button className="rounded-xl bg-action px-5 py-2.5 text-sm font-medium text-white opacity-50 cursor-not-allowed">
            Disabled
          </button>
        </div>
      </section>

      {/* ─── Badges ─── */}
      <section className="space-y-6">
        <SectionHeader title="Badges" description="Status indicators and labels." />
        <div className="flex flex-wrap gap-3">
          <Badge label="Aligned" bg="bg-aligned/10" text="text-aligned" />
          <Badge label="Drifting" bg="bg-drifting/10" text="text-drifting" />
          <Badge label="Misaligned" bg="bg-misaligned/10" text="text-misaligned" />
          <Badge label="Violation" bg="bg-violation/10" text="text-violation" />
          <Badge label="Ethos" bg="bg-ethos-100" text="text-ethos-700" />
          <Badge label="Logos" bg="bg-logos-100" text="text-logos-700" />
          <Badge label="Pathos" bg="bg-pathos-100" text="text-pathos-700" />
        </div>
      </section>

      {/* ─── Data Visualization Colors ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="Data Visualization"
          description="How the dimension colors work in charts. Positive traits are lighter shades, negative traits are darker."
        />

        <div className="glass-strong rounded-2xl p-8 space-y-8">
          {/* Simulated dimension bars */}
          <div className="space-y-4">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Dimension Bars</p>
            <DimensionBarDemo label="Ethos" value={0.84} from="var(--ethos-400)" to="var(--ethos-600)" />
            <DimensionBarDemo label="Logos" value={0.92} from="var(--logos-400)" to="var(--logos-600)" />
            <DimensionBarDemo label="Pathos" value={0.67} from="var(--pathos-400)" to="var(--pathos-600)" />
          </div>

          {/* Simulated trait scores */}
          <div className="border-t border-border pt-6 space-y-4">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Trait Scores (positive + negative)</p>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-4">
              <TraitBar label="Virtue" score={0.91} color="var(--ethos-400)" />
              <TraitBar label="Goodwill" score={0.85} color="var(--ethos-300)" />
              <TraitBar label="Manipulation" score={0.12} color="var(--ethos-700)" />
              <TraitBar label="Deception" score={0.08} color="var(--ethos-800)" />
              <TraitBar label="Accuracy" score={0.94} color="var(--logos-400)" />
              <TraitBar label="Reasoning" score={0.88} color="var(--logos-300)" />
              <TraitBar label="Fabrication" score={0.05} color="var(--logos-700)" />
              <TraitBar label="Broken Logic" score={0.10} color="var(--logos-800)" />
              <TraitBar label="Recognition" score={0.78} color="var(--pathos-400)" />
              <TraitBar label="Compassion" score={0.72} color="var(--pathos-300)" />
              <TraitBar label="Dismissal" score={0.15} color="var(--pathos-700)" />
              <TraitBar label="Exploitation" score={0.06} color="var(--pathos-800)" />
            </div>
          </div>

          {/* Chart color reference */}
          <div className="border-t border-border pt-6 space-y-4">
            <p className="text-xs font-mono text-muted uppercase tracking-wider">Chart Line Colors</p>
            <div className="flex items-center gap-6 text-sm">
              <span className="flex items-center gap-2">
                <span className="h-1 w-8 rounded-full" style={{ background: "var(--ethos-500)" }} />
                Ethos
              </span>
              <span className="flex items-center gap-2">
                <span className="h-1 w-8 rounded-full" style={{ background: "var(--logos-500)" }} />
                Logos
              </span>
              <span className="flex items-center gap-2">
                <span className="h-1 w-8 rounded-full" style={{ background: "var(--pathos-500)" }} />
                Pathos
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Cards ─── */}
      <section className="space-y-6">
        <SectionHeader title="Cards" description="Glass card variants for content panels." />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface p-6 space-y-2">
            <h3 className="font-semibold">Solid card</h3>
            <p className="text-sm text-muted">White surface with warm stone border. Default for most content.</p>
          </div>
          <div className="glass rounded-2xl p-6 space-y-2">
            <h3 className="font-semibold">Glass card</h3>
            <p className="text-sm text-muted">Frosted glass with backdrop blur. Use over colored or image backgrounds.</p>
          </div>
          <div
            className="rounded-2xl p-6 space-y-2 text-white"
            style={{
              background: "linear-gradient(135deg, var(--ethos-500), var(--logos-500))",
            }}
          >
            <h3 className="font-semibold">Gradient card</h3>
            <p className="text-sm text-white/80">Dimension gradient background. Use sparingly for hero elements.</p>
          </div>
        </div>
      </section>

      {/* ─── CSS Variables Reference ─── */}
      <section className="space-y-6">
        <SectionHeader
          title="CSS Variables"
          description="Copy-paste reference for all design tokens."
        />
        <div className="glass-strong rounded-2xl p-6 overflow-x-auto">
          <pre className="text-xs font-mono text-foreground/80 leading-relaxed whitespace-pre">{`/* Base */
var(--background)     /* #faf7f2  warm cream */
var(--surface)        /* #ffffff  white */
var(--foreground)     /* #2a2018  warm near-black */
var(--muted)          /* #8b7e74  warm gray */
var(--border)         /* #e6ddd2  warm stone */
var(--action)         /* #4a90a4  teal action */

/* Dimensions — use 400 (positive) and 700-800 (negative) */
var(--ethos-{50-900})   /* terracotta rose */
var(--logos-{50-900})   /* cerulean blue */
var(--pathos-{50-900})  /* amber gold */

/* Alignment */
var(--aligned)        /* #16a34a  green */
var(--drifting)       /* #d97706  amber */
var(--misaligned)     /* #dc2626  red */
var(--violation)      /* #991b1b  deep red */

/* Tailwind classes */
bg-ethos-{50-900}  text-ethos-{50-900}
bg-logos-{50-900}  text-logos-{50-900}
bg-pathos-{50-900} text-pathos-{50-900}
glass  glass-subtle  glass-strong`}</pre>
        </div>
      </section>
    </div>
  );
}

/* ─── Sub-components ─── */

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <h2 className="text-xl font-bold tracking-tight">{title}</h2>
      <p className="mt-1 text-sm text-muted">{description}</p>
    </div>
  );
}

function PhilosophyCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="glass-strong rounded-2xl p-6 space-y-2">
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm text-muted leading-relaxed">{body}</p>
    </div>
  );
}

function Swatch({
  name,
  color,
  hex,
  dark,
  border,
  compact,
}: {
  name: string;
  color: string;
  hex: string;
  dark?: boolean;
  border?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "flex-1" : ""}>
      <div
        className={`${compact ? "h-12" : "h-20"} rounded-xl ${border ? "border border-border" : ""}`}
        style={{ backgroundColor: color }}
      />
      <p className={`mt-2 text-xs font-medium ${dark && !compact ? "" : ""}`}>{name}</p>
      <p className="text-xs font-mono text-muted">{hex}</p>
    </div>
  );
}

function DimensionScale({
  name,
  subtitle,
  description,
  cssPrefix,
  hexes,
}: {
  name: string;
  subtitle: string;
  description: string;
  cssPrefix: string;
  hexes: string[];
}) {
  const shades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900];

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-base font-semibold">{name}</h3>
        <p className="text-xs text-muted">{subtitle}</p>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
      <div className="flex gap-1">
        {shades.map((shade, i) => (
          <div key={shade} className="flex-1 text-center">
            <div
              className="h-14 rounded-lg first:rounded-l-xl last:rounded-r-xl"
              style={{ backgroundColor: `var(--${cssPrefix}-${shade})` }}
            />
            <p className="mt-1.5 text-[10px] font-mono text-muted">{shade}</p>
            <p className="text-[9px] font-mono text-muted/70">{hexes[i]}</p>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between text-[10px] font-mono text-muted">
        <span>positive traits</span>
        <span>negative traits</span>
      </div>
    </div>
  );
}

function StatusSwatch({ name, color, hex }: { name: string; color: string; hex: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4">
      <div className="h-10 w-10 rounded-full" style={{ backgroundColor: color }} />
      <div>
        <p className="text-sm font-medium">{name}</p>
        <p className="text-xs font-mono text-muted">{hex}</p>
      </div>
    </div>
  );
}

function Badge({ label, bg, text }: { label: string; bg: string; text: string }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${bg} ${text}`}>
      {label}
    </span>
  );
}

function DimensionBarDemo({
  label,
  value,
  from,
  to,
}: {
  label: string;
  value: number;
  from: string;
  to: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="tabular-nums font-mono text-muted">{pct}%</span>
      </div>
      <div className="h-3 rounded-full bg-border/40">
        <div
          className="h-3 rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${from}, ${to})`,
          }}
        />
      </div>
    </div>
  );
}

function TraitBar({ label, score, color }: { label: string; score: number; color: string }) {
  const pct = Math.round(score * 100);
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between">
        <span className="text-xs">{label}</span>
        <span className="text-xs font-mono text-muted">{score.toFixed(2)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-border/40">
        <div
          className="h-1.5 rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function GradientSample({
  name,
  from,
  to,
  via,
  css,
}: {
  name: string;
  from: string;
  to: string;
  via?: string;
  css: string;
}) {
  const bg = via
    ? `linear-gradient(135deg, ${from}, ${via}, ${to})`
    : `linear-gradient(135deg, ${from}, ${to})`;

  return (
    <div className="overflow-hidden rounded-xl">
      <div className="h-16" style={{ background: bg }} />
      <div className="bg-surface border border-border border-t-0 rounded-b-xl px-4 py-2.5">
        <p className="text-sm font-medium">{name}</p>
        <p className="text-xs font-mono text-muted">{css}</p>
      </div>
    </div>
  );
}

function TraitGroup({
  dimension,
  positive,
  negative,
  cssPrefix,
}: {
  dimension: string;
  positive: { name: string; shade: string }[];
  negative: { name: string; shade: string }[];
  cssPrefix: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 space-y-4">
      <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: `var(--${cssPrefix}-500)` }}>
        {dimension}
      </h3>
      <div className="space-y-2">
        <p className="text-[10px] font-mono text-muted uppercase tracking-wider">Positive</p>
        {positive.map((t) => (
          <div key={t.name} className="flex items-center gap-3">
            <div
              className="h-5 w-5 rounded"
              style={{ backgroundColor: `var(--${cssPrefix}-${t.shade})` }}
            />
            <span className="text-sm">{t.name}</span>
            <span className="ml-auto text-xs font-mono text-muted">{cssPrefix}-{t.shade}</span>
          </div>
        ))}
      </div>
      <div className="space-y-2">
        <p className="text-[10px] font-mono text-muted uppercase tracking-wider">Negative</p>
        {negative.map((t) => (
          <div key={t.name} className="flex items-center gap-3">
            <div
              className="h-5 w-5 rounded"
              style={{ backgroundColor: `var(--${cssPrefix}-${t.shade})` }}
            />
            <span className="text-sm">{t.name}</span>
            <span className="ml-auto text-xs font-mono text-muted">{cssPrefix}-{t.shade}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
