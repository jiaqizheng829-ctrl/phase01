import { useState } from "react";
import type { FormEvent } from "react";
import type { ZoneInput } from "../../api/locations";

type Props = {
  initial?: ZoneInput;
  submitLabel: string;
  onSubmit: (zone: ZoneInput) => Promise<void>;
  onCancel?: () => void;
};

export default function ZoneForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [low, setLow] = useState(
    String(initial?.moisture_threshold_low ?? 0.2),
  );
  const [high, setHigh] = useState(
    String(initial?.moisture_threshold_high ?? 0.8),
  );
  const [schedule, setSchedule] = useState(
    JSON.stringify(initial?.schedule ?? {}, null, 2),
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const cleanName = name.trim();
    const lowValue = Number(low);
    const highValue = Number(high);

    if (!cleanName || cleanName.length > 128) {
      setError("Enter a zone name of 1–128 characters.");
      return;
    }

    if (
      !low.trim() ||
      !high.trim() ||
      !Number.isFinite(lowValue) ||
      !Number.isFinite(highValue) ||
      lowValue < 0 ||
      highValue > 1 ||
      lowValue >= highValue
    ) {
      setError("Thresholds must satisfy 0 ≤ low < high ≤ 1.");
      return;
    }

    let parsedSchedule: Record<string, unknown>;

    try {
      const parsed = JSON.parse(schedule);
      if (
        parsed === null ||
        typeof parsed !== "object" ||
        Array.isArray(parsed)
      ) {
        throw new Error("Invalid schedule");
      }
      parsedSchedule = parsed;
    } catch {
      setError('Schedule must be a JSON object, such as {}.');
      return;
    }

    setSaving(true);

    try {
      await onSubmit({
        name: cleanName,
        moisture_threshold_low: lowValue,
        moisture_threshold_high: highValue,
        schedule: parsedSchedule,
      });
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Could not save zone.",
      );
    } finally {
      setSaving(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-lg border border-slate-600 bg-slate-800 p-2 text-slate-100";

  return (
    <form onSubmit={handleSubmit} className="space-y-3" noValidate>
      <fieldset disabled={saving} className="space-y-3">
        <label className="block text-sm text-slate-300">
          Zone name
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={inputClass}
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm text-slate-300">
            Moisture low (0–1)
            <input
              type="number"
              step="0.0001"
              min="0"
              max="1"
              value={low}
              onChange={(event) => setLow(event.target.value)}
              className={inputClass}
            />
          </label>

          <label className="block text-sm text-slate-300">
            Moisture high (0–1)
            <input
              type="number"
              step="0.0001"
              min="0"
              max="1"
              value={high}
              onChange={(event) => setHigh(event.target.value)}
              className={inputClass}
            />
          </label>
        </div>

        <label className="block text-sm text-slate-300">
          Schedule (JSON object)
          <textarea
            rows={3}
            value={schedule}
            onChange={(event) => setSchedule(event.target.value)}
            className={inputClass}
          />
        </label>

        {error && (
          <p role="alert" className="text-sm text-red-300">
            {error}
          </p>
        )}

        <div className="flex gap-2">
          <button
            type="submit"
            className="rounded-lg bg-emerald-600 px-3 py-2 text-white disabled:opacity-50"
          >
            {saving ? "Saving..." : submitLabel}
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-slate-600 px-3 py-2 text-slate-200"
            >
              Cancel
            </button>
          )}
        </div>
      </fieldset>
    </form>
  );
}