from django.db import models
from apps.hospitality_group.models import Outlet


class ServiceNode(models.Model):
    """
    Represents tables, kitchen stations, or washing areas in 3D space.
    The core visual element of the Digital Twin - drives color-coded status.
    
    Replaces: MachineType + MachineNode (from manufacturing version)
    """
    NODE_TYPE_CHOICES = [
        ('TABLE', 'Table'),
        ('KITCHEN', 'Kitchen Station'),
        ('WASH', 'Washing Station'),
        ('BAR', 'Bar Counter'),
        ('ENTRY', 'Entry/Reception'),
    ]
    
    # Color-coded status system for 3D visualization
    STATUS_CHOICES = [
        ('BLUE', 'Empty / Ready'),           # 🔵 Available
        ('RED', 'Occupied - Waiting'),       # 🔴 Food not served yet
        ('GREEN', 'Occupied - Served'),      # 🟢 Food served, eating
        ('YELLOW', 'Issue / Delay'),         # 🟡 Problem (wait > 15min, wrong order)
        ('GREY', 'Maintenance / Reserved'),  # ⚪ Not available
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='service_nodes')
    name = models.CharField(max_length=100, help_text="Node identifier (e.g., Table-1, Kitchen-Main)")
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='TABLE')
    
    # 3D Position for Three.js rendering
    pos_x = models.FloatField(default=0.0, help_text="X coordinate in 3D space")
    pos_y = models.FloatField(default=0.0, help_text="Y coordinate in 3D space")
    pos_z = models.FloatField(default=0.0, help_text="Z coordinate in 3D space")
    
    # Table-specific attributes
    capacity = models.IntegerField(default=4, help_text="Seating capacity (for tables)")
    
    # Status - THE KEY DRIVER for 3D node colors
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BLUE')
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['outlet', 'name']
        verbose_name = 'Service Node'
        verbose_name_plural = 'Service Nodes'
        unique_together = ['outlet', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.node_type}) - {self.get_current_status_display()}"


class ServiceFlow(models.Model):
    """
    Directional paths between nodes for operational flow visualization.
    E.g., Kitchen → Table (Food Delivery), Table → Wash (Dirty Dishes)
    
    Replaces: MachineEdge (from manufacturing version)
    """
    FLOW_TYPE_CHOICES = [
        ('FOOD_DELIVERY', 'Food Delivery'),      # Kitchen → Table
        ('DISH_RETURN', 'Dish Return'),          # Table → Washing
        ('ORDER_PATH', 'Order Path'),            # Table → Kitchen (order transmitted)
        ('CUSTOMER_FLOW', 'Customer Flow'),      # Entry → Table → Exit
    ]
    
    source_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='outgoing_flows')
    target_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='incoming_flows')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES, default='FOOD_DELIVERY')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['source_node', 'target_node']
        verbose_name = 'Service Flow'
        verbose_name_plural = 'Service Flows'
        unique_together = ['source_node', 'target_node', 'flow_type']
    
    def __str__(self):
        return f"{self.source_node.name} → {self.target_node.name} ({self.flow_type})"
