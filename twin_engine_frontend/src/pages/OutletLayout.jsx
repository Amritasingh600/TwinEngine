import { useState } from 'react';
import { useParams, Link, Outlet } from 'react-router-dom';
import { useAuth, ROLES } from '../utils/AuthContext';

/*
  Role-based navigation tabs:
  MANAGER  → Floor, Orders, Predictions, Inventory, Reports  (all)
  CHEF     → Inventory
  CASHIER  → Orders
  HOST     → Floor
  WAITER   → Floor, Orders
*/
const ROLE_NAV = {
  [ROLES.MANAGER]: [
    { to: '', label: 'Floor', icon: '🏗️' },
    { to: 'orders', label: 'Orders', icon: '📦' },
    { to: 'predictions', label: 'Predictions', icon: '🤖' },
    { to: 'inventory', label: 'Inventory', icon: '📦' },
    { to: 'reports', label: 'Reports', icon: '📊' },
  ],
  [ROLES.CHEF]: [
    { to: 'orders', label: 'Orders', icon: '📦' },
    { to: 'inventory', label: 'Inventory', icon: '📦' },
  ],
  [ROLES.CASHIER]: [
    { to: 'orders', label: 'Orders', icon: '📦' },
  ],
  [ROLES.HOST]: [
    { to: '', label: 'Floor', icon: '🏗️' },
  ],
  [ROLES.WAITER]: [
    { to: '', label: 'Floor', icon: '🏗️' },
    { to: 'orders', label: 'Orders', icon: '📦' },
  ],
};

const ROLE_LABELS = {
  [ROLES.MANAGER]: 'Manager',
  [ROLES.CHEF]: 'Chef',
  [ROLES.CASHIER]: 'Cashier',
  [ROLES.HOST]: 'Host',
  [ROLES.WAITER]: 'Waiter',
};

const ROLE_COLORS = {
  [ROLES.MANAGER]: '#4F46E5',
  [ROLES.CHEF]: '#EA580C',
  [ROLES.CASHIER]: '#059669',
  [ROLES.HOST]: '#7C3AED',
  [ROLES.WAITER]: '#D97706',
};

export default function OutletLayout() {
  const { outletId } = useParams();
  const { user, logout, role } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  const navItems = ROLE_NAV[role] || ROLE_NAV[ROLES.WAITER];
  const username = user?.user?.username || user?.username || 'User';
  const firstName = user?.user?.first_name || username;
  const outletName = user?.outlet_name || '';
  const roleLabel = ROLE_LABELS[role] || role;
  const roleColor = ROLE_COLORS[role] || 'var(--primary)';

  return (
    <div>
      <header className="topbar">
        <Link to="/" className="topbar-brand">TwinEngine</Link>
        <nav className="topbar-nav">
          {navItems.map((n) => (
            <Link key={n.to} to={`/outlet/${outletId}/${n.to}`}>
              {n.label}
            </Link>
          ))}
        </nav>

        {/* User profile area */}
        <div className="profile-area">
          <div
            className="profile-trigger"
            onClick={() => setShowProfile(!showProfile)}
          >
            <span className="profile-avatar" style={{ background: roleColor }}>
              {firstName[0]?.toUpperCase() || '?'}
            </span>
            <div className="profile-info">
              <span className="profile-name">{firstName}</span>
              <span className="profile-role" style={{ color: roleColor }}>{roleLabel}</span>
            </div>
            <span className="profile-chevron">{showProfile ? '▲' : '▼'}</span>
          </div>

          {/* Dropdown */}
          {showProfile && (
            <div className="profile-dropdown">
              <div className="profile-dropdown-header">
                <span className="profile-avatar-lg" style={{ background: roleColor }}>
                  {firstName[0]?.toUpperCase() || '?'}
                </span>
                <div>
                  <strong style={{ fontSize: 14 }}>
                    {user?.user?.first_name
                      ? `${user.user.first_name} ${user.user.last_name || ''}`
                      : username}
                  </strong>
                  <p className="text-sm">@{username}</p>
                </div>
              </div>
              <div className="profile-dropdown-body">
                <div className="profile-row">
                  <span className="text-sm">Role</span>
                  <span className="badge" style={{ background: roleColor, color: '#fff' }}>{roleLabel}</span>
                </div>
                {outletName && (
                  <div className="profile-row">
                    <span className="text-sm">Outlet</span>
                    <span style={{ fontWeight: 500, fontSize: 13 }}>{outletName}</span>
                  </div>
                )}
                {user?.phone && (
                  <div className="profile-row">
                    <span className="text-sm">Phone</span>
                    <span style={{ fontSize: 13 }}>{user.phone}</span>
                  </div>
                )}
              </div>
              <div className="profile-dropdown-footer">
                <Link to="/" className="profile-link" onClick={() => setShowProfile(false)}>
                  ← Switch Outlet
                </Link>
                <button onClick={logout} className="btn-logout">
                  ⏻ Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </header>
      <div className="container">
        <Outlet context={{ outletId: Number(outletId), role }} />
      </div>
    </div>
  );
}
