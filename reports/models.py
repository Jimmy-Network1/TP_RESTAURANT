from django.db import models


class ReportSnapshot(models.Model):
    PERIOD_DAY = 'day'
    PERIOD_WEEK = 'week'
    PERIOD_MONTH = 'month'
    PERIOD_YEAR = 'year'

    PERIOD_CHOICES = [
        (PERIOD_DAY, 'Jour'),
        (PERIOD_WEEK, 'Semaine'),
        (PERIOD_MONTH, 'Mois'),
        (PERIOD_YEAR, 'Année'),
    ]

    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, default=PERIOD_DAY)
    period_start = models.DateField()
    period_end = models.DateField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rapport {self.get_period_type_display()} {self.period_start} - {self.period_end}"
