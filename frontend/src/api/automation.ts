const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type StrategyKey = "conservative" | "aggressive";

export type StrategySettingsDto = {
  location_id: string;
  strategy_key: StrategyKey | null;
};

export type ZoneRecommendationDto = {
  zone_id: string;
  latest_moisture: number | null;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  action: "irrigate" | "wait";
  reason: string;
};

export type EvaluationDto = {
  location_id: string;
  strategy_key: StrategyKey;
  action: "irrigate" | "wait";
  reason: string;
  zones: ZoneRecommendationDto[];
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
      // Keep the fallback message if the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

function automationPath(locationId: string): string {
  return `/api/locations/${encodeURIComponent(locationId)}/automation`;
}

export function getAutomationSettings(
  locationId: string,
  signal?: AbortSignal,
): Promise<StrategySettingsDto> {
  return request<StrategySettingsDto>(
    automationPath(locationId),
    { signal },
  );
}

export function saveAutomationSettings(
  locationId: string,
  strategyKey: StrategyKey,
  signal?: AbortSignal,
): Promise<StrategySettingsDto> {
  return request<StrategySettingsDto>(
    automationPath(locationId),
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ strategy_key: strategyKey }),
      signal,
    },
  );
}

export function evaluateAutomation(
  locationId: string,
  signal?: AbortSignal,
): Promise<EvaluationDto> {
  return request<EvaluationDto>(
    `${automationPath(locationId)}/evaluate`,
    {
      method: "POST",
      signal,
    },
  );
}