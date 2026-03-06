import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getPredictionDashboard, getBusyHours, getRevenue, getStaffing, trainModels } from '../services/api';
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
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');
  const [trainMsg, setTrainMsg] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    setTrainMsg('');
    const errors = [];
    try {
      const [d, b, r, s] = await Promise.all([
        getPredictionDashboard(outletId, date).catch((e) => { errors.push(e); return null; }),
        getBusyHours(outletId, date).catch((e) => { errors.push(e); return null; }),
        getRevenue(outletId, date).catch((e) => { errors.push(e); return null; }),
        getStaffing(outletId, date).catch((e) => { errors.push(e); return null; }),
      ]);

      const dData = d?.data;
      const bData = b?.data;
      const rData = r?.data;
      const sData = s?.data;

      setDashboard(dData ?? null);
      setBusyHours(bData ?? null);
      setRevenue(rData ?? null);
      setStaffing(sData ?? null);

      /* Check if everything came back as fallback/error dicts */
      const allFallback = dData?.fallback || (!dData && errors.length > 0);
      if (allFallback) {
        setError('ML models may not be trained yet. Click "Train Models" to initialise them.');
      } else if (errors.length === 4) {
        setError('Failed to load predictions. Please check your connection or try logging in again.');
      } else if (errors.length > 0 && errors.length < 4) {
        setError('Some predictions could not be loaded.');
      }
    } catch {
      setError('Failed to load predictions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    setTrainMsg('');
    setError('');
    try {
      const { data } = await trainModels(outletId);
      setTrainMsg(data.status === 'training complete'
        ? '✅ Models trained successfully! Refreshing predictions...'
        : '⏳ Training dispatched. Refresh in a minute.');
      if (data.status === 'training complete') {
        setTimeout(load, 1500);
      }
    } catch (e) {
      setTrainMsg('❌ Training failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setTraining(false);
    }
  };

  useEffect(() => { if (outletId) load(); }, [outletId, date]);

  /* Only MANAGER can view predictions */
  if (role !== ROLES.MANAGER) {
    return (
      <div className="empty-state" style={{ marginTop: 40 }}>
        <h3>🔒 Access Denied</h3>
        <p>ML Predictions are available to Managers only.</p>
      </div>
    );
  }

  /* Helper: compute total revenue from the response */
  const totalRevenue =
    dashboard?.revenue?.next_week?.total_predicted_revenue
    ?? dashboard?.revenue?.next_day?.predicted_revenue
    ?? null;

  /* Helper: inventory alerts array (backend key is "inventory_alerts") */
  const invAlerts = dashboard?.inventory_alerts?.inventory_alerts ?? [];
  const expiringSoon = dashboard?.inventory_alerts?.expiring_soon ?? [];

  /* Helper: convert staffing_recommendation object → array */
  const shiftRows = staffing?.staffing_recommendation
    ? Object.entries(staffing.staffing_recommendation).map(([shift, info]) => ({
        shift,
        ...info,
      }))
    : [];

  return (
    <div>
      <div className="flex-between">
        <h2>🤖 ML Predictions</h2>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {loading && <p>Loading predictions...</p>}
      {error && <p className="text-error" style={{ margin: '12px 0' }}>{error}</p>}
      {trainMsg && <p style={{ margin: '12px 0', color: trainMsg.startsWith('❌') ? '#FF9090' : '#4EB89D' }}>{trainMsg}</p>}

      {/* Train models button — always visible for managers */}
      <button
        onClick={handleTrain}
        disabled={training}
        style={{ margin: '8px 0 16px', padding: '8px 16px', cursor: training ? 'not-allowed' : 'pointer' }}
      >
        {training ? '⏳ Training...' : '🧠 Train Models'}
      </button>

      {!loading && !dashboard && !error && (
        <div className="empty-state" style={{ marginTop: 20 }}>
          <p>No prediction data available. Try training the models first.</p>
        </div>
      )}

      {!loading && dashboard && !dashboard.fallback && (
        <>
          {/* Summary cards */}
          <div className="grid-3" style={{ marginTop: 12 }}>
            <SummaryCard
              title="Predicted Footfall"
              value={dashboard.footfall?.total_predicted_guests ?? '-'}
            />
            <SummaryCard
              title="Predicted Revenue"
              value={totalRevenue != null ? fmtCurrency(totalRevenue) : '-'}
            />
            <SummaryCard
              title="Inventory Alerts"
              value={dashboard.inventory_alerts?.total_alerts ?? invAlerts.length}
            />
          </div>

          {/* Busy hours */}
          {busyHours?.hourly_forecast && (
            <Section title="Busy Hours">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Peak hour: <strong>{busyHours.peak_hour}:00</strong> &nbsp;|&nbsp;
                Total predicted orders: <strong>{busyHours.total_predicted_orders}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{busyHours.confidence}</strong>
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Predicted Orders</th>
                    <th>Intensity</th>
                  </tr>
                </thead>
                <tbody>
                  {busyHours.hourly_forecast.map((h) => {
                    const pct = busyHours.total_predicted_orders
                      ? h.predicted_orders / busyHours.total_predicted_orders
                      : 0;
                    const isBusy = pct > 0.08;
                    return (
                      <tr key={h.hour}>
                        <td>{h.hour}:00</td>
                        <td>{h.predicted_orders}</td>
                        <td>
                          <span
                            className="badge"
                            style={{
                              background: isBusy ? '#FF9090' : '#A5E2E2',
                              color: '#2D2428',
                            }}
                          >
                            {isBusy ? 'Busy' : 'Slow'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
          )}

          {/* Revenue forecast */}
          {revenue?.next_week?.daily_breakdown && (
            <Section title="Revenue Forecast (Next 7 Days)">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Today: <strong>{fmtCurrency(revenue.next_day?.predicted_revenue ?? 0)}</strong> &nbsp;|&nbsp;
                Week total: <strong>{fmtCurrency(revenue.next_week?.total_predicted_revenue ?? 0)}</strong>
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Predicted Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {revenue.next_week.daily_breakdown.map((d) => (
                    <tr key={d.date}>
                      <td>{d.date}</td>
                      <td>{fmtCurrency(d.predicted_revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Staffing */}
          {shiftRows.length > 0 && (
            <Section title="Staffing Recommendations">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Total staff needed: <strong>{staffing.total_staff_needed}</strong> &nbsp;|&nbsp;
                Estimated cost: <strong>{staffing.estimated_cost}</strong>
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Shift</th>
                    <th>Waiters</th>
                    <th>Chefs</th>
                    <th>Peak Orders/hr</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {shiftRows.map((s) => (
                    <tr key={s.shift}>
                      <td>{s.shift}</td>
                      <td>{s.recommended_waiters}</td>
                      <td>{s.recommended_chefs}</td>
                      <td>{s.predicted_peak_orders_per_hour}</td>
                      <td style={{ fontSize: 12 }}>{s.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Inventory alerts */}
          {invAlerts.length > 0 && (
            <Section title="Inventory Alerts">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Category</th>
                    <th>Current Qty</th>
                    <th>Days Until Stockout</th>
                    <th>Urgency</th>
                    <th>Suggested Order</th>
                  </tr>
                </thead>
                <tbody>
                  {invAlerts.map((a, i) => (
                    <tr key={i}>
                      <td>{a.item}</td>
                      <td>{a.category}</td>
                      <td>{a.current_quantity} {a.unit}</td>
                      <td>{a.days_until_stockout}</td>
                      <td className="text-error">{a.urgency}</td>
                      <td>{a.suggested_order_qty} {a.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Expiring soon */}
          {expiringSoon.length > 0 && (
            <Section title="Expiring Soon">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Expiry Date</th>
                    <th>Days Left</th>
                  </tr>
                </thead>
                <tbody>
                  {expiringSoon.map((e, i) => (
                    <tr key={i}>
                      <td>{e.item}</td>
                      <td>{e.expiry_date}</td>
                      <td className={e.days_left <= 1 ? 'text-error' : ''}>{e.days_left}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Footfall by hour */}
          {dashboard.footfall?.hourly_guests && (
            <Section title="Hourly Footfall Forecast">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Total guests: <strong>{dashboard.footfall.total_predicted_guests}</strong> &nbsp;|&nbsp;
                Avg party size: <strong>{dashboard.footfall.avg_party_size}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{dashboard.footfall.confidence}</strong>
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Predicted Guests</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.footfall.hourly_guests.map((h) => (
                    <tr key={h.hour}>
                      <td>{h.hour}:00</td>
                      <td>{h.predicted_guests}</td>
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
