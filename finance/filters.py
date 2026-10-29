import django_filters

from .models import Expense, Income


class TransactionFilter(django_filters.FilterSet):

    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        fields = ["account", "category", "user"]


class ExpenseFilter(TransactionFilter):
    class Meta(TransactionFilter.Meta):
        model = Expense


class IncomeFilter(TransactionFilter):
    class Meta(TransactionFilter.Meta):
        model = Income
