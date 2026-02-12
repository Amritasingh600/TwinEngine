from django.db import models
from apps.factory_graph.models import MachineNode


class SensorData(models.Model):
    """
    Stores telemetry from Flask Mock App or real IoT devices.
    """
    machine_node = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='sensor_data')
    temperature = models.FloatField(help_text="Temperature reading in Celsius")
    vibration = models.FloatField(help_text="Vibration level (arbitrary units or Hz)")
    torque = models.FloatField(help_text="Torque reading in Nm")
    rpm = models.FloatField(help_text="Rotations per minute")
    tool_wear = models.FloatField(help_text="Tool wear indicator (0-1 scale or minutes)")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Sensor Data'
        verbose_name_plural = 'Sensor Data'
        indexes = [
            models.Index(fields=['machine_node', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.machine_node.name} - Temp: {self.temperature}°C @ {self.timestamp.strftime('%H:%M:%S')}"


class AnomalyAlert(models.Model):
    """
    Log of anomaly detections (Good/Bad) from the ML model.
    """
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    sensor_data = models.ForeignKey(SensorData, on_delete=models.CASCADE, related_name='anomaly_alerts')
    ai_prediction = models.CharField(max_length=50, help_text="ML model prediction (e.g., 'ANOMALY', 'NORMAL')")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    resolved_status = models.BooleanField(default=False, help_text="Whether this alert has been resolved")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Engineer notes or resolution details")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Anomaly Alert'
        verbose_name_plural = 'Anomaly Alerts'
        indexes = [
            models.Index(fields=['sensor_data', '-created_at']),
            models.Index(fields=['resolved_status']),
        ]
    
    def __str__(self):
        status = "✓ Resolved" if self.resolved_status else "⚠ Active"
        return f"{self.sensor_data.machine_node.name} - {self.ai_prediction} ({self.severity}) {status}"
