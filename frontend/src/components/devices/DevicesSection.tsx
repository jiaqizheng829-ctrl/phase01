import { useEffect, useState } from "react";

import {
  getDevices,
  provisionDevices,
  type DeviceDto,
  type DeviceFamily,
} from "../../api/devices";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";
import DeviceList from "./DeviceList";

type Props = {
  onProvisioned?: () => void;
};

export default function DevicesSection({ onProvisioned }: Props) {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setDevices([]);

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
      } catch {
        if (!controller.signal.aborted) {
          setError("Could not load devices. Please try again.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, [family, reload]);

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
        <p
          role="alert"
          className="mt-4 rounded-lg bg-red-950 p-3 text-red-300"
        >
          {error}
        </p>
      )}

      {loading ? (
        <p role="status" className="mt-5 text-slate-400">
          Loading devices...
        </p>
      ) : (
        !error && <DeviceList devices={devices} />
      )}
    </section>
  );
}