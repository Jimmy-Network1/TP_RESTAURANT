from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("payments/", views.PaymentsView.as_view(), name="payments"),
    path("payments/new/", views.PaymentCreateView.as_view(), name="payment_new"),
    path("invoices/", views.InvoicesView.as_view(), name="invoices"),
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("cashdesk/", views.CashDeskView.as_view(), name="cashdesk"),
]
