import calendar
from datetime import timedelta

from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ExpenseFilter, IncomeFilter
from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory
from .permissions import IsOwnerOrAdmin
from .serializers import (
    AccountSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    IncomeCategorySerializer,
    IncomeSerializer,
    ReportQuerySerializer,
)


class ProtectedDestroyMixin:
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": _("Bu yozuvga bog'langan kirim yoki chiqimlar bor, o'chirib bo'lmaydi.")},
                status=status.HTTP_400_BAD_REQUEST,
            )



class AccountViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):


    serializer_class = AccountSerializer
    permission_classes = [IsOwnerOrAdmin]
    filterset_fields = ["type", "currency", "user"]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at"]

    def get_queryset(self):
        qs = Account.objects.select_related("user").with_balance()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class BaseCategoryViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrAdmin]
    search_fields = ["name_uz", "name_ru", "name_en"]
    ordering_fields = ["name_uz", "created_at"]

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.request.user.is_staff:
            return qs
        return qs.filter(Q(user__isnull=True) | Q(user=self.request.user))

    def perform_create(self, serializer):
        owner = None if self.request.user.is_staff else self.request.user
        serializer.save(user=owner)


class ExpenseCategoryViewSet(BaseCategoryViewSet):


    model = ExpenseCategory
    serializer_class = ExpenseCategorySerializer


class IncomeCategoryViewSet(BaseCategoryViewSet):


    model = IncomeCategory
    serializer_class = IncomeCategorySerializer



class BaseTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrAdmin]
    search_fields = ["note"]
    ordering_fields = ["date", "amount", "created_at"]

    def get_queryset(self):
        qs = self.model.objects.select_related("account", "category", "user")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)


class ExpenseViewSet(BaseTransactionViewSet):


    model = Expense
    serializer_class = ExpenseSerializer
    filterset_class = ExpenseFilter


class IncomeViewSet(BaseTransactionViewSet):


    model = Income
    serializer_class = IncomeSerializer
    filterset_class = IncomeFilter


def period_range(period, day):
    if period == "daily":
        return day, day
    if period == "weekly":
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=6)
    # monthly
    last = calendar.monthrange(day.year, day.month)[1]
    return day.replace(day=1), day.replace(day=last)


class ReportView(APIView):

    @extend_schema(
        parameters=[
            OpenApiParameter("period", str, enum=["daily", "weekly", "monthly", "custom"]),
            OpenApiParameter("date", str, description="YYYY-MM-DD, standart: bugun"),
            OpenApiParameter("date_from", str, description="period=custom uchun"),
            OpenApiParameter("date_to", str, description="period=custom uchun"),
            OpenApiParameter("account", int),
            OpenApiParameter("user", int, description="Faqat admin uchun"),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        params = ReportQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        p = params.validated_data

        if p["period"] == "custom":
            start, end = p["date_from"], p["date_to"]
        else:
            start, end = period_range(p["period"], p.get("date") or timezone.localdate())

        flt = Q(date__gte=start, date__lte=end)
        if request.user.is_staff:
            if p.get("user"):
                flt &= Q(user_id=p["user"])
        else:
            flt &= Q(user=request.user)
        if p.get("account"):
            flt &= Q(account_id=p["account"])

        incomes = Income.objects.filter(flt)
        expenses = Expense.objects.filter(flt)

        return Response({
            "period": p["period"],
            "date_from": start,
            "date_to": end,
            "totals": self.totals(incomes, expenses),
            "income_by_category": self.by_category(incomes, IncomeCategory),
            "expense_by_category": self.by_category(expenses, ExpenseCategory),
            "by_day": self.by_day(incomes, expenses),
        })

    @staticmethod
    def totals(incomes, expenses):
        data = {}
        for row in incomes.values("account__currency").annotate(s=Sum("amount")):
            data.setdefault(row["account__currency"], {"income": 0, "expense": 0})["income"] = row["s"]
        for row in expenses.values("account__currency").annotate(s=Sum("amount")):
            data.setdefault(row["account__currency"], {"income": 0, "expense": 0})["expense"] = row["s"]
        return [
            {"currency": cur, "income": v["income"], "expense": v["expense"],
             "difference": v["income"] - v["expense"]}
            for cur, v in sorted(data.items())
        ]

    @staticmethod
    def by_category(qs, category_model):
        rows = list(
            qs.values("category_id", "account__currency")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        names = {
            c.id: c.name
            for c in category_model.objects.filter(id__in={r["category_id"] for r in rows})
        }
        return [
            {"category_id": r["category_id"], "category": names.get(r["category_id"]),
             "currency": r["account__currency"], "total": r["total"]}
            for r in rows
        ]

    @staticmethod
    def by_day(incomes, expenses):
        data = {}
        for kind, qs in (("income", incomes), ("expense", expenses)):
            for row in qs.values("date", "account__currency").annotate(s=Sum("amount")):
                key = (row["date"], row["account__currency"])
                data.setdefault(key, {"income": 0, "expense": 0})[kind] = row["s"]
        return [
            {"date": d, "currency": cur, **v}
            for (d, cur), v in sorted(data.items())
        ]
