import { useEffect, useState } from "react";

import {
  createSensor,
  getSensors,
  type Sensor,
} from "../api/sensors";

const laterSections = [
  { id: "configuration", title: "Configuration" },
  { id: "automation", title: "Automation" },
  { id: "overview", title: "Overview" },
  { id: "controls", title: "Controls" },
  { id: "events", title: "Events" },
];

export default function DashboardPage() {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadSensors() {
    setLoading(true);
    setError(null);

    try {
      setSensors(await getSensors());
    } catch {
      setError("Could not load sensors. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSensors();
  }, []);

  async function handleCreate(type: "moisture" | "light") {
    setCreating(type);
    setError(null);

    try {
      const sensor = await createSensor({ type });
      setSensors((currentSensors) => [...currentSensors, sensor]);
    } catch {
      setError("Could not create the sensor.");
    } finally {
      setCreating(null);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-emerald-400">
          Dashboard
        </h1>
        <p className="mt-2 text-slate-400">
          Greenhouse devices and controls.
        </p>
      </header>

      <section
        id="sensors"
        className="rounded-xl border border-slate-700 bg-slate-900 p-5"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Sensors</h2>
            <p className="mt-1 text-sm text-slate-400">
              Create and view greenhouse sensors.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void handleCreate("moisture")}
              disabled={creating !== null}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {creating === "moisture" ? "Creating..." : "Add moisture sensor"}
            </button>

            <button
              type="button"
              onClick={() => void handleCreate("light")}
              disabled={creating !== null}
              className="rounded-lg bg-amber-500 px-3 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
            >
              {creating === "light" ? "Creating..." : "Add light sensor"}
            </button>
          </div>
        </div>

        {loading && (
          <p className="mt-5 text-slate-400">Loading sensors...</p>
        )}

        {error && (
          <p className="mt-5 rounded-lg bg-red-950 p-3 text-red-300">
            {error}
          </p>
        )}

        {!loading && !error && sensors.length === 0 && (
          <p className="mt-5 text-slate-400">
            No sensors have been created yet.
          </p>
        )}

        {!loading && sensors.length > 0 && (
          <ul className="mt-5 grid gap-3 sm:grid-cols-2">
            {sensors.map((sensor) => (
              <li
                key={sensor.id}
                className="rounded-lg border border-slate-700 bg-slate-800 p-4"
              >
                <h3 className="font-semibold text-slate-100">
                  {sensor.display_name}
                </h3>
                <p className="mt-1 text-sm text-emerald-400">
                  {sensor.device_type}
                </p>
                <pre className="mt-3 overflow-auto text-xs text-slate-400">
                  {JSON.stringify(sensor.default_config, null, 2)}
                </pre>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {laterSections.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="rounded-xl border border-slate-700 bg-slate-900 p-5"
          >
            <h2 className="text-xl font-semibold text-slate-100">
              {section.title}
            </h2>
            <p className="mt-3 text-slate-400">
              This feature is not implemented yet.
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
