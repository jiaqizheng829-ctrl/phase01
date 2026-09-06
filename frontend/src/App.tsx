import { useEffect, useState } from "react";

type HealthState = "loading" | "healthy" | "unavailable";

const API_URL = "http://localhost:8000";


export default function App() {
  const [healthState, setHealthState] = useState<HealthState>("loading");

  useEffect(() => {
    async function loadHealth() {
      try {
        const response = await fetch(`${API_URL}/health`);

        if (!response.ok) {
          throw new Error("Health check failed");
        }

        const data: { status: string; db: string } = await response.json();

        setHealthState(
          data.status === "ok" && data.db === "ok"
            ? "healthy"
            : "unavailable",
        );
      } catch {
        setHealthState("unavailable");
      }
    }

    void loadHealth();
  }, []);

  const statusText = {
    loading: "Checking backend...",
    healthy: "Backend and database are healthy",
    unavailable: "Backend is unavailable",
  }[healthState];

  const statusColor = {
    loading: "bg-amber-500",
    healthy: "bg-emerald-500",
    unavailable: "bg-rose-500",
  }[healthState];

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <p className="text-sm font-medium text-emerald-400">PHASE 1</p>
        <h1 className="mt-2 text-3xl font-bold">Greenhouse Dashboard</h1>
        <p className="mt-3 text-slate-400">
          Project foundation: React, FastAPI, PostgreSQL, Docker, and Alembic.
        </p>

        <div className="mt-8 rounded-xl border border-slate-700 bg-slate-800 p-5">
          <h2 className="text-lg font-semibold">System health</h2>
          <div className="mt-3 flex items-center gap-3">
            <span className={`h-3 w-3 rounded-full ${statusColor}`} />
            <span>{statusText}</span>
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-dashed border-slate-700 p-5 text-slate-400">
          Dashboard features will be added in later phases.
        </div>
      </section>
    </main>
  );
}
