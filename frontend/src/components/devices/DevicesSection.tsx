import { useEffect, useState } from "react";

import {
  assignDeviceZone,
  getDevices,
  provisionDevices,
  type DeviceDto,
  type DeviceFamily,
} from "../../api/devices";
import {
  getLocationConfig,
  getLocations,
  type LocationConfig,
} from "../../api/locations";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";
import DeviceList from "./DeviceList";

type Props = {
  onProvisioned?: () => void;
  refreshKey?: number;
  onAssignmentChanged?: () => void;
};

export default function DevicesSection({
  onProvisioned,
  refreshKey = 0,
  onAssignmentChanged,
}: Props) {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [configurations, setConfigurations] = useState<LocationConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [assignmentsLoading, setAssignmentsLoading] = useState(true);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zoneError, setZoneError] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError(null);

    async function load() {
      try {
        const result = await getDevices(
          family,
          undefined,
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setDevices(result);
        }
      } catch (caught) {
        if (!controller.signal.aborted) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Could not load devices.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => controller.abort();
  }, [family, reload, refreshKey]);

  useEffect(() => {
    let active = true;

    setAssignmentsLoading(true);
    setZoneError("");

    async function loadZones() {
      try {
        const locations = await getLocations();
        const configs = await Promise.all(
          locations.map((location) => getLocationConfig(location.id)),
        );

        if (active) setConfigurations(configs);
      } catch (caught) {
        if (active) {
          setConfigurations([]);
          setZoneError(
            caught instanceof Error
              ? caught.message
              : "Could not load zones. Click Refresh to retry.",
          );
        }
      } finally {
        if (active) setAssignmentsLoading(false);
      }
    }

    void loadZones();

    return () => {
      active = false;
    };
  }, [reload, refreshKey]);

  function changeFamily(nextFamily: DeviceFamily) {
    setDevices([]);
    setLoading(true);
    setError(null);
    setNotice(null);
    setFamily(nextFamily);
  }

  function refreshDevices() {
    setError(null);
    setLoading(true);
    setReload((current) => current + 1);
  }

  async function handleProvision() {
    setProvisioning(true);
    setError(null);
    setNotice(null);

    try {
      const created = await provisionDevices(family);
      setNotice(
        `Created ${created.length} devices in the ${family} family.`,
      );
      refreshDevices();
      onProvisioned?.();
    } catch {
      setError(
        "Could not confirm kit creation. Refresh the list before trying again.",
      );
    } finally {
      setProvisioning(false);
    }
  }

  async function handleAssign(deviceId: string, zoneId: string | null) {
    const updated = await assignDeviceZone(deviceId, zoneId);

    setDevices((current) =>
      current.map((device) =>
        device.id === updated.id ? updated : device,
      ),
    );

    onAssignmentChanged?.();
  }

  return (
    <section
      id="devices"
      className="rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">
            Devices
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Each kit adds two sensors and two actuators.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <DeviceFamilySwitcher
            family={family}
            onChange={changeFamily}
            disabled={provisioning}
          />

          <button
            type="button"
            onClick={refreshDevices}
            disabled={loading || provisioning}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 disabled:opacity-50"
          >
            Refresh
          </button>

          <button
            type="button"
            onClick={() => void handleProvision()}
            disabled={loading || provisioning}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {provisioning ? "Creating kit..." : "Create device kit"}
          </button>
        </div>
      </div>

      {notice && (
        <p role="status" className="mt-4 text-emerald-300">
          {notice}
        </p>
      )}

      {error && (
        <p role="alert" className="mt-4 rounded-lg bg-red-950 p-3 text-red-300">
          {error}
        </p>
      )}

      {zoneError && (
        <p role="alert" className="mt-4 text-red-300">
          {zoneError}
        </p>
      )}

      {loading ? (
        <p role="status" className="mt-5 text-slate-400">
          Loading devices...
        </p>
      ) : (
        !error && (
          <DeviceList
            devices={devices}
            configurations={configurations}
            assignmentsLoading={
              assignmentsLoading || Boolean(zoneError) || provisioning
            }
            onAssign={handleAssign}
          />
        )
      )}
    </section>
  );
}