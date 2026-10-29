from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    IncomeCategoryViewSet,
    IncomeViewSet,
    ReportView,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("expense-categories", ExpenseCategoryViewSet, basename="expense-category")
router.register("income-categories", IncomeCategoryViewSet, basename="income-category")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("incomes", IncomeViewSet, basename="income")

urlpatterns = [
    path("reports/", ReportView.as_view(), name="reports"),
    path("", include(router.urls)),
]
