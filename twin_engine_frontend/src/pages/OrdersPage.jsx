import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getOrders, updateOrderStatus, createOrder, getNodes, createPayment, getPayments, updatePayment } from '../services/api';
import { ROLES } from '../utils/AuthContext';

const STATUS_COLOR = {
  PLACED: '#D97706',
  PREPARING: '#EA580C',
  READY: '#7C3AED',
  SERVED: '#059669',
  COMPLETED: '#4F46E5',
  CANCELLED: '#6B7280',
};

const STATUS_ICON = {
  PLACED: '📋',
  PREPARING: '🔥',
  READY: '✅',
  SERVED: '🍽️',
  COMPLETED: '💰',
  CANCELLED: '❌',
};

const STATUS_LABEL = {
  PLACED: 'Placed',
  PREPARING: 'Preparing',
  READY: 'Ready',
  SERVED: 'Served',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
};

const PAYMENT_COLOR = {
  PENDING: '#D97706',
  SUCCESS: '#059669',
};

/*
 * Role behaviour:
 *  MANAGER  – full access, lifecycle buttons, create orders, payment
 *  CASHIER  – dropdown with ALL status options (any→any), create orders, payment toggle
 *  CHEF     – read-only card view, active orders only, auto-refresh
 *  WAITER   – read-only table view
 */

const ALL_STATUSES = ['PLACED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED', 'CANCELLED'];
const ACTIVE_STATUSES = ['PLACED', 'PREPARING', 'READY', 'SERVED'];

/** Safely render an order item — handles both strings and {name, price} objects */
const formatItem = (item) => {
  if (typeof item === 'string') return item;
  if (item && typeof item === 'object' && item.name) {
    return item.price ? `${item.name} (₹${item.price})` : item.name;
  }
  return String(item);
};

