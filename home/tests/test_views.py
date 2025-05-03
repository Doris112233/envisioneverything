from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

class HomeViewsTests(TestCase):
   

    ## setup test data
    def setUp(self):

        self.librarian_group = Group.objects.create(name='librarian')
        
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpassword123'
        )
        
        self.librarian_user = User.objects.create_user(
            username='librarian_user',
            email='librarian@example.com',
            password='testpassword123'
        )
        

        self.librarian_user.groups.add(self.librarian_group)
        
        site = Site.objects.get_current()
        
        # create google acc for test
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='dummy-client-id',
            secret='dummy-secret'
        )
        
        social_app.sites.add(site)
    
    ## test home for unauth
    def test_homepage_view_unauthenticated(self):
        url = reverse('homepage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_librarian', response.context)
        self.assertFalse(response.context['is_librarian'])
    
    ## test home for auth
    def test_homepage_view_authenticated_regular_user(self):
        self.client.login(username='regular_user', password='testpassword123')
        url = reverse('homepage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_librarian', response.context)
        self.assertFalse(response.context['is_librarian'])
    
    ## test home for librarian
    def test_homepage_view_authenticated_librarian(self):
        self.client.login(username='librarian_user', password='testpassword123')
        url = reverse('homepage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_librarian', response.context)
        self.assertTrue(response.context['is_librarian'])