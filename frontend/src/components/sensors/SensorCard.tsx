import { useEffect, useRef, useState } from "react";

import type { Sensor } from "../../api/sensors";
import {
  getReadings,
  readSensor,
  updateSampling,
  type ReadingDto,
} from "../../api/readings";

type Props = {
  sensor: Sensor;
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

export default function SensorCard({ sensor }: Props) {
  const [latest, setLatest] = useState<ReadingDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [reading, setReading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [interval, setIntervalValue] = useState(
    String(sensor.sampling_interval_seconds),
  );
  const [tracking, setTracking] = useState(sensor.tracking_enabled);
  const [savedTracking, setSavedTracking] = useState(
    sensor.tracking_enabled,
  );

  const [pollError, setPollError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const mounted = useRef(false);
  const isMqtt = sensor.default_config.protocol === "mqtt";

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const readings = await getReadings(
          sensor.id,
          1,
          controller.signal,
        );

        if (!controller.signal.aborted) {
          const incoming = readings[0];

          if (incoming) {
            setLatest((current) =>
              !current ||
              Date.parse(incoming.recorded_at) >=
                Date.parse(current.recorded_at)
                ? incoming
                : current,
            );
          }

          setPollError(null);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setPollError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);

          // Temporary polling; Phase 12 replaces this with WebSocket.
          timer = setTimeout(() => void poll(), 5000);
        }
      }
    }

    void poll();

    return () => {
      controller.abort();
      if (timer !== undefined) {
        clearTimeout(timer);
      }
    };
  }, [sensor.id]);

  async function handleRead() {
    setReading(true);
    setActionError(null);
    setNotice(null);

    try {
      const result = await readSensor(sensor.id);

      if (mounted.current) {
        setLatest((current) =>
          !current ||
          Date.parse(result.recorded_at) >=
            Date.parse(current.recorded_at)
            ? result
            : current,
        );
        setNotice("Reading saved.");
      }
    } catch (error) {
      if (mounted.current) {
        setActionError(errorMessage(error));
      }
    } finally {
      if (mounted.current) {
        setReading(false);
      }
    }
  }

  async function handleSave() {
    const seconds = Number(interval);

    setActionError(null);
    setNotice(null);

    if (
      !Number.isInteger(seconds) ||
      seconds < 5 ||
      seconds > 2147483647
    ) {
      setActionError(
        "Enter a whole number between 5 and 2147483647 seconds.",
      );
      return;
    }

    setSaving(true);

    try {
      const saved = await updateSampling(sensor.id, {
        sampling_interval_seconds: seconds,
        tracking_enabled: tracking,
      });

      if (mounted.current) {
        setIntervalValue(String(saved.sampling_interval_seconds));
        setTracking(saved.tracking_enabled);
        setSavedTracking(saved.tracking_enabled);
        setNotice("Sampling settings saved.");
      }
    } catch (error) {
      if (mounted.current) {
        setActionError(errorMessage(error));
      }
    } finally {
      if (mounted.current) {
        setSaving(false);
      }
    }
  }

  return (
    <li className="min-w-0 rounded-lg border border-slate-700 bg-slate-800 p-4">
      <h3 className="font-semibold text-slate-100">
        {sensor.display_name}
      </h3>

      <p className="mt-1 text-sm text-slate-400">
        {sensor.device_type.replace(/_/g, " ")}
      </p>

      <div className="mt-4">
        {latest ? (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-2xl font-semibold text-emerald-400">
                {latest.value.toLocaleString(undefined, {
                  maximumFractionDigits: 4,
                })}{" "}
                <span className="text-sm">{latest.unit}</span>
              </p>

              <span className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-200">
                {latest.source}
              </span>
            </div>

            <p className="mt-2 text-xs text-slate-400">
              Last reading:{" "}
              {new Date(latest.recorded_at).toLocaleString()}
            </p>
          </>
        ) : (
          <p className="text-sm text-slate-400">
            {loading ? "Loading latest reading..." : "No stored readings yet."}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={() => void handleRead()}
        disabled={reading || isMqtt}
        className="mt-4 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {reading ? "Reading..." : "Read now"}
      </button>

      {isMqtt && (
        <p className="mt-2 text-xs text-slate-400">
          MQTT readings arrive from the device. Manual reads are unavailable.
        </p>
      )}

      <fieldset
        disabled={saving}
        className="mt-5 space-y-3 border-t border-slate-700 pt-4"
      >
        <label className="block text-sm text-slate-300">
          Sampling interval (seconds)
          <input
            type="number"
            min={5}
            max={2147483647}
            step={1}
            value={interval}
            onChange={(event) => {
              setIntervalValue(event.target.value);
              setNotice(null);
            }}
            className="mt-2 block w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </label>

        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={tracking}
            onChange={(event) => {
              setTracking(event.target.checked);
              setNotice(null);
            }}
            className="accent-emerald-500"
          />
          Tracking enabled
        </label>

        <button
          type="button"
          onClick={() => void handleSave()}
          className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-100 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save settings"}
        </button>
      </fieldset>

      {!savedTracking && (
        <p className="mt-3 text-xs text-amber-300">
          Tracking is off. Automatic sampling is paused; manual reads
          remain available for simulation sensors.
        </p>
      )}

      {notice && (
        <p role="status" className="mt-3 text-sm text-emerald-300">
          {notice}
        </p>
      )}

      {actionError && (
        <p role="alert" className="mt-3 text-sm text-red-300">
          {actionError}
        </p>
      )}

      {pollError && (
        <p role="alert" className="mt-3 text-sm text-red-300">
          Could not refresh the latest reading: {pollError}
        </p>
      )}
    </li>
  );
}