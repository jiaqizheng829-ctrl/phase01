const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type DeviceFamily = "simulation" | "edge";
export type DeviceRole = "sensor" | "actuator";

export type DeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: DeviceFamily;
  display_name: string;
  default_config: Record<string, unknown>;
  zone_id: string | null;
  location_id: string | null;
};

async function checkResponse(response: Response): Promise<void> {
  if (response.ok) return;

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
    // Keep the fallback message if the response is not JSON.
  }

  throw new Error(message);
}

export async function getDevices(
  family: DeviceFamily,
  role?: DeviceRole,
  signal?: AbortSignal,
): Promise<DeviceDto[]> {
  const params = new URLSearchParams({ family });

  if (role) {
    params.set("role", role);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/devices?${params.toString()}`,
    { signal },
  );

  await checkResponse(response);
  return response.json() as Promise<DeviceDto[]>;
}

export async function provisionDevices(
  family: DeviceFamily,
): Promise<DeviceDto[]> {
  const params = new URLSearchParams({ family });

  const response = await fetch(
    `${API_BASE_URL}/api/devices/provision?${params.toString()}`,
    { method: "POST" },
  );

  await checkResponse(response);
  return response.json() as Promise<DeviceDto[]>;
}

export async function assignDeviceZone(
  deviceId: string,
  zoneId: string | null,
): Promise<DeviceDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${encodeURIComponent(deviceId)}/zone`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zone_id: zoneId }),
    },
  );

  await checkResponse(response);
  return response.json() as Promise<DeviceDto>;
}