"""
Raw Data Collector — Aggregates all operational data for a given outlet + date range.

Collects:
  - Orders (all statuses, items, waiters, wait times)
  - Payments (methods, totals, tips)
  - Table utilisation (status history, occupancy)
  - Inventory levels (low stock, expiring)
  - Staff on shift
  - Existing daily summaries (if any)

Returns a single structured dict ready to be sent to GPT-4o.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum, Avg, Count, Max, Min, F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def _decimal_to_float(obj):
    """Recursively convert Decimal → float for JSON serialisation."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_decimal_to_float(i) for i in obj]
    return obj


def collect_raw_data(outlet, start_date, end_date):
    """
    Collect ALL raw operational data for an outlet in a date range.

    Returns a dict with keys:
        outlet_info, orders, payments, tables, inventory, staff, summary_stats
    """
    from apps.order_engine.models import OrderTicket, PaymentLog
    from apps.layout_twin.models import ServiceNode
    from apps.predictive_core.models import InventoryItem, StaffSchedule
    from apps.insights_hub.models import DailySummary

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # ── 1. Outlet info ──
    outlet_info = {
        "name": outlet.name,
        "brand": outlet.brand.name,
        "city": outlet.city,
        "seating_capacity": outlet.seating_capacity,
        "opening_time": str(outlet.opening_time),
        "closing_time": str(outlet.closing_time),
    }

    # ── 2. Orders ──
    orders_qs = OrderTicket.objects.filter(
        table__outlet=outlet,
        placed_at__date__gte=start_date,
        placed_at__date__lte=end_date,
    ).select_related('table', 'waiter', 'waiter__user')

    orders_list = []
    for o in orders_qs:
        orders_list.append({
            "order_id": o.pk,
            "table": o.table.name,
            "waiter": o.waiter.user.get_full_name() or o.waiter.user.username if o.waiter else "Unassigned",
            "status": o.status,
            "items": o.items,
            "party_size": o.party_size,
            "subtotal": float(o.subtotal),
            "tax": float(o.tax),
            "total": float(o.total),
            "placed_at": o.placed_at.isoformat(),
            "served_at": o.served_at.isoformat() if o.served_at else None,
            "completed_at": o.completed_at.isoformat() if o.completed_at else None,
            "wait_time_minutes": o.wait_time_minutes,
            "is_long_wait": o.is_long_wait,
            "special_requests": o.special_requests or "",
        })

    # ── 3. Order aggregates ──
    order_agg = orders_qs.aggregate(
        total_revenue=Sum('total'),
        total_orders=Count('id'),
        avg_ticket=Avg('total'),
        total_guests=Sum('party_size'),
        avg_wait=Avg(
            F('served_at') - F('placed_at'),
            filter=Q(served_at__isnull=False),
        ),
    )
    order_agg = _decimal_to_float(order_agg)
    # Convert avg_wait timedelta to minutes
    if order_agg.get('avg_wait'):
        order_agg['avg_wait_minutes'] = order_agg['avg_wait'].total_seconds() / 60
    else:
        order_agg['avg_wait_minutes'] = 0
    order_agg.pop('avg_wait', None)

    status_breakdown = dict(
        orders_qs.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
    )

    # ── 4. Payments ──
    payments_qs = PaymentLog.objects.filter(
        order__table__outlet=outlet,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    payment_agg = payments_qs.aggregate(
        total_collected=Sum('amount', filter=Q(status='SUCCESS')),
        total_tips=Sum('tip_amount', filter=Q(status='SUCCESS')),
        payment_count=Count('id', filter=Q(status='SUCCESS')),
        refund_count=Count('id', filter=Q(status='REFUNDED')),
    )
    payment_agg = _decimal_to_float(payment_agg)

    payment_methods = dict(
        payments_qs.filter(status='SUCCESS')
        .values_list('method')
        .annotate(count=Count('id'))
        .values_list('method', 'count')
    )

    # ── 5. Tables ──
    tables_qs = ServiceNode.objects.filter(outlet=outlet, node_type='TABLE', is_active=True)
    table_statuses = dict(
        tables_qs.values_list('current_status').annotate(count=Count('id')).values_list('current_status', 'count')
    )
    total_tables = tables_qs.count()
    total_capacity = tables_qs.aggregate(cap=Sum('capacity'))['cap'] or 0

    # ── 6. Inventory ──
    inventory_qs = InventoryItem.objects.filter(outlet=outlet)
    low_stock_items = list(
        inventory_qs.filter(current_quantity__lte=F('reorder_threshold'))
        .values('name', 'category', 'current_quantity', 'reorder_threshold', 'unit')
    )
    low_stock_items = _decimal_to_float(low_stock_items)

    inventory_summary = {
        "total_items": inventory_qs.count(),
        "low_stock_count": len(low_stock_items),
        "low_stock_items": low_stock_items,
    }

    # ── 7. Staff ──
    try:
        staff_schedules = StaffSchedule.objects.filter(
            staff__outlet=outlet,
            date__gte=start_date,
            date__lte=end_date,
        )
        staff_summary = {
            "total_shifts": staff_schedules.count(),
            "by_shift": dict(
                staff_schedules.values_list('shift')
                .annotate(count=Count('id'))
                .values_list('shift', 'count')
            ),
        }
    except Exception:
        staff_summary = {"total_shifts": 0, "by_shift": {}}

    # ── 8. Existing daily summaries ──
    existing_summaries = list(
        DailySummary.objects.filter(
            outlet=outlet,
            date__gte=start_date,
            date__lte=end_date,
        ).values(
            'date', 'total_revenue', 'total_orders', 'total_guests',
            'avg_wait_time', 'delayed_orders', 'cancelled_orders',
            'peak_hour', 'sales_by_category', 'top_selling_items',
        )
    )
    existing_summaries = _decimal_to_float(existing_summaries)
    # Convert date to string
    for s in existing_summaries:
        s['date'] = str(s['date'])

    # ── Assemble payload ──
    raw_data = {
        "report_period": {
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        "outlet_info": outlet_info,
        "order_summary": {
            **order_agg,
            "status_breakdown": status_breakdown,
        },
        "orders_detail": orders_list,
        "payment_summary": {
            **payment_agg,
            "methods_breakdown": payment_methods,
        },
        "table_overview": {
            "total_tables": total_tables,
            "total_capacity": total_capacity,
            "current_status_breakdown": table_statuses,
        },
        "inventory_summary": inventory_summary,
        "staff_summary": staff_summary,
        "existing_daily_summaries": existing_summaries,
    }

    logger.info(
        "Raw data collected for %s (%s -> %s): %d orders, Rs.%.2f revenue",
        outlet.name, start_date, end_date,
        order_agg.get('total_orders', 0) or 0,
        order_agg.get('total_revenue', 0) or 0,
    )

    return raw_data
