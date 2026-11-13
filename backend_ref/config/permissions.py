from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_balconista(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and not user.is_staff
        and user.groups.filter(name='Balconista').exists()
    )


class IsAdminOrBalconista(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_staff
                or is_balconista(user)
            )
        )


class IsAdminOrBalconistaReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_staff
                or (
                    request.method in SAFE_METHODS
                    and is_balconista(user)
                )
            )
        )