from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "date_joined"]
        read_only_fields = ["id", "username", "role", "date_joined"]

    def get_role(self, obj) -> str:
        return "admin" if obj.is_staff else "user"


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "password2", "first_name", "last_name", "email"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": _("Parollar mos kelmadi.")})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
