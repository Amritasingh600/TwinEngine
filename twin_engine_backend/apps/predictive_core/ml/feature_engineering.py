"""
Shared feature engineering utilities for all prediction models.
Queries Django ORM and returns clean pandas DataFrames.
"""
import logging

import pandas as pd
import numpy as np
from datetime import timedelta
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def build_demand_features(outlet_id, min_days=7):
    """
    Build feature matrix from SalesData for demand/footfall/revenue models.

    Returns:
        pd.DataFrame with columns:
            hour, day_of_week, is_holiday, is_weekend,
            total_orders, total_revenue, avg_ticket_size,
            prev_week_orders, rolling_avg_orders_7d, rolling_avg_revenue_7d

        None if insufficient data.
    """
    from apps.predictive_core.models import SalesData

    qs = SalesData.objects.filter(outlet_id=outlet_id).order_by('date', 'hour')
    if qs.count() < min_days * 8:  # at least 8 hours/day
        return None

    df = pd.DataFrame(list(qs.values(
        'date', 'hour', 'day_of_week', 'is_holiday',
        'total_orders', 'total_revenue', 'avg_ticket_size',
        'avg_wait_time_minutes'
    )))

    # Derived features
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['date'] = pd.to_datetime(df['date'])

    # Cast decimal fields to float
    df['total_revenue'] = df['total_revenue'].astype(float)
    df['avg_ticket_size'] = df['avg_ticket_size'].astype(float)

    # Lag features (same hour, 7 days ago)
    df = df.sort_values(['date', 'hour']).reset_index(drop=True)
    df['prev_week_orders'] = df.groupby('hour')['total_orders'].shift(7)
    df['prev_week_revenue'] = df.groupby('hour')['total_revenue'].shift(7)

    # Rolling averages (7-day window per hour)
    df['rolling_avg_orders_7d'] = (
        df.groupby('hour')['total_orders']
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )
    df['rolling_avg_revenue_7d'] = (
        df.groupby('hour')['total_revenue']
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

    # Fill NaN lags with rolling average
    df['prev_week_orders'] = df['prev_week_orders'].fillna(df['rolling_avg_orders_7d'])
    df['prev_week_revenue'] = df['prev_week_revenue'].fillna(df['rolling_avg_revenue_7d'])

    return df


def build_prediction_row(outlet_id, target_date, hour):
    """
    Build a single feature row for a future date+hour (for prediction time).
    Uses historical data to compute lag & rolling features.
    """
    from apps.predictive_core.models import SalesData

    day_of_week = target_date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    # Get same hour from 7 days ago
    week_ago = target_date - timedelta(days=7)
    prev_week = SalesData.objects.filter(
        outlet_id=outlet_id, date=week_ago, hour=hour
    ).first()

    # Rolling 7-day average for this hour
    start = target_date - timedelta(days=7)
    rolling = SalesData.objects.filter(
        outlet_id=outlet_id, date__gte=start, date__lt=target_date, hour=hour
    ).values_list('total_orders', 'total_revenue')

    avg_orders = np.mean([r[0] for r in rolling]) if rolling else 0
    avg_revenue = np.mean([float(r[1]) for r in rolling]) if rolling else 0

    return {
        'hour': hour,
        'day_of_week': day_of_week,
        'is_holiday': 0,  # can be enhanced with a holiday calendar
        'is_weekend': is_weekend,
        'prev_week_orders': prev_week.total_orders if prev_week else avg_orders,
        'prev_week_revenue': float(prev_week.total_revenue) if prev_week else avg_revenue,
        'rolling_avg_orders_7d': avg_orders,
        'rolling_avg_revenue_7d': avg_revenue,
    }


def get_historical_averages(outlet_id, day_of_week):
    """
    Fallback: simple historical averages grouped by hour for a given day_of_week.
    Works even with minimal data.
    """
    from apps.predictive_core.models import SalesData

    qs = SalesData.objects.filter(
        outlet_id=outlet_id, day_of_week=day_of_week
    ).values('hour').annotate(
        avg_orders=models.Avg('total_orders'),
        avg_revenue=models.Avg('total_revenue'),
    ).order_by('hour')

    return {row['hour']: row for row in qs}


def build_food_demand_features(outlet_id, min_days=7):
    """
    Build feature matrix for food category demand prediction.
    Explodes category_sales JSON into per-category rows.

    Returns:
        dict of {category: pd.DataFrame} or None if insufficient data.
    """
    from apps.predictive_core.models import SalesData

    qs = SalesData.objects.filter(outlet_id=outlet_id).order_by('date', 'hour')
    if qs.count() < min_days * 8:
        return None

    records = list(qs.values(
        'date', 'hour', 'day_of_week', 'is_holiday',
        'total_orders', 'category_sales'
    ))

    # Explode category_sales JSON into per-category rows
    rows = []
    for rec in records:
        cat_sales = rec.get('category_sales') or {}
        if isinstance(cat_sales, dict):
            for category, sales_val in cat_sales.items():
                rows.append({
                    'date': rec['date'],
                    'hour': rec['hour'],
                    'day_of_week': rec['day_of_week'],
                    'is_holiday': rec['is_holiday'],
                    'is_weekend': 1 if rec['day_of_week'] >= 5 else 0,
                    'total_orders': rec['total_orders'],
                    'category': category,
                    'category_sales': float(sales_val) if sales_val else 0.0,
                })

    if not rows:
        return None

    df = pd.DataFrame(rows)

    # Group by category and build per-category DataFrames
    category_dfs = {}
    for cat, group in df.groupby('category'):
        group = group.sort_values(['date', 'hour']).reset_index(drop=True)
        # Rolling avg per category
        group['rolling_avg_cat_7d'] = (
            group['category_sales']
            .rolling(7, min_periods=1).mean()
        )
        category_dfs[cat] = group

    return category_dfs


def build_revenue_features(outlet_id, min_days=7):
    """
    Build feature matrix from DailySummary for revenue forecasting.

    Returns:
        pd.DataFrame or None if insufficient data.
    """
    from apps.insights_hub.models import DailySummary

    qs = DailySummary.objects.filter(outlet_id=outlet_id).order_by('date')
    if qs.count() < min_days:
        return None

    df = pd.DataFrame(list(qs.values(
        'date', 'total_revenue', 'total_orders', 'total_guests',
        'avg_wait_time', 'peak_hour', 'delayed_orders',
        'cancelled_orders', 'staff_count'
    )))

    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.weekday
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['total_revenue'] = df['total_revenue'].astype(float)

    # Lag features
    df = df.sort_values('date').reset_index(drop=True)
    df['prev_day_revenue'] = df['total_revenue'].shift(1)
    df['prev_week_revenue'] = df['total_revenue'].shift(7)
    df['prev_day_orders'] = df['total_orders'].shift(1)

    # Rolling averages
    df['rolling_avg_revenue_7d'] = (
        df['total_revenue'].rolling(7, min_periods=1).mean()
    )
    df['rolling_avg_revenue_30d'] = (
        df['total_revenue'].rolling(30, min_periods=1).mean()
    )

    # Fill NaN lags
    df['prev_day_revenue'] = df['prev_day_revenue'].fillna(df['rolling_avg_revenue_7d'])
    df['prev_week_revenue'] = df['prev_week_revenue'].fillna(df['rolling_avg_revenue_7d'])
    df['prev_day_orders'] = df['prev_day_orders'].fillna(df['total_orders'].rolling(7, min_periods=1).mean())

    return df


def build_footfall_features(outlet_id, min_days=7):
    """
    Build feature matrix for footfall (guest count) prediction.
    Uses SalesData orders as proxy for guest traffic + OrderTicket party_size averages.

    Returns:
        pd.DataFrame or None if insufficient data.
    """
    from apps.predictive_core.models import SalesData
    from apps.order_engine.models import OrderTicket

    qs = SalesData.objects.filter(outlet_id=outlet_id).order_by('date', 'hour')
    if qs.count() < min_days * 8:
        return None

    df = pd.DataFrame(list(qs.values(
        'date', 'hour', 'day_of_week', 'is_holiday',
        'total_orders', 'total_revenue'
    )))

    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['date'] = pd.to_datetime(df['date'])
    df['total_revenue'] = df['total_revenue'].astype(float)

    # Estimate guests from OrderTicket party_size averages
    avg_party = OrderTicket.objects.filter(
        table__outlet_id=outlet_id
    ).aggregate(avg_ps=models.Avg('party_size'))['avg_ps'] or 2.0

    # Estimated guests = total_orders * avg_party_size
    df['estimated_guests'] = (df['total_orders'] * float(avg_party)).astype(int)

    # Lag features
    df = df.sort_values(['date', 'hour']).reset_index(drop=True)
    df['prev_week_guests'] = df.groupby('hour')['estimated_guests'].shift(7)
    df['rolling_avg_guests_7d'] = (
        df.groupby('hour')['estimated_guests']
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )
    df['prev_week_guests'] = df['prev_week_guests'].fillna(df['rolling_avg_guests_7d'])

    return df, float(avg_party)
