from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Evento
from .models import Evento, Profile, Comunidad
from datetime import datetime, date, time

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# -------------- Formulario Comunidad ----------------
class ComunidadForm(forms.ModelForm):
    class Meta:
        model = Comunidad
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre de la comunidad"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "placeholder": "Descripción de la comunidad..."}),
        }


# -------------- Formulario Evento ----------------
class EventForm(forms.ModelForm):
    """
    Form para crear/editar eventos.
    - Fecha con hint y soporta formatos DD/MM/YYYY y YYYY-MM-DD.
    - Hora de inicio/fin con soporte AM/PM y 24h.
    - Filtra 'comunidad' a las comunidades donde el user es propietario o miembro.
    """

    fecha = forms.DateField(
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "placeholder": "DD/MM/YYYY",
                "class": "input-date",
                "autocomplete": "off",
            }
        ),
        required=True,
    )

    hora_inicio = forms.TimeField(
        required=True,
        widget=forms.TimeInput(
            attrs={
                "placeholder": "08:30 AM",
                "class": "input-time",
                "autocomplete": "off",
            }
        ),
        input_formats=["%I:%M %p", "%H:%M"],
    )

    hora_fin = forms.TimeField(
        required=True,
        widget=forms.TimeInput(
            attrs={
                "placeholder": "10:00 AM",
                "class": "input-time",
                "autocomplete": "off",
            }
        ),
        input_formats=["%I:%M %p", "%H:%M"],
    )

    class Meta:
        model = Evento
        # 'hora' en el modelo será llenado con hora_inicio en save()
        fields = ["titulo", "descripcion", "fecha", "lugar", "tipo", "comunidad"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe el evento..."}),
            "lugar": forms.TextInput(attrs={"placeholder": "Ej: Auditorio Principal"}),
            # 'tipo' usa el widget por defecto (select) acorde a tus choices en el modelo
        }

    def __init__(self, *args, **kwargs):
        """
        Espera kwargs.pop('user', None) para filtrar queryset de comunidades.
        """
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filtrar queryset de comunidades por propietario o miembro
        if "comunidad" in self.fields:
            if user is not None:
                self.fields["comunidad"].queryset = Comunidad.objects.filter(
                    Q(propietario=user) | Q(miembros=user)
                ).distinct()
            else:
                self.fields["comunidad"].queryset = Comunidad.objects.none()

        # Si editando, rellenar hora_inicio desde instance.hora (si existe)
        if self.instance and getattr(self.instance, "hora", None):
            try:
                self.initial.setdefault("hora_inicio", self.instance.hora)
            except Exception:
                # si por alguna razón el valor no encaja, lo ignoramos
                pass

    def clean(self):
        cleaned = super().clean()

        fecha = cleaned.get("fecha")
        h_inicio = cleaned.get("hora_inicio")
        h_fin = cleaned.get("hora_fin")

        # Validar fecha no en pasado (comparando solo fechas)
        if fecha:
            today = date.today()
            if fecha < today:
                self.add_error("fecha", "La fecha no puede ser anterior a hoy.")

        # Validar horas
        if h_inicio and h_fin:
            # Simple comparación de objetos time
            if h_fin <= h_inicio:
                self.add_error("hora_fin", "La hora de fin debe ser posterior a la hora de inicio.")

        return cleaned

    def save(self, commit=True):
        """
        Guardamos el Evento. Como el modelo tiene solo 'hora' (no hora_inicio/hora_fin),
        tomamos hora_inicio como hora principal del evento.
        """
        evento = super().save(commit=False)

        hora_inicio = self.cleaned_data.get("hora_inicio")
        if hora_inicio:
            evento.hora = hora_inicio

        # NOTA: asignar evento.creado_por lo hacemos desde la vista (es más seguro).
        if commit:
            evento.save()
            # Si hubo muchos-a-muchos (no en este modelo en particular), llamar self.save_m2m()

        return evento