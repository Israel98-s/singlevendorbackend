from rest_framework.permissions import BasePermission

class IsVendorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        return request.user.is_authenticated and (request.user.is_vendor or request.user.is_staff or request.user.is_superuser)