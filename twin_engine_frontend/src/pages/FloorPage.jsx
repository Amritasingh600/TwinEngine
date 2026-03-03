import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getNodes, updateNodeStatus } from '../services/api';
import { useFloorSocket } from '../utils/useFloorSocket';
import { STATUS_COLORS, STATUS_LABELS } from '../utils/helpers';

export default function FloorPage() {
  const { outletId } = useOutletContext();
  const { nodes: wsNodes, connected } = useFloorSocket(outletId);
  const [nodes, setNodes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initial load via REST
  useEffect(() => {
    getNodes(outletId)
      .then((res) => setNodes(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [outletId]);

  // Merge WebSocket updates
  useEffect(() => {
    if (wsNodes.length > 0) setNodes(wsNodes);
  }, [wsNodes]);

  const handleStatusChange = async (nodeId, status) => {
    try {
      await updateNodeStatus(nodeId, status);
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, current_status: status } : n))
      );
    } catch {
      alert('Failed to update status');
    }
  };

  if (loading) return <p>Loading floor...</p>;

  const tables = nodes.filter((n) => n.node_type === 'TABLE');
  const others = nodes.filter((n) => n.node_type !== 'TABLE');

  const counts = {};
  tables.forEach((t) => {
    counts[t.current_status] = (counts[t.current_status] || 0) + 1;
  });

  return (
    <div>
      <div className="flex-between" style={{ marginBottom: 12 }}>
        <h2>Floor Map</h2>
        <span className={connected ? 'badge badge-green' : 'badge badge-grey'}>
          {connected ? 'Live' : 'Offline'}
        </span>
      </div>

      {/* Status summary */}
      <div className="flex-row" style={{ gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        {Object.entries(STATUS_COLORS).map(([s, color]) => (
          <span key={s} className="badge" style={{ background: color, color: '#fff' }}>
            {STATUS_LABELS[s]}: {counts[s] || 0}
          </span>
        ))}
      </div>

      {/* Tables grid */}
      <h3>Tables ({tables.length})</h3>
      <div className="grid-4">
        {tables.map((n) => (
          <div
            key={n.id}
            className="card card-node"
            style={{ borderLeft: `4px solid ${STATUS_COLORS[n.current_status]}` }}
            onClick={() => setSelected(selected?.id === n.id ? null : n)}
          >
            <strong>{n.name}</strong>
            <span className="text-sm">Cap: {n.capacity}</span>
            <span
              className="badge"
              style={{
                background: STATUS_COLORS[n.current_status],
                color: '#fff',
                fontSize: 11,
              }}
            >
              {STATUS_LABELS[n.current_status]}
            </span>
          </div>
        ))}
      </div>

      {/* Selected node detail */}
      {selected && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>{selected.name}</h3>
          <p>Type: {selected.node_type} &middot; Capacity: {selected.capacity}</p>
          <p>Status: {STATUS_LABELS[selected.current_status]}</p>
          <div className="flex-row" style={{ gap: 6, marginTop: 8 }}>
            {Object.keys(STATUS_COLORS).map((s) => (
              <button
                key={s}
                className="btn-sm"
                style={{
                  background: STATUS_COLORS[s],
                  color: '#fff',
                  opacity: selected.current_status === s ? 1 : 0.5,
                }}
                onClick={() => handleStatusChange(selected.id, s)}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Other nodes */}
      {others.length > 0 && (
        <>
          <h3 style={{ marginTop: 20 }}>Other Stations ({others.length})</h3>
          <div className="grid-4">
            {others.map((n) => (
              <div key={n.id} className="card card-node">
                <strong>{n.name}</strong>
                <span className="text-sm">{n.node_type}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
