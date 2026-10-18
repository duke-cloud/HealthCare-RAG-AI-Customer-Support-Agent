from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms

class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name  = forms.CharField(max_length=50)
    username   = forms.CharField(max_length=50)
    email      = forms.EmailField()
    password   = forms.CharField(widget=forms.PasswordInput())
    role       = forms.ChoiceField(choices=[('patient','Patient'),('staff','Staff')])

    def clean_username(self):
        u = self.cleaned_data['username']
        if User.objects.filter(username=u).exists():
            raise forms.ValidationError('Username taken.')
        return u

def register(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        cd = form.cleaned_data
        user = User.objects.create_user(cd['username'], cd['email'], cd['password'],
                                        first_name=cd['first_name'], last_name=cd['last_name'])
        user.profile.role = cd['role']; user.profile.save()
        login(request, user)
        messages.success(request, f"Welcome to HealthCare RAG, {user.first_name}!")
        return redirect('dashboard')
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form = AuthenticationForm(request, data=request.POST or None)
    if form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request); return redirect('login')
