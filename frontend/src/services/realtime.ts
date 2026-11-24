export type RealtimeEvent = {
  type: string;
  payload: unknown;
};

export function subscribeRealtime(
  _onEvent: (event: RealtimeEvent) => void,
): () => void {
  // Phase 11: no-op. EventFeed polls the alerts API.
  // Phase 12 replaces this with the dashboard WebSocket connection.
  return () => {};
}