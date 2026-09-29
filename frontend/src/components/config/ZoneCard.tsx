import { useEffect, useState } from "react";
import type { DeviceDto } from "../../api/devices";
import {
  deleteZone,
  getZoneDevices,
  updateZone,
  type ZoneInput,
  type ZoneRead,
} from "../../api/locations";
import ZoneForm from "./ZoneForm";

type Props = {
  zone: ZoneRead;
  isLastZone: boolean;
  refreshKey: number;
  onChanged: () => void;
};

export default function ZoneCard({
  zone,
  isLastZone,
  refreshKey,
  onChanged,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [deviceError, setDeviceError] = useState("");
  const [notice, setNotice] = useState("");
  const [deviceReload, setDeviceReload] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setDeviceError("");

    getZoneDevices(zone.location_id, zone.id)
      .then((result) => {
        if (active) setDevices(result);
      })
      .catch((caught) => {
        if (active) {
          setDeviceError(
            caught instanceof Error
              ? caught.message
              : "Could not load devices.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [zone.location_id, zone.id, refreshKey, deviceReload]);

  async function saveZone(input: ZoneInput) {
    await updateZone(zone.location_id, zone.id, input);
    setEditing(false);
    setNotice("Zone updated.");
    setError("");
    onChanged();
  }

  async function removeZone() {
    setError("");
    setNotice("");

    if (isLastZone) {
      setError("The last zone cannot be deleted.");
      return;
    }

    if (!window.confirm(`Delete "${zone.name}"? Its devices will be unassigned.`)) {
      return;
    }

    setDeleting(true);

    try {
      await deleteZone(zone.location_id, zone.id);
      onChanged();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Could not delete zone.",
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <article className="space-y-3 rounded-lg border border-slate-700 bg-slate-800 p-4">
      {editing ? (
        <ZoneForm
          initial={zone}
          submitLabel="Save changes"
          onSubmit={saveZone}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <>
          <h4 className="font-semibold text-slate-100">{zone.name}</h4>

          <p className="text-sm text-slate-300">
            Moisture: {zone.moisture_threshold_low}–
            {zone.moisture_threshold_high}
          </p>

          <details className="text-sm text-slate-400">
            <summary className="cursor-pointer">Schedule</summary>
            <pre className="mt-2 overflow-auto">
              {JSON.stringify(zone.schedule, null, 2)}
            </pre>
          </details>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={deleting}
              onClick={() => {
                setError("");
                setNotice("");
                setEditing(true);
              }}
              className="rounded-lg border border-slate-500 px-3 py-2 text-sm text-slate-100 disabled:opacity-50"
            >
              Edit
            </button>

            <button
              type="button"
              disabled={deleting || isLastZone}
              onClick={() => void removeZone()}
              className="rounded-lg border border-red-800 px-3 py-2 text-sm text-red-300 disabled:opacity-50"
            >
              {deleting ? "Deleting..." : "Delete zone"}
            </button>
          </div>

          {isLastZone && (
            <p className="text-sm text-slate-400">
              Keep at least one zone in this location.
            </p>
          )}
        </>
      )}

      {error && <p role="alert" className="text-red-300">{error}</p>}
      {notice && <p role="status" className="text-emerald-300">{notice}</p>}

      <div className="border-t border-slate-700 pt-3">
        <div className="flex items-center justify-between gap-2">
          <h5 className="text-sm font-medium text-slate-200">
            Assigned devices
          </h5>
          <button
            type="button"
            disabled={loading}
            onClick={() => setDeviceReload((current) => current + 1)}
            className="text-sm text-emerald-400 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <p className="mt-2 text-sm text-slate-400">Loading devices...</p>
        ) : deviceError ? (
          <p role="alert" className="mt-2 text-sm text-red-300">
            {deviceError}
          </p>
        ) : devices.length === 0 ? (
          <p className="mt-2 text-sm text-slate-400">No assigned devices.</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm text-slate-300">
            {devices.map((device) => (
              <li key={device.id}>{device.display_name}</li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}