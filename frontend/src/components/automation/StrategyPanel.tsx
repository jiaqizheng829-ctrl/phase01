import { useEffect, useState } from "react";

import {
  getLocations,
  type LocationSummary,
} from "../../api/locations";
import {
  evaluateAutomation,
  getAutomationSettings,
  saveAutomationSettings,
  type EvaluationDto,
  type StrategyKey,
} from "../../api/automation";

const selectClass =
  "w-full rounded-lg border border-slate-600 bg-slate-950 px-3 py-2 text-slate-100";

const buttonClass =
  "rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

function LocationStrategy({ locationId }: { locationId: string }) {
  const [selected, setSelected] = useState<StrategyKey>("conservative");
  const [saved, setSaved] = useState<StrategyKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"save" | "evaluate" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluationDto | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const settings = await getAutomationSettings(
          locationId,
          controller.signal,
        );

        if (controller.signal.aborted) return;

        setSaved(settings.strategy_key);
        setSelected(settings.strategy_key ?? "conservative");
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => controller.abort();
  }, [locationId]);

  async function save() {
    setBusy("save");
    setError(null);
    setNotice(null);
    setResult(null);

    try {
      const settings = await saveAutomationSettings(locationId, selected);
      setSaved(settings.strategy_key);
      setNotice("Strategy saved.");
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function evaluate() {
    setBusy("evaluate");
    setError(null);
    setNotice(null);
    setResult(null);

    try {
      setResult(await evaluateAutomation(locationId));
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  const unsaved = selected !== saved;

  if (loading) {
    return (
      <p role="status" className="mt-4 text-slate-400">
        Loading strategy...
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-4">
      <label className="block text-slate-200">
        Strategy
        <select
          value={selected}
          disabled={busy !== null}
          onChange={(event) => {
            setSelected(event.target.value as StrategyKey);
            setResult(null);
            setNotice(null);
          }}
          className={`mt-2 ${selectClass}`}
        >
          <option value="conservative">Conservative</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </label>

      <p className="text-sm text-slate-400">
        Conservative recommends irrigation below the zone's lower
        threshold. Aggressive uses the midpoint of its lower and upper
        thresholds.
      </p>

      <p className="text-sm text-slate-300">
        Saved strategy: {saved ?? "Not configured"}
      </p>

      {unsaved && (
        <p className="text-sm text-amber-300">
          Save your selection before evaluating.
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void save()}
          disabled={busy !== null}
          className={buttonClass}
        >
          {busy === "save" ? "Saving..." : "Save strategy"}
        </button>

        <button
          type="button"
          onClick={() => void evaluate()}
          disabled={busy !== null || saved === null || unsaved}
          className={buttonClass}
        >
          {busy === "evaluate" ? "Evaluating..." : "Evaluate"}
        </button>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      {notice && (
        <p role="status" className="text-emerald-300">
          {notice}
        </p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="rounded-lg border border-slate-600 p-4">
            <h3 className="font-semibold text-emerald-300">
              Recommendation: {result.action}
            </h3>
            <p className="mt-1 text-slate-300">{result.reason}</p>
            <p className="mt-2 text-sm text-slate-400">
              Strategy: {result.strategy_key}. Recommendations only;
              no pump commands are sent.
            </p>
          </div>

          {result.zones.map((zone) => (
            <div
              key={zone.zone_id}
              className="rounded-lg bg-slate-800 p-4"
            >
              <h4 className="break-all font-medium text-slate-100">
                Zone: {zone.zone_id}
              </h4>
              <p className="mt-2 text-slate-300">
                Moisture: {zone.latest_moisture ?? "No reading"}
              </p>
              <p className="text-sm text-slate-400">
                Low: {zone.moisture_threshold_low} · High:{" "}
                {zone.moisture_threshold_high}
              </p>
              <p className="mt-2 font-semibold text-emerald-300">
                {zone.action}
              </p>
              <p className="mt-1 text-sm text-slate-300">
                {zone.reason}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function StrategyPanel({
  refreshKey,
}: {
  refreshKey: number;
}) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [locationId, setLocationId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const items = await getLocations();
        if (!active) return;

        setLocations(items);
        setLocationId((current) =>
          items.some((item) => item.id === current)
            ? current
            : (items[0]?.id ?? ""),
        );
      } catch (error) {
        if (active) setError(errorMessage(error));
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [refreshKey]);

  return (
    <section
      id="automation"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <h2 className="text-xl font-semibold text-slate-100">
        Automation
      </h2>
      <p className="mt-1 text-sm text-slate-400">
        Choose a strategy per location and evaluate saved zone readings.
      </p>

      {loading ? (
        <p role="status" className="mt-4 text-slate-400">
          Loading locations...
        </p>
      ) : error ? (
        <p role="alert" className="mt-4 text-red-300">
          {error}
        </p>
      ) : locations.length === 0 ? (
        <p className="mt-4 text-slate-400">
          Create a location in Configuration first.
        </p>
      ) : (
        <>
          <label className="mt-4 block text-slate-200">
            Location
            <select
              value={locationId}
              onChange={(event) => setLocationId(event.target.value)}
              className={`mt-2 ${selectClass}`}
            >
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>
          </label>

          <LocationStrategy key={locationId} locationId={locationId} />
        </>
      )}
    </section>
  );
}