import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getOrders, updateOrderStatus } from '../services/api';

const STATUS_COLOR = {
  PLACED: '#F59E0B',
  PREPARING: '#F97316',
  READY: '#8B5CF6',
  SERVED: '#22C55E',
  COMPLETED: '#3B82F6',
  CANCELLED: '#6B7280',
};

export default function OrdersPage() {
  const { outletId } = useOutletContext();
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchOrders = () => {
    const params = { table__outlet: outletId, ordering: '-placed_at' };
    if (filter) params.status = filter;
    getOrders(params)
      .then((res) => setOrders(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setLoading(true);
    fetchOrders();
  }, [outletId, filter]);

  const handleStatus = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      fetchOrders();
    } catch (err) {
      alert(err.response?.data?.detail || err.response?.data?.status?.[0] || 'Failed');
    }
  };

  const nextStatus = {
    PLACED: 'PREPARING',
    PREPARING: 'READY',
    READY: 'SERVED',
    SERVED: 'COMPLETED',
  };

  if (loading) return <p>Loading orders...</p>;

  return (
    <div>
      <div className="flex-between">
        <h2>Orders</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="PLACED">Placed</option>
          <option value="PREPARING">Preparing</option>
          <option value="READY">Ready</option>
          <option value="SERVED">Served</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {orders.length === 0 && <p>No orders found.</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Table</th>
            <th>Status</th>
            <th>Party</th>
            <th>Total</th>
            <th>Placed</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>{o.id}</td>
              <td>{o.table_name}</td>
              <td>
                <span
                  className="badge"
                  style={{ background: STATUS_COLOR[o.status] || '#888', color: '#fff' }}
                >
                  {o.status}
                </span>
              </td>
              <td>{o.party_size}</td>
              <td>Rs. {o.total}</td>
              <td>{new Date(o.placed_at).toLocaleTimeString()}</td>
              <td>
                {nextStatus[o.status] && (
                  <button
                    className="btn-sm"
                    onClick={() => handleStatus(o.id, nextStatus[o.status])}
                  >
                    {nextStatus[o.status]}
                  </button>
                )}
                {o.status !== 'CANCELLED' && o.status !== 'COMPLETED' && (
                  <button
                    className="btn-sm"
                    style={{ background: '#6B7280', marginLeft: 4 }}
                    onClick={() => handleStatus(o.id, 'CANCELLED')}
                  >
                    Cancel
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
