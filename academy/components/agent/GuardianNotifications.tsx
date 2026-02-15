"use client";

import { useState /* useEffect, useCallback */ } from "react";
import { AnimatePresence, motion } from "motion/react";
// import type { GuardianPhoneStatus } from "@/lib/types";
// import {
//   getGuardianPhoneStatus,
//   submitGuardianPhone,
//   verifyGuardianPhone,
//   optOutNotifications,
//   optInNotifications,
// } from "@/lib/api";

interface Props {
  agentId: string;
  agentName: string;
}

export default function GuardianNotifications({ agentId, agentName }: Props) {
  const [showToast, setShowToast] = useState(false);

  // ── Coming soon placeholder ──────────────────────────────────────────
  return (
    <>
      <button
        onClick={() => {
          setShowToast(true);
          setTimeout(() => setShowToast(false), 2500);
        }}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3 text-sm text-foreground/60 transition-colors hover:bg-foreground/[0.04] hover:text-foreground/80"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
        </svg>
        Get notified about {agentName || "this agent"}&apos;s character development
      </button>

      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-2 rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3 text-center text-sm text-foreground/60"
          >
            Coming soon. Guardian notifications are in development.
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );

  // ── Full SMS verification flow (uncomment when ready) ────────────────
  //
  // const [status, setStatus] = useState<GuardianPhoneStatus | null>(null);
  // const [expanded, setExpanded] = useState(false);
  // const [phone, setPhone] = useState("");
  // const [code, setCode] = useState("");
  // const [error, setError] = useState("");
  // const [loading, setLoading] = useState(false);
  //
  // const loadStatus = useCallback(async () => {
  //   try {
  //     const s = await getGuardianPhoneStatus(agentId);
  //     setStatus(s);
  //     if (s.hasPhone && !s.verified) setExpanded(true);
  //   } catch {
  //     // Non-fatal
  //   }
  // }, [agentId]);
  //
  // useEffect(() => {
  //   loadStatus();
  // }, [loadStatus]);
  //
  // const handleSubmitPhone = async () => {
  //   setError("");
  //   setLoading(true);
  //   try {
  //     const s = await submitGuardianPhone(agentId, phone);
  //     setStatus(s);
  //     setPhone("");
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : "Failed to submit phone");
  //   } finally {
  //     setLoading(false);
  //   }
  // };
  //
  // const handleVerify = async () => {
  //   setError("");
  //   setLoading(true);
  //   try {
  //     const s = await verifyGuardianPhone(agentId, code);
  //     setStatus(s);
  //     setCode("");
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : "Verification failed");
  //   } finally {
  //     setLoading(false);
  //   }
  // };
  //
  // const handleToggleNotifications = async () => {
  //   if (!status) return;
  //   setLoading(true);
  //   try {
  //     const s = status.optedOut
  //       ? await optInNotifications(agentId)
  //       : await optOutNotifications(agentId);
  //     setStatus(s);
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : "Failed to update");
  //   } finally {
  //     setLoading(false);
  //   }
  // };
  //
  // if (!status) return null;
  //
  // // Verified state
  // if (status.hasPhone && status.verified) {
  //   return (
  //     <div className="flex items-center justify-between rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3">
  //       <div className="flex items-center gap-2">
  //         <span className="inline-flex items-center rounded-full bg-green-100 dark:bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400">
  //           Verified
  //         </span>
  //         <span className="text-sm text-foreground/60">
  //           Guardian notifications {status.optedOut ? "paused" : "active"}
  //         </span>
  //       </div>
  //       <button
  //         onClick={handleToggleNotifications}
  //         disabled={loading}
  //         className="text-sm text-foreground/50 hover:text-foreground/70 underline"
  //       >
  //         {status.optedOut ? "Resume" : "Pause"}
  //       </button>
  //     </div>
  //   );
  // }
  //
  // // Collapsed
  // if (!expanded) {
  //   return (
  //     <button
  //       onClick={() => setExpanded(true)}
  //       className="flex w-full items-center justify-center gap-2 rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] px-4 py-3 text-sm text-foreground/60 transition-colors hover:bg-foreground/[0.04] hover:text-foreground/80"
  //     >
  //       <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
  //         <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
  //       </svg>
  //       Get notified about {agentName || "this agent"}&apos;s character development
  //     </button>
  //   );
  // }
  //
  // // Expanded: verification code entry
  // if (status.hasPhone && !status.verified) {
  //   return (
  //     <AnimatePresence>
  //       <motion.div
  //         initial={{ opacity: 0, height: 0 }}
  //         animate={{ opacity: 1, height: "auto" }}
  //         className="rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4 space-y-3"
  //       >
  //         <div className="flex items-center justify-between">
  //           <p className="text-sm text-foreground/60">
  //             Enter the 6-digit code sent to your phone.
  //           </p>
  //           <button onClick={() => setExpanded(false)} className="text-xs text-foreground/40 hover:text-foreground/60">
  //             Close
  //           </button>
  //         </div>
  //         <div className="flex gap-2">
  //           <input
  //             type="text"
  //             inputMode="numeric"
  //             maxLength={6}
  //             value={code}
  //             onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
  //             placeholder="000000"
  //             className="w-28 rounded-md border border-foreground/10 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm font-mono tracking-widest"
  //           />
  //           <button
  //             onClick={handleVerify}
  //             disabled={loading || code.length !== 6}
  //             className="rounded-md bg-[#2e4a6e] text-white px-3 py-1.5 text-sm font-medium disabled:opacity-50"
  //           >
  //             Verify
  //           </button>
  //         </div>
  //         {error && <p className="text-sm text-red-600">{error}</p>}
  //       </motion.div>
  //     </AnimatePresence>
  //   );
  // }
  //
  // // Expanded: phone entry form
  // return (
  //   <AnimatePresence>
  //     <motion.div
  //       initial={{ opacity: 0, height: 0 }}
  //       animate={{ opacity: 1, height: "auto" }}
  //       className="rounded-lg border border-foreground/[0.06] bg-foreground/[0.02] p-4 space-y-3"
  //     >
  //       <div className="flex items-center justify-between">
  //         <p className="text-sm text-foreground/60">
  //           Get notified about {agentName || "this agent"}&apos;s progress via SMS.
  //         </p>
  //         <button onClick={() => setExpanded(false)} className="text-xs text-foreground/40 hover:text-foreground/60">
  //           Close
  //         </button>
  //       </div>
  //       <div className="flex gap-2">
  //         <input
  //           type="tel"
  //           value={phone}
  //           onChange={(e) => setPhone(e.target.value)}
  //           placeholder="+1 (555) 123-4567"
  //           className="flex-1 rounded-md border border-foreground/10 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm"
  //         />
  //         <button
  //           onClick={handleSubmitPhone}
  //           disabled={loading || phone.length < 10}
  //           className="rounded-md bg-[#2e4a6e] text-white px-3 py-1.5 text-sm font-medium disabled:opacity-50"
  //         >
  //           Send code
  //         </button>
  //       </div>
  //       <p className="text-[11px] leading-relaxed text-foreground/40">
  //         By submitting your phone number, you consent to receive SMS notifications
  //         from Ethos Academy about {agentName || "your agent"}&apos;s evaluation
  //         results and homework assignments. Message frequency varies. Msg &amp; data
  //         rates may apply. Reply STOP to opt out at any time. Reply HELP for help.{" "}
  //         <a href="/privacy" className="underline hover:text-foreground/60">Privacy Policy</a>{" "}
  //         &middot;{" "}
  //         <a href="/terms" className="underline hover:text-foreground/60">Terms</a>
  //       </p>
  //       {error && <p className="text-sm text-red-600">{error}</p>}
  //     </motion.div>
  //   </AnimatePresence>
  // );
}
