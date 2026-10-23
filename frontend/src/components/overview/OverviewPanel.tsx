import { useEffect, useState } from "react";

import {
  getLocations,
  type LocationSummary,
} from "../../api/locations";
import {
  fetchOverview,
  type LocationOverviewDto,
} from "../../api/overview";

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Could not load overview.";
}

function LocationOverview({ locationId }: { locationId: string }) {
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError(null);

    async function load() {
      try {
        const result = await fetchOverview(
          locationId,
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setOverview(result);
        }
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
  }, [locationId, refresh]);

  return (
    <div className="mt-4 space-y-4">
      <button
        type="button"
        onClick={() => setRefresh((current) => current + 1)}
        disabled={loading}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
      >
        {loading ? "Loading..." : "Refresh"}
      </button>

      {loading && (
        <p role="status" className="text-slate-400">
          Loading overview...
        </p>
      )}

      {error && (
        <p
          role="alert"
          className="rounded-lg bg-red-950 p-3 text-red-300"
        >
          {error}
        </p>
      )}

      {!loading && !error && overview && (
        <>
          <h3 className="text-lg font-semibold text-slate-100">
            {overview.location.name}
          </h3>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-800 p-4">
              <p className="text-sm text-slate-400">
                Assigned sensors
              </p>
              <p className="mt-1 text-3xl font-bold text-emerald-400">
                {overview.device_counts.sensor}
              </p>
            </div>

            <div className="rounded-lg bg-slate-800 p-4">
              <p className="text-sm text-slate-400">
                Assigned actuators
              </p>
              <p className="mt-1 text-3xl font-bold text-emerald-400">
                {overview.device_counts.actuator}
              </p>
            </div>
          </div>

          <div className="rounded-lg border border-slate-600 p-4">
            <h4 className="font-semibold text-slate-100">
              Saved strategy
            </h4>
            <p className="mt-1 text-slate-300">
              {overview.strategy_key ?? "No strategy saved."}
            </p>

            <h4 className="mt-4 font-semibold text-slate-100">
              Recommendation
            </h4>

            {overview.last_recommendation ? (
              <>
                <p className="mt-1 font-semibold text-emerald-300">
                  {overview.last_recommendation.action}
                </p>
                <p className="mt-1 text-slate-300">
                  {overview.last_recommendation.reason}
                </p>
              </>
            ) : (
              <p className="mt-1 text-slate-400">
                Save a strategy in Automation to get a recommendation.
              </p>
            )}

            <p className="mt-3 text-sm text-slate-400">
              Recommendations are calculated when this overview loads.
              No pump commands are sent.
            </p>
          </div>

          {overview.zones.length === 0 && (
            <p className="text-slate-400">
              This location has no zones.
            </p>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {overview.zones.map((zone) => {
              const readings = new Map(
                zone.latest_readings.map((reading) => [
                  reading.device_id,
                  reading,
                ]),
              );

              return (
                <div
                  key={zone.id}
                  className="rounded-lg border border-slate-700 bg-slate-800 p-4"
                >
                  <h4 className="text-lg font-semibold text-slate-100">
                    {zone.name}
                  </h4>
                  <p className="mt-1 text-sm text-slate-400">
                    Moisture thresholds: {zone.moisture_threshold_low}
                    {" – "}
                    {zone.moisture_threshold_high}
                  </p>

                  {zone.devices.length === 0 ? (
                    <p className="mt-4 text-slate-400">
                      No devices assigned to this zone.
                    </p>
                  ) : (
                    <ul className="mt-4 space-y-3">
                      {zone.devices.map((device) => {
                        const reading = readings.get(device.id);

                        return (
                          <li
                            key={device.id}
                            className="rounded-lg bg-slate-900 p-3"
                          >
                            <p className="font-medium text-slate-100">
                              {device.display_name}
                            </p>
                            <p className="mt-1 text-sm text-slate-400">
                              {device.role} · {device.device_type}
                            </p>

                            {reading ? (
                              <>
                                <p className="mt-3 text-xl font-semibold text-emerald-300">
                                  {reading.value} {reading.unit}
                                </p>
                                <p className="mt-1 text-sm text-slate-400">
                                  Last reading:{" "}
                                  {new Date(
                                    reading.recorded_at,
                                  ).toLocaleString()}
                                </p>
                                <p className="mt-1 text-sm text-slate-300">
                                  Tracking:{" "}
                                  {reading.tracking_enabled ? "On" : "Off"}
                                </p>
                                <p className="text-sm text-slate-300">
                                  Sampling interval:{" "}
                                  {reading.sampling_interval_seconds} seconds
                                </p>
                              </>
                            ) : (
                              <p className="mt-3 text-sm text-slate-400">
                                No reading available.
                              </p>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export default function OverviewPanel({
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

    async function loadLocations() {
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
        if (active) {
          setError(errorMessage(error));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadLocations();
    return () => {
      active = false;
    };
  }, [refreshKey]);

  return (
    <section
      id="overview"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <h2 className="text-xl font-semibold text-slate-100">
        Overview
      </h2>
      <p className="mt-1 text-sm text-slate-400">
        View assigned devices, latest readings and recommendations.
        Use Refresh to load current data.
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
              className="mt-2 w-full rounded-lg border border-slate-600 bg-slate-950 px-3 py-2 text-slate-100"
            >
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>
          </label>

          <LocationOverview key={locationId} locationId={locationId} />
        </>
      )}
    </section>
  );
}