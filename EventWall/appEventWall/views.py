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
    comunidad = None
    initial = {}
    if comunidad_id:
        comunidad = get_object_or_404(Comunidad, id=comunidad_id)
        # permiso: solo propietario o miembro
        is_propietario = comunidad.propietario == request.user
        is_miembro = comunidad.miembros.filter(pk=request.user.pk).exists() if hasattr(comunidad, "miembros") else False
        if not (is_propietario or is_miembro):
            messages.error(request, "No tienes permiso para crear eventos en esta comunidad.")
            return redirect('comunidad_detalle', pk=comunidad.id)
        initial['comunidad'] = comunidad

    if request.method == 'POST':
        # pasar user para que el formulario filtre comunidades (si el form lo hace)
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            evento = form.save(commit=False)

            # SI venimos desde la URL con comunidad_id, forzamos la comunidad
            if comunidad is not None:
                evento.comunidad = comunidad

            evento.creado_por = request.user

            # seguridad: si por alguna razón comunidad está asignada en el form, comprobamos permisos
            if evento.comunidad:
                is_propietario = evento.comunidad.propietario == request.user
                is_miembro = evento.comunidad.miembros.filter(pk=request.user.pk).exists() if hasattr(evento.comunidad, "miembros") else False
                if not (is_propietario or is_miembro):
                    messages.error(request, "No puedes publicar en esa comunidad.")
                    return redirect('eventos_list')

            evento.save()
            messages.success(request, "Evento guardado.")
            return redirect('comunidad_detalle', pk=evento.comunidad.id) if evento.comunidad else redirect('eventos_list')
    else:
        form = EventForm(initial=initial, user=request.user)

    return render(request, 'evento_form.html', {'form': form, 'comunidad': comunidad})


@login_required
def evento_editar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=evento, user=request.user)
        if form.is_valid():
            evento = form.save(commit=False)
            if evento.comunidad and not evento.comunidad.es_miembro(request.user):
                messages.error(request, "No tienes permiso para asociar este evento a esa comunidad.")
                return redirect("eventos_list")
            evento.save()
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

    # Tus comunidades (propietario)
    tus_comunidades_qs = Comunidad.objects.filter(propietario=request.user).order_by("-creada_en").prefetch_related("miembros")

    # Resultados de búsqueda: buscar en todas las comunidades (incluye tus propias)
    resultados_qs = Comunidad.objects.none()
    if q:
        resultados_qs = (
            Comunidad.objects.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            )
            .order_by("-creada_en")
            .prefetch_related("miembros")
        )

    # Convertir a listas (para poder iterar 2 veces y añadir atributos)
    tus_comunidades = list(tus_comunidades_qs)
    resultados_list = list(resultados_qs)

    # Evitar que las comunidades que son tuyas aparezcan en "resultados"
    tus_ids = {c.id for c in tus_comunidades}
    resultados = [c for c in resultados_list if c.id not in tus_ids]

    # Añadimos atributo booleano para plantilla (evita llamadas complejas en template)
    for c in tus_comunidades + resultados:
        try:
            c.is_miembro = c.miembros.filter(pk=request.user.pk).exists()
        except Exception:
            c.is_miembro = False

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
            # añadir propietario a miembros para simplificar comprobaciones
            if hasattr(comunidad, "miembros"):
                comunidad.miembros.add(request.user)
            messages.success(request, "Comunidad creada.")
            return redirect("Comunidades")
    else:
        form = ComunidadForm()
    return render(request, "ComunidadCreacion.html", {"form": form})


@login_required
def comunidad_detalle(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk)
    eventos = comunidad.eventos.order_by("fecha", "hora")
    es_miembro = comunidad.es_miembro(request.user)
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