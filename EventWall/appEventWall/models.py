from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class Evento(models.Model):
    TIPO_CHOICES = [
        ('conferencia', 'Conferencia'),
        ('taller', 'Taller'),
        ('reunion', 'Reunión'),
        ('otro', 'Otro'),
    ]

   
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=100, blank=True)

    # Tipo con choices (del modelo nuevo)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='otro',
        blank=True
    )


    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True
    )

    comunidad = models.ForeignKey(
        'Comunidad',
        on_delete=models.CASCADE,
        related_name='eventos',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.titulo
    
class Comunidad(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comunidades'
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return self.nombre