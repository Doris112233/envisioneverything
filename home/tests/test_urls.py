from django.test import SimpleTestCase
from django.urls import reverse, resolve
from home.views import homepage

class HomeUrlsTests(SimpleTestCase):

    
    def test_homepage_url_resolves(self):
        url = reverse('homepage')
        self.assertEqual(resolve(url).func, homepage)
    
    def test_homepage_url_reverse(self):
        url = reverse('homepage')
        self.assertEqual(url, '/')