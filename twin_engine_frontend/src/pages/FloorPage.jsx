import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getNodes, updateNodeStatus, getAllStaff, updateStaffMember } from '../services/api';
import { useFloorSocket } from '../utils/useFloorSocket';
import { STATUS_COLORS, STATUS_LABELS } from '../utils/helpers';
import { ROLES } from '../utils/AuthContext';

/*
 * Role behaviour:
 *  MANAGER  – full status control on every table
 *  HOST     – all 4 status options: Available, Waiting, Served, Delay + staff management
 *  WAITER   – read-only floor view (no status buttons)
 */

/* Labels for staff areas */
const AREA_LABELS = {
  MANAGER: { label: 'Management', icon: '👔' },
  WAITER: { label: 'Dining Hall', icon: '🍽️' },
  CHEF: { label: 'Kitchen', icon: '👨‍🍳' },
  HOST: { label: 'Front Desk', icon: '🎙️' },
  CASHIER: { label: 'Billing', icon: '💳' },
};

export default function FloorPage() {
  const { outletId, role } = useOutletContext();
  const { nodes: wsNodes, connected } = useFloorSocket(outletId);
  const [nodes, setNodes] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [allStaff, setAllStaff] = useState([]);
  const [expandedArea, setExpandedArea] = useState(null);

  useEffect(() => {
    getNodes(outletId)
      .then((res) => setNodes(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));

    // Periodically re-fetch tables to pick up status changes from order completions
    const interval = setInterval(() => {
      getNodes(outletId)
        .then((res) => setNodes(res.data.results || res.data))
        .catch(() => {});
    }, 20000);
    return () => clearInterval(interval);
  }, [outletId]);

  useEffect(() => {
    if (role === ROLES.HOST || role === ROLES.MANAGER) {
      getAllStaff(outletId)
        .then((res) => setAllStaff(res.data.results || res.data))
        .catch(() => {});
    }
  }, [outletId, role]);

  useEffect(() => {
    if (wsNodes.length > 0) setNodes(wsNodes);
  }, [wsNodes]);

  const handleStatusChange = async (nodeId, status) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === nodeId ? { ...n, current_status: status } : n))
    );
    try {
      await updateNodeStatus(nodeId, status);
    } catch {
      getNodes(outletId)
        .then((res) => setNodes(res.data.results || res.data))
        .catch(() => {});
      alert('Failed to update status');
    }
  };

  const toggleShift = async (staffId, currentlyOnShift) => {
    const updated = !currentlyOnShift;
    setAllStaff((prev) =>
      prev.map((s) => (s.id === staffId ? { ...s, is_on_shift: updated } : s))
    );
    try {
      await updateStaffMember(staffId, { is_on_shift: updated });
    } catch {
      setAllStaff((prev) =>
        prev.map((s) => (s.id === staffId ? { ...s, is_on_shift: currentlyOnShift } : s))
      );
      alert('Failed to update staff');
    }
  };

  const canChangeStatus = role === ROLES.MANAGER || role === ROLES.HOST;
  const canEditStaff = role === ROLES.HOST || role === ROLES.MANAGER;

  if (loading) return <p style={{ padding: 20 }}>Loading floor...</p>;

  const tables = nodes.filter((n) => n.node_type === 'TABLE');
  const others = nodes.filter((n) => n.node_type !== 'TABLE');

  const counts = {};
  tables.forEach((t) => {
    counts[t.current_status] = (counts[t.current_status] || 0) + 1;
  });

  /* All 4 core status options for HOST, MANAGER gets extra GREY */
  const statusOptions = [
    { key: 'BLUE', label: 'Available', color: STATUS_COLORS.BLUE },
    { key: 'RED', label: 'Waiting', color: STATUS_COLORS.RED },
    { key: 'GREEN', label: 'Served', color: STATUS_COLORS.GREEN },
    { key: 'YELLOW', label: 'Delay', color: STATUS_COLORS.YELLOW },
  ];
  if (role === ROLES.MANAGER) {
    statusOptions.push({ key: 'GREY', label: 'Inactive', color: STATUS_COLORS.GREY });
  }

  const staffByRole = {};
  allStaff.forEach((s) => {
    if (!staffByRole[s.role]) staffByRole[s.role] = [];
    staffByRole[s.role].push(s);
  });
  const onShiftTotal = allStaff.filter((s) => s.is_on_shift).length;

  return (
    <div>
      {/* Page header */}
      <div className="flex-between" style={{ marginBottom: 16 }}>
        <h2>🏗️ Floor Map</h2>
        <span className={connected ? 'badge badge-green' : 'badge badge-orange'}>
          {connected ? '● Live' : '● Connecting...'}
        </span>
      </div>

      {/* Status summary strip */}
      <div className="status-strip">
        {Object.entries(STATUS_COLORS).map(([s, color]) => (
          <div key={s} className="status-strip-item">
            <span className="status-dot" style={{ background: color }} />
            <span className="status-strip-label">{STATUS_LABELS[s]}</span>
            <strong>{counts[s] || 0}</strong>
          </div>
        ))}
      </div>

      {/* Tables grid */}
      <p className="section-title">Tables ({tables.length})</p>
      <div className="grid-4">
        {tables.map((n) => {
          const isExpanded = expandedId === n.id && canChangeStatus;
          return (
            <div
              key={n.id}
              className={`table-card${isExpanded ? ' expanded' : ''}`}
              onClick={() =>
                canChangeStatus && setExpandedId(expandedId === n.id ? null : n.id)
              }
            >
              <div className="table-card-indicator" style={{ background: STATUS_COLORS[n.current_status] }} />
              <div className="table-card-header">
                <strong>{n.name}</strong>
                <span className="text-sm">Cap {n.capacity}</span>
              </div>
              <span
                className="badge"
                style={{
                  background: STATUS_COLORS[n.current_status],
                  color: '#fff',
                  alignSelf: 'flex-start',
                }}
              >
                {STATUS_LABELS[n.current_status]}
              </span>

              {isExpanded && (
                <div className="status-buttons" onClick={(e) => e.stopPropagation()}>
                  {statusOptions.map((opt) => (
                    <button
                      key={opt.key}
                      className={`status-btn${n.current_status === opt.key ? ' active' : ''}`}
                      style={{
                        background: opt.color,
                        opacity: n.current_status === opt.key ? 1 : 0.55,
                      }}
                      onClick={() => handleStatusChange(n.id, opt.key)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {canChangeStatus && (
        <p className="text-hint">Click a table to change its status</p>
      )}

      {/* ───── Staff Areas ───── */}
      {canEditStaff && (
        <>
          <p className="section-title">Staff Areas ({onShiftTotal} on shift)</p>
          <div className="staff-grid">
            {Object.entries(AREA_LABELS).map(([roleKey, { label, icon }]) => {
              const members = staffByRole[roleKey] || [];
              const onShift = members.filter((m) => m.is_on_shift).length;
              const isAreaExpanded = expandedArea === roleKey;

              return (
                <div
                  key={roleKey}
                  className={`staff-area-card${isAreaExpanded ? ' expanded' : ''}`}
                  onClick={() => setExpandedArea(isAreaExpanded ? null : roleKey)}
                >
                  <div className="staff-area-header">
                    <span style={{ fontSize: 28 }}>{icon}</span>
                    <div>
                      <strong style={{ fontSize: 14, color: 'var(--gray-800)' }}>{label}</strong>
                      <div className="text-sm">
                        <span style={{ color: 'var(--success)', fontWeight: 600 }}>{onShift}</span>
                        {' / '}
                        <span>{members.length} staff</span>
                      </div>
                    </div>
                    <span className="staff-count-badge" style={{
                      background: onShift > 0 ? 'var(--success-light)' : 'var(--gray-100)',
                      color: onShift > 0 ? 'var(--success)' : 'var(--gray-400)',
                    }}>
                      {onShift}
                    </span>
                  </div>

                  {isAreaExpanded && (
                    <div className="staff-member-list" onClick={(e) => e.stopPropagation()}>
                      <div className="staff-list-header">
                        <span>Employee</span>
                        <span>Action</span>
                      </div>
                      {members.length === 0 && (
                        <p className="text-sm" style={{ textAlign: 'center', padding: 12 }}>
                          No employees in this area
                        </p>
                      )}
                      {members.map((m) => (
                        <div key={m.id} className="staff-member-row">
                          <div className="staff-member-info">
                            <span className="staff-avatar">
                              {(m.user?.first_name?.[0] || m.user?.username?.[0] || '?').toUpperCase()}
                            </span>
                            <div>
                              <span style={{ fontWeight: 500, fontSize: 13 }}>
                                {m.user?.first_name
                                  ? `${m.user.first_name} ${m.user.last_name || ''}`
                                  : m.user?.username}
                              </span>
                              <span className="text-sm">{m.phone || ''}</span>
                            </div>
                          </div>
                          <button
                            className={`staff-toggle-btn ${m.is_on_shift ? 'on' : 'off'}`}
                            onClick={() => toggleShift(m.id, m.is_on_shift)}
                          >
                            {m.is_on_shift ? '✕ Remove' : '+ Add'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Other nodes */}
      {others.length > 0 && (
        <>
          <p className="section-title">Other Stations ({others.length})</p>
          <div className="grid-4">
            {others.map((n) => (
              <div key={n.id} className="card card-node" style={{ borderLeft: '4px solid var(--gray-300)' }}>
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
