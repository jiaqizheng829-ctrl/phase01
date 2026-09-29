import { useState } from "react";
import type { DeviceDto } from "../../api/devices";
import type { LocationConfig } from "../../api/locations";

type Props = {
  devices: DeviceDto[];
  configurations?: LocationConfig[];
  assignmentsLoading?: boolean;
  onAssign?: (deviceId: string, zoneId: string | null) => Promise<void>;
};

export default function DeviceList({
  devices,
  configurations = [],
  assignmentsLoading = false,
  onAssign,
}: Props) {
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function changeZone(deviceId: string, value: string) {
    if (!onAssign) return;

    setSavingId(deviceId);
    setError("");
    setNotice("");

    try {
      await onAssign(deviceId, value || null);
      setNotice("Device assignment updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not update assignment.",
      );
    } finally {
      setSavingId(null);
    }
  }

  if (devices.length === 0) {
    return (
      <p className="mt-5 text-slate-400">
        No devices in this family yet.
      </p>
    );
  }

  return (
    <div>
      {error && (
        <p role="alert" className="mt-4 text-red-300">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-4 text-emerald-300">
          {notice}
        </p>
      )}

      <ul className="mt-5 grid gap-3 sm:grid-cols-2">
        {devices.map((device) => {
          const knownZone = configurations.some((config) =>
            config.zones.some((zone) => zone.id === device.zone_id),
          );

          return (
            <li
              key={device.id}
              className="rounded-lg border border-slate-700 bg-slate-800 p-4"
            >
              <h3 className="font-semibold text-slate-100">
                {device.display_name}
              </h3>

              <p className="mt-1 text-sm text-slate-400">
                {device.device_type.replace(/_/g, " ")}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-emerald-950 px-3 py-1 text-xs text-emerald-300">
                  {device.role}
                </span>
                <span className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-200">
                  {device.device_family}
                </span>
              </div>

              {onAssign && (
                <label className="mt-4 block text-sm text-slate-300">
                  Assigned zone
                  <select
                    value={device.zone_id ?? ""}
                    disabled={assignmentsLoading || savingId !== null}
                    onChange={(event) =>
                      void changeZone(device.id, event.target.value)
                    }
                    className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 p-2 text-slate-100 disabled:opacity-50"
                  >
                    <option value="">Unassigned</option>

                    {device.zone_id && !knownZone && (
                      <option value={device.zone_id} disabled>
                        {assignmentsLoading
                          ? "Loading current zone..."
                          : "Current zone unavailable — refresh"}
                      </option>
                    )}

                    {configurations.map((config) => (
                      <optgroup
                        key={config.location.id}
                        label={config.location.name}
                      >
                        {config.zones.map((zone) => (
                          <option key={zone.id} value={zone.id}>
                            {config.location.name} — {zone.name}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>

                  {savingId === device.id && (
                    <span className="mt-1 block text-emerald-300">
                      Saving...
                    </span>
                  )}
                </label>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}