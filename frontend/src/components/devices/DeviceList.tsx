import type { DeviceDto } from "../../api/devices";

type Props = {
  devices: DeviceDto[];
};

export default function DeviceList({ devices }: Props) {
  if (devices.length === 0) {
    return (
      <p className="mt-5 text-slate-400">
        No devices in this family yet.
      </p>
    );
  }

  return (
    <ul className="mt-5 grid gap-3 sm:grid-cols-2">
      {devices.map((device) => (
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
        </li>
      ))}
    </ul>
  );
}