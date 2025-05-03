from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from .models import Product, Borrow, Collection, Review

admin.site.register(Product)
admin.site.register(Borrow)
admin.site.register(Collection)
admin.site.register(Review)