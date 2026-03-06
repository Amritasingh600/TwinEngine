import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getPredictionDashboard, getBusyHours, getRevenue, getStaffing, generateData } from '../services/api';
import { fmtDate, fmtCurrency } from '../utils/helpers';
import { ROLES } from '../utils/AuthContext';

export default function PredictionsPage() {
  const { outletId, role } = useOutletContext();
  const [date, setDate] = useState(fmtDate());
  const [dashboard, setDashboard] = useState(null);
  const [busyHours, setBusyHours] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [staffing, setStaffing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Generate data state
  const [genDate, setGenDate] = useState(fmtDate());
  const [genOrderCount, setGenOrderCount] = useState(40);
  const [genDays, setGenDays] = useState(14);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState(null);
  const [genError, setGenError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [d, b, r, s] = await Promise.all([
        getPredictionDashboard(outletId, date).catch(() => null),
        getBusyHours(outletId, date).catch(() => null),
        getRevenue(outletId, date).catch(() => null),
        getStaffing(outletId, date).catch(() => null),
      ]);
      setDashboard(d?.data);
      setBusyHours(b?.data);
      setRevenue(r?.data);
      setStaffing(s?.data);
    } catch {
      setError('Failed to load predictions. Models may need training.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [outletId, date]);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenError('');
    setGenResult(null);
    try {
      const { data } = await generateData(outletId, genDate, genOrderCount, genDays);
      setGenResult(data);
      // Refresh predictions after generating data
      load();
    } catch (err) {
      setGenError(
        err.response?.data?.error || 'Failed to generate data. Check console for details.'
      );
    } finally {
      setGenerating(false);
    }
  };

  /* Only MANAGER can view predictions */
  if (role !== ROLES.MANAGER) {
    return (
      <div className="empty-state" style={{ marginTop: 40 }}>
        <h3>🔒 Access Denied</h3>
        <p>ML Predictions are available to Managers only.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex-between">
        <h2>🤖 ML Predictions</h2>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {/* ── Generate Data Section ── */}
      <div className="card" style={{ marginTop: 12, border: '1px solid #E0E7FF', background: '#F5F3FF' }}>
        <h3 style={{ margin: '0 0 8px' }}>⚡ Generate Restaurant Data</h3>
        <p className="text-sm" style={{ color: '#6B7280', margin: '0 0 12px' }}>
          Generate multi-day historical data across all tables: orders, payments, inventory
          depletion, staff schedules, hourly sales data &amp; daily summaries — enough for
          ML predictions &amp; reports.
        </p>
        <div className="flex-row" style={{ gap: 10, flexWrap: 'wrap', alignItems: 'end' }}>
          <label>
            Date
            <input type="date" value={genDate} onChange={(e) => setGenDate(e.target.value)} />
          </label>
          <label>
            Orders/Day
            <input
              type="number" min="5" max="200" value={genOrderCount}
              onChange={(e) => setGenOrderCount(Number(e.target.value))}
              style={{ width: 80 }}
            />
          </label>
          <label>
            Days
            <input
              type="number" min="1" max="30" value={genDays}
              onChange={(e) => setGenDays(Number(e.target.value))}
              style={{ width: 60 }}
            />
          </label>
          <button
            onClick={handleGenerate}
            disabled={generating}
            style={{
              background: generating ? '#9CA3AF' : '#4F46E5',
              color: '#fff',
              fontWeight: 600,
              padding: '8px 20px',
              border: 'none',
              borderRadius: 8,
              cursor: generating ? 'not-allowed' : 'pointer',
            }}
          >
            {generating ? 'Generating...' : 'Generate'}
          </button>
        </div>

        {genError && <p className="text-error" style={{ marginTop: 8 }}>{genError}</p>}

        {genResult && (
          <div style={{ marginTop: 12, padding: 12, background: '#ECFDF5', borderRadius: 8, fontSize: 14 }}>
            <p style={{ fontWeight: 600, color: '#065F46', margin: '0 0 6px' }}>
              ✅ {genResult.message}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 4 }}>
              {Object.entries(genResult.created || {}).map(([key, val]) => (
                <span key={key} style={{ color: '#374151' }}>
                  <strong>{key.replace(/_/g, ' ')}:</strong> {val}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading && <p>Loading predictions...</p>}
      {error && <p className="text-error">{error}</p>}

      {!loading && dashboard && (
        <>
          {/* Summary cards */}
          <div className="grid-3" style={{ marginTop: 12 }}>
            <SummaryCard
              title="Predicted Footfall"
              value={dashboard.footfall?.predicted_footfall ?? '-'}
            />
            <SummaryCard
              title="Predicted Revenue"
              value={
                dashboard.revenue?.hourly_predictions
                  ? fmtCurrency(
                      dashboard.revenue.hourly_predictions.reduce(
                        (s, h) => s + (h.predicted_revenue || 0),
                        0
                      )
                    )
                  : '-'
              }
            />
            <SummaryCard
              title="Inventory Alerts"
              value={dashboard.inventory_alerts?.alerts?.length ?? 0}
            />
          </div>

          {/* Busy hours */}
          {busyHours?.hourly_predictions && (
            <Section title="Busy Hours">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Prediction</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {busyHours.hourly_predictions.map((h) => (
                    <tr key={h.hour}>
                      <td>{h.hour}:00</td>
                      <td>
                        <span
                          className="badge"
                          style={{
                            background: h.is_busy ? '#EF4444' : '#22C55E',
                            color: '#fff',
                          }}
                        >
                          {h.is_busy ? 'Busy' : 'Slow'}
                        </span>
                      </td>
                      <td>{(h.confidence * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Revenue forecast */}
          {revenue?.hourly_predictions && (
            <Section title="Revenue Forecast">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Predicted Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {revenue.hourly_predictions.map((h) => (
                    <tr key={h.hour}>
                      <td>{h.hour}:00</td>
                      <td>{fmtCurrency(h.predicted_revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Staffing */}
          {staffing?.shift_recommendations && (
            <Section title="Staffing Recommendations">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Shift</th>
                    <th>Recommended Staff</th>
                    <th>Currently Scheduled</th>
                  </tr>
                </thead>
                <tbody>
                  {staffing.shift_recommendations.map((s) => (
                    <tr key={s.shift}>
                      <td>{s.shift}</td>
                      <td>{s.recommended_count}</td>
                      <td>{s.current_scheduled ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Inventory alerts */}
          {dashboard.inventory_alerts?.alerts?.length > 0 && (
            <Section title="Inventory Alerts">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Current Qty</th>
                    <th>Reorder Level</th>
                    <th>Alert</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.inventory_alerts.alerts.map((a, i) => (
                    <tr key={i}>
                      <td>{a.item_name || a.name}</td>
                      <td>{a.current_quantity}</td>
                      <td>{a.reorder_threshold}</td>
                      <td className="text-error">{a.alert || 'Low Stock'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function SummaryCard({ title, value }) {
  return (
    <div className="card">
      <p className="text-sm">{title}</p>
      <p style={{ fontSize: 22, fontWeight: 600, margin: '4px 0 0' }}>{value}</p>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginTop: 20 }}>
      <h3>{title}</h3>
      {children}
    </div>
  );
}
