from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from .models import Patron

admin.site.register(Patron)