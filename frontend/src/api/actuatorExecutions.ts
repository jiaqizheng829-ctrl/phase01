const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface ActuatorExecutionDto {
  id: string;
  device_id: string;
  success: boolean;
  policy_applied: string[];
  message: string | null;
  created_at: string;
}

export async function getActuatorExecutions(
  limit = 20,
  signal?: AbortSignal,
): Promise<ActuatorExecutionDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/actuators/executions?limit=${limit}`,
    { signal },
  );

  if (!response.ok) {
    throw new Error("Could not load execution logs.");
  }

  return (await response.json()) as ActuatorExecutionDto[];
}