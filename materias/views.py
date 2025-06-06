from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import Curso,Materia, Gestion, Horario, Dia, Dia_Horario, MateriaGestionCurso, GestionCurso
from .serializers import (
    CursoSerializer, MateriaSerializer, GestionSerializer,
    HorarioSerializer, DiaSerializer, DiaHorarioSerializer,
    MateriaGestionCursoSerializer, GestionCursoSerializer
)


#funciones del admin
class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [IsAdminUser]

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [IsAdminUser]

class GestionViewSet(viewsets.ModelViewSet):
    queryset = Gestion.objects.all()
    serializer_class = GestionSerializer
    permission_classes = [IsAdminUser]

class GestionCursoViewSet(viewsets.ModelViewSet):
    queryset = GestionCurso.objects.all()
    serializer_class = GestionCursoSerializer
    permission_classes = [IsAdminUser]

class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAdminUser]

class DiaViewSet(viewsets.ModelViewSet):
    queryset = Dia.objects.all()
    serializer_class = DiaSerializer
    permission_classes = [IsAdminUser]

class DiaHorarioViewSet(viewsets.ModelViewSet):
    queryset = Dia_Horario.objects.all()
    serializer_class = DiaHorarioSerializer
    permission_classes = [IsAdminUser]

class MateriaGestionCursoViewSet(viewsets.ModelViewSet):
    queryset = MateriaGestionCurso.objects.all()
    serializer_class = MateriaGestionCursoSerializer
    permission_classes = [IsAdminUser]