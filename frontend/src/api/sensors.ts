const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type Sensor = {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
};

type CreateSensorPayload = {
  type: "moisture" | "light";
  display_name?: string;
};

export async function getSensors(): Promise<Sensor[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`);

  if (!response.ok) {
    throw new Error("Could not load sensors.");
  }

  return response.json() as Promise<Sensor[]>;
}

export async function createSensor(
  payload: CreateSensorPayload,
): Promise<Sensor> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Could not create sensor.");
  }

  return response.json() as Promise<Sensor>;
}
