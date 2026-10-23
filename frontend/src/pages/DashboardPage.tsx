import { useEffect, useState } from "react";

import DevicesSection from "../components/devices/DevicesSection";
import ConfigurationSection from "../components/config/ConfigurationSection";
import SensorCard from "../components/sensors/SensorCard";
import StrategyPanel from "../components/automation/StrategyPanel";
import OverviewPanel from "../components/overview/OverviewPanel";
import {
  createSensor,
  getSensors,
  type Sensor,
} from "../api/sensors";

const laterSections = [
  { id: "controls", title: "Controls" },
  { id: "events", title: "Events" },
];

export default function DashboardPage() {
  const [configurationRefresh, setConfigurationRefresh] = useState(0);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refreshConfiguration() {
    setConfigurationRefresh((current) => current + 1);
  }

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
      setSensors((current) => [...current, sensor]);
      refreshConfiguration();
    } catch {
      setError("Could not create the sensor.");
    } finally {
      setCreating(null);
    }
  }

  function handleProvisioned() {
    void loadSensors();
    refreshConfiguration();
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-emerald-400">
          Dashboard
        </h1>
        <p className="mt-2 text-slate-400">
          Greenhouse devices, locations and controls.
        </p>
      </header>

      <DevicesSection
        onProvisioned={handleProvisioned}
        refreshKey={configurationRefresh}
        onAssignmentChanged={refreshConfiguration}
      />

      <section
        id="sensors"
        className="rounded-xl border border-slate-700 bg-slate-900 p-5"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">
              Sensors
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              View saved readings and manage sensor sampling.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleCreate("moisture")}
              disabled={creating !== null}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {creating === "moisture"
                ? "Creating..."
                : "Add moisture sensor"}
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
          <p role="status" className="mt-5 text-slate-400">
            Loading sensors...
          </p>
        )}

        {error && (
          <p
            role="alert"
            className="mt-5 rounded-lg bg-red-950 p-3 text-red-300"
          >
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
              <SensorCard key={sensor.id} sensor={sensor} />
            ))}
          </ul>
        )}
      </section>

      <ConfigurationSection
        refreshKey={configurationRefresh}
        onChanged={refreshConfiguration}
      />

      <StrategyPanel refreshKey={configurationRefresh} />

      <OverviewPanel refreshKey={configurationRefresh} />

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