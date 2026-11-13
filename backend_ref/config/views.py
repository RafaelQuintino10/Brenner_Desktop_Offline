# from django.contrib.auth import authenticate, get_user_model
# from django.db import connection
# from rest_framework import status
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.authtoken.models import Token
# from rest_framework.permissions import AllowAny, IsAdminUser
# from rest_framework.response import Response
# from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.db import connection
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from config.permissions import (
    IsAdminOrBalconista,
    is_balconista,
)
from rest_framework.response import Response
from rest_framework.views import APIView


# class LoginView(APIView):
#     """Login restrito aos usuários staff via e-mail + senha (Django User padrão)."""
#     authentication_classes = []
#     permission_classes = [AllowAny]

#     def post(self, request):
#         email = str(request.data.get('email') or '').strip()
#         password = request.data.get('password') or ''
#         invalid = {'detail': 'E-mail ou senha inválidos.'}
#         if not email or not password:
#             return Response(invalid, status=status.HTTP_400_BAD_REQUEST)

#         # Não exige modelo User personalizado, preservando tabelas e usuários existentes.
#         # Rejeita duplicatas, para nunca autenticar uma conta ambígua.
#         users = list(get_user_model().objects.filter(
#             email__iexact=email, is_active=True, is_staff=True,
#         )[:2])
#         if len(users) != 1:
#             return Response(invalid, status=status.HTTP_400_BAD_REQUEST)
#         user = authenticate(request, username=users[0].get_username(), password=password)
#         if not user or not user.is_staff or not user.is_active:
#             return Response(invalid, status=status.HTTP_400_BAD_REQUEST)
#         token, _ = Token.objects.get_or_create(user=user)
#         return Response({'token': token.key, 'email': user.email, 'username': user.get_username()})
class LoginView(APIView):
    """Login exclusivo do administrador."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        email = str(request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        invalid = {'detail': 'E-mail ou senha inválidos.'}

        if not email or not password:
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        users = list(get_user_model().objects.filter(
            email__iexact=email,
            is_active=True,
            is_staff=True,
        )[:2])

        if len(users) != 1:
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request,
            username=users[0].get_username(),
            password=password
        )

        if not user or not user.is_staff or not user.is_active:
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'email': user.email,
            'username': user.get_username(),
            'is_staff': True,
            'role': 'admin',
        })


class BalconistaLoginView(APIView):
    """Login exclusivo do balconista."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        email = str(request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        invalid = {'detail': 'E-mail ou senha inválidos.'}

        if not email or not password:
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        users = list(get_user_model().objects.filter(
            email__iexact=email,
            is_active=True,
            is_staff=False,
            groups__name='Balconista',
        ).distinct()[:2])

        if len(users) != 1:
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request,
            username=users[0].get_username(),
            password=password
        )

        if not user or not is_balconista(user):
            return Response(
                invalid,
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'email': user.email,
            'username': user.get_username(),
            'is_staff': False,
            'role': 'balconista',
        })


# class LogoutView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAdminUser]

#     def post(self, request):
#         if request.auth:
#             request.auth.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrBalconista]

    def post(self, request):
        if request.auth:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WhoAmI(APIView):
    permission_classes = [IsAdminOrBalconista]

    def get(self, request):
        return Response({
            'username': request.user.get_username(),
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'role': (
                'admin'
                if request.user.is_staff
                else 'balconista'
            ),
        })



class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.utils import OperationalError
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except OperationalError:
            return Response({'status': 'unavailable'}, status=503)
        return Response({'status': 'ok', 'database': 'postgresql'})
