import { useEffect, useState } from "react";

import {
  getActuatorExecutions,
  type ActuatorExecutionDto,
} from "../../api/actuatorExecutions";

export default function ExecutionLogPanel() {
  const [logs, setLogs] = useState<ActuatorExecutionDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadLogs() {
      setLoading(true);
      setError(null);

      try {
        const rows = await getActuatorExecutions(
          20,
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setLogs(rows);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load execution logs.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadLogs();

    return () => controller.abort();
  }, [refreshKey]);

  return (
    <section
      id="executions"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-100">
          Execution log
        </h2>

        <button
          type="button"
          disabled={loading}
          onClick={() => setRefreshKey((value) => value + 1)}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <p className="mt-2 text-slate-400">
        Latest 20 execution attempts, newest first.
        Refresh to load current records.
      </p>

      <p className="mt-2 text-sm text-slate-400">
        Attempts are simulated. Command names are not checked
        against allowed commands in this phase.
      </p>

      {error && (
        <p role="alert" className="mt-4 text-red-300">
          {error}
        </p>
      )}

      {loading && (
        <p role="status" className="mt-4 text-slate-400">
          Loading execution logs...
        </p>
      )}

      {!loading && !error && logs.length === 0 && (
        <p className="mt-4 text-slate-400">
          No execution attempts yet.
        </p>
      )}

      <ul className="mt-4 space-y-3">
        {logs.map((log) => (
          <li
            key={log.id}
            className="rounded-lg border border-slate-700 bg-slate-800 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span
                className={
                  log.success
                    ? "font-semibold text-emerald-300"
                    : "font-semibold text-red-300"
                }
              >
                {log.success ? "Success" : "Failed"}
              </span>

              <time
                dateTime={log.created_at}
                className="text-sm text-slate-400"
              >
                {new Date(log.created_at).toLocaleString()}
              </time>
            </div>

            <p className="mt-3 break-all text-slate-200">
              Device: {log.device_id}
            </p>

            <p className="mt-2 text-slate-300">
              Policies: {log.policy_applied.join(", ")}
            </p>

            <p className="mt-2 break-words text-slate-300">
              Message: {log.message ?? "—"}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}