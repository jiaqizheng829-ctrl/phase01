const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type ReadingDto = {
  device_id: string;
  value: number;
  unit: string;
  source: "simulation" | "vendor" | "mqtt";
  recorded_at: string;
};

export type SamplingSettings = {
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
};

export type SamplingDto = SamplingSettings & {
  device_id: string;
};

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    try {
      const body: unknown = await response.json();

      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP status message if the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function readSensor(
  deviceId: string,
): Promise<ReadingDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/sensors/${encodeURIComponent(deviceId)}/read`,
    { method: "POST" },
  );

  return readResponse<ReadingDto>(response);
}

export async function getReadings(
  deviceId: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<ReadingDto[]> {
  const params = new URLSearchParams({ limit: String(limit) });

  const response = await fetch(
    `${API_BASE_URL}/api/sensors/${encodeURIComponent(deviceId)}/readings?${params}`,
    { signal },
  );

  return readResponse<ReadingDto[]>(response);
}

export async function updateSampling(
  deviceId: string,
  settings: SamplingSettings,
): Promise<SamplingDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${encodeURIComponent(deviceId)}/sampling`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    },
  );

  return readResponse<SamplingDto>(response);
}