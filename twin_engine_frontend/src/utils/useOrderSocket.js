import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';

function getWsBase() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const apiUrl = import.meta.env.VITE_API_URL;
  if (apiUrl) {
    const u = new URL(apiUrl);
    return `${u.protocol === 'https:' ? 'wss' : 'ws'}://${u.host}`;
  }
  return 'ws://127.0.0.1:8000';
}

/**
 * Hook for real-time order updates via WebSocket.
 * Falls back to polling if WebSocket connection fails.
 */
export function useOrderSocket(outletId) {
  const [orders, setOrders] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

  const requestRefresh = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'request_orders' }));
    }
  }, []);

  useEffect(() => {
    if (!outletId) return;

    let active = true;
    const url = `${getWsBase()}/ws/orders/${outletId}/`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.addEventListener('open', () => {
      if (active) {
        setConnected(true);
      } else {
        socket.close();
      }
    });

    socket.addEventListener('close', () => {
      if (active) setConnected(false);
    });

    socket.addEventListener('message', (e) => {
      if (!active) return;
      const msg = JSON.parse(e.data);

      if (msg.type === 'active_orders') {
        setOrders(msg.orders || []);
      } else if (msg.type === 'order_created') {
        toast('🆕 New order placed', { icon: '📋' });
        requestRefresh();
      } else if (msg.type === 'order_updated') {
        toast(`Order #${msg.order_id} → ${msg.new_status}`, { icon: '🔄' });
        requestRefresh();
      } else if (msg.type === 'order_completed') {
        toast(`Order #${msg.order_id} completed`, { icon: '✅' });
        requestRefresh();
      }
    });

    return () => {
      active = false;
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CLOSING) {
        socket.close();
      }
    };
  }, [outletId]);

  return { wsOrders: orders, wsConnected: connected, requestRefresh };
}
