from django.contrib import admin

from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "currency", "initial_balance", "user"]
    list_filter = ["type", "currency"]
    search_fields = ["name", "user__username"]


@admin.register(ExpenseCategory, IncomeCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name_uz", "name_ru", "name_en", "user"]
    search_fields = ["name_uz", "name_ru", "name_en"]


@admin.register(Expense, Income)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "date", "amount", "account", "category", "user"]
    list_filter = ["date", "account__currency"]
    search_fields = ["note", "user__username"]
    date_hierarchy = "date"
