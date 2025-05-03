from django.urls import path, include
from django.shortcuts import render
from . import views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path("logout", views.logout_view),
    path("profile/", views.profile_view, name="profile")
]