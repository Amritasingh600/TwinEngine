import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getOutlets } from '../services/api';
import { useAuth } from '../utils/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [outlets, setOutlets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOutlets()
      .then((res) => setOutlets(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <header className="topbar">
        <h1>TwinEngine</h1>
        <span>
          {user?.username || user?.user?.username || 'User'}{' '}
          <button onClick={logout} className="btn-sm">Logout</button>
        </span>
      </header>

      <div className="container">
        <h2>Select Outlet</h2>
        {outlets.length === 0 && <p>No outlets found.</p>}
        <div className="grid-2">
          {outlets.map((o) => (
            <Link key={o.id} to={`/outlet/${o.id}`} className="card card-link">
              <h3>{o.name}</h3>
              <p>{o.city} &middot; {o.seating_capacity} seats</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
