/** Map node status to hex color — TwinEngine pastel palette */
export const STATUS_COLORS = {
  BLUE: '#A3F8F8',
  RED: '#FF9090',
  GREEN: '#A5E2E2',
  YELLOW: '#FFAFCC',
  GREY: '#DFBEBF',
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
