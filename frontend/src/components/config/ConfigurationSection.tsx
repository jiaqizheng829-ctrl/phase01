import { useEffect, useState } from "react";
import {
  addZone,
  deleteLocation,
  getLocationConfig,
  getLocations,
  type LocationConfig,
  type LocationSummary,
  type ZoneInput,
} from "../../api/locations";
import LocationConfigWizard from "./LocationConfigWizard";
import ZoneCard from "./ZoneCard";
import ZoneForm from "./ZoneForm";

type Props = {
  refreshKey: number;
  onChanged: () => void;
};

export default function ConfigurationSection({
  refreshKey,
  onChanged,
}: Props) {
  const [locations, setLocations] = useState<LocationSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [config, setConfig] = useState<LocationConfig | null>(null);
  const [creating, setCreating] = useState(false);
  const [addingZone, setAddingZone] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [configLoading, setConfigLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [listError, setListError] = useState("");
  const [configError, setConfigError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    setListLoading(true);
    setListError("");

    getLocations()
      .then((result) => {
        if (!active) return;

        setLocations(result);
        setSelectedId((current) =>
          result.some((location) => location.id === current) ? current : "",
        );
      })
      .catch((caught) => {
        if (active) {
          setListError(
            caught instanceof Error
              ? caught.message
              : "Could not load locations.",
          );
        }
      })
      .finally(() => {
        if (active) setListLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshKey]);

  useEffect(() => {
    let active = true;
    setConfig(null);
    setConfigError("");

    if (!selectedId) {
      setConfigLoading(false);
      return;
    }

    setConfigLoading(true);

    getLocationConfig(selectedId)
      .then((result) => {
        if (active) setConfig(result);
      })
      .catch((caught) => {
        if (active) {
          setConfigError(
            caught instanceof Error
              ? caught.message
              : "Could not load configuration.",
          );
        }
      })
      .finally(() => {
        if (active) setConfigLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedId, refreshKey]);

  function handleCreated(created: LocationConfig) {
    setLocations((current) => [created.location, ...current]);
    setSelectedId(created.location.id);
    setCreating(false);
    setAddingZone(false);
    setActionError("");
    setNotice("Location created.");
    onChanged();
  }

  async function handleAddZone(input: ZoneInput) {
    await addZone(selectedId, input);
    setAddingZone(false);
    setNotice("Zone added.");
    onChanged();
  }

  async function handleDeleteLocation() {
    if (!config) return;

    const location = config.location;

    if (
      !window.confirm(
        `Delete "${location.name}" and all its zones? Devices will remain unassigned.`,
      )
    ) {
      return;
    }

    setDeleting(true);
    setActionError("");
    setNotice("");

    try {
      await deleteLocation(location.id);
      setLocations((current) =>
        current.filter((item) => item.id !== location.id),
      );
      setSelectedId("");
      setConfig(null);
      setAddingZone(false);
      setNotice("Location deleted.");
      onChanged();
    } catch (caught) {
      setActionError(
        caught instanceof Error
          ? caught.message
          : "Could not delete location.",
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <section
      id="configuration"
      className="space-y-5 rounded-xl border border-slate-700 bg-slate-900 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-100">
          Configuration
        </h2>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onChanged}
            disabled={listLoading || deleting}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 disabled:opacity-50"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={() => {
              setCreating(true);
              setNotice("");
              setActionError("");
            }}
            disabled={creating || deleting}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            New location
          </button>
        </div>
      </div>

      {notice && (
        <p role="status" className="text-emerald-300">{notice}</p>
      )}
      {actionError && (
        <p role="alert" className="text-red-300">{actionError}</p>
      )}

      {creating && (
        <LocationConfigWizard
          onCreated={handleCreated}
          onCancel={() => setCreating(false)}
        />
      )}

      {listError && (
        <p role="alert" className="text-red-300">{listError}</p>
      )}
      {listLoading && (
        <p className="text-slate-400">Loading locations...</p>
      )}
      {!listLoading && !listError && locations.length === 0 && (
        <p className="text-slate-400">No locations yet. Create one above.</p>
      )}

      <label className="block text-sm text-slate-300">
        Select location
        <select
          value={selectedId}
          disabled={listLoading || deleting}
          onChange={(event) => {
            setSelectedId(event.target.value);
            setConfig(null);
            setAddingZone(false);
            setNotice("");
            setActionError("");
          }}
          className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-800 p-2 text-slate-100"
        >
          <option value="">Choose a location</option>
          {locations.map((location) => (
            <option key={location.id} value={location.id}>
              {location.name}
            </option>
          ))}
        </select>
      </label>

      {configLoading && (
        <p className="text-slate-400">Loading configuration...</p>
      )}
      {configError && (
        <p role="alert" className="text-red-300">{configError}</p>
      )}

      {config && (
        <fieldset disabled={deleting} className="space-y-4">
          <p className="break-all text-sm text-slate-400">
            Location ID: {config.location.id}
          </p>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setAddingZone(true)}
              disabled={addingZone}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50"
            >
              Add zone
            </button>
            <button
              type="button"
              onClick={() => void handleDeleteLocation()}
              className="rounded-lg border border-red-800 px-3 py-2 text-sm text-red-300"
            >
              {deleting ? "Deleting..." : "Delete location"}
            </button>
          </div>

          {addingZone && (
            <ZoneForm
              key={selectedId}
              submitLabel="Save new zone"
              onSubmit={handleAddZone}
              onCancel={() => setAddingZone(false)}
            />
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {config.zones.map((zone) => (
              <ZoneCard
                key={zone.id}
                zone={zone}
                isLastZone={config.zones.length === 1}
                refreshKey={refreshKey}
                onChanged={onChanged}
              />
            ))}
          </div>
        </fieldset>
      )}
    </section>
  );
}