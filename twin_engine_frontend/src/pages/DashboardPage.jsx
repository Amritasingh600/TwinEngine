import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getOutlets } from '../services/api';
import { useAuth, ROLES } from '../utils/AuthContext';

const ROLE_LABELS = {
  [ROLES.MANAGER]: 'Manager',
  [ROLES.CHEF]: 'Chef',
  [ROLES.CASHIER]: 'Cashier',
  [ROLES.HOST]: 'Host / Hostess',
  [ROLES.WAITER]: 'Waiter',
};

/* Where each role lands after picking an outlet */
const ROLE_DEFAULT_PAGE = {
  [ROLES.MANAGER]: '',
  [ROLES.CHEF]: 'orders',
  [ROLES.CASHIER]: 'orders',
  [ROLES.HOST]: '',
  [ROLES.WAITER]: '',
};

const ROLE_DESCRIPTIONS = {
  [ROLES.MANAGER]: 'Full access — Floor, Orders, Predictions, Inventory, Reports',
  [ROLES.CHEF]: 'View kitchen orders and manage inventory',
  [ROLES.CASHIER]: 'Handle customer orders, billing and payments',
  [ROLES.HOST]: 'Manage floor layout, table allocation and guest seating',
  [ROLES.WAITER]: 'View floor and manage orders',
};

const ROLE_COLORS = {
  [ROLES.MANAGER]: '#E7A4A3',
  [ROLES.CHEF]: '#FF9090',
  [ROLES.CASHIER]: '#A5E2E2',
  [ROLES.HOST]: '#FFAFCC',
  [ROLES.WAITER]: '#DFBEBF',
};

export default function DashboardPage() {
  const { user, logout, role } = useAuth();
  const [outlets, setOutlets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOutlets()
      .then((res) => setOutlets(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const defaultPage = ROLE_DEFAULT_PAGE[role] || '';
  const firstName = user?.user?.first_name || user?.user?.username || 'User';
  const username = user?.user?.username || user?.username || 'User';
  const roleColor = ROLE_COLORS[role] || 'var(--primary)';

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <header className="topbar">
        <h1>◆ TwinEngine</h1>
        <div className="profile-area">
          <div className="profile-trigger">
            <span className="profile-avatar" style={{ background: roleColor, color: '#2D2428' }}>
              {firstName[0]?.toUpperCase() || '?'}
            </span>
            <div className="profile-info">
              <span className="profile-name">{firstName}</span>
              <span className="profile-role" style={{ color: roleColor }}>
                {ROLE_LABELS[role] || role}
              </span>
            </div>
          </div>
          <button onClick={logout} className="btn-logout">
            ⏻ Logout
          </button>
        </div>
      </header>

      <div className="container">
        {/* Role banner */}
        <div className="welcome-banner">
          <h3>Welcome back, {firstName} 👋</h3>
          <p>{ROLE_DESCRIPTIONS[role] || ''}</p>
          {user?.outlet_name && (
            <p style={{ marginTop: 4 }}>Outlet: <strong>{user.outlet_name}</strong></p>
          )}
        </div>

        <h2>Select Outlet</h2>
        {outlets.length === 0 && (
          <div className="empty-state">
            <h3>No outlets found</h3>
            <p>Contact your administrator to get outlet access.</p>
          </div>
        )}
        <div className="grid-2">
          {outlets.map((o) => (
            <Link
              key={o.id}
              to={`/outlet/${o.id}/${defaultPage}`}
              className="card card-link"
            >
              <h3>{o.name}</h3>
              <p className="text-sm">{o.city} &middot; {o.seating_capacity} seats</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
