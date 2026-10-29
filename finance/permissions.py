from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdmin(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner_id = getattr(obj, "user_id", None)
        if owner_id is None:
            return request.method in SAFE_METHODS
        return owner_id == request.user.id