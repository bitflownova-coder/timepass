export type WSMessage =
  | { type: 'pong' }
  | { type: 'file_change'; data: { path: string; event_type: string; timestamp: string } }
  | { type: 'error_parsed'; data: any }
  | { type: string; data: any };

type MessageHandler = (msg: WSMessage) => void;

export class EngineWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private workspacePath: string;
  private pingInterval: ReturnType<typeof setInterval> | null = null;

  constructor(workspacePath: string) {
    this.workspacePath = workspacePath;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const url = `ws://127.0.0.1:7779/ws/${encodeURIComponent(this.workspacePath)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Connected to Copilot Engine');
      // Start ping every 30s
      this.pingInterval = setInterval(() => {
        this.send({ type: 'ping' });
      }, 30000);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        this.handlers.forEach((h) => h(msg));
      } catch {
        console.warn('[WS] Invalid message:', event.data);
      }
    };

    this.ws.onclose = () => {
      console.log('[WS] Disconnected. Reconnecting in 5s...');
      this.cleanup();
      this.reconnectTimer = setTimeout(() => this.connect(), 5000);
    };

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err);
    };
  }

  disconnect() {
    this.cleanup();
    this.ws?.close();
    this.ws = null;
  }

  subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  send(msg: Record<string, any>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  private cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
