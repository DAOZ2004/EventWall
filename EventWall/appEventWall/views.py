from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import Evento
from .forms import EventForm
from .models import Profile, Evento, Comunidad
from .forms import CustomUserCreationForm, EventForm, ComunidadForm




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
def evento_crear(request, comunidad_id=None):
    comunidad = None
    if comunidad_id is not None:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id, propietario=request.user)

    if request.method == "POST":
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.creado_por = request.user
            if comunidad is not None:
                evento.comunidad = comunidad   # lo forzamos a esta comunidad
            evento.save()
            # Si venimos desde una comunidad, regresamos ahí
            if comunidad is not None:
                return redirect("comunidad_detalle", pk=comunidad.id)
            return redirect("eventos_list")
    else:
        initial = {}
        if comunidad is not None:
            initial["comunidad"] = comunidad
        form = EventForm(user=request.user, initial=initial)

    return render(
        request,
        "evento_form.html",
        {"form": form, "comunidad": comunidad},
    )

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

@login_required
def comunidades_list(request):
    # Solo las comunidades creadas por el usuario actual
    comunidades = Comunidad.objects.filter(propietario=request.user)
    return render(request, "Comunidades.html", {"comunidades": comunidades})


@login_required
def crear_comunidad_view(request):
    if request.method == "POST":
        form = ComunidadForm(request.POST)
        if form.is_valid():
            comunidad = form.save(commit=False)
            comunidad.propietario = request.user
            comunidad.save()
            return redirect("Comunidades")   # nombre del url de lista
    else:
        form = ComunidadForm()

    return render(request, "ComunidadCreacion.html", {"form": form})

@login_required
def comunidad_detalle(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk, propietario=request.user)
    eventos = comunidad.eventos.order_by("fecha", "hora")
    return render(
        request,
        "comunidad_detalle.html",
        {"comunidad": comunidad, "eventos": eventos},
    )

@login_required
def comunidad_eliminar(request, pk):
    """
    Permite al propietario (propietario) eliminar su comunidad.
    Muestra un formulario de confirmación GET -> POST para borrar.
    """
    comunidad = get_object_or_404(Comunidad, pk=pk, propietario=request.user)

    if request.method == "POST":
        # eliminar y redirigir con mensaje
        comunidad.delete()
        messages.success(request, "La comunidad se eliminó correctamente.")
        return redirect("Comunidades")  # nombre de la URL de la lista de comunidades

    # GET -> mostrar confirmación
    return render(request, "comunidad_confirm_delete.html", {"comunidad": comunidad})