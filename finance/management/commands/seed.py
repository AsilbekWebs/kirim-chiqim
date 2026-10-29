from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from finance.models import Account, Expense, ExpenseCategory, Income, IncomeCategory

User = get_user_model()

EXPENSE_CATEGORIES = [
    ("Yo'l kira", "Проезд", "Transport"),
    ("Tushlik", "Обед", "Lunch"),
    ("Salomatlik", "Здоровье", "Health"),
]
INCOME_CATEGORIES = [
    ("Oylik", "Зарплата", "Salary"),
    ("Avans", "Аванс", "Advance"),
    ("Kunlik ish haqi", "Дневной заработок", "Daily wage"),
]


class Command(BaseCommand):
    help = "Admin, user, umumiy turlar va namunaviy ma'lumotlarni yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self.make_user("admin", "admin12345", is_admin=True)
        user = self.make_user("user", "user12345")

        exp_cats = [
            ExpenseCategory.objects.get_or_create(
                name_uz=uz, user=None, defaults={"name_ru": ru, "name_en": en}
            )[0]
            for uz, ru, en in EXPENSE_CATEGORIES
        ]
        inc_cats = [
            IncomeCategory.objects.get_or_create(
                name_uz=uz, user=None, defaults={"name_ru": ru, "name_en": en}
            )[0]
            for uz, ru, en in INCOME_CATEGORIES
        ]

        cash, _ = Account.objects.get_or_create(
            user=user, name="Naqd pul",
            defaults={"type": Account.Type.CASH, "currency": "UZS", "initial_balance": Decimal("200000")},
        )
        card, _ = Account.objects.get_or_create(
            user=user, name="Karta",
            defaults={"type": Account.Type.CARD, "currency": "UZS"},
        )
        usd, _ = Account.objects.get_or_create(
            user=user, name="Valyuta",
            defaults={"type": Account.Type.CURRENCY, "currency": "USD", "initial_balance": Decimal("100")},
        )
        Account.objects.get_or_create(
            user=admin, name="Naqd pul",
            defaults={"type": Account.Type.CASH, "currency": "UZS"},
        )

        # Namunaviy tranzaksiyalar — faqat user'da hali yo'q bo'lsa
        if not Income.objects.filter(user=user).exists():
            today = timezone.localdate()
            d = lambda n: today - timedelta(days=n)  # noqa: E731
            Income.objects.bulk_create([
                Income(user=user, account=card, category=inc_cats[0], amount=Decimal("5000000"), date=d(10), note="Oktabr oyligi"),
                Income(user=user, account=card, category=inc_cats[1], amount=Decimal("1500000"), date=d(3)),
                Income(user=user, account=cash, category=inc_cats[2], amount=Decimal("300000"), date=d(1)),
                Income(user=user, account=usd, category=inc_cats[2], amount=Decimal("50"), date=today),
            ])
            Expense.objects.bulk_create([
                Expense(user=user, account=cash, category=exp_cats[0], amount=Decimal("12000"), date=d(2), note="Taksi"),
                Expense(user=user, account=cash, category=exp_cats[1], amount=Decimal("35000"), date=d(1)),
                Expense(user=user, account=card, category=exp_cats[2], amount=Decimal("250000"), date=d(5), note="Dorixona"),
                Expense(user=user, account=card, category=exp_cats[1], amount=Decimal("40000"), date=today),
                Expense(user=user, account=usd, category=exp_cats[2], amount=Decimal("20"), date=today),
            ])

        self.stdout.write(self.style.SUCCESS(
            "Tayyor! Login: admin / admin12345 (admin), user / user12345 (foydalanuvchi)"
        ))

    @staticmethod
    def make_user(username, password, is_admin=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": is_admin, "is_superuser": is_admin},
        )
        if created:
            user.set_password(password)
            user.save()
        return user
