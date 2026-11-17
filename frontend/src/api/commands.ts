const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type CommandType =
  | "start_pump"
  | "stop_pump"
  | "set_light_level";

export type CommandStatus = "success" | "failed" | "rejected";

export interface CommandRequest {
  command_type: CommandType;
  device_id: string;
  payload?: Record<string, unknown>;
}

export interface CommandLogDto {
  id: string;
  command_type: string;
  device_id: string;
  payload: Record<string, unknown>;
  status: CommandStatus;
  error_message: string | null;
  created_at: string;
}

async function responseError(response: Response): Promise<Error> {
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

  return new Error(message);
}

export async function executeCommand(
  command: CommandRequest,
): Promise<CommandLogDto> {
  const response = await fetch(`${API_BASE_URL}/api/commands`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(command),
  });

  // A rejected command returns its saved log row with HTTP 409.
  if (!response.ok && response.status !== 409) {
    throw await responseError(response);
  }

  return (await response.json()) as CommandLogDto;
}

export async function getCommandHistory(
  limit = 50,
  signal?: AbortSignal,
): Promise<CommandLogDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/commands?limit=${limit}`,
    { signal },
  );

  if (!response.ok) {
    throw await responseError(response);
  }

  return (await response.json()) as CommandLogDto[];
}