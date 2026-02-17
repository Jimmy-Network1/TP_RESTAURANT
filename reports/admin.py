from django.contrib import admin

from .models import ReportSnapshot


@admin.register(ReportSnapshot)
class ReportSnapshotAdmin(admin.ModelAdmin):
    list_display = ('period_type', 'period_start', 'period_end', 'created_at')
    list_filter = ('period_type',)
