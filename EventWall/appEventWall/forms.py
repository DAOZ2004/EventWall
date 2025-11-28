from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Evento
from .models import Evento, Profile, Comunidad

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
class ComunidadForm(forms.ModelForm):
    class Meta:
        model = Comunidad
        fields = ["nombre", "descripcion"]


class EventForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["titulo", "descripcion", "fecha", "hora", "lugar", "tipo", "comunidad"]

    def __init__(self, *args, **kwargs):
        # Recuperamos el usuario que viene desde la vista
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user is not None:
           
            self.fields["comunidad"].queryset = Comunidad.objects.filter(
                propietario=user
            )
        else:
            # Si por alguna razón no hay usuario, no mostramos comunidades
            self.fields["comunidad"].queryset = Comunidad.objects.none()