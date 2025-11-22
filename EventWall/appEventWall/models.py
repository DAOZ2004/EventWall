from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class Evento(models.Model):
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.titulo