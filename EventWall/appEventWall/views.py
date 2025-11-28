from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Profile
from .forms import CustomUserCreationForm


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home') 

    else:
        form = AuthenticationForm()

    return render(request, "Login.html", {"form": form})


def registro_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, "registro.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    
    return render(request, "home.html")

@login_required
def perfil_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, "perfil.html", {"profile": profile})

@login_required
def eventos_view(request):
    return render(request, "Eventos.html")

@login_required
def comunidades_view(request):
    return render(request, "Comunidades.html")

@login_required
def crear_comunidad_view(request):
    return render(request, "ComunidadCreacion.html")