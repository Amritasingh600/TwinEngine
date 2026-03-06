import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  getPredictionDashboard, getBusyHours, getRevenue, getStaffing,
  getFootfall, getFoodDemand, getInventoryAlerts,
  generateData, trainModels,
} from '../services/api';
import { fmtDate, fmtCurrency } from '../utils/helpers';
import { ROLES } from '../utils/AuthContext';

const PIE_COLORS = ['#E7A4A3', '#A5E2E2', '#FFAFCC', '#FF9090', '#A3F8F8', '#DFBEBF', '#FFC7DD', '#FFE1ED'];

export default function PredictionsPage() {
  const { outletId, role } = useOutletContext();
  const [date, setDate] = useState(fmtDate());
  const [dashboard, setDashboard] = useState(null);
  const [busyHours, setBusyHours] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [staffing, setStaffing] = useState(null);
  const [footfall, setFootfall] = useState(null);
  const [foodDemand, setFoodDemand] = useState(null);
  const [invAlertsDirect, setInvAlertsDirect] = useState(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');
  const [trainMsg, setTrainMsg] = useState('');

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
    setTrainMsg('');
    const errors = [];
    try {
      const [d, b, r, s, f, fd, ia] = await Promise.all([
        getPredictionDashboard(outletId, date).catch((e) => { errors.push(e); return null; }),
        getBusyHours(outletId, date).catch((e) => { errors.push(e); return null; }),
        getRevenue(outletId, date).catch((e) => { errors.push(e); return null; }),
        getStaffing(outletId, date).catch((e) => { errors.push(e); return null; }),
        getFootfall(outletId, date).catch(() => null),
        getFoodDemand(outletId, date).catch(() => null),
        getInventoryAlerts(outletId).catch(() => null),
      ]);

      setDashboard(d?.data ?? null);
      setBusyHours(b?.data ?? null);
      setRevenue(r?.data ?? null);
      setStaffing(s?.data ?? null);
      setFootfall(f?.data ?? null);
      setFoodDemand(fd?.data ?? null);
      setInvAlertsDirect(ia?.data ?? null);

      /* Check if everything came back as fallback/error dicts */
      const allFallback = d?.data?.fallback || (!d?.data && errors.length > 0);
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
        toast.success('Models trained successfully!');
        setTimeout(load, 1500);
      }
    } catch (e) {
      toast.error('Training failed');
      setTrainMsg('❌ Training failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setTraining(false);
    }
  };

  useEffect(() => { if (outletId) load(); }, [outletId, date]);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenError('');
    setGenResult(null);
    try {
      const { data } = await generateData(outletId, genDate, genOrderCount, genDays);
      setGenResult(data);
      toast.success('Data generated successfully');
      load();
    } catch (err) {
      setGenError(err.response?.data?.error || 'Failed to generate data.');
      toast.error('Generation failed');
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

  /* Helper: compute total revenue from the response */
  const totalRevenue =
    dashboard?.revenue?.next_week?.total_predicted_revenue
    ?? dashboard?.revenue?.next_day?.predicted_revenue
    ?? null;

  /* Helper: inventory alerts — prefer direct endpoint, fallback to dashboard */
  const invAlerts = invAlertsDirect?.inventory_alerts
    ?? dashboard?.inventory_alerts?.inventory_alerts ?? [];
  const expiringSoon = invAlertsDirect?.expiring_soon
    ?? dashboard?.inventory_alerts?.expiring_soon ?? [];

  /* Chart data transforms */
  const busyChartData = busyHours?.hourly_forecast?.map((h) => ({
    hour: `${h.hour}:00`,
    orders: h.predicted_orders,
  })) ?? [];

  const revenueChartData = revenue?.next_week?.daily_breakdown?.map((d) => ({
    date: d.date.slice(5),
    revenue: Math.round(d.predicted_revenue),
  })) ?? [];

  const footfallChartData = (footfall?.hourly_guests || dashboard?.footfall?.hourly_guests)?.map((h) => ({
    hour: `${h.hour}:00`,
    guests: h.predicted_guests,
  })) ?? [];

  const foodDemandChartData = foodDemand?.food_demand
    ? Object.entries(foodDemand.food_demand).map(([name, qty]) => ({
        name,
        value: typeof qty === 'number' ? qty : qty?.predicted_quantity ?? 0,
      }))
    : [];

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

      {loading && <div className="spinner-wrap"><div className="spinner" /><span>Loading predictions...</span></div>}
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
            <SummaryCard title="Predicted Footfall"
              value={footfall?.total_predicted_guests ?? dashboard.footfall?.total_predicted_guests ?? '-'} />
            <SummaryCard title="Predicted Revenue"
              value={totalRevenue != null ? fmtCurrency(totalRevenue) : '-'} />
            <SummaryCard title="Inventory Alerts"
              value={invAlerts.length} />
          </div>

          {/* ── Busy Hours (Bar Chart) ── */}
          {busyChartData.length > 0 && (
            <Section title="Busy Hours Forecast">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Peak hour: <strong>{busyHours.peak_hour}:00</strong> &nbsp;|&nbsp;
                Total orders: <strong>{busyHours.total_predicted_orders}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{busyHours.confidence}</strong>
              </p>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={busyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0e0e0" />
                    <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="orders" name="Predicted Orders" fill="#E7A4A3" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Section>
          )}

          {/* ── Revenue Forecast (Line Chart + Table) ── */}
          {revenueChartData.length > 0 && (
            <Section title="Revenue Forecast (Next 7 Days)">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Today: <strong>{fmtCurrency(revenue.next_day?.predicted_revenue ?? 0)}</strong> &nbsp;|&nbsp;
                Week total: <strong>{fmtCurrency(revenue.next_week?.total_predicted_revenue ?? 0)}</strong>
              </p>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={revenueChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0e0e0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => `₹${v.toLocaleString('en-IN')}`} />
                    <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#E7A4A3" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <table className="data-table" style={{ marginTop: 12 }}>
                <thead><tr><th>Date</th><th>Predicted Revenue</th></tr></thead>
                <tbody>
                  {revenue.next_week.daily_breakdown.map((d) => (
                    <tr key={d.date}><td>{d.date}</td><td>{fmtCurrency(d.predicted_revenue)}</td></tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* ── Staffing ── */}
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

          {/* ── Inventory Alerts ── */}
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

          {/* ── Footfall (Area Chart) ── */}
          {footfallChartData.length > 0 && (
            <Section title="Hourly Footfall Forecast">
              <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 6 }}>
                Total guests: <strong>{footfall?.total_predicted_guests ?? dashboard.footfall?.total_predicted_guests}</strong> &nbsp;|&nbsp;
                Avg party: <strong>{footfall?.avg_party_size ?? dashboard.footfall?.avg_party_size}</strong> &nbsp;|&nbsp;
                Confidence: <strong>{footfall?.confidence ?? dashboard.footfall?.confidence}</strong>
              </p>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <AreaChart data={footfallChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0e0e0" />
                    <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="guests" name="Guests" fill="#A5E2E2" stroke="#4EB89D" fillOpacity={0.4} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Section>
          )}

          {/* ── Food Demand (Pie Chart) ── */}
          {foodDemandChartData.length > 0 && (
            <Section title="Predicted Food Demand">
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={foodDemandChartData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                      outerRadius={100} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                      {foodDemandChartData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
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
