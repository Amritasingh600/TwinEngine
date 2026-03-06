import { useState, useEffect, useRef } from 'react';

function getWsBase() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  // In production, derive from API URL (same origin)
  const apiUrl = import.meta.env.VITE_API_URL;
  if (apiUrl) {
    const u = new URL(apiUrl);
    return `${u.protocol === 'https:' ? 'wss' : 'ws'}://${u.host}`;
  }
  // Dev: connect to Django backend directly (Vite proxy doesn't reliably proxy WS)
  return 'ws://127.0.0.1:8000';
}

/**
 * Hook for WebSocket connection to floor status stream.
 * Returns the latest node states and a boolean for connection status.
 */
export function useFloorSocket(outletId) {
  const [nodes, setNodes] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    if (!outletId) return;

    let active = true;
    const url = `${getWsBase()}/ws/floor/${outletId}/`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.addEventListener('open', () => {
      if (active) {
        setConnected(true);
      } else {
        // Strict Mode unmounted before open — close now that handshake is done
        socket.close();
      }
    });

    socket.addEventListener('close', () => {
      if (active) setConnected(false);
    });

    socket.addEventListener('message', (e) => {
      if (!active) return;
      const msg = JSON.parse(e.data);
      if (msg.type === 'floor_state') {
        setNodes(msg.nodes);
      } else if (msg.type === 'floor_update' || msg.type === 'node_status_change') {
        setNodes((prev) =>
          prev.map((n) =>
            n.id === msg.node_id ? { ...n, current_status: msg.status || msg.new_status } : n
          )
        );
      }
    });

    return () => {
      active = false;
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CLOSING) {
        socket.close();
      }
      // If still CONNECTING, the open handler above will close it
    };
  }, [outletId]);

  return { nodes, connected };
}
