from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory

User = get_user_model()


class FinanceAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", password="Parol12345!")
        self.other = User.objects.create_user("vali", password="Parol12345!")
        self.admin = User.objects.create_user("boss", password="Parol12345!", is_staff=True)

        self.account = Account.objects.create(
            user=self.user, name="Naqd pul", initial_balance=Decimal("100000")
        )
        self.exp_cat = ExpenseCategory.objects.create(
            name_uz="Tushlik", name_ru="Обед", name_en="Lunch"
        )
        self.inc_cat = IncomeCategory.objects.create(name_uz="Oylik")
        self.client.force_authenticate(self.user)

    def test_login_returns_tokens(self):
        self.client.force_authenticate(None)
        res = self.client.post(reverse("login"), {"username": "ali", "password": "Parol12345!"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertEqual(res.data["user"]["role"], "user")

    def test_balance_is_calculated(self):
        Income.objects.create(user=self.user, account=self.account, category=self.inc_cat, amount=50000)
        Expense.objects.create(user=self.user, account=self.account, category=self.exp_cat, amount=30000)
        res = self.client.get(reverse("account-detail", args=[self.account.id]))
        self.assertEqual(Decimal(str(res.data["balance"])), Decimal("120000"))

    def test_expense_cannot_exceed_balance(self):
        res = self.client.post(reverse("expense-list"), {
            "account": self.account.id, "category": self.exp_cat.id, "amount": "200000",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("amount", res.data)

    def test_user_cannot_use_foreign_account(self):
        foreign = Account.objects.create(user=self.other, name="Karta")
        res = self.client.post(reverse("income-list"), {
            "account": foreign.id, "category": self.inc_cat.id, "amount": "1000",
        })
        self.assertEqual(res.status_code, 400)

    def test_user_sees_only_own_accounts(self):
        Account.objects.create(user=self.other, name="Begona")
        res = self.client.get(reverse("account-list"))
        self.assertEqual(res.data["count"], 1)

    def test_admin_sees_all_accounts(self):
        Account.objects.create(user=self.other, name="Begona")
        self.client.force_authenticate(self.admin)
        res = self.client.get(reverse("account-list"))
        self.assertEqual(res.data["count"], 2)

    def test_category_name_follows_language(self):
        url = reverse("expense-category-detail", args=[self.exp_cat.id])
        self.assertEqual(self.client.get(url, HTTP_ACCEPT_LANGUAGE="ru").data["name"], "Обед")
        self.assertEqual(self.client.get(url + "?lang=en").data["name"], "Lunch")
        self.assertEqual(self.client.get(url, HTTP_ACCEPT_LANGUAGE="uz").data["name"], "Tushlik")

    def test_user_cannot_edit_global_category(self):
        url = reverse("expense-category-detail", args=[self.exp_cat.id])
        res = self.client.patch(url, {"name_uz": "X"})
        self.assertEqual(res.status_code, 403)

    def test_monthly_report(self):
        Income.objects.create(user=self.user, account=self.account, category=self.inc_cat, amount=50000)
        Expense.objects.create(user=self.user, account=self.account, category=self.exp_cat, amount=20000)
        res = self.client.get(reverse("reports"), {"period": "monthly"})
        self.assertEqual(res.status_code, 200)
        total = res.data["totals"][0]
        self.assertEqual(total["currency"], "UZS")
        self.assertEqual(total["difference"], Decimal("30000"))

    def test_account_with_transactions_cannot_be_deleted(self):
        Income.objects.create(user=self.user, account=self.account, category=self.inc_cat, amount=1000)
        res = self.client.delete(reverse("account-detail", args=[self.account.id]))
        self.assertEqual(res.status_code, 400)
