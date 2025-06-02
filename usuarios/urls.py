from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios import views

router = DefaultRouter()

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('listar/', views.obtener_usuarios),
    path('alumnos/', views.alumnos_por_gestion),
]