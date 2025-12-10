from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
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
    # Campo fecha con placeholder / hint
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

    # Campos de hora inicio / fin — permiten AM/PM y 24h
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
        # guardamos en el modelo los campos que existen: 'hora' lo manejamos manualmente desde hora_inicio
        fields = ["titulo", "descripcion", "fecha", "lugar", "tipo", "comunidad"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe el evento..."}),
            "lugar": forms.TextInput(attrs={"placeholder": "Ej: Auditorio Principal"}),
            # 'tipo' dejará el widget por defecto (select) que usa tus choices en el modelo
        }

    def __init__(self, *args, **kwargs):
        """
        Espera un keyword arg 'user' (el request.user) para filtrar las comunidades.
        """
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filtrar queryset de comunidades por propietario (tu campo es 'propietario')
        if "comunidad" in self.fields:
            if user is not None:
                self.fields["comunidad"].queryset = Comunidad.objects.filter(propietario=user)
            else:
                self.fields["comunidad"].queryset = Comunidad.objects.none()

        # Si venimos con una instancia (edición) rellenamos hora_inicio con el valor existente
        if self.instance and getattr(self.instance, "hora", None):
            # instance.hora es un datetime.time
            self.initial.setdefault("hora_inicio", self.instance.hora)
            # si quieres intentar inferir hora_fin (no hay campo), lo dejamos vacío por defecto

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
                # Error general o en campo específico
                self.add_error("hora_fin", "La hora de fin debe ser posterior a la hora de inicio.")

        return cleaned

    def save(self, commit=True):
        """
        Guardamos el Evento. Como el modelo tiene sólo 'hora' (no hora_inicio/hora_fin),
        tomamos hora_inicio como hora principal del evento (puedes ajustar esto).
        """
        evento = super().save(commit=False)

        # Si el formulario trae hora_inicio, la asignamos al campo 'hora' del modelo.
        hora_inicio = self.cleaned_data.get("hora_inicio")
        if hora_inicio:
            evento.hora = hora_inicio

        # asignar creador se hace normalmente en la vista; dejamos esto por seguridad:
        # if not evento.creado_por and hasattr(self, 'user'):
        #     evento.creado_por = self.user

        if commit:
            evento.save()
        return evento