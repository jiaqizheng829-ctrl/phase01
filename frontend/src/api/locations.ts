import type { DeviceDto } from "./devices";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type LocationSummary = {
  id: string;
  name: string;
};

export type ZoneInput = {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
};

export type ZoneRead = ZoneInput & {
  id: string;
  location_id: string;
};

export type LocationConfig = {
  location: LocationSummary;
  zones: ZoneRead[];
};

export type LocationCreateInput = {
  location_name: string;
  zones: ZoneInput[];
};

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((item: { msg: string }) => item.msg)
          .join("; ");
      }
    } catch {
      // Keep the fallback message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function jsonBody(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function locationPath(locationId: string): string {
  return `/api/locations/${encodeURIComponent(locationId)}`;
}

function zonePath(locationId: string, zoneId: string): string {
  return `${locationPath(locationId)}/zones/${encodeURIComponent(zoneId)}`;
}

export function getLocations(): Promise<LocationSummary[]> {
  return request<LocationSummary[]>("/api/locations");
}

export function getLocationConfig(
  locationId: string,
): Promise<LocationConfig> {
  return request<LocationConfig>(`${locationPath(locationId)}/config`);
}

export function createLocation(
  input: LocationCreateInput,
): Promise<LocationConfig> {
  return request<LocationConfig>(
    "/api/locations/config",
    jsonBody("POST", input),
  );
}

export function deleteLocation(locationId: string): Promise<void> {
  return request<void>(locationPath(locationId), {
    method: "DELETE",
  });
}

export function addZone(
  locationId: string,
  input: ZoneInput,
): Promise<ZoneRead> {
  return request<ZoneRead>(
    `${locationPath(locationId)}/zones`,
    jsonBody("POST", input),
  );
}

export function updateZone(
  locationId: string,
  zoneId: string,
  input: Partial<ZoneInput>,
): Promise<ZoneRead> {
  return request<ZoneRead>(
    zonePath(locationId, zoneId),
    jsonBody("PATCH", input),
  );
}

export function deleteZone(
  locationId: string,
  zoneId: string,
): Promise<void> {
  return request<void>(zonePath(locationId, zoneId), {
    method: "DELETE",
  });
}

export function getZoneDevices(
  locationId: string,
  zoneId: string,
): Promise<DeviceDto[]> {
  return request<DeviceDto[]>(
    `${zonePath(locationId, zoneId)}/devices`,
  );
}