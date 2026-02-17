from django.shortcuts import render

from .models import ReportSnapshot


def dashboard(request):
    snapshots = ReportSnapshot.objects.all().order_by('-created_at')[:10]
    return render(request, 'reports/dashboard.html', {'snapshots': snapshots})
