import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  getTodaySchedules,
  getSchedules,
  createSchedule,
  checkInSchedule,
  checkOutSchedule,
  getAllStaff,
} from '../services/api';

const SHIFTS = [
  { value: 'MORNING', label: 'Morning (6AM–2PM)' },
  { value: 'AFTERNOON', label: 'Afternoon (2PM–10PM)' },
  { value: 'NIGHT', label: 'Night (10PM–6AM)' },
  { value: 'SPLIT', label: 'Split Shift' },
];

const SHIFT_COLOR = {
  MORNING: '#FFDBA4',
  AFTERNOON: '#A5E2E2',
  NIGHT: '#CDB4DB',
  SPLIT: '#FFAFCC',
};

export default function SchedulePage() {
  const { outletId } = useOutletContext();
  const [todaySchedules, setTodaySchedules] = useState([]);
  const [allSchedules, setAllSchedules] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('today'); // 'today' | 'all' | 'create'
  const [form, setForm] = useState({ staff: '', date: '', shift: 'MORNING', start_time: '', end_time: '', notes: '' });
  const [creating, setCreating] = useState(false);

  const fetchToday = () =>
    getTodaySchedules(outletId)
      .then((r) => setTodaySchedules(r.data.results || r.data || []))
      .catch(() => {});

  const fetchAll = () =>
    getSchedules({ staff__outlet: outletId, ordering: '-date' })
      .then((r) => setAllSchedules(r.data.results || r.data || []))
      .catch(() => {});

  const fetchStaff = () =>
    getAllStaff(outletId)
      .then((r) => setStaff(r.data.results || r.data || []))
      .catch(() => {});

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchToday(), fetchAll(), fetchStaff()]).finally(() => setLoading(false));
  }, [outletId]);

  const handleCheckIn = async (id) => {
    try {
      await checkInSchedule(id);
      toast.success('Checked in');
      fetchToday();
    } catch { toast.error('Check-in failed'); }
  };

  const handleCheckOut = async (id) => {
    try {
      await checkOutSchedule(id);
      toast.success('Checked out');
      fetchToday();
    } catch { toast.error('Check-out failed'); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.staff || !form.date) { toast.error('Staff and date are required'); return; }
    setCreating(true);
    try {
      await createSchedule(form);
      toast.success('Schedule created');
      setForm({ staff: '', date: '', shift: 'MORNING', start_time: '', end_time: '', notes: '' });
      fetchToday();
      fetchAll();
      setTab('today');
    } catch (err) {
      const msg = err.response?.data;
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg) || 'Failed to create');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="spinner-wrap"><div className="spinner" /></div>;

  return (
    <div className="page-content">
      <h2>📅 Staff Schedule</h2>

      {/* Tab bar */}
      <div className="flex-row" style={{ gap: 8, marginBottom: 16 }}>
        {['today', 'all', 'create'].map((t) => (
          <button key={t} className={`btn-sm ${tab === t ? '' : 'btn-outline'}`}
            style={tab === t ? { background: 'var(--primary)', color: '#fff' } : {}}
            onClick={() => setTab(t)}>
            {t === 'today' ? "Today's Schedule" : t === 'all' ? 'All Schedules' : '+ New'}
          </button>
        ))}
      </div>

      {/* ───── Today ───── */}
      {tab === 'today' && (
        <>
          {todaySchedules.length === 0 && <p className="text-hint">No schedules for today.</p>}
          {todaySchedules.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {todaySchedules.map((s) => (
                <div key={s.id} className="card" style={{ padding: 14 }}>
                  <div className="flex-row" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
                    <strong>{s.staff_name || `Staff #${s.staff}`}</strong>
                    <span className="badge" style={{
                      background: SHIFT_COLOR[s.shift] || '#E0E0E0',
                      color: '#2D2428', fontSize: 11,
                    }}>{s.shift}</span>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--gray-500)', lineHeight: 1.8 }}>
                    <div>Role: <strong>{s.staff_role || '—'}</strong></div>
                    {s.start_time && <div>Time: {s.start_time?.slice(0, 5)} – {s.end_time?.slice(0, 5)}</div>}
                    {s.notes && <div>Notes: {s.notes}</div>}
                    {s.is_ai_suggested && <div style={{ color: '#8E44AD' }}>🤖 AI suggested</div>}
                  </div>
                  <div className="flex-row" style={{ gap: 6, marginTop: 10 }}>
                    {!s.checked_in && (
                      <button className="btn-sm" style={{ background: '#A5E2E2' }} onClick={() => handleCheckIn(s.id)}>
                        Check In
                      </button>
                    )}
                    {s.checked_in && !s.checked_out && (
                      <button className="btn-sm" style={{ background: '#FFAFCC' }} onClick={() => handleCheckOut(s.id)}>
                        Check Out
                      </button>
                    )}
                    {s.checked_in && <span style={{ fontSize: 11, color: '#4CAF50' }}>✓ In{s.checked_out ? ' → Out' : ''}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ───── All Schedules ───── */}
      {tab === 'all' && (
        <>
          {allSchedules.length === 0 && <p className="text-hint">No schedules found.</p>}
          {allSchedules.length > 0 && (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Staff</th>
                  <th>Role</th>
                  <th>Date</th>
                  <th>Shift</th>
                  <th>Time</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {allSchedules.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 500 }}>{s.staff_name || `#${s.staff}`}</td>
                    <td>{s.staff_role || '—'}</td>
                    <td>{s.date}</td>
                    <td>
                      <span className="badge" style={{
                        background: SHIFT_COLOR[s.shift] || '#E0E0E0',
                        color: '#2D2428', fontSize: 11,
                      }}>{s.shift}</span>
                    </td>
                    <td style={{ fontSize: 12 }}>
                      {s.start_time ? `${s.start_time.slice(0, 5)} – ${s.end_time?.slice(0, 5)}` : '—'}
                    </td>
                    <td style={{ fontSize: 12 }}>
                      {s.checked_in && s.checked_out ? '✅ Done'
                        : s.checked_in ? '🟢 In'
                        : s.is_confirmed ? '📋 Confirmed'
                        : '⏳ Pending'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* ───── Create ───── */}
      {tab === 'create' && (
        <form onSubmit={handleCreate} style={{ maxWidth: 420 }}>
          <div className="form-group">
            <label>Staff Member</label>
            <select value={form.staff} onChange={(e) => setForm({ ...form, staff: e.target.value })} required>
              <option value="">Select staff…</option>
              {staff.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.user?.first_name ? `${s.user.first_name} ${s.user.last_name}` : s.user?.username || `#${s.id}`} — {s.role}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Date</label>
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Shift</label>
            <select value={form.shift} onChange={(e) => setForm({ ...form, shift: e.target.value })}>
              {SHIFTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div className="flex-row" style={{ gap: 12 }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Start Time</label>
              <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>End Time</label>
              <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
            </div>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <input type="text" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional notes…" />
          </div>
          <button type="submit" className="btn" disabled={creating}>
            {creating ? 'Creating…' : 'Create Schedule'}
          </button>
        </form>
      )}
    </div>
  );
}
