import { useState, useEffect, useRef } from 'react';

function getWsBase() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;

  // In production, derive from API URL (same origin)
  const apiUrl = import.meta.env.VITE_API_URL;
  if (apiUrl) {
    const u = new URL(apiUrl);
    return `${u.protocol === 'https:' ? 'wss' : 'ws'}://${u.host}`;
  }

  // Dev fallback
  return 'ws://127.0.0.1:8000';
}

/**
 * React hook for WebSocket connection to floor status stream
 */
export function useFloorSocket(outletId) {

  const [nodes, setNodes] = useState([]);
  const [connected, setConnected] = useState(false);

  const ws = useRef(null);
  const reconnectTimer = useRef(null);

  useEffect(() => {

    if (!outletId) return;

    let active = true;

    const url = `${getWsBase()}/ws/floor/${outletId}/`;

    function connect() {

      const socket = new WebSocket(url);
      ws.current = socket;

      socket.addEventListener('open', () => {

        if (!active) {
          socket.close();
          return;
        }

        setConnected(true);
        console.log("WebSocket connected");
      });

      socket.addEventListener('close', () => {

        if (!active) return;

        setConnected(false);
        console.log("WebSocket closed");

        // attempt reconnect
        reconnectTimer.current = setTimeout(() => {
          if (active) connect();
        }, 3000);
      });

      socket.addEventListener('error', (err) => {
        console.error("WebSocket error:", err);
      });

      socket.addEventListener('message', (e) => {

        if (!active) return;

        let msg;

        try {
          msg = JSON.parse(e.data);
        } catch (err) {
          console.error("Invalid WebSocket message:", e.data);
          return;
        }

        switch (msg.type) {

          case 'floor_state':
            setNodes(msg.nodes);
            break;

          case 'floor_update':
          case 'node_status_change':

            setNodes((prev) =>
              prev.map((n) =>
                n.id === msg.node_id
                  ? { ...n, current_status: msg.status || msg.new_status }
                  : n
              )
            );

            break;

          default:
            console.warn("Unknown WS message type:", msg.type);
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

  }, [outletId]);

  return { nodes, connected };

}