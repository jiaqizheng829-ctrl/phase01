const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface AlertDto {
  id: string;
  location_id: string | null;
  zone_id: string | null;
  device_id: string | null;
  severity: "info" | "warning" | "critical";
  message: string;
  event_type: string;
  status: "active" | "resolved";
  created_at: string;
}

export interface AlertFilters {
  status?: "active" | "resolved" | "all";
  location_id?: string;
  zone_id?: string;
  since?: string;
  limit?: number;
}

export async function getAlerts(
  filters: AlertFilters = {},
  signal?: AbortSignal,
): Promise<AlertDto[]> {
  const params = new URLSearchParams({
    status: filters.status ?? "active",
    limit: String(filters.limit ?? 50),
  });

  if (filters.location_id) {
    params.set("location_id", filters.location_id);
  }

  if (filters.zone_id) {
    params.set("zone_id", filters.zone_id);
  }

  if (filters.since) {
    params.set("since", filters.since);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/alerts?${params.toString()}`,
    { signal },
  );

  if (!response.ok) {
    throw new Error(`Could not load alerts (${response.status}).`);
  }

  return (await response.json()) as AlertDto[];
}