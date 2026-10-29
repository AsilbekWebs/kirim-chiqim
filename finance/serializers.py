from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import serializers

from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory



class AccountSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    balance = serializers.SerializerMethodField()
    owner = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Account
        fields = [
            "id", "name", "type", "type_display", "currency",
            "initial_balance", "balance", "owner", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_balance(self, obj) -> float:
        value = getattr(obj, "balance_value", None)
        if value is None:
            value = obj.get_balance()
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        instance.balance_value = None
        return instance

    def validate_name(self, value):
        user = self.context["request"].user
        qs = Account.objects.filter(user=user, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("Bu nomli hisob allaqachon mavjud."))
        return value

    def validate_currency(self, value):

        inst = self.instance
        if inst and inst.currency != value and (inst.incomes.exists() or inst.expenses.exists()):
            raise serializers.ValidationError(
                _("Kirim yoki chiqimi bor hisobning valyutasini o'zgartirib bo'lmaydi.")
            )
        return value



class BaseCategorySerializer(serializers.ModelSerializer):

    name = serializers.CharField(read_only=True)
    is_global = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ["id", "name", "name_uz", "name_ru", "name_en", "is_global", "created_at"]
        read_only_fields = ["created_at"]


class ExpenseCategorySerializer(BaseCategorySerializer):
    class Meta(BaseCategorySerializer.Meta):
        model = ExpenseCategory


class IncomeCategorySerializer(BaseCategorySerializer):
    class Meta(BaseCategorySerializer.Meta):
        model = IncomeCategory



class BaseTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    currency = serializers.CharField(source="account.currency", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        fields = [
            "id", "amount", "date", "account", "account_name", "currency",
            "category", "category_name", "note", "created_at",
        ]
        read_only_fields = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            category_model = self.Meta.model._meta.get_field("category").related_model
            self.fields["account"].queryset = Account.objects.filter(user=request.user)
            self.fields["category"].queryset = category_model.objects.filter(
                Q(user__isnull=True) | Q(user=request.user)
            )

    def validate(self, attrs):
        request = self.context["request"]
        account = attrs.get("account") or getattr(self.instance, "account", None)
        category = attrs.get("category") or getattr(self.instance, "category", None)


        if not request.user.is_staff and account.user_id != request.user.id:
            raise serializers.ValidationError({"account": _("Bu hisob sizga tegishli emas.")})


        if category.user_id is not None and category.user_id != account.user_id:
            raise serializers.ValidationError(
                {"category": _("Bu tur ushbu foydalanuvchiga tegishli emas.")}
            )


        attrs["user"] = account.user
        return attrs


class ExpenseSerializer(BaseTransactionSerializer):
    class Meta(BaseTransactionSerializer.Meta):
        model = Expense

    def validate(self, attrs):
        attrs = super().validate(attrs)
        account = attrs.get("account") or self.instance.account
        amount = attrs.get("amount") or self.instance.amount


        available = account.get_balance()
        if self.instance and self.instance.account_id == account.id:
            available += self.instance.amount
        if amount > available:
            raise serializers.ValidationError(
                {"amount": _("Hisobda mablag' yetarli emas. Mavjud qoldiq: %(balance)s %(currency)s")
                 % {"balance": available, "currency": account.currency}}
            )
        return attrs


class IncomeSerializer(BaseTransactionSerializer):
    class Meta(BaseTransactionSerializer.Meta):
        model = Income



class ReportQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly", "custom"], default="monthly"
    )
    date = serializers.DateField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    account = serializers.IntegerField(required=False)
    user = serializers.IntegerField(required=False, help_text="Faqat admin uchun")

    def validate(self, attrs):
        if attrs["period"] == "custom":
            if not attrs.get("date_from") or not attrs.get("date_to"):
                raise serializers.ValidationError(
                    _("custom davr uchun date_from va date_to majburiy.")
                )
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError(
                    _("date_from date_to dan katta bo'lishi mumkin emas.")
                )
        return attrs
