from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomerProfile, ProducerProfile, User
from catalog.models import Category, Product
from orders.models import Order, OrderItem, ProducerOrder
from payments.models import PaymentTransaction, WeeklySettlement


class ProducerSettlementPageTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Vegetables", slug="vegetables")
        self.producer = User.objects.create_user(
            username="settlementproducer",
            email="settlementproducer@example.com",
            password="StrongPass123!",
            role=User.Role.PRODUCER,
        )
        ProducerProfile.objects.create(
            user=self.producer,
            business_name="Settlement Farm",
            postcode="BS1 4DJ",
        )
        self.other_producer = User.objects.create_user(
            username="otherproducer",
            email="otherproducer@example.com",
            password="StrongPass123!",
            role=User.Role.PRODUCER,
        )
        ProducerProfile.objects.create(
            user=self.other_producer,
            business_name="Other Farm",
            postcode="BS5 1AA",
        )
        self.customer = User.objects.create_user(
            username="settlementcustomer",
            email="settlementcustomer@example.com",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        CustomerProfile.objects.create(user=self.customer, postcode="BS3 2AA")

        self.potatoes = Product.objects.create(
            producer=self.producer,
            category=self.category,
            slug="bulk-potatoes",
            name="Bulk Potatoes",
            price=Decimal("10.00"),
            stock=Decimal("100"),
        )
        self.carrots = Product.objects.create(
            producer=self.producer,
            category=self.category,
            slug="bulk-carrots",
            name="Bulk Carrots",
            price=Decimal("5.00"),
            stock=Decimal("80"),
        )
        self.other_product = Product.objects.create(
            producer=self.other_producer,
            category=self.category,
            slug="other-product",
            name="Other Product",
            price=Decimal("7.00"),
            stock=Decimal("50"),
        )

        self.qualifying_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            delivery_date=date(2026, 5, 6),
        )
        OrderItem.objects.create(
            order=self.qualifying_order,
            product=self.potatoes,
            quantity=2,
            unit_price=Decimal("10.00"),
        )
        OrderItem.objects.create(
            order=self.qualifying_order,
            product=self.carrots,
            quantity=1,
            unit_price=Decimal("5.00"),
        )
        self.qualifying_order.recalculate_totals()
        self.qualifying_order.save()

        self.qualifying_producer_order = ProducerOrder.objects.create(
            parent_order=self.qualifying_order,
            producer=self.producer,
            status=ProducerOrder.Status.COMPLETED,
            subtotal=Decimal("25.00"),
        )
        self.qualifying_producer_order.created_at = timezone.now()
        self.qualifying_producer_order.save(update_fields=["created_at"])

        self.pending_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            delivery_date=date(2026, 5, 8),
        )
        OrderItem.objects.create(
            order=self.pending_order,
            product=self.potatoes,
            quantity=3,
            unit_price=Decimal("10.00"),
        )
        self.pending_order.recalculate_totals()
        self.pending_order.save()
        ProducerOrder.objects.create(
            parent_order=self.pending_order,
            producer=self.producer,
            status=ProducerOrder.Status.PENDING,
            subtotal=Decimal("30.00"),
        )

        self.accepted_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            delivery_date=date(2026, 5, 9),
        )
        OrderItem.objects.create(
            order=self.accepted_order,
            product=self.potatoes,
            quantity=1,
            unit_price=Decimal("10.00"),
        )
        self.accepted_order.recalculate_totals()
        self.accepted_order.save()
        ProducerOrder.objects.create(
            parent_order=self.accepted_order,
            producer=self.producer,
            status=ProducerOrder.Status.ACCEPTED,
            subtotal=Decimal("10.00"),
        )

        self.other_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            delivery_date=date(2026, 5, 7),
        )
        OrderItem.objects.create(
            order=self.other_order,
            product=self.other_product,
            quantity=2,
            unit_price=Decimal("7.00"),
        )
        self.other_order.recalculate_totals()
        self.other_order.save()
        ProducerOrder.objects.create(
            parent_order=self.other_order,
            producer=self.other_producer,
            status=ProducerOrder.Status.COMPLETED,
            subtotal=Decimal("14.00"),
        )

        period_start = date(2026, 5, 5) - timedelta(days=date(2026, 5, 5).weekday())
        period_end = period_start + timedelta(days=6)
        WeeklySettlement.objects.create(
            producer=self.producer,
            period_start=period_start,
            period_end=period_end,
            gross_sales=Decimal("25.00"),
            commission_total=Decimal("1.25"),
            payout_total=Decimal("23.75"),
            status=WeeklySettlement.Status.PAID,
        )

    def test_producer_can_access_own_settlement_page(self):
        self.client.force_login(self.producer)
        response = self.client.get(reverse("producer_settlements"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Payment Settlements")
        self.assertContains(response, "Settlement Farm")
        self.assertContains(response, "Bulk Potatoes")
        self.assertContains(response, "Bulk Carrots")

    def test_customer_cannot_access_producer_settlement_page(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("producer_settlements"))

        self.assertRedirects(
            response,
            reverse("after_login"),
            fetch_redirect_response=False,
        )

    def test_producer_settlements_only_include_own_qualifying_orders(self):
        self.client.force_login(self.producer)
        response = self.client.get(reverse("producer_settlements"))

        self.assertContains(response, "#{}".format(self.qualifying_order.id))
        self.assertNotContains(response, "#{}".format(self.pending_order.id))
        self.assertNotContains(response, "#{}".format(self.accepted_order.id))
        self.assertNotContains(response, "Other Product")

    def test_producer_settlement_calculates_commission_and_payout_correctly(self):
        self.client.force_login(self.producer)
        response = self.client.get(reverse("producer_settlements"))

        self.assertContains(response, "25.00")
        self.assertContains(response, "1.25")
        self.assertContains(response, "23.75")

    def test_producer_settlement_csv_download_works(self):
        self.client.force_login(self.producer)
        response = self.client.get(f"{reverse('producer_settlements')}?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("producer-settlement-report.csv", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("Settlement Period,Order Number,Customer,Products,Order Date,Gross Amount,Commission (5%),Producer Payout (95%),Payment Status", content)
        self.assertIn("25.00,1.25,23.75,Processed", content)

    def test_producer_dashboard_shows_settlement_preview_from_real_orders(self):
        self.client.force_login(self.producer)
        response = self.client.get(reverse("producer_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Payment Settlement")
        self.assertContains(response, "25.00")
        self.assertContains(response, "1.25")
        self.assertContains(response, "23.75")
        self.assertContains(response, "Processed")


class AdminFinanceReportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="adminfinance",
            email="adminfinance@example.com",
            password="StrongPass123!",
        )
        self.producer = User.objects.create_user(
            username="financeproducer",
            email="financeproducer@example.com",
            password="StrongPass123!",
            role=User.Role.PRODUCER,
        )
        ProducerProfile.objects.create(
            user=self.producer,
            business_name="Finance Farm",
            postcode="BS1 2AB",
        )
        self.other_producer = User.objects.create_user(
            username="financeproducer2",
            email="financeproducer2@example.com",
            password="StrongPass123!",
            role=User.Role.PRODUCER,
        )
        ProducerProfile.objects.create(
            user=self.other_producer,
            business_name="Market Garden Co",
            postcode="BS3 3CC",
        )
        self.customer = User.objects.create_user(
            username="financecustomer",
            email="financecustomer@example.com",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        self.category = Category.objects.create(name="Finance Vegetables", slug="finance-vegetables")
        self.potatoes = Product.objects.create(
            producer=self.producer,
            category=self.category,
            slug="finance-potatoes",
            name="Finance Potatoes",
            price=Decimal("10.00"),
            stock=Decimal("100"),
        )
        self.carrots = Product.objects.create(
            producer=self.other_producer,
            category=self.category,
            slug="finance-carrots",
            name="Finance Carrots",
            price=Decimal("10.00"),
            stock=Decimal("100"),
        )

        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.COMPLETED,
            subtotal=Decimal("150.00"),
            commission_total=Decimal("7.50"),
            total=Decimal("157.50"),
            delivery_date=date(2026, 4, 28),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.potatoes,
            quantity=8,
            unit_price=Decimal("10.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.carrots,
            quantity=7,
            unit_price=Decimal("10.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.order,
            producer=self.producer,
            status=ProducerOrder.Status.COMPLETED,
            subtotal=Decimal("80.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.order,
            producer=self.other_producer,
            status=ProducerOrder.Status.DISPATCHED,
            subtotal=Decimal("70.00"),
        )
        PaymentTransaction.objects.create(
            order=self.order,
            status=PaymentTransaction.Status.SUCCEEDED,
            provider="manual",
            amount=Decimal("157.50"),
            currency="GBP",
            provider_reference="demo-finance-001",
        )
        self.second_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.COMPLETED,
            subtotal=Decimal("100.00"),
            commission_total=Decimal("5.00"),
            total=Decimal("105.00"),
            delivery_date=date(2026, 5, 3),
        )
        OrderItem.objects.create(
            order=self.second_order,
            product=self.potatoes,
            quantity=10,
            unit_price=Decimal("10.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.second_order,
            producer=self.producer,
            status=ProducerOrder.Status.COMPLETED,
            subtotal=Decimal("100.00"),
        )
        PaymentTransaction.objects.create(
            order=self.second_order,
            status=PaymentTransaction.Status.SUCCEEDED,
            provider="manual",
            amount=Decimal("105.00"),
            currency="GBP",
            provider_reference="demo-finance-002",
        )
        self.non_qualifying_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            subtotal=Decimal("30.00"),
            commission_total=Decimal("1.50"),
            total=Decimal("31.50"),
            delivery_date=date(2026, 5, 4),
        )
        OrderItem.objects.create(
            order=self.non_qualifying_order,
            product=self.potatoes,
            quantity=3,
            unit_price=Decimal("10.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.non_qualifying_order,
            producer=self.producer,
            status=ProducerOrder.Status.ACCEPTED,
            subtotal=Decimal("30.00"),
        )
        self.mixed_status_order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PAID,
            subtotal=Decimal("90.00"),
            commission_total=Decimal("4.50"),
            total=Decimal("94.50"),
            delivery_date=date(2026, 5, 5),
        )
        OrderItem.objects.create(
            order=self.mixed_status_order,
            product=self.potatoes,
            quantity=4,
            unit_price=Decimal("10.00"),
        )
        OrderItem.objects.create(
            order=self.mixed_status_order,
            product=self.carrots,
            quantity=5,
            unit_price=Decimal("10.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.mixed_status_order,
            producer=self.producer,
            status=ProducerOrder.Status.COMPLETED,
            subtotal=Decimal("40.00"),
        )
        ProducerOrder.objects.create(
            parent_order=self.mixed_status_order,
            producer=self.other_producer,
            status=ProducerOrder.Status.ACCEPTED,
            subtotal=Decimal("50.00"),
        )
        PaymentTransaction.objects.create(
            order=self.mixed_status_order,
            status=PaymentTransaction.Status.SUCCEEDED,
            provider="manual",
            amount=Decimal("94.50"),
            currency="GBP",
            provider_reference="demo-finance-003",
        )

    def test_admin_can_view_finance_report(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_finance_report"),
            {"from": "2026-04-21", "to": "2026-05-05"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Network Commission Report")
        self.assertContains(response, "250.00")
        self.assertContains(response, "12.50")
        self.assertContains(response, "237.50")
        self.assertContains(response, "2")
        self.assertContains(response, "demo-finance-001")
        self.assertContains(response, "Finance Farm")
        self.assertContains(response, "Market Garden Co")

    def test_non_admin_cannot_view_finance_report(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("admin_finance_report"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_download_finance_report_csv(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            f"{reverse('admin_finance_report')}?from=2026-04-21&to=2026-05-05&format=csv"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("brfn-commission-report.csv", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("Order Number,Order Date,Customer,Order Gross,Commission (5%),Total Producer Payout (95%),Order Status,Payment Status,Payment Reference,Producer,Producer Gross,Producer Payout,Producer Order Status,Items", content)
        self.assertIn("150.00,7.50,142.50", content)
        self.assertIn("Finance Farm,80.00,76.00,Completed", content)
        self.assertIn("Market Garden Co,70.00,66.50,Dispatched", content)
        self.assertIn("demo-finance-001", content)

    def test_admin_report_can_filter_by_producer_and_order_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_finance_report"),
            {
                "from": "2026-04-21",
                "to": "2026-05-05",
                "producer": "Market Garden Co",
                "order_status": Order.Status.COMPLETED,
            },
        )

        self.assertContains(response, "#{}".format(self.order.id))
        self.assertNotContains(response, "#{}".format(self.second_order.id))
        self.assertNotContains(response, "#{}".format(self.non_qualifying_order.id))

    def test_admin_report_lists_all_producers_and_shows_empty_state_for_non_qualifying_filter(self):
        self.client.force_login(self.admin)
        third_producer = User.objects.create_user(
            username="financeproducer3",
            email="financeproducer3@example.com",
            password="StrongPass123!",
            role=User.Role.PRODUCER,
        )
        ProducerProfile.objects.create(
            user=third_producer,
            business_name="Pending Produce",
            postcode="BS9 1ZZ",
        )

        response = self.client.get(
            reverse("admin_finance_report"),
            {
                "from": "2026-04-21",
                "to": "2026-05-05",
                "producer": "Pending Produce",
            },
        )

        self.assertContains(response, "Finance Farm")
        self.assertContains(response, "Market Garden Co")
        self.assertContains(response, "Pending Produce")
        self.assertContains(response, "No reportable orders for Pending Produce in this date range.")

    def test_admin_report_shows_selected_order_breakdown(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_finance_report"),
            {
                "from": "2026-04-21",
                "to": "2026-05-05",
                "order_id": self.order.id,
            },
        )

        self.assertContains(response, "Order #{}".format(self.order.id))
        self.assertContains(response, "£7.50")
        self.assertContains(response, "£76.00")
        self.assertContains(response, "£66.50")

    def test_admin_report_filter_includes_selected_producer_even_if_other_supplier_not_finalised(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_finance_report"),
            {
                "from": "2026-04-21",
                "to": "2026-05-05",
                "producer": "Finance Farm",
            },
        )

        self.assertContains(response, "#{}".format(self.mixed_status_order.id))
        self.assertContains(response, "demo-finance-003")
