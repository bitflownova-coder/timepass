import React, { useEffect, useRef } from 'react';
import { useWorkspace } from './WorkspaceContext';
import { useNotifications } from './NotificationContext';
import { useQueryClient } from '@tanstack/react-query';

const WS_BASE = 'ws://127.0.0.1:7779/ws';

/**
 * Connects to the Copilot Engine WebSocket and routes real-time events
 * into the notification toast system + invalidates relevant queries.
 */
export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { workspace } = useWorkspace();
  const { addToast } = useNotifications();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);
  const pingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!workspace) return;

    let isMounted = true;

    function connect() {
      if (!isMounted) return;

      const encodedPath = encodeURIComponent(workspace);
      const ws = new WebSocket(`${WS_BASE}/${encodedPath}`);
      wsRef.current = ws;

      ws.onopen = () => {
        // Start keepalive ping
        pingRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30_000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleEvent(data);
        } catch {
          // ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        cleanup();
        if (isMounted) {
          reconnectRef.current = setTimeout(connect, 5000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    function cleanup() {
      if (pingRef.current) {
        clearInterval(pingRef.current);
        pingRef.current = null;
      }
    }

    function handleEvent(data: any) {
      switch (data.type) {
        case 'drift_detected':
          addToast(
            data.severity === 'CRITICAL' || data.severity === 'HIGH' ? 'error' : 'warning',
            `Drift: ${data.entity_name || 'Code change'}`,
            `${data.drift_type} in ${data.file_path?.split(/[/\\]/).pop() ?? 'unknown'}`,
            8000
          );
          queryClient.invalidateQueries({ queryKey: ['autonomous-dashboard'] });
          queryClient.invalidateQueries({ queryKey: ['drifts'] });
          break;

        case 'risk_update':
          if (data.overall_score > 6) {
            addToast('warning', `Risk score: ${data.overall_score.toFixed(1)}`, data.health_level, 6000);
          }
          queryClient.invalidateQueries({ queryKey: ['autonomous-dashboard'] });
          queryClient.invalidateQueries({ queryKey: ['risk-trend'] });
          break;

        case 'security_finding':
          addToast(
            'error',
            `Security: ${data.finding_type || 'Issue found'}`,
            data.message,
            10000
          );
          break;

        case 'scan_complete':
          addToast('success', 'Scan Complete', data.message || 'Full scan finished');
          queryClient.invalidateQueries({ queryKey: ['pipeline'] });
          break;

        case 'error':
          addToast('error', 'Engine Error', data.message, 8000);
          break;

        case 'pong':
          // keepalive response, ignore
          break;

        default:
          // Unknown event — could log for debugging
          break;
      }
    }

    connect();

    return () => {
      isMounted = false;
      cleanup();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [workspace, addToast, queryClient]);

  return <>{children}</>;
}
