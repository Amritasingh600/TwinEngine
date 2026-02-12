from django.db import models
from apps.manufacturers.models import Manufacturer


class MachineType(models.Model):
    """
    Defines the generic machine template and its 3D assets.
    """
    name = models.CharField(max_length=100, help_text="Machine type name (e.g., Roller, Grinder)")
    model_3d_embed_code = models.TextField(help_text="Sketchfab or other 3D model embed code")
    description = models.TextField(blank=True, null=True, help_text="Machine description and capabilities")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Machine Type'
        verbose_name_plural = 'Machine Types'
    
    def __str__(self):
        return self.name


class MachineNode(models.Model):
    """
    The specific instance of a machine in a 3D coordinate space.
    """
    STATUS_CHOICES = [
        ('NORMAL', 'Normal'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('OFFLINE', 'Offline'),
    ]
    
    name = models.CharField(max_length=150, help_text="Unique machine instance name")
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='machines')
    machine_type = models.ForeignKey(MachineType, on_delete=models.PROTECT, related_name='instances')
    
    # 3D Position
    pos_x = models.FloatField(default=0.0, help_text="X coordinate in 3D space")
    pos_y = models.FloatField(default=0.0, help_text="Y coordinate in 3D space")
    pos_z = models.FloatField(default=0.0, help_text="Z coordinate in 3D space")
    
    # AI & Video
    video_feed_url = models.URLField(blank=True, null=True, help_text="Cloudinary video URL or RTSP stream")
    hf_endpoint = models.URLField(blank=True, null=True, help_text="Hugging Face inference endpoint")
    hf_key = models.CharField(max_length=255, blank=True, null=True, help_text="Hugging Face API key")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['manufacturer', 'name']
        verbose_name = 'Machine Node'
        verbose_name_plural = 'Machine Nodes'
        unique_together = ['manufacturer', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.machine_type.name}) - {self.status}"


class MachineEdge(models.Model):
    """
    Explicitly defines the directional material flow between nodes.
    """
    FLOW_TYPE_CHOICES = [
        ('MATERIAL', 'Material Flow'),
        ('DATA', 'Data Flow'),
        ('CONTROL', 'Control Signal'),
    ]
    
    source_node = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target_node = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='incoming_edges')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES, default='MATERIAL')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['source_node', 'target_node']
        verbose_name = 'Machine Edge'
        verbose_name_plural = 'Machine Edges'
        unique_together = ['source_node', 'target_node', 'flow_type']
    
    def __str__(self):
        return f"{self.source_node.name} → {self.target_node.name} ({self.flow_type})"
