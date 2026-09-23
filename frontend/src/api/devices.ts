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
};

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

  if (!response.ok) {
    throw new Error("Could not load devices.");
  }

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

  if (!response.ok) {
    throw new Error("Could not provision the device kit.");
  }

  return response.json() as Promise<DeviceDto[]>;
}