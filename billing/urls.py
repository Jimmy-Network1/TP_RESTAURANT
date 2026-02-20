from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("payments/", views.SimplePage.as_view(template_name="billing/payments.html"), name="payments"),
    path("payments/new/", views.SimplePage.as_view(template_name="billing/payment_form.html"), name="payment_new"),
    path("invoices/", views.SimplePage.as_view(template_name="billing/invoices.html"), name="invoices"),
    path("invoices/<int:pk>/", views.SimplePage.as_view(template_name="billing/invoice_detail.html"), name="invoice_detail"),
    path("cashdesk/", views.SimplePage.as_view(template_name="billing/cashdesk.html"), name="cashdesk"),
]
