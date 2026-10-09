from django.db import models

class Sensor(models.Model):
    SOURCE_CHOICES = [
        ('SIMULATION', 'Simulation'),
        ('PUBLIC_DATASET', 'Public Dataset'),
        ('REAL_SENSOR', 'Real Sensor'),
    ]
    sensor_id = models.CharField(max_length=64, unique=True)
    location = models.CharField(max_length=120, default='Cold room')
    product_type = models.CharField(max_length=40, default='Food')
    active = models.BooleanField(default=True)
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='SIMULATION')

    def __str__(self):
        return f"{self.sensor_id} ({self.source_type})"

class SensorReading(models.Model):
    SOURCE_CHOICES = [
        ('SIMULATION', 'Simulation'),
        ('PUBLIC_DATASET', 'Public Dataset'),
        ('REAL_SENSOR', 'Real Sensor'),
    ]
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(db_index=True)
    temperature = models.FloatField()
    humidity = models.FloatField(null=True)
    ambient_temperature = models.FloatField(null=True)
    power_kw = models.FloatField(null=True)
    compressor_state = models.BooleanField(default=False)
    door_open = models.BooleanField(default=False)
    data_source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='SIMULATION')

    class Meta:
        ordering = ['timestamp']
        constraints = [
            models.UniqueConstraint(fields=['sensor', 'timestamp'], name='sensor_time')
        ]

    def __str__(self):
        return f"{self.sensor.sensor_id} @ {self.timestamp}: {self.temperature}°C [{self.data_source}]"
