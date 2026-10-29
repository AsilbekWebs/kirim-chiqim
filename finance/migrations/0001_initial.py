from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpenseCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_uz", models.CharField(max_length=100, verbose_name="Nomi (uz)")),
                ("name_ru", models.CharField(blank=True, max_length=100, verbose_name="Nomi (ru)")),
                ("name_en", models.CharField(blank=True, max_length=100, verbose_name="Nomi (en)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Chiqim turi",
                "verbose_name_plural": "Chiqim turlari",
                "ordering": ["name_uz"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="IncomeCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_uz", models.CharField(max_length=100, verbose_name="Nomi (uz)")),
                ("name_ru", models.CharField(blank=True, max_length=100, verbose_name="Nomi (ru)")),
                ("name_en", models.CharField(blank=True, max_length=100, verbose_name="Nomi (en)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Kirim turi",
                "verbose_name_plural": "Kirim turlari",
                "ordering": ["name_uz"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Nomi")),
                ("type", models.CharField(choices=[("cash", "Naqd pul"), ("card", "Karta"), ("currency", "Valyuta")], default="cash", max_length=10, verbose_name="Turi")),
                ("currency", models.CharField(choices=[("UZS", "UZS"), ("USD", "USD"), ("EUR", "EUR"), ("RUB", "RUB")], default="UZS", max_length=3, verbose_name="Valyuta")),
                ("initial_balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15, verbose_name="Boshlang'ich qoldiq")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accounts", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Hisob",
                "verbose_name_plural": "Hisoblar",
                "ordering": ["id"],
                "constraints": [models.UniqueConstraint(fields=("user", "name"), name="unique_account_name_per_user")],
            },
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Summa")),
                ("date", models.DateField(default=django.utils.timezone.localdate, verbose_name="Sana")),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expenses", to="finance.account", verbose_name="Hisob")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expenses", to="finance.expensecategory", verbose_name="Chiqim turi")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Chiqim",
                "verbose_name_plural": "Chiqimlar",
                "ordering": ["-date", "-id"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Income",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Summa")),
                ("date", models.DateField(default=django.utils.timezone.localdate, verbose_name="Sana")),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="Izoh")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="incomes", to="finance.account", verbose_name="Hisob")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="incomes", to="finance.incomecategory", verbose_name="Kirim turi")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Foydalanuvchi")),
            ],
            options={
                "verbose_name": "Kirim",
                "verbose_name_plural": "Kirimlar",
                "ordering": ["-date", "-id"],
                "abstract": False,
            },
        ),
    ]
