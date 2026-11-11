from django.test import SimpleTestCase
from django.urls import reverse


class HealthViewTest(SimpleTestCase):

    def test_retorna_ok(self):
        resposta = self.client.get(reverse('health'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {'status': 'ok'})
