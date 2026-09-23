import type { DeviceFamily } from "../../api/devices";

type Props = {
  family: DeviceFamily;
  onChange: (family: DeviceFamily) => void;
  disabled?: boolean;
};

export default function DeviceFamilySwitcher({
  family,
  onChange,
  disabled = false,
}: Props) {
  return (
    <label className="flex items-center gap-3 text-sm text-slate-300">
      Device family
      <select
        value={family}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value as DeviceFamily)
        }
        className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-white disabled:opacity-50"
      >
        <option value="simulation">Simulation</option>
        <option value="edge">Edge</option>
      </select>
    </label>
  );
}