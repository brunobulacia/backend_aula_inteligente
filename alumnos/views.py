from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser 
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FichaInscripcion
from .serializers import FichaInscripcionSerializer, InscripcionSerializer

class FichaInscripcionViewSet(viewsets.ModelViewSet):
    queryset = FichaInscripcion.objects.all()
    serializer_class = FichaInscripcionSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['POST'], url_path='inscribir-alumno')
    def inscribir_alumno(self, request):
        serializer = InscripcionSerializer(data=request.data)
        if serializer.is_valid():
            ficha = serializer.save()
            return Response({'mensaje': 'Inscripción exitosa'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 