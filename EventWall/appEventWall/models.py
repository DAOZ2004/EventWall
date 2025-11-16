from django.db import models

# Create your models here.

class Evento(models.Model):
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.titulo