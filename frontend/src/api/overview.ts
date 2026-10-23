const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type OverviewDeviceDto = {
  id: string;
  device_type: string;
  role: "sensor" | "actuator";
  display_name: string;
};

export type LatestReadingDto = {
  device_id: string;
  value: number;
  unit: string;
  recorded_at: string;
  tracking_enabled: boolean;
  sampling_interval_seconds: number;
};

export type OverviewZoneDto = {
  id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  devices: OverviewDeviceDto[];
  latest_readings: LatestReadingDto[];
};

export type LocationOverviewDto = {
  location: {
    id: string;
    name: string;
  };
  device_counts: {
    sensor: number;
    actuator: number;
  };
  zones: OverviewZoneDto[];
  strategy_key: string | null;
  last_recommendation: {
    action: "irrigate" | "wait";
    reason: string;
  } | null;
};

export async function fetchOverview(
  locationId: string,
  signal?: AbortSignal,
): Promise<LocationOverviewDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${encodeURIComponent(locationId)}/overview`,
    { signal },
  );

  if (!response.ok) {
    let message = `Could not load overview (${response.status}).`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // Keep the fallback message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<LocationOverviewDto>;
}