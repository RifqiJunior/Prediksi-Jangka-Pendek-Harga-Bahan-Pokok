# models.py
from django.db import models

class Result(models.Model):
    komoditas = models.CharField(max_length=100)
    wema_average = models.FloatField()
    mape = models.FloatField()
    mape_percentage = models.FloatField()
    actual_values = models.TextField()
    forecast_values = models.FloatField(default=0.0)
    absolute_errors = models.FloatField(default=0.0)
    percentage_errors = models.TextField(default="[]")

    def __str__(self):
        return self.komoditas

class Meta:
    app_label = 'apps'
