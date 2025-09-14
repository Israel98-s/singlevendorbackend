from rest_framework import permissions

class IsVendorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_vendor or request.user.is_staff)