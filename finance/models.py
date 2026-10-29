from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

MONEY = {"max_digits": 15, "decimal_places": 2}
ZERO = Decimal("0.00")


class TranslatedNameModel(models.Model):

    name_uz = models.CharField(_("Nomi (uz)"), max_length=100)
    name_ru = models.CharField(_("Nomi (ru)"), max_length=100, blank=True)
    name_en = models.CharField(_("Nomi (en)"), max_length=100, blank=True)

    class Meta:
        abstract = True

    @property
    def name(self):
        lang = (get_language() or "uz")[:2]
        return getattr(self, f"name_{lang}", "") or self.name_uz

    def __str__(self):
        return self.name


class Category(TranslatedNameModel):


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Foydalanuvchi"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name_uz"]

    @property
    def is_global(self):
        return self.user_id is None


class ExpenseCategory(Category):
    class Meta(Category.Meta):
        verbose_name = _("Chiqim turi")
        verbose_name_plural = _("Chiqim turlari")


class IncomeCategory(Category):
    class Meta(Category.Meta):
        verbose_name = _("Kirim turi")
        verbose_name_plural = _("Kirim turlari")


class AccountQuerySet(models.QuerySet):
    def with_balance(self):

        money = DecimalField(**MONEY)

        def total(model):
            sq = (
                model.objects.filter(account=OuterRef("pk"))
                .values("account")
                .annotate(s=Sum("amount"))
                .values("s")
            )
            return Coalesce(Subquery(sq, output_field=money), Value(ZERO), output_field=money)

        return self.annotate(
            total_income=total(Income),
            total_expense=total(Expense),
        ).annotate(
            balance_value=F("initial_balance") + F("total_income") - F("total_expense")
        )


class Account(models.Model):

    class Type(models.TextChoices):
        CASH = "cash", _("Naqd pul")
        CARD = "card", _("Karta")
        CURRENCY = "currency", _("Valyuta")

    class Currency(models.TextChoices):
        UZS = "UZS", "UZS"
        USD = "USD", "USD"
        EUR = "EUR", "EUR"
        RUB = "RUB", "RUB"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts",
        verbose_name=_("Foydalanuvchi"),
    )
    name = models.CharField(_("Nomi"), max_length=100)
    type = models.CharField(_("Turi"), max_length=10, choices=Type.choices, default=Type.CASH)
    currency = models.CharField(
        _("Valyuta"), max_length=3, choices=Currency.choices, default=Currency.UZS
    )
    initial_balance = models.DecimalField(_("Boshlang'ich qoldiq"), default=ZERO, **MONEY)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AccountQuerySet.as_manager()

    class Meta:
        ordering = ["id"]
        verbose_name = _("Hisob")
        verbose_name_plural = _("Hisoblar")
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_account_name_per_user")
        ]

    def __str__(self):
        return f"{self.name} ({self.currency})"

    def get_balance(self):
        income = self.incomes.aggregate(s=Sum("amount"))["s"] or ZERO
        expense = self.expenses.aggregate(s=Sum("amount"))["s"] or ZERO
        return self.initial_balance + income - expense


class Transaction(models.Model):


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Foydalanuvchi"),
    )
    amount = models.DecimalField(
        _("Summa"), validators=[MinValueValidator(Decimal("0.01"))], **MONEY
    )
    date = models.DateField(_("Sana"), default=timezone.localdate)
    note = models.CharField(_("Izoh"), max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-date", "-id"]


class Expense(Transaction):
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="expenses", verbose_name=_("Hisob")
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name=_("Chiqim turi"),
    )

    class Meta(Transaction.Meta):
        verbose_name = _("Chiqim")
        verbose_name_plural = _("Chiqimlar")

    def __str__(self):
        return f"-{self.amount} {self.account.currency} ({self.date})"


class Income(Transaction):
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="incomes", verbose_name=_("Hisob")
    )
    category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.PROTECT,
        related_name="incomes",
        verbose_name=_("Kirim turi"),
    )

    class Meta(Transaction.Meta):
        verbose_name = _("Kirim")
        verbose_name_plural = _("Kirimlar")

    def __str__(self):
        return f"+{self.amount} {self.account.currency} ({self.date})"
