"""
Model 4: Inventory Depletion Alert
Calculates days until stockout and generates restock urgency alerts.
No ML training required -- rule-based linear projection.
"""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# Urgency thresholds (days until stockout)
URGENCY_LEVELS = {
    'CRITICAL': 2,   # <= 2 days
    'HIGH': 4,       # 3-4 days
    'MODERATE': 7,   # 5-7 days
}
DEFAULT_LEAD_TIME_DAYS = 3  # assumed supplier delivery time


class InventoryPredictor:
    """Predicts inventory depletion and generates restock alerts."""

    def predict(self, outlet_id: int) -> dict:
        from apps.predictive_core.models import InventoryItem
        from apps.order_engine.models import OrderTicket

        items = InventoryItem.objects.filter(outlet_id=outlet_id)
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Get recent orders to estimate consumption
        recent_orders = OrderTicket.objects.filter(
            table__outlet_id=outlet_id,
            placed_at__gte=week_ago,
            status__in=['COMPLETED', 'SERVED'],
        )

        # Count item mentions in orders (from items JSON field)
        item_consumption = self._estimate_consumption(recent_orders, days=7)

        alerts = []
        expiring_soon = []

        for item in items:
            daily_rate = item_consumption.get(item.name.lower(), 0)

            if daily_rate > 0:
                days_until_stockout = float(item.current_quantity) / daily_rate
            elif item.is_low_stock:
                days_until_stockout = 1  # already low, assume critical
            else:
                days_until_stockout = 30  # no consumption data -> assume OK

            # Determine urgency
            if days_until_stockout <= URGENCY_LEVELS['CRITICAL'] or item.is_low_stock:
                urgency = 'CRITICAL'
            elif days_until_stockout <= URGENCY_LEVELS['HIGH']:
                urgency = 'HIGH'
            elif days_until_stockout <= URGENCY_LEVELS['MODERATE']:
                urgency = 'MODERATE'
            else:
                urgency = 'OK'

            # Suggested reorder quantity
            suggested_qty = max(
                0,
                float(item.par_level) - float(item.current_quantity) + (daily_rate * DEFAULT_LEAD_TIME_DAYS)
            )

            if urgency != 'OK':
                alerts.append({
                    "item": item.name,
                    "category": item.category,
                    "current_quantity": float(item.current_quantity),
                    "unit": item.unit,
                    "daily_consumption_rate": round(daily_rate, 2),
                    "days_until_stockout": round(days_until_stockout, 1),
                    "urgency": urgency,
                    "suggested_order_qty": round(suggested_qty, 1),
                })

            # Expiry check
            if item.expiry_date and item.expiry_date <= (now.date() + timedelta(days=7)):
                days_left = (item.expiry_date - now.date()).days
                expiring_soon.append({
                    "item": item.name,
                    "expiry_date": str(item.expiry_date),
                    "days_left": max(days_left, 0),
                })

        # Sort alerts by urgency
        urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2}
        alerts.sort(key=lambda x: urgency_order.get(x['urgency'], 3))

        return {
            "outlet_id": outlet_id,
            "inventory_alerts": alerts,
            "expiring_soon": expiring_soon,
            "total_critical": sum(1 for a in alerts if a['urgency'] == 'CRITICAL'),
            "total_alerts": len(alerts),
        }

    def _estimate_consumption(self, orders_qs, days: int) -> dict:
        """
        Parse OrderTicket.items JSON to estimate daily consumption per ingredient.
        Returns: {"item_name_lower": daily_consumption_rate}
        """
        item_counts = {}
        for order in orders_qs:
            items_list = order.items if isinstance(order.items, list) else []
            for entry in items_list:
                name = entry.get('name', '') if isinstance(entry, dict) else str(entry)
                name_lower = name.lower().strip()
                if name_lower:
                    qty = entry.get('quantity', 1) if isinstance(entry, dict) else 1
                    item_counts[name_lower] = item_counts.get(name_lower, 0) + qty

        # Convert to daily rate
        return {name: count / max(days, 1) for name, count in item_counts.items()}
