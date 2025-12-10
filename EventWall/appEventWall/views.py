from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .forms import CustomUserCreationForm, EventForm, ComunidadForm
from .models import Profile, Evento, Comunidad


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "Login.html", {"form": form})


def registro_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "registro.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def perfil_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, "perfil.html", {"profile": profile})


# ------------------- EVENTOS -------------------

@login_required
def eventos_list(request):
    eventos = Evento.objects.order_by("fecha", "hora")
    return render(request, "eventos_list.html", {"eventos": eventos})


@login_required
def evento_detalle(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return render(request, "evento_detalle.html", {"evento": evento})


@login_required
def evento_crear(request, comunidad_id=None):
    """
    Crear un evento. Si comunidad_id se pasa, intentamos crear dentro de esa comunidad.
    Se requiere que el usuario sea propietario o miembro de la comunidad para crear en ella.
    """
    comunidad = None
    initial = {}

    if comunidad_id:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id)
        # comprobar permiso: propietario o miembro
        is_propietario = comunidad.propietario == request.user
        is_miembro = False
        if hasattr(comunidad, "miembros"):
            is_miembro = comunidad.miembros.filter(pk=request.user.pk).exists()
        if not (is_propietario or is_miembro):
            messages.error(request, "No tienes permiso para crear eventos en esta comunidad.")
            return redirect("comunidad_detalle", pk=comunidad.id)
        initial["comunidad"] = comunidad

    if request.method == "POST":
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.creado_por = request.user
            # verificar seguridad: si la comunidad elegida no permite al usuario publicar
            if evento.comunidad:
                is_propietario = evento.comunidad.propietario == request.user
                is_miembro = False
                if hasattr(evento.comunidad, "miembros"):
                    is_miembro = evento.comunidad.miembros.filter(pk=request.user.pk).exists()
                if not (is_propietario or is_miembro):
                    messages.error(request, "No puedes publicar en esa comunidad.")
                    return redirect("eventos_list")
            evento.save()
            messages.success(request, "Evento guardado.")
            if evento.comunidad:
                return redirect("comunidad_detalle", pk=evento.comunidad.id)
            return redirect("eventos_list")
    else:
        form = EventForm(initial=initial, user=request.user)

    return render(request, "evento_form.html", {"form": form, "comunidad": comunidad})


@login_required
def evento_editar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    # restricción opcional: solo creador puede editar (si quieres)
    # if evento.creado_por != request.user:
    #     messages.error(request, "No puedes editar este evento.")
    #     return redirect("eventos_list")

    if request.method == "POST":
        form = EventForm(request.POST, instance=evento, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento actualizado.")
            return redirect("eventos_list")
    else:
        form = EventForm(instance=evento, user=request.user)

    return render(request, "evento_form.html", {"form": form, "evento": evento})


@login_required
def evento_eliminar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        evento.delete()
        messages.success(request, "Evento eliminado.")
        return redirect("eventos_list")
    return render(request, "evento_eliminar.html", {"evento": evento})


# ------------------- COMUNIDADES -------------------

@login_required
def comunidades_list(request):
    q = request.GET.get("q", "").strip()

    tus_comunidades = list(Comunidad.objects.filter(propietario=request.user).order_by("-creada_en"))

    resultados = []
    if q:
        resultados = list(
            Comunidad.objects.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            ).exclude(propietario=request.user).order_by("-creada_en")
        )

    # Añadir atributo is_miembro en cada comunidad (una consulta por comunidad, pero controlada).
    # Si tienes muchos items y preocupan las consultas, se puede optimizar con prefetch_related.
    for c in tus_comunidades:
        c.is_miembro = c.miembros.filter(pk=request.user.pk).exists() if hasattr(c, "miembros") else False

    for c in resultados:
        c.is_miembro = c.miembros.filter(pk=request.user.pk).exists() if hasattr(c, "miembros") else False

    context = {
        "comunidades": tus_comunidades,
        "query": q,
        "resultados": resultados,
    }
    return render(request, "Comunidades.html", context)


@login_required
def crear_comunidad_view(request):
    if request.method == "POST":
        form = ComunidadForm(request.POST)
        if form.is_valid():
            comunidad = form.save(commit=False)
            comunidad.propietario = request.user
            comunidad.save()
            # si existe campo miembros y quieres agregar al propietario automáticamente:
            if hasattr(comunidad, "miembros"):
                comunidad.miembros.add(request.user)
            messages.success(request, "Comunidad creada.")
            return redirect("Comunidades")
    else:
        form = ComunidadForm()
    return render(request, "ComunidadCreacion.html", {"form": form})


@login_required
def comunidad_detalle(request, pk):
    """
    Vista que muestra una comunidad y sus eventos.
    Se permite ver independientemente del propietario (si quieres restringir, modifica aquí).
    """
    comunidad = get_object_or_404(Comunidad, pk=pk)
    eventos = comunidad.eventos.order_by("fecha", "hora")
    es_miembro = False
    if hasattr(comunidad, "miembros"):
        es_miembro = comunidad.miembros.filter(pk=request.user.pk).exists()
    return render(request, "comunidad_detalle.html", {"comunidad": comunidad, "eventos": eventos, "es_miembro": es_miembro})


@login_required
def comunidad_eliminar(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk, propietario=request.user)
    if request.method == "POST":
        comunidad.delete()
        messages.success(request, "La comunidad se eliminó correctamente.")
        return redirect("Comunidades")
    return render(request, "comunidad_confirm_delete.html", {"comunidad": comunidad})


@login_required
def unirse_comunidad(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk)
    if request.method == "POST":
        if comunidad.propietario == request.user:
            messages.info(request, "Eres el propietario de la comunidad.")
        else:
            if hasattr(comunidad, "miembros"):
                comunidad.miembros.add(request.user)
                messages.success(request, f"Te uniste a {comunidad.nombre}.")
            else:
                messages.error(request, "Acción no soportada (campo miembros no definido).")
    return redirect("comunidad_detalle", pk=comunidad.pk)


@login_required
def salir_comunidad(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk)
    if request.method == "POST":
        if hasattr(comunidad, "miembros"):
            comunidad.miembros.remove(request.user)
            messages.success(request, f"Has salido de {comunidad.nombre}.")
        else:
            messages.error(request, "Acción no soportada (campo miembros no definido).")
    return redirect("comunidad_detalle", pk=comunidad.pk)


@login_required
def comunidad_miembros(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk)
    miembros = comunidad.miembros.all().order_by("username") if hasattr(comunidad, "miembros") else []
    return render(request, "comunidad_miembros.html", {"comunidad": comunidad, "miembros": miembros})


@login_required
def comunidades_buscar(request):
    q = request.GET.get("q", "").strip()
    resultados = Comunidad.objects.none()
    if q:
        resultados = Comunidad.objects.filter(
            Q(nombre__icontains=q) | Q(descripcion__icontains=q)
        ).exclude(propietario=request.user).order_by("-creada_en")
    return render(request, "comunidades_buscar.html", {"query": q, "resultados": resultados})