import { useState } from 'react';
import { useAuth } from '../utils/AuthContext';
import { ROLES } from '../utils/AuthContext';
import { useNavigate } from 'react-router-dom';

const ROLE_LABELS = {
  [ROLES.MANAGER]: 'Manager',
  [ROLES.CHEF]: 'Chef',
  [ROLES.CASHIER]: 'Cashier',
  [ROLES.HOST]: 'Host / Hostess',
  [ROLES.WAITER]: 'Waiter',
};

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!selectedRole) {
      setError('Please select your role');
      return;
    }

    setBusy(true);
    try {
      const profile = await login(username, password);
      /* Verify the backend role matches what the user selected */
      if (profile.role !== selectedRole) {
        setError(
          `Your account role is "${ROLE_LABELS[profile.role] || profile.role}", not "${ROLE_LABELS[selectedRole]}". Please select the correct role.`
        );
        setBusy(false);
        return;
      }
      navigate('/dashboard');
    } catch {
      setError('Invalid credentials');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-center">
      <form onSubmit={handleSubmit} className="login-card">
        <h2 style={{ marginBottom: 4, color: '#2D2428' }}>◆ TwinEngine</h2>
        <p className="login-sub">Sign in to your dashboard</p>

        {error && <p className="text-error" style={{ textAlign: 'center', color: '#FF9090' }}>{error}</p>}

        <label>
          Role
          <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)} required>
            <option value="">-- Select Role --</option>
            {Object.entries(ROLE_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <button type="submit" disabled={busy}>
          {busy ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}
