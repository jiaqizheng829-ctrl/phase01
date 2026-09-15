import { useEffect, useState } from "react";

type HealthState = "loading" | "healthy" | "degraded" | "unavailable";

export default function HealthStatus() {
  const [healthStatus, setHealthStatus] =
    useState<HealthState>("loading");

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const response = await fetch("http://localhost:8000/health");

        if (!response.ok) {
          throw new Error("Health request failed");
        }

        const data = await response.json();

        if (!cancelled) {
          setHealthStatus(
            data.status === "ok" && data.db === "ok"
              ? "healthy"
              : "degraded",
          );
        }
      } catch {
        if (!cancelled) {
          setHealthStatus("unavailable");
        }
      }
    }

    void checkHealth();
    const timer = window.setInterval(checkHealth, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const labels = {
    loading: "Checking system...",
    healthy: "API: ok · DB: ok",
    degraded: "API reachable · Database check failed",
    unavailable: "API unreachable",
  };

  const colors = {
    loading: "text-slate-300",
    healthy: "text-emerald-400",
    degraded: "text-amber-400",
    unavailable: "text-rose-400",
  };

  return (
    <p role="status" className={`text-sm ${colors[healthStatus]}`}>
      {labels[healthStatus]}
    </p>
  );
}
