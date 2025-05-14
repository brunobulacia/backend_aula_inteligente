from django.urls import path, include
from rest_framework.routers import DefaultRouter
from usuarios import views

router = DefaultRouter()

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
]