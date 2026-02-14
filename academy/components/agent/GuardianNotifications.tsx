"use client";

import { useState, useEffect, useCallback } from "react";
import type { GuardianPhoneStatus } from "@/lib/types";
import {
  getGuardianPhoneStatus,
  submitGuardianPhone,
  verifyGuardianPhone,
  optOutNotifications,
  optInNotifications,
} from "@/lib/api";

interface Props {
  agentId: string;
  agentName: string;
}

export default function GuardianNotifications({ agentId, agentName }: Props) {
  const [status, setStatus] = useState<GuardianPhoneStatus | null>(null);
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const s = await getGuardianPhoneStatus(agentId);
      setStatus(s);
    } catch {
      // Non-fatal: component just shows "add phone" state
    }
  }, [agentId]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleSubmitPhone = async () => {
    setError("");
    setLoading(true);
    try {
      const s = await submitGuardianPhone(agentId, phone);
      setStatus(s);
      setPhone("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit phone");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setError("");
    setLoading(true);
    try {
      const s = await verifyGuardianPhone(agentId, code);
      setStatus(s);
      setCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleNotifications = async () => {
    if (!status) return;
    setLoading(true);
    try {
      const s = status.optedOut
        ? await optInNotifications(agentId)
        : await optOutNotifications(agentId);
      setStatus(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    } finally {
      setLoading(false);
    }
  };

  if (!status) return null;

  // Verified state
  if (status.hasPhone && status.verified) {
    return (
      <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-green-100 dark:bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400">
              Verified
            </span>
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              Guardian notifications {status.optedOut ? "paused" : "active"}
            </span>
          </div>
          <button
            onClick={handleToggleNotifications}
            disabled={loading}
            className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 underline"
          >
            {status.optedOut ? "Resume notifications" : "Stop notifications"}
          </button>
        </div>
      </div>
    );
  }

  // Unverified state (phone submitted, waiting for code)
  if (status.hasPhone && !status.verified) {
    return (
      <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 p-4 space-y-3">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Enter the 6-digit code sent to your phone.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            placeholder="000000"
            className="w-28 rounded-md border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm font-mono tracking-widest"
          />
          <button
            onClick={handleVerify}
            disabled={loading || code.length !== 6}
            className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-3 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            Verify
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    );
  }

  // No phone state
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 p-4 space-y-3">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Get notified about {agentName || "this agent"}&apos;s progress via SMS.
      </p>
      <div className="flex gap-2">
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+1 (555) 123-4567"
          className="flex-1 rounded-md border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-1.5 text-sm"
        />
        <button
          onClick={handleSubmitPhone}
          disabled={loading || phone.length < 10}
          className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-3 py-1.5 text-sm font-medium disabled:opacity-50"
        >
          Send code
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
