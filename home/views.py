# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from user.models import Patron

# Create your views here.

def homepage(request):
    has_pfp = False
    is_librarian = False
    patron = None
    if request.user.is_authenticated:
        is_librarian = request.user.groups.filter(name='librarian').exists()
        if hasattr(request.user, 'patron'):
            has_pfp = True
            patron = request.user.patron
    else:
        patron = None

    context = {
        'is_librarian': is_librarian,
        'has_pfp': has_pfp,
        'patron': patron
    }
    
    return render(request, 'home/index.html', context)

