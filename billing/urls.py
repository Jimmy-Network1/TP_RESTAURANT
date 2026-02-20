from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("payments/", views.PaymentsView.as_view(), name="payments"),
    path("payments/new/", views.PaymentCreateView.as_view(), name="payment_new"),
    path("invoices/", views.SimplePage.as_view(template_name="billing/invoices.html"), name="invoices"),
    path("invoices/<int:pk>/", views.SimplePage.as_view(template_name="billing/invoice_detail.html"), name="invoice_detail"),
    path("cashdesk/", views.CashDeskView.as_view(), name="cashdesk"),
]
