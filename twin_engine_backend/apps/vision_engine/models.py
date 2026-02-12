from django.db import models
from apps.factory_graph.models import MachineNode


class VisionLog(models.Model):
    """
    Records every item detected and counted by the AI.
    """
    machine_node = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='vision_logs')
    object_type = models.CharField(max_length=100, help_text="Type of object detected (e.g., apple, bottle)")
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(help_text="AI confidence score (0.0 - 1.0)")
    current_total = models.IntegerField(default=0, help_text="Cumulative count at this timestamp")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Vision Log'
        verbose_name_plural = 'Vision Logs'
        indexes = [
            models.Index(fields=['machine_node', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.machine_node.name} - {self.object_type} @ {self.timestamp.strftime('%H:%M:%S')}"


class DetectionZone(models.Model):
    """
    Stores the line coordinates for counting logic per machine.
    """
    machine_node = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='detection_zones')
    line_y_coordinate = models.FloatField(help_text="Y-coordinate of the detection line in the video frame")
    active_status = models.BooleanField(default=True, help_text="Whether this zone is currently active")
    loop_count = models.IntegerField(default=0, help_text="Number of objects that crossed the line")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['machine_node', 'line_y_coordinate']
        verbose_name = 'Detection Zone'
        verbose_name_plural = 'Detection Zones'
    
    def __str__(self):
        return f"{self.machine_node.name} - Line Y={self.line_y_coordinate} (Count: {self.loop_count})"
