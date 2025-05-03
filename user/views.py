from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import PatronSettingsForm
from .models import Patron

def librarian(request):
    is_librarian = False
    if request.user.is_authenticated:
        is_librarian = request.user.groups.filter(name='librarian').exists()
    context = {
        'is_librarian': is_librarian,
    }
    return context

def logout_view(request):
    logout(request)
    return redirect("/")

def profile_view(request):
    context = librarian(request) 
    context['form'] = PatronSettingsForm()
    
    if hasattr(request.user, 'patron'):
        context['patron'] = request.user.patron

    if request.POST:
        patron_form = PatronSettingsForm(request.POST, request.FILES)
        if patron_form.is_valid():
            this_patron = patron_form.save(commit=False)
            context['has_pfp'] = True
            if hasattr(request.user, 'patron'):
                existing_patron = request.user.patron
                existing_patron.profile_picture = this_patron.profile_picture
                existing_patron.save()
                
            else:
                this_patron.user = request.user
                context['patron'] = this_patron
                this_patron.save()
            return render(request, "user/profile.html", context)
        else:
            print("Form errors:", PatronSettingsForm.errors)

    # code block for pfp
    has_pfp = False
    if request.user.is_authenticated:
        is_librarian = request.user.groups.filter(name='librarian').exists()
        if hasattr(request.user, 'patron'):
            has_pfp = True
    context['has_pfp'] = has_pfp
    #end pfp code block

    return render(request, "user/profile.html", context)
