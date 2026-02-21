from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomerProfile, AuditLog
from billing.models import CashSession, Payment
from inventory.models import Ingredient, StockMovement, InventoryAlert
from menu.models import Category, Dish
from orders.models import Order, OrderItem
from reservations.models import Reservation


User = get_user_model()


def create_user(username, group=None, is_staff=False):
    user = User.objects.create_user(username=username, password="Test@237")
    user.is_staff = is_staff
    user.save()
    if group:
        g, _ = Group.objects.get_or_create(name=group)
        user.groups.add(g)
    return user


class FullAppTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Plats", is_active=True)

    def test_client_access_restrictions(self):
        client_user = create_user("client_test")
        self.client.login(username="client_test", password="Test@237")
        resp = self.client.get(reverse("orders:list"))
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse("inventory:stock"))
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse("billing:cashdesk"))
        self.assertEqual(resp.status_code, 302)

    def test_cashier_access_and_payment_requires_session(self):
        cashier = create_user("cashier_test", group="caissier")
        order = Order.objects.create(status=Order.STATUS_READY, total_amount=1000)
        self.client.login(username="cashier_test", password="Test@237")
        resp = self.client.post(reverse("billing:payment_new"), {"order_id": order.id, "method": "cash", "amount": "1000"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Payment.objects.count(), 0)

        CashSession.objects.create(opened_by=cashier, opening_amount=0)
        resp = self.client.post(reverse("billing:payment_new"), {"order_id": order.id, "method": "cash", "amount": "500"})
        self.assertEqual(Payment.objects.count(), 0)
        resp = self.client.post(reverse("billing:payment_new"), {"order_id": order.id, "method": "cash", "amount": "1000"})
        self.assertEqual(Payment.objects.count(), 1)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)

    def test_menu_availability_and_cart_block(self):
        dish = Dish.objects.create(
            name="Ndole plantain",
            category=self.category,
            price=1000,
            availability=Dish.AVAILABILITY_IN_STOCK,
            is_active=True,
        )
        Ingredient.objects.create(name="Ndole plantain", quantity_in_stock=0, alert_threshold=1)
        resp = self.client.get(reverse("public:menu"))
        self.assertEqual(resp.status_code, 200)
        dishes = resp.context["dishes"]
        target = [d for d in dishes if d.id == dish.id][0]
        self.assertFalse(target.can_order)

        resp = self.client.post(reverse("public:cart_add", args=[dish.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_checkout_decrements_stock_and_creates_movement(self):
        dish = Dish.objects.create(
            name="Poulet roti",
            category=self.category,
            price=2000,
            availability=Dish.AVAILABILITY_IN_STOCK,
            is_active=True,
        )
        ingredient = Ingredient.objects.create(name="Poulet roti", quantity_in_stock=5, alert_threshold=2)
        session = self.client.session
        session["cart"] = {str(dish.id): 2}
        session.save()

        resp = self.client.post(reverse("public:checkout"), {"order_type": Order.TYPE_DELIVERY})
        self.assertEqual(resp.status_code, 302)
        ingredient.refresh_from_db()
        self.assertEqual(float(ingredient.quantity_in_stock), 3.0)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_stock_movement_creates_alert_and_audit(self):
        manager = create_user("gerant_test", group="gerant")
        self.client.login(username="gerant_test", password="Test@237")
        ing = Ingredient.objects.create(name="Riz", quantity_in_stock=5, alert_threshold=3)
        resp = self.client.post(reverse("inventory:movement_new"), {
            "ingredient": ing.id,
            "movement_type": StockMovement.TYPE_OUT,
            "quantity": "3",
            "note": "Perte",
        })
        self.assertEqual(resp.status_code, 302)
        ing.refresh_from_db()
        self.assertEqual(float(ing.quantity_in_stock), 2.0)
        self.assertEqual(InventoryAlert.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="STOCK_MOVE").count(), 1)

    def test_delivery_assigned_only_and_payment(self):
        courier = create_user("livreur_test", group="livreur")
        other = create_user("livreur_other", group="livreur")
        order = Order.objects.create(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_DONE, assigned_delivery=courier, total_amount=1500)
        self.client.login(username="livreur_other", password="Test@237")
        resp = self.client.get(reverse("delivery:detail", args=[order.id]))
        self.assertEqual(resp.status_code, 302)

        self.client.login(username="livreur_test", password="Test@237")
        CashSession.objects.create(opened_by=courier, opening_amount=0)
        resp = self.client.post(reverse("delivery:detail", args=[order.id]), {"action": "paid"})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(Payment.objects.count(), 1)

    def test_reservation_cancel_creates_audit(self):
        client_user = create_user("client_resa")
        profile = CustomerProfile.objects.create(user=client_user, phone="699000000")
        res = Reservation.objects.create(
            customer_profile=profile,
            customer_name="Client",
            reservation_datetime=timezone.now() + timedelta(hours=2),
            party_size=2,
            status=Reservation.STATUS_PENDING,
        )
        self.client.login(username="client_resa", password="Test@237")
        resp = self.client.post(reverse("reservations:client_detail", args=[res.id]), {"reason": "Changement"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(AuditLog.objects.filter(action="RESERVATION_STATUS").count(), 1)

    def test_role_guard_blocks_staff_without_group(self):
        user = create_user("staff_nogroup", is_staff=True)
        self.client.login(username="staff_nogroup", password="Test@237")
        resp = self.client.get(reverse("orders:list"))
        self.assertEqual(resp.status_code, 302)

    def test_kitchen_transitions(self):
        cook = create_user("cuisinier_test", group="cuisinier")
        order = Order.objects.create(status=Order.STATUS_PENDING)
        self.client.login(username="cuisinier_test", password="Test@237")
        resp = self.client.post(reverse("kitchen:action", args=[order.id]), {"action": "start"})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PREPARING)
        resp = self.client.post(reverse("kitchen:action", args=[order.id]), {"action": "ready"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_READY)

    def test_server_tables_access(self):
        server = create_user("serveur_test", group="serveur")
        self.client.login(username="serveur_test", password="Test@237")
        resp = self.client.get(reverse("tables:plan"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("tables:list"))
        self.assertEqual(resp.status_code, 302)

    def test_delivery_flow_start_and_finish(self):
        courier = create_user("livreur_flow", group="livreur")
        order = Order.objects.create(order_type=Order.TYPE_DELIVERY, status=Order.STATUS_READY, assigned_delivery=courier)
        self.client.login(username="livreur_flow", password="Test@237")
        resp = self.client.post(reverse("delivery:detail", args=[order.id]), {"action": "start"})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_ON_ROUTE)
        resp = self.client.post(reverse("delivery:detail", args=[order.id]), {"action": "delivered"})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_DONE)

    def test_cashdesk_open_close_and_payments_log(self):
        cashier = create_user("cashier3", group="caissier")
        self.client.login(username="cashier3", password="Test@237")
        resp = self.client.post(reverse("billing:cashdesk"), {"action": "open", "opening_amount": "5000"})
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.create(status=Order.STATUS_SERVED, total_amount=2000)
        resp = self.client.post(reverse("billing:payment_new"), {"order_id": order.id, "method": "cash", "amount": "2000"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Payment.objects.count(), 1)
        resp = self.client.post(reverse("billing:cashdesk"), {"action": "close", "closing_amount": "7000"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(AuditLog.objects.filter(action="CASH_OPEN").exists())
        self.assertTrue(AuditLog.objects.filter(action="CASH_CLOSE").exists())

    def test_reservation_staff_update_and_checkin(self):
        manager = create_user("gerant_resa", group="gerant")
        profile_user = create_user("client_r", group=None)
        profile = CustomerProfile.objects.create(user=profile_user, phone="699000000")
        from tablesapp.models import Table
        table = Table.objects.create(name="T1", capacity=4, status="free", zone="Salle", active=True)
        res = Reservation.objects.create(
            customer_profile=profile,
            customer_name="Client",
            reservation_datetime=timezone.now() + timedelta(hours=3),
            party_size=2,
            status=Reservation.STATUS_PENDING,
        )
        self.client.login(username="gerant_resa", password="Test@237")
        resp = self.client.post(reverse("reservations:staff_detail", args=[res.id]), {
            "status": Reservation.STATUS_CONFIRMED,
            "table": table.id,
        })
        self.assertEqual(resp.status_code, 302)
        res.refresh_from_db()
        self.assertEqual(res.status, Reservation.STATUS_CONFIRMED)
        resp = self.client.get(reverse("reservations:staff_checkin", args=[res.id]))
        self.assertEqual(resp.status_code, 302)
        res.refresh_from_db()
        self.assertEqual(res.status, Reservation.STATUS_COMPLETED)
        self.assertTrue(AuditLog.objects.filter(action="RESERVATION_STATUS").exists())

    def test_order_cancel_creates_audit_log(self):
        manager = create_user("gerant_cancel", group="gerant")
        order = Order.objects.create(status=Order.STATUS_PENDING)
        self.client.login(username="gerant_cancel", password="Test@237")
        resp = self.client.post(reverse("orders:cancel", args=[order.id]), {"reason": "Client absent"})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        self.assertTrue(AuditLog.objects.filter(action="ORDER_STATUS").exists())

    def test_kds_ready_creates_notification(self):
        cook = create_user("cook_notif", group="cuisinier")
        order = Order.objects.create(
            status=Order.STATUS_PREPARING,
            order_type=Order.TYPE_DELIVERY,
        )
        self.client.login(username="cook_notif", password="Test@237")
        resp = self.client.post(reverse("kitchen:action", args=[order.id]), {"action": "ready"})
        self.assertEqual(resp.status_code, 302)
        from orders.models import OrderNotification
        self.assertEqual(OrderNotification.objects.count(), 1)
