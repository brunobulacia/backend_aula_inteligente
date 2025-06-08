from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios import views

router = DefaultRouter()
router.register('usuarios', views.UsuarioViewSet, basename='usuarios')
router.register('direcciones', views.DireccionViewSet, basename='direcciones')


urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('listar/', views.obtener_usuarios),
    path('alumnos/', views.alumnos_por_gestion),
    path('profesores/', views.obtener_profesores, name='obtener_profesores'),
    path('', include(router.urls)),
]