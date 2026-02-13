"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "motion/react";
import { fadeUp, fadeIn, whileInView } from "../../lib/motion";

function CountUp({ target, suffix = "" }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    const duration = 2000;
    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }, [isInView, target]);

  return (
    <span ref={ref}>
      {value.toLocaleString()}{suffix}
    </span>
  );
}

export default function ScaleStatement() {
  return (
    <section className="relative overflow-hidden border-t border-border/50 bg-white py-24">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <motion.div {...whileInView} variants={fadeUp}>
          <p className="text-6xl font-bold tracking-tight sm:text-7xl">
            <CountUp target={12} /> traits.
          </p>
          <p className="mt-2 text-5xl font-bold tracking-tight text-muted sm:text-6xl">
            <CountUp target={3} /> dimensions.
          </p>
          <p className="mt-2 text-4xl font-bold tracking-tight text-muted/50 sm:text-5xl">
            <CountUp target={208} /> behavioral indicators.
          </p>
        </motion.div>

        <motion.div
          className="mt-12 flex justify-center gap-8"
          {...whileInView}
          variants={fadeIn}
        >
          {[
            { label: "Integrity", sublabel: "Ethos", color: "bg-ethos-500" },
            { label: "Logic", sublabel: "Logos", color: "bg-logos-500" },
            { label: "Empathy", sublabel: "Pathos", color: "bg-pathos-500" },
          ].map((dim) => (
            <div key={dim.label} className="text-center">
              <div className={`mx-auto h-3 w-16 rounded-full ${dim.color}`} />
              <p className="mt-2 text-sm font-semibold">{dim.label}</p>
              <p className="text-xs text-muted">{dim.sublabel}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
