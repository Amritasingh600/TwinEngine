import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twinengine_core.settings')

import django
django.setup()

from datetime import date
from apps.insights_hub.data_generator import generate_outlet_data
from apps.order_engine.models import OrderTicket
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule
from apps.insights_hub.models import DailySummary

results = generate_outlet_data(4, date(2026, 3, 6), order_count=5, days=3)
print('=== RESULTS ===')
for k, v in results.items():
    print(f'  {k}: {v}')

o = 4
print('\n=== DB COUNTS (outlet 4) ===')
print(f'  OrderTickets: {OrderTicket.objects.filter(table__outlet_id=o).count()}')
print(f'  SalesData rows: {SalesData.objects.filter(outlet_id=o).count()}')
dates = list(SalesData.objects.filter(outlet_id=o).values_list("date", flat=True).distinct())
print(f'  SalesData dates: {dates}')
print(f'  DailySummary: {DailySummary.objects.filter(outlet_id=o).count()}')
ds_dates = list(DailySummary.objects.filter(outlet_id=o).values_list("date", flat=True).distinct())
print(f'  DailySummary dates: {ds_dates}')
print(f'  InventoryItems: {InventoryItem.objects.filter(outlet_id=o).count()}')
print(f'  StaffSchedules: {StaffSchedule.objects.filter(staff__outlet_id=o).count()}')

print('\n=== INVENTORY LEVELS ===')
for item in InventoryItem.objects.filter(outlet_id=o).order_by('name')[:6]:
    print(f'  {item.name}: {item.current_quantity:.1f} {item.unit} (low={item.is_low_stock})')
