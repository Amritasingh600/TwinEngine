import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'twinengine_core.settings'
django.setup()

from apps.hospitality_group.models import Brand, Outlet
from apps.order_engine.models import OrderTicket, PaymentLog
from apps.layout_twin.models import ServiceNode
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule
from apps.insights_hub.models import DailySummary
from datetime import date

print("=== Brands ===")
for b in Brand.objects.all():
    print(f"  ID={b.id} name={b.name}")

print("\n=== Outlets ===")
for o in Outlet.objects.all():
    print(f"  ID={o.id} name={o.name} brand={o.brand.name}")

print("\n=== ServiceNodes ===")
for o in Outlet.objects.all():
    cnt = ServiceNode.objects.filter(outlet=o).count()
    print(f"  Outlet {o.id}: {cnt} nodes")

print("\n=== Orders ===")
total = OrderTicket.objects.count()
print(f"  Total: {total}")
for o in Outlet.objects.all():
    qs = OrderTicket.objects.filter(table__outlet=o)
    cnt = qs.count()
    if cnt > 0:
        mn = qs.order_by('placed_at').first().placed_at
        mx = qs.order_by('-placed_at').first().placed_at
        today_cnt = qs.filter(placed_at__date=date.today()).count()
        print(f"  Outlet {o.id}: {cnt} orders, dates {mn} to {mx}, today={today_cnt}")
    else:
        print(f"  Outlet {o.id}: 0 orders")

print("\n=== Payments ===")
print(f"  Total: {PaymentLog.objects.count()}")

print("\n=== SalesData ===")
sd = SalesData.objects.all()
print(f"  Total: {sd.count()}")
if sd.exists():
    print(f"  Date range: {sd.order_by('date').first().date} to {sd.order_by('-date').first().date}")

print("\n=== Inventory ===")
print(f"  Total: {InventoryItem.objects.count()}")

print("\n=== Schedules ===")
print(f"  Total: {StaffSchedule.objects.count()}")

print("\n=== DailySummary ===")
print(f"  Total: {DailySummary.objects.count()}")
