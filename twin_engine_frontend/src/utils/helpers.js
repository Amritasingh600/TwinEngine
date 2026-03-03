/** Map node status to hex color */
export const STATUS_COLORS = {
  BLUE: '#3B82F6',
  RED: '#EF4444',
  GREEN: '#22C55E',
  YELLOW: '#F59E0B',
  GREY: '#6B7280',
};

export const STATUS_LABELS = {
  BLUE: 'Available',
  RED: 'Waiting',
  GREEN: 'Served',
  YELLOW: 'Delay',
  GREY: 'Inactive',
};

/** Format date to YYYY-MM-DD */
export function fmtDate(d = new Date()) {
  return d.toISOString().slice(0, 10);
}

/** Format currency (INR) */
export function fmtCurrency(n) {
  return `Rs. ${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 0 })}`;
}
