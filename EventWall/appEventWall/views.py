from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Profile
from .forms import CustomUserCreationForm
from .models import Evento
from .forms import EventForm



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
def comunidades_view(request):
    return render(request, "Comunidades.html")

@login_required
def crear_comunidad_view(request):
    return render(request, "ComunidadCreacion.html")

@login_required
def eventos_list(request):
    eventos = Evento.objects.order_by('fecha', 'hora')
    return render(request, "eventos_list.html", {"eventos": eventos})

@login_required
def evento_detalle(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return render(request, "evento_detalle.html", {"evento": evento})

@login_required
def evento_crear(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.creado_por = request.user
            evento.save()
            return redirect("eventos_list")
    else:
        form = EventForm()
    return render(request, "evento_form.html", {"form": form})

@login_required
def evento_editar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect("eventos_list")
    else:
        form = EventForm(instance=evento)
    return render(request, "evento_form.html", {"form": form, "evento": evento})

@login_required
def evento_eliminar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        evento.delete()
        return redirect("eventos_list")
    return render(request, "evento_eliminar.html", {"evento": evento})