from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from orders.models import Order
from billing.models import Payment


User = get_user_model()


def create_user(username, group_name=None, is_staff=False):
    user = User.objects.create_user(username=username, password="Test@237")
    user.is_staff = is_staff
    user.save()
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


class AccessControlTests(TestCase):
    def test_client_cannot_access_orders_backoffice(self):
        client_user = create_user("client_test")
        self.client.login(username="client_test", password="Test@237")
        resp = self.client.get(reverse("orders:list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("public:home"), resp["Location"])

    def test_cashier_can_access_cashdesk_but_not_inventory(self):
        cashier = create_user("cashier_test", group_name="caissier")
        self.client.login(username="cashier_test", password="Test@237")
        resp_cash = self.client.get(reverse("billing:cashdesk"))
        self.assertEqual(resp_cash.status_code, 200)
        resp_inv = self.client.get(reverse("inventory:stock"))
        self.assertEqual(resp_inv.status_code, 302)

    def test_manager_can_access_menu_backoffice(self):
        manager = create_user("gerant_test", group_name="gerant")
        self.client.login(username="gerant_test", password="Test@237")
        resp = self.client.get(reverse("menu:list"))
        self.assertEqual(resp.status_code, 200)

    def test_payment_requires_open_cash_session(self):
        cashier = create_user("cashier2", group_name="caissier")
        order = Order.objects.create(status=Order.STATUS_READY, total_amount=1000)
        self.client.login(username="cashier2", password="Test@237")
        resp = self.client.post(
            reverse("billing:payment_new"),
            {"order_id": order.id, "method": "cash", "amount": "1000"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Payment.objects.count(), 0)

    def test_delivery_detail_restricted_to_assigned_courier(self):
        courier1 = create_user("livreur1", group_name="livreur")
        courier2 = create_user("livreur2", group_name="livreur")
        order = Order.objects.create(
            order_type=Order.TYPE_DELIVERY,
            status=Order.STATUS_ON_ROUTE,
            assigned_delivery=courier1,
        )
        self.client.login(username="livreur2", password="Test@237")
        resp = self.client.get(reverse("delivery:detail", args=[order.id]))
        self.assertEqual(resp.status_code, 302)
