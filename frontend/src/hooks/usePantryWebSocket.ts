import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { StockUpdatedEvent } from '../types';

type StockUpdateHandler = (event: StockUpdatedEvent) => void;

export function usePantryWebSocket(onStockUpdate?: StockUpdateHandler) {
  const { user } = useAuth();
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isUnmountingRef = useRef<boolean>(false);
  const callbackRef = useRef<StockUpdateHandler | undefined>(onStockUpdate);

  useEffect(() => {
    callbackRef.current = onStockUpdate;
  }, [onStockUpdate]);

  const connect = useCallback(() => {
    const token = localStorage.getItem('token');
    if (!token || !user) {
      return;
    }

    // Determine WS URL based on API base URL or window.location
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const wsBase = apiBase.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
    const wsUrl = `${wsBase}/ws/pantry?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        // Keepalive ping every 25 seconds to prevent proxy / Render connection timeouts
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          } else {
            clearInterval(pingInterval);
          }
        }, 25000);

        (ws as unknown as { pingInterval: NodeJS.Timeout }).pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') {
          return;
        }
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.type === 'STOCK_UPDATED' && callbackRef.current) {
            callbackRef.current(parsed as StockUpdatedEvent);
          }
        } catch {
          // Non-JSON message ignored
        }
      };

      ws.onclose = () => {
        const interval = (ws as unknown as { pingInterval?: NodeJS.Timeout }).pingInterval;
        if (interval) clearInterval(interval);

        // Auto-reconnect after 3 seconds if not unmounted and user is logged in
        if (!isUnmountingRef.current && localStorage.getItem('token')) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // Reconnect on next cycle
      if (!isUnmountingRef.current) {
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }
  }, [user]);

  useEffect(() => {
    isUnmountingRef.current = false;
    connect();

    return () => {
      isUnmountingRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [connect]);
}
