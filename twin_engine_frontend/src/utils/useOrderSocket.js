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
 * Includes auto reconnect and safe message handling.
 */
export function useOrderSocket(outletId) {

  const [orders, setOrders] = useState([]);
  const [connected, setConnected] = useState(false);

  const ws = useRef(null);
  const reconnectTimer = useRef(null);

  const requestRefresh = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'request_orders' }));
    }
  }, []);

  useEffect(() => {

    if (!outletId) return;

    let active = true;

    const url = `${getWsBase()}/ws/orders/${outletId}/`;

    function connect() {

      const socket = new WebSocket(url);
      ws.current = socket;

      socket.addEventListener('open', () => {

        if (!active) {
          socket.close();
          return;
        }

        setConnected(true);
        console.log('Orders WebSocket connected');

        requestRefresh();
      });

      socket.addEventListener('close', () => {

        if (!active) return;

        setConnected(false);
        console.log('Orders WebSocket disconnected');

        reconnectTimer.current = setTimeout(() => {
          if (active) connect();
        }, 3000);
      });

      socket.addEventListener('error', (err) => {
        console.error('Orders WebSocket error:', err);
      });

      socket.addEventListener('message', (e) => {

        if (!active) return;

        let msg;

        try {
          msg = JSON.parse(e.data);
        } catch (err) {
          console.error('Invalid WS message:', e.data);
          return;
        }

        switch (msg.type) {

          case 'active_orders':
            setOrders(msg.orders || []);
            break;

          case 'order_created':
            toast('New order placed', { icon: '📋' });
            requestRefresh();
            break;

          case 'order_updated':
            toast(`Order #${msg.order_id} → ${msg.new_status}`, { icon: '🔄' });
            requestRefresh();
            break;

          case 'order_completed':
            toast(`Order #${msg.order_id} completed`, { icon: '✅' });
            requestRefresh();
            break;

          default:
            console.warn('Unknown order WS message:', msg.type);
        }

      });
    }

    connect();

    return () => {

      active = false;

      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }

      if (
        ws.current &&
        (ws.current.readyState === WebSocket.OPEN ||
         ws.current.readyState === WebSocket.CONNECTING)
      ) {
        ws.current.close();
      }

    };

  }, [outletId, requestRefresh]);

  return {
    wsOrders: orders,
    wsConnected: connected,
    requestRefresh
  };
}