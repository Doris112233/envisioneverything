from django.apps import AppConfig
from datetime import datetime, timedelta


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
