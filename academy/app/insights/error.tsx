"use client";

import { useEffect } from "react";

export default function ExploreError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[ExploreError]", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center px-4">
      <div className="text-center">
        <h2 className="text-lg font-semibold text-foreground">
          Failed to load graph
        </h2>
        <p className="mt-2 text-sm text-muted">
          {error.message || "Could not initialize the graph visualization."}
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-4 rounded-lg bg-action px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-action-hover"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
