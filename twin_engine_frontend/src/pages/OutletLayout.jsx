import { useState, useEffect } from 'react';
import { useParams, Link, Outlet } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';

const NAV = [
  { to: '', label: 'Floor' },
  { to: 'orders', label: 'Orders' },
  { to: 'predictions', label: 'Predictions' },
  { to: 'inventory', label: 'Inventory' },
  { to: 'reports', label: 'Reports' },
];

export default function OutletLayout() {
  const { outletId } = useParams();
  const { user, logout } = useAuth();

  return (
    <div>
      <header className="topbar">
        <Link to="/" className="topbar-brand">TwinEngine</Link>
        <nav className="topbar-nav">
          {NAV.map((n) => (
            <Link key={n.to} to={`/outlet/${outletId}/${n.to}`}>
              {n.label}
            </Link>
          ))}
        </nav>
        <span>
          {user?.username || user?.user?.username || ''}{' '}
          <button onClick={logout} className="btn-sm">Logout</button>
        </span>
      </header>
      <div className="container">
        <Outlet context={{ outletId: Number(outletId) }} />
      </div>
    </div>
  );
}
