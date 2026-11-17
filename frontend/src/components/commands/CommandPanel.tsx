import { useEffect, useRef, useState } from "react";

import {
  executeCommand,
  getCommandHistory,
  type CommandLogDto,
  type CommandType,
} from "../../api/commands";
import { getDevices, type DeviceDto } from "../../api/devices";

interface Props {
  refreshKey?: number;
  onChanged?: () => void;
}

const buttonClass =
  "rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white " +
  "disabled:cursor-not-allowed disabled:opacity-40";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

export default function CommandPanel({
  refreshKey = 0,
  onChanged,
}: Props) {
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [history, setHistory] = useState<CommandLogDto[]>([]);
  const [levels, setLevels] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const mounted = useRef(false);
  const requestNumber = useRef(0);
  const submitting = useRef(false);

  async function reload() {
    const current = ++requestNumber.current;
    setLoading(true);
    setError(null);

    try {
      const [simulation, edge, rows] = await Promise.all([
        getDevices("simulation", "actuator"),
        getDevices("edge", "actuator"),
        getCommandHistory(),
      ]);

      if (!mounted.current || current !== requestNumber.current) return;

      setDevices([...simulation, ...edge]);
      setHistory(rows);
    } catch (err) {
      if (mounted.current && current === requestNumber.current) {
        setError(errorMessage(err));
      }
    } finally {
      if (mounted.current && current === requestNumber.current) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      requestNumber.current += 1;
    };
  }, []);

  useEffect(() => {
    void reload();
  }, [refreshKey]);

  async function submit(device: DeviceDto, type: CommandType) {
    if (
      submitting.current ||
      loading ||
      !device.allowed_commands.includes(type)
    ) {
      return;
    }

    const payload: Record<string, unknown> = {};

    if (type === "set_light_level") {
      const value = levels[device.id] ?? "1";
      const level = Number(value);

      if (value.trim() === "" || !Number.isFinite(level)) {
        setError("Enter a valid light level.");
        return;
      }

      payload.level = level;
    }

    submitting.current = true;
    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      const result = await executeCommand({
        command_type: type,
        device_id: device.id,
        payload,
      });

      if (mounted.current) {
        setNotice(
          `${result.status}: ${result.command_type}` +
            (result.error_message ? ` — ${result.error_message}` : ""),
        );
      }
    } catch (err) {
      if (mounted.current) {
        setNotice(
          `Could not confirm the command result: ${errorMessage(err)}. ` +
            "Check the refreshed history before retrying.",
        );
      }
    } finally {
      if (mounted.current) {
        await reload();
      }

      submitting.current = false;

      if (mounted.current) {
        setBusy(false);
        onChanged?.();
      }
    }
  }

  function disabled(device: DeviceDto, type: CommandType) {
    return busy || loading || !device.allowed_commands.includes(type);
  }

  return (
    <section
      id="controls"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-100">Controls</h2>
        <button
          type="button"
          className={buttonClass}
          disabled={busy || loading}
          onClick={() => void reload()}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <p className="mt-2 text-sm text-slate-400">
        Available actions depend on each actuator's current state.
      </p>

      {error && (
        <p role="alert" className="mt-4 rounded-lg bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      {notice && (
        <p role="status" className="mt-4 rounded-lg bg-slate-800 p-3 text-slate-100">
          {notice}
        </p>
      )}

      {loading && (
        <p role="status" className="mt-4 text-slate-400">
          Refreshing actuators and history...
        </p>
      )}

      {!loading && !error && devices.length === 0 && (
        <p className="mt-4 text-slate-400">No actuators found.</p>
      )}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {devices.map((device) => (
          <article
            key={device.id}
            className="rounded-lg border border-slate-700 bg-slate-800 p-4"
          >
            <h3 className="font-semibold text-slate-100">
              {device.display_name}
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              {device.device_family} · State: {device.state ?? "unknown"}
            </p>

            <div className="mt-4 flex flex-wrap items-end gap-2">
              {device.device_type === "water_pump" && (
                <>
                  <button
                    type="button"
                    className={buttonClass}
                    disabled={disabled(device, "start_pump")}
                    onClick={() => void submit(device, "start_pump")}
                  >
                    Start pump
                  </button>
                  <button
                    type="button"
                    className={buttonClass}
                    disabled={disabled(device, "stop_pump")}
                    onClick={() => void submit(device, "stop_pump")}
                  >
                    Stop pump
                  </button>
                </>
              )}

              {device.device_type === "grow_light" && (
                <>
                  <label className="text-sm text-slate-300">
                    Light level
                    <input
                      type="number"
                      step="any"
                      value={levels[device.id] ?? "1"}
                      disabled={busy || loading}
                      onChange={(event) => {
                        const value = event.target.value;
                        setLevels((current) => ({
                          ...current,
                          [device.id]: value,
                        }));
                      }}
                      className="mt-1 block w-28 rounded border border-slate-600 bg-slate-950 px-3 py-2 text-white"
                    />
                  </label>
                  <button
                    type="button"
                    className={buttonClass}
                    disabled={disabled(device, "set_light_level")}
                    onClick={() => void submit(device, "set_light_level")}
                  >
                    Set light level
                  </button>
                </>
              )}
            </div>
          </article>
        ))}
      </div>

      <h3 className="mt-8 text-lg font-semibold text-slate-100">
        Command history
      </h3>
      <p className="mt-1 text-sm text-slate-400">
        Latest 50 attempts, newest first.
      </p>

      {!loading && !error && history.length === 0 && (
        <p className="mt-4 text-slate-400">No commands have been recorded.</p>
      )}

      {history.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-600 text-slate-100">
              <tr>
                <th className="p-3">Time</th>
                <th className="p-3">Device</th>
                <th className="p-3">Command</th>
                <th className="p-3">Payload</th>
                <th className="p-3">Status</th>
                <th className="p-3">Message</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id} className="border-b border-slate-800">
                  <td className="whitespace-nowrap p-3">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="p-3" title={row.device_id}>
                    {devices.find((device) => device.id === row.device_id)
                      ?.display_name ?? row.device_id}
                  </td>
                  <td className="p-3">{row.command_type}</td>
                  <td className="p-3">
                    <code>{JSON.stringify(row.payload)}</code>
                  </td>
                  <td
                    className={`p-3 font-semibold ${
                      row.status === "success"
                        ? "text-emerald-400"
                        : row.status === "rejected"
                          ? "text-amber-400"
                          : "text-red-400"
                    }`}
                  >
                    {row.status}
                  </td>
                  <td className="p-3">{row.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}