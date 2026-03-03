import { useState, useEffect, useRef } from 'react';

const WS_BASE =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

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

    const url = `${WS_BASE}/ws/floor/${outletId}/`;
    ws.current = new WebSocket(url);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);

    ws.current.onmessage = (e) => {
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
    };

    return () => {
      ws.current?.close();
    };
  }, [outletId]);

  return { nodes, connected };
}
