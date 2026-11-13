from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class EmailLoginTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='admin_brenner', email='admin@exemplo.com', password='SenhaSegura!1234'
        )
        self.outro = User.objects.create_user(
            username='cliente', email='cliente@exemplo.com', password='SenhaSegura!1234'
        )

    def test_login_with_email(self):
        res = self.client.post('/api/auth/login/', {'email': 'ADMIN@EXEMPLO.COM', 'password': 'SenhaSegura!1234'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', res.data)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + res.data['token'])
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['email'], 'admin@exemplo.com')

    def test_username_no_longer_accepted(self):
        res = self.client.post('/api/auth/login/', {'username': 'admin_brenner', 'password': 'SenhaSegura!1234'})
        self.assertEqual(res.status_code, 400)

    def test_wrong_password(self):
        res = self.client.post('/api/auth/login/', {'email': 'admin@exemplo.com', 'password': 'errada'})
        self.assertEqual(res.status_code, 400)

    def test_non_staff_rejected(self):
        res = self.client.post('/api/auth/login/', {'email': 'cliente@exemplo.com', 'password': 'SenhaSegura!1234'})
        self.assertEqual(res.status_code, 400)

    def test_duplicate_staff_email_rejected(self):
        get_user_model().objects.create_user(
            username='duplicado', email='ADMIN@exemplo.com', password='SenhaSegura!1234', is_staff=True
        )
        res = self.client.post('/api/auth/login/', {'email': 'admin@exemplo.com', 'password': 'SenhaSegura!1234'})
        self.assertEqual(res.status_code, 400)
