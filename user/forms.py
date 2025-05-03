from django.forms import ModelForm
from django import forms
from .models import Patron

class PatronSettingsForm(ModelForm):
    profile_picture = forms.ImageField()
    class Meta:
        model = Patron
        fields = ['profile_picture']