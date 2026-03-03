import { useState } from 'react';
import { useAuth } from '../utils/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError('Invalid credentials');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-center">
      <form onSubmit={handleSubmit} className="card" style={{ width: 340 }}>
        <h2>TwinEngine Login</h2>
        {error && <p className="text-error">{error}</p>}
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
