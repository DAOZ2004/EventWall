"""
URL configuration for EventWall project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from appEventWall import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    # 📌 Eventos
    path('eventosLista/', views.eventos_list, name='eventos_list'),
    path('eventos/nuevo/', views.evento_crear, name='evento_crear'),
    path('eventos/<int:pk>/', views.evento_detalle, name='evento_detalle'),
    path('eventos/<int:pk>/editar/', views.evento_editar, name='evento_editar'),
    path('eventos/<int:pk>/eliminar/', views.evento_eliminar, name='evento_eliminar'),
    path("comunidades/", views.comunidades_list, name="Comunidades"),
    path("comunidades/nueva/", views.crear_comunidad_view, name="CrearComunidad"),
]
