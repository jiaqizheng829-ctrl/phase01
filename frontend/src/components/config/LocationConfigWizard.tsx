import { useState } from "react";
import {
  createLocation,
  type LocationConfig,
  type ZoneInput,
} from "../../api/locations";
import ZoneForm from "./ZoneForm";

type Props = {
  onCreated: (config: LocationConfig) => void;
  onCancel: () => void;
};

export default function LocationConfigWizard({
  onCreated,
  onCancel,
}: Props) {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [zones, setZones] = useState<ZoneInput[]>([]);
  const [formVersion, setFormVersion] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function nextStep() {
    const cleaned = name.trim();

    if (!cleaned || cleaned.length > 128) {
      setError("Enter a location name of 1–128 characters.");
      return;
    }

    setName(cleaned);
    setError("");
    setStep(2);
  }

  async function addDraftZone(zone: ZoneInput) {
    if (zones.some((existing) => existing.name === zone.name)) {
      throw new Error("Zone names must be unique within this location.");
    }

    setZones((current) => [...current, zone]);
    setFormVersion((current) => current + 1);
    setError("");
  }

  async function saveLocation() {
    if (zones.length === 0) {
      setError("Add at least one zone before creating the location.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const config = await createLocation({
        location_name: name,
        zones,
      });
      onCreated(config);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not create location.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-600 p-4">
      <h3 className="text-lg font-semibold text-slate-100">
        New location — Step {step} of 2
      </h3>

      {step === 1 ? (
        <div className="space-y-3">
          <label className="block text-sm text-slate-300">
            Location name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-800 p-2 text-slate-100"
            />
          </label>

          <button
            type="button"
            onClick={nextStep}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-white"
          >
            Next: add zones
          </button>
        </div>
      ) : (
        <fieldset disabled={saving} className="space-y-4">
          <p className="text-slate-300">
            Location: <strong>{name}</strong>
          </p>

          <ZoneForm
            key={formVersion}
            submitLabel="Add zone to draft"
            onSubmit={addDraftZone}
          />

          <div>
            <h4 className="font-medium text-slate-100">
              Zones ready to save ({zones.length})
            </h4>

            {zones.length === 0 ? (
              <p className="mt-2 text-sm text-slate-400">
                Fill in the zone form and click Add zone to draft.
              </p>
            ) : (
              <ul className="mt-2 space-y-2">
                {zones.map((zone, index) => (
                  <li
                    key={zone.name}
                    className="flex items-center justify-between gap-3 rounded-lg bg-slate-800 p-3"
                  >
                    <span className="text-sm text-slate-200">
                      {zone.name}: {zone.moisture_threshold_low}–
                      {zone.moisture_threshold_high}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setZones((current) =>
                          current.filter((_, itemIndex) => itemIndex !== index),
                        )
                      }
                      className="text-sm text-red-300"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <p className="text-sm text-slate-400">
            Only zones in the list above will be saved.
          </p>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                setError("");
                setStep(1);
              }}
              className="rounded-lg border border-slate-600 px-3 py-2 text-slate-200"
            >
              Back
            </button>

            <button
              type="button"
              onClick={() => void saveLocation()}
              disabled={saving || zones.length === 0}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-white disabled:opacity-50"
            >
              {saving ? "Creating..." : "Create location"}
            </button>
          </div>
        </fieldset>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-300">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={onCancel}
        disabled={saving}
        className="text-sm text-slate-300 underline disabled:opacity-50"
      >
        Cancel
      </button>
    </div>
  );
}