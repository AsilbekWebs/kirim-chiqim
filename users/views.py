from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):


    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class LoginView(TokenObtainPairView):


    serializer_class = LoginSerializer


class MeView(generics.RetrieveUpdateAPIView):


    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):


    queryset = User.objects.order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ["username", "first_name", "last_name", "email"]