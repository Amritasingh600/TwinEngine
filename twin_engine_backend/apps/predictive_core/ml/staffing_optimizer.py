"""
Model 5: Staff Optimization Model
Recommends waiters and chefs per shift based on predicted demand.
Algorithm: Ratio-based rules using outputs from Models 1 & 2.
"""
import logging
import math

logger = logging.getLogger(__name__)

# Tunable ratios (can be adjusted per outlet later)
TABLES_PER_WAITER = 4           # 1 waiter handles 4 active tables
ORDERS_PER_CHEF_PER_HOUR = 14   # 1 chef can handle 14 orders/hour
MIN_WAITERS = 1
MIN_CHEFS = 1
HOURLY_WAGE = 200  # Rs. per hour (rough average)

# Shift hour ranges
SHIFT_HOURS = {
    'MORNING':   (6, 14),
    'AFTERNOON': (14, 22),
    'NIGHT':     (22, 6),  # wraps around midnight
}


class StaffingOptimizer:
    """Recommends staffing levels based on predicted demand."""

    def predict(self, outlet_id: int, target_date, demand_forecast: dict = None) -> dict:
        """
        Generate staffing recommendations per shift.

        Args:
            outlet_id: outlet to predict for
            target_date: date to predict
            demand_forecast: output from BusyHoursPredictor.predict()
                             if None, will call it internally
        """
        from apps.hospitality_group.models import Outlet

        outlet = Outlet.objects.get(id=outlet_id)
        total_tables = outlet.service_nodes.filter(node_type='TABLE').count() or 15

        # Get demand forecast if not provided
        if demand_forecast is None:
            from .demand_model import BusyHoursPredictor
            demand_forecast = BusyHoursPredictor().predict(outlet_id, target_date)

        hourly = {h['hour']: h['predicted_orders'] for h in demand_forecast.get('hourly_forecast', [])}

        recommendations = {}
        total_staff = 0
        total_hours = 0

        for shift_name, (start_h, end_h) in SHIFT_HOURS.items():
            # Get hours in this shift
            if start_h < end_h:
                shift_hours_list = list(range(start_h, end_h))
            else:  # night shift wraps
                shift_hours_list = list(range(start_h, 24)) + list(range(0, end_h))

            # Peak demand in this shift
            shift_orders = [hourly.get(h, 0) for h in shift_hours_list]
            peak_orders = max(shift_orders) if shift_orders else 0
            total_shift_orders = sum(shift_orders)

            # Calculate active tables at peak (assume 70% of orders are concurrent)
            active_tables_at_peak = min(math.ceil(peak_orders * 0.7), total_tables)

            # Waiters needed
            waiters = max(MIN_WAITERS, math.ceil(active_tables_at_peak / TABLES_PER_WAITER))

            # Chefs needed (based on peak hourly orders)
            chefs = max(MIN_CHEFS, math.ceil(peak_orders / ORDERS_PER_CHEF_PER_HOUR))

            shift_staff = waiters + chefs
            shift_duration = len(shift_hours_list)
            total_staff += shift_staff
            total_hours += shift_staff * shift_duration

            recommendations[shift_name] = {
                "recommended_waiters": waiters,
                "recommended_chefs": chefs,
                "predicted_peak_orders_per_hour": peak_orders,
                "predicted_total_orders": total_shift_orders,
                "reason": self._build_reason(waiters, chefs, peak_orders, active_tables_at_peak),
            }

        estimated_cost = total_hours * HOURLY_WAGE

        return {
            "date": str(target_date),
            "outlet_id": outlet_id,
            "staffing_recommendation": recommendations,
            "total_staff_needed": total_staff,
            "estimated_cost": "Rs.{:,.0f}".format(estimated_cost),
        }

    def _build_reason(self, waiters, chefs, peak_orders, active_tables):
        parts = []
        parts.append("{} waiter(s) for ~{} active tables".format(waiters, active_tables))
        parts.append("{} chef(s) for ~{} orders/hr at peak".format(chefs, peak_orders))
        return " | ".join(parts)
