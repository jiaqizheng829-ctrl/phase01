import { useEffect, useState } from "react";

import { getAlerts, type AlertDto } from "../../api/alerts";
import {
  getLocations,
  getLocationConfig,
  type LocationSummary,
  type ZoneRead,
} from "../../api/locations";

interface Props {
  refreshKey?: number;
}

const severityClass = {
  info: "bg-sky-950 text-sky-300",
  warning: "bg-amber-950 text-amber-300",
  critical: "bg-red-950 text-red-300",
};

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

export default function EventFeed({ refreshKey = 0 }: Props) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [zones, setZones] = useState<ZoneRead[]>([]);
  const [locationId, setLocationId] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [zonesLoading, setZonesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [zoneError, setZoneError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setLocationError(null);

    getLocations()
      .then((rows) => {
        if (!active) return;
        setLocations(rows);
        if (locationId && !rows.some((row) => row.id === locationId)) {
          setLocationId("");
          setZoneId("");
        }
      })
      .catch((err: unknown) => {
        if (active) setLocationError(messageOf(err));
      });

    return () => {
      active = false;
    };
  }, [refreshKey, reloadKey, locationId]);

  useEffect(() => {
    let active = true;
    setZones([]);
    setZoneError(null);

    if (!locationId) {
      setZonesLoading(false);
      return;
    }

    setZonesLoading(true);

    getLocationConfig(locationId)
      .then((config) => {
        if (!active) return;
        setZones(config.zones);
        setZoneId((current) =>
          config.zones.some((zone) => zone.id === current) ? current : "",
        );
      })
      .catch((err: unknown) => {
        if (active) setZoneError(messageOf(err));
      })
      .finally(() => {
        if (active) setZonesLoading(false);
      });

    return () => {
      active = false;
    };
  }, [locationId, refreshKey, reloadKey]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let inFlight = false;

    setAlerts([]);
    setLoading(true);
    setError(null);
    setLastUpdated(null);

    async function load() {
      if (inFlight) return;
      inFlight = true;

      try {
        const rows = await getAlerts(
          {
            status: "active",
            location_id: locationId || undefined,
            zone_id: zoneId || undefined,
            limit: 50,
          },
          controller.signal,
        );

        if (!active) return;
        setAlerts(rows);
        setError(null);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        if (active) setError(messageOf(err));
      } finally {
        inFlight = false;
        if (active) setLoading(false);
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), 5000);

    return () => {
      active = false;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [locationId, zoneId, refreshKey, reloadKey]);

  return (
    <section
      id="events"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-100">
          Events
        </h2>
        <button
          type="button"
          onClick={() => setReloadKey((current) => current + 1)}
          className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white"
        >
          Refresh
        </button>
      </div>

      <p className="mt-2 text-sm text-slate-400">
        Latest 50 active alerts, newest first. Updates every 5 seconds.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm text-slate-300">
          Location
          <select
            value={locationId}
            onChange={(event) => {
              setLocationId(event.target.value);
              setZoneId("");
            }}
            className="mt-1 block w-full rounded-lg border border-slate-600 bg-slate-950 p-2 text-slate-100"
          >
            <option value="">All locations</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-300">
          Zone
          <select
            value={zoneId}
            disabled={!locationId || zonesLoading || zoneError !== null}
            onChange={(event) => setZoneId(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-600 bg-slate-950 p-2 text-slate-100 disabled:opacity-50"
          >
            <option value="">
              {zonesLoading ? "Loading zones..." : "All zones"}
            </option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {(locationError || zoneError) && (
        <p role="alert" className="mt-3 text-amber-300">
          Could not load filter options: {locationError ?? zoneError}
        </p>
      )}

      {error && (
        <p role="alert" className="mt-4 rounded-lg bg-red-950 p-3 text-red-300">
          {error} Retrying automatically.
        </p>
      )}

      {loading && (
        <p role="status" className="mt-4 text-slate-400">
          Loading alerts...
        </p>
      )}

      {!loading && !error && alerts.length === 0 && (
        <p className="mt-4 text-slate-400">
          No active alerts match these filters.
        </p>
      )}

      {lastUpdated && (
        <p className="mt-3 text-xs text-slate-500">
          Last updated: {lastUpdated}
        </p>
      )}

      <ul className="mt-4 space-y-3">
        {alerts.map((alert) => (
          <li
            key={alert.id}
            className="rounded-lg border border-slate-700 bg-slate-800 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span
                className={`rounded-full px-2 py-1 text-xs font-semibold ${severityClass[alert.severity]}`}
              >
                {alert.severity}
              </span>
              <time
                dateTime={alert.created_at}
                className="text-xs text-slate-400"
              >
                {new Date(alert.created_at).toLocaleString()}
              </time>
            </div>

            <p className="mt-3 font-medium text-slate-100">
              {alert.message}
            </p>
            <p className="mt-1 text-sm text-slate-400">
              {alert.event_type}
            </p>

            <dl className="mt-3 space-y-1 break-all text-xs text-slate-400">
              <div>
                <dt className="inline">Device: </dt>
                <dd className="inline">{alert.device_id ?? "Not available"}</dd>
              </div>
              <div>
                <dt className="inline">Location: </dt>
                <dd className="inline">
                  {locations.find((row) => row.id === alert.location_id)?.name
                    ?? alert.location_id
                    ?? "Unassigned"}
                </dd>
              </div>
              <div>
                <dt className="inline">Zone: </dt>
                <dd className="inline">
                  {zones.find((row) => row.id === alert.zone_id)?.name
                    ?? alert.zone_id
                    ?? "Unassigned"}
                </dd>
              </div>
            </dl>
          </li>
        ))}
      </ul>
    </section>
  );
}