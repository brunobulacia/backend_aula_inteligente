from django.shortcuts import render
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework import status, viewsets
from django.utils import timezone
from .models import Usuario, Direccion
from alumnos.models import MateriasInscritasGestion
from .serializers import UsuarioSerializer

#admin

@api_view(['POST'])
def register(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user = Usuario.objects.get(email=serializer.data['email'])
        user.save();
        
        token = Token.objects.create(user=user)
        return Response({"token": token.key, "usuario": serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    user = get_object_or_404(Usuario, email=request.data['email'])

    if not user.check_password(request.data['password']):
        return Response({"error": "Contraseña invalida"}, status=status.HTTP_400_BAD_REQUEST)
    user.last_login = timezone.now()
    user.save()
    token, created = Token.objects.get_or_create(user=user)
    serializer = UsuarioSerializer(instance=user)

    return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def obtener_usuarios(request):
    tipo = request.query_params.get('tipo')

    if tipo:
        usuarios = Usuario.objects.filter(tipo_usuario=tipo)
    else:
        usuarios = Usuario.objects.all()
    serializer = UsuarioSerializer(usuarios, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def alumnos_por_gestion(request):
    gestion_id = request.query_params.get('gestion_id')

    if not gestion_id:
        return Response({"error": "Debés enviar el parámetro 'gestion_id'"}, status=400)

    inscritos = MateriasInscritasGestion.objects.filter(gestion_id=gestion_id)
    alumnos = list(set(mi.ficha.matricula.alumno for mi in inscritos))
    serializer = UsuarioSerializer(alumnos, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_fcm_token(request):
    token = request.data.get('fcm_token')
    if not token:
        return Response({'error': 'No se envió ningún token'}, status=400)

    usuario = request.user
    usuario.fcm_token = token
    usuario.save()
    return Response({'mensaje': 'Token guardado correctamente'})