export default function OrdersPage() {
  const { outletId, role } = useOutletContext();
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionMap, setActionMap] = useState({});
  const [showCreate, setShowCreate] = useState(false);
  const [tables, setTables] = useState([]);
  const [payments, setPayments] = useState({});     // orderId → latest payment status
  const [newOrder, setNewOrder] = useState({
    table: '',
    party_size: 1,
    customer_name: '',
    items: '',
    special_requests: '',
    subtotal: 0,
    tax: 0,
    total: 0,
  });
  const [creating, setCreating] = useState(false);

  const isChef = role === ROLES.CHEF;
  const isWaiter = role === ROLES.WAITER;
  const isCashier = role === ROLES.CASHIER;
  const isManager = role === ROLES.MANAGER;
  const isReadOnly = isChef || isWaiter;
  const canCreateOrder = isManager || isCashier;
  const canManagePayment = isManager || isCashier;

  /* ─── Fetch orders ─── */
  const fetchOrders = () => {
    const params = { table__outlet: outletId, ordering: '-placed_at' };
    if (filter) params.status = filter;
    getOrders(params)
      .then((res) => {
        let data = res.data.results || res.data;
        setOrders(data);
      })
      .catch((err) => console.error('Failed to fetch orders:', err))
      .finally(() => setLoading(false));
  };

  /* ─── Fetch payments for all orders ─── */
  const fetchPayments = () => {
    if (!canManagePayment) return;
    getPayments()
      .then((res) => {
        const list = res.data.results || res.data;
        const map = {};
        list.forEach((p) => {
          // Keep the latest payment per order
          if (!map[p.order] || new Date(p.created_at) > new Date(map[p.order].created_at)) {
            map[p.order] = p;
          }
        });
        setPayments(map);
      })
      .catch((err) => console.error('Failed to fetch payments:', err));
  };

  useEffect(() => {
    setLoading(true);
    fetchOrders();
    fetchPayments();
    // Auto-refresh for chef (15s) and cashier/manager (30s) to see table availability changes
    const interval = setInterval(() => {
      fetchOrders();
      if (canManagePayment) fetchPayments();
    }, isChef ? 15000 : 30000);
    return () => clearInterval(interval);
  }, [outletId, filter]);

  /* ─── Load tables for order creation ─── */
  const fetchTables = () => {
    getNodes(outletId)
      .then((res) => {
        const all = res.data.results || res.data;
        setTables(all.filter((n) => n.node_type === 'TABLE'));
      })
      .catch(() => {});
  };

  useEffect(() => {
    if (!canCreateOrder) return;
    fetchTables();
  }, [outletId]);

  /* ─── Status change ─── */
  const handleStatus = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      setActionMap((prev) => ({ ...prev, [orderId]: '' }));
      fetchOrders();
      // Refresh table list so completed orders free up tables
      if (canCreateOrder) fetchTables();
    } catch (err) {
      alert(err.response?.data?.detail || err.response?.data?.status?.[0] || 'Failed');
    }
  };

  /* ─── Payment toggle ─── */
  const handlePaymentToggle = async (order) => {
    const existing = payments[order.id];
    if (existing && existing.status === 'SUCCESS') {
      // Already paid — mark pending
      try {
        await updatePayment(existing.id, { status: 'PENDING' });
        fetchPayments();
      } catch {
        alert('Failed to update payment');
      }
    } else if (existing && existing.status === 'PENDING') {
      // Mark as done
      try {
        await updatePayment(existing.id, { status: 'SUCCESS' });
        fetchPayments();
      } catch {
        alert('Failed to update payment');
      }
    } else {
      // No payment yet — create one as PENDING, user toggles to mark Done
      try {
        await createPayment({
          order: order.id,
          amount: order.total,
          method: 'CASH',
        });
        fetchPayments();
      } catch {
        alert('Failed to create payment');
      }
    }
  };

  /* ─── Create order ─── */
  const handleCreateOrder = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const payload = {
        table: Number(newOrder.table),
        party_size: Number(newOrder.party_size),
        customer_name: newOrder.customer_name || undefined,
        items: newOrder.items ? newOrder.items.split(',').map((i) => i.trim()) : [],
        special_requests: newOrder.special_requests || undefined,
        subtotal: Number(newOrder.subtotal) || 0,
        tax: Number(newOrder.tax) || 0,
        total: Number(newOrder.total) || 0,
      };
      await createOrder(payload);
      setShowCreate(false);
      setNewOrder({ table: '', party_size: 1, customer_name: '', items: '', special_requests: '', subtotal: 0, tax: 0, total: 0 });
      fetchOrders();
      fetchTables();
    } catch (err) {
      alert(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to create order');
    } finally {
      setCreating(false);
    }
  };

  /** Next natural status in lifecycle */
  const NEXT_STATUS = {
    PLACED: 'PREPARING',
    PREPARING: 'READY',
    READY: 'SERVED',
    SERVED: 'COMPLETED',
  };

  const NEXT_LABEL = {
    PLACED: 'Start Preparing',
    PREPARING: 'Mark Ready',
    READY: 'Mark Served',
    SERVED: 'Mark Completed',
  };

  const canAdvance = (order) => {
    if (isReadOnly) return false;
    const next = NEXT_STATUS[order.status];
    if (!next) return false;
    if (isManager) return true;
    return false;
  };

  const canCancel = (order) => {
    if (isReadOnly) return false;
    if (order.status === 'CANCELLED' || order.status === 'COMPLETED') return false;
    return isManager || isCashier;
  };

  /** Cashier dropdown — every status except current */
  const getDropdownActions = (order) => {
    return ALL_STATUSES
      .filter((s) => s !== order.status)
      .map((s) => ({ value: s, label: STATUS_LABEL[s] }));
  };

  // Only show available (BLUE) tables in create form
  const availableTables = tables.filter((t) => t.current_status === 'BLUE');

  // Filter options for the table view dropdown
  const filterStatuses = ALL_STATUSES;

  /* ─── Chef card renderer ─── */
  const renderChefCard = (o) => {
    const elapsed = Math.floor((Date.now() - new Date(o.placed_at).getTime()) / 60000);
    const isUrgent = elapsed > 15 && ['PLACED', 'PREPARING'].includes(o.status);

    return (
      <div
        key={o.id}
        className={`order-card${isUrgent ? ' order-card-urgent' : ''}`}
      >
        {/* Status bar at top */}
        <div className="order-card-status-bar" style={{ background: STATUS_COLOR[o.status] }}>
          <span>{STATUS_ICON[o.status]} {STATUS_LABEL[o.status]}</span>
          <span>{elapsed}m ago</span>
        </div>

        {/* Header */}
        <div className="order-card-header">
          <div>
            <strong className="order-card-table">{o.table_name}</strong>
            <span className="order-card-meta">Party of {o.party_size}</span>
          </div>
          {o.customer_name && (
            <span className="order-card-customer">👤 {o.customer_name}</span>
          )}
        </div>

        {/* Items */}
        <div className="order-card-items">
          <span className="order-card-items-label">🍽️ Items</span>
          {Array.isArray(o.items) && o.items.length > 0 ? (
            <ul className="order-card-items-list">
              {o.items.map((item, i) => (
                <li key={i}>{formatItem(item)}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm" style={{ color: 'var(--gray-400)' }}>No items listed</p>
          )}
        </div>

        {/* Special requests */}
        {o.special_requests && (
          <div className="order-card-requests">
            <span>⚠️ {o.special_requests}</span>
          </div>
        )}

        {/* Footer */}
        <div className="order-card-footer">
          <span className="order-card-total">₹{o.total}</span>
          <span className="text-sm" style={{ color: 'var(--gray-400)' }}>
            {new Date(o.placed_at).toLocaleTimeString()}
          </span>
        </div>
      </div>
    );
  };

  if (loading) return <p style={{ padding: 20 }}>Loading orders...</p>;

  /* ═══════════════════════════════════════════
   *  CHEF VIEW — card-based kitchen display
   * ═══════════════════════════════════════════ */
  if (isChef) {
    const activeOrders = orders.filter((o) => ACTIVE_STATUSES.includes(o.status));
    const completedOrders = orders.filter((o) => !ACTIVE_STATUSES.includes(o.status));

    return (
      <div>
        <div className="flex-between">
          <h2>👨‍🍳 Kitchen Orders</h2>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ minWidth: 140 }}>
            <option value="">All Orders</option>
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABEL[s]}</option>
            ))}
          </select>
        </div>

        <p className="text-hint">
          🔄 Auto-refreshes every 15s · {activeOrders.length} active · {completedOrders.length} completed/cancelled
        </p>

        {orders.length === 0 && (
          <div className="empty-state">
            <h3>🍳 No orders yet!</h3>
            <p>Orders will appear here once they are placed.</p>
          </div>
        )}

        {/* Active orders — prominent */}
        {activeOrders.length > 0 && (
          <>
            <h3 style={{ margin: '16px 0 8px', color: 'var(--primary)' }}>🔥 Active Orders ({activeOrders.length})</h3>
            <div className="order-card-grid">
              {activeOrders.map((o) => renderChefCard(o))}
            </div>
          </>
        )}

        {activeOrders.length === 0 && completedOrders.length > 0 && (
          <div className="empty-state" style={{ padding: '20px' }}>
            <h3>🍳 Kitchen is clear!</h3>
            <p>No active orders right now. Completed orders shown below.</p>
          </div>
        )}

        {/* Completed/Cancelled orders — dimmed */}
        {completedOrders.length > 0 && (
          <>
            <h3 style={{ margin: '24px 0 8px', color: 'var(--gray-400)' }}>📋 Past Orders ({completedOrders.length})</h3>
            <div className="order-card-grid" style={{ opacity: 0.6 }}>
              {completedOrders.map((o) => renderChefCard(o))}
            </div>
          </>
        )}
      </div>
    );
  }

  /* ═══════════════════════════════════════════
   *  TABLE VIEW — Waiter / Cashier / Manager
   * ═══════════════════════════════════════════ */
  return (
    <div>
      <div className="flex-between">
        <h2>📦 Orders</h2>
        <div className="flex-row" style={{ gap: 8 }}>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ minWidth: 140 }}>
            <option value="">All Statuses</option>
            {filterStatuses.map((s) => (
              <option key={s} value={s}>{STATUS_LABEL[s]}</option>
            ))}
          </select>
          {canCreateOrder && (
            <button className="btn-sm" onClick={() => setShowCreate(!showCreate)}>
              {showCreate ? '✕ Close' : '+ New Order'}
            </button>
          )}
        </div>
      </div>

      {/* Waiter info banner */}
      {isWaiter && (
        <p className="text-hint">
          📋 View-only — order status is managed by the Cashier.
        </p>
      )}

      {/* ───── Create Order Form (Cashier & Manager only) ───── */}
      {showCreate && canCreateOrder && (
        <form className="create-form" onSubmit={handleCreateOrder}>
          <h3>Register New Order</h3>
          <div className="form-grid">
            <label>
              Table * <span className="text-hint" style={{ fontSize: 11 }}>(only available tables)</span>
              <select
                value={newOrder.table}
                onChange={(e) => setNewOrder({ ...newOrder, table: e.target.value })}
                required
              >
                <option value="">Select table...</option>
                {availableTables.length === 0 && (
                  <option value="" disabled>No available tables</option>
                )}
                {availableTables.map((t) => (
                  <option key={t.id} value={t.id}>{t.name} (Cap {t.capacity})</option>
                ))}
              </select>
            </label>
            <label>
              Party Size
              <input
                type="number" min="1" value={newOrder.party_size}
                onChange={(e) => setNewOrder({ ...newOrder, party_size: e.target.value })}
              />
            </label>
            <label>
              Customer Name
              <input
                type="text" value={newOrder.customer_name}
                onChange={(e) => setNewOrder({ ...newOrder, customer_name: e.target.value })}
                placeholder="Walk-in"
              />
            </label>
            <label>
              Items (comma-separated)
              <input
                type="text" value={newOrder.items}
                onChange={(e) => setNewOrder({ ...newOrder, items: e.target.value })}
                placeholder="Burger, Fries, Cola"
              />
            </label>
            <label>
              Subtotal (₹)
              <input
                type="number" min="0" step="0.01" value={newOrder.subtotal}
                onChange={(e) => setNewOrder({ ...newOrder, subtotal: e.target.value })}
              />
            </label>
            <label>
              Tax (₹)
              <input
                type="number" min="0" step="0.01" value={newOrder.tax}
                onChange={(e) => setNewOrder({ ...newOrder, tax: e.target.value })}
              />
            </label>
            <label>
              Total (₹)
              <input
                type="number" min="0" step="0.01" value={newOrder.total}
                onChange={(e) => setNewOrder({ ...newOrder, total: e.target.value })}
              />
            </label>
            <label>
              Special Requests
              <input
                type="text" value={newOrder.special_requests}
                onChange={(e) => setNewOrder({ ...newOrder, special_requests: e.target.value })}
                placeholder="No onions..."
              />
            </label>
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button type="submit" disabled={creating || availableTables.length === 0}>
              {creating ? 'Creating...' : 'Register Order'}
            </button>
            <button type="button" style={{ background: 'var(--gray-400)' }} onClick={() => setShowCreate(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Cashier hint */}
      {isCashier && !showCreate && (
        <p className="text-hint">
          Change order status freely using the dropdown. Mark payment Done / Pending separately. Completing an order auto-marks the table Available.
        </p>
      )}

      {orders.length === 0 && (
        <div className="empty-state">
          <h3>No orders found</h3>
          <p>Try changing the status filter above.</p>
        </div>
      )}

      {orders.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>S.No</th>
              <th>Table</th>
              <th>Status</th>
              <th>Party</th>
              <th>Items</th>
              <th>Total</th>
              <th>Placed</th>
              {canManagePayment && <th>Payment</th>}
              {!isReadOnly && <th>Action</th>}
            </tr>
          </thead>
          <tbody>
            {orders.map((o, idx) => {
              const actions = getDropdownActions(o);
              const selectedAction = actionMap[o.id] || '';
              const payment = payments[o.id];
              const paymentStatus = payment?.status || 'PENDING';
              const isPaid = paymentStatus === 'SUCCESS';

              return (
                <tr key={o.id}>
                  <td style={{ fontWeight: 600, color: 'var(--gray-500)' }}>{idx + 1}</td>
                  <td style={{ fontWeight: 500 }}>{o.table_name}</td>
                  <td>
                    <span
                      className="badge"
                      style={{ background: STATUS_COLOR[o.status] || '#888', color: '#fff' }}
                    >
                      {STATUS_ICON[o.status] || ''} {STATUS_LABEL[o.status]}
                    </span>
                  </td>
                  <td>{o.party_size}</td>
                  <td className="text-sm" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {Array.isArray(o.items) ? o.items.map(formatItem).join(', ') : (o.items || '—')}
                  </td>
                  <td style={{ fontWeight: 600 }}>₹{o.total}</td>
                  <td style={{ color: 'var(--gray-500)' }}>{new Date(o.placed_at).toLocaleTimeString()}</td>

                  {/* Payment column */}
                  {canManagePayment && (
                    <td>
                      <button
                        className={`payment-toggle ${isPaid ? 'paid' : 'pending'}`}
                        onClick={() => handlePaymentToggle(o)}
                        title={isPaid ? 'Click to mark Pending' : 'Click to mark Done'}
                      >
                        {isPaid ? '✓ Done' : '○ Pending'}
                      </button>
                    </td>
                  )}

                  {/* Action column */}
                  {!isReadOnly && (
                    <td>
                      {/* Cashier gets full dropdown with all statuses */}
                      {isCashier && actions.length > 0 && (
                        <div className="flex-row" style={{ gap: 4 }}>
                          <select
                            className="action-select"
                            value={selectedAction}
                            onChange={(e) =>
                              setActionMap((prev) => ({ ...prev, [o.id]: e.target.value }))
                            }
                          >
                            <option value="">Change status...</option>
                            {actions.map((a) => (
                              <option key={a.value} value={a.value}>
                                {STATUS_ICON[a.value]} {a.label}
                              </option>
                            ))}
                          </select>
                          <button
                            className="btn-sm"
                            disabled={!selectedAction}
                            style={{
                              background: selectedAction === 'CANCELLED' ? 'var(--danger)' : 'var(--primary)',
                              opacity: selectedAction ? 1 : 0.4,
                            }}
                            onClick={() => selectedAction && handleStatus(o.id, selectedAction)}
                          >
                            Go
                          </button>
                        </div>
                      )}

                      {/* Manager gets direct lifecycle buttons */}
                      {isManager && canAdvance(o) && (
                        <button
                          className="btn-sm"
                          onClick={() => handleStatus(o.id, NEXT_STATUS[o.status])}
                        >
                          {NEXT_LABEL[o.status] || NEXT_STATUS[o.status]}
                        </button>
                      )}
                      {isManager && canCancel(o) && (
                        <button
                          className="btn-sm"
                          style={{ background: 'var(--danger)', marginLeft: 4 }}
                          onClick={() => handleStatus(o.id, 'CANCELLED')}
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
