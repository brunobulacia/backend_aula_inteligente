from django.shortcuts import render
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAdminUser, BasePermission, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FichaInscripcion, MateriasInscritasGestion, Nota, Asistencia, Participacion, Matricula
from materias.models import MateriaGestionCurso
from usuarios.models import Usuario
from .serializers import FichaInscripcionSerializer, InscripcionSerializer, MateriasInscritasGestionSerializer, NotaSerializer, AsistenciaSerializer, ParticipacionSerializer, CalificacionSerializer
from usuarios.serializers import UsuarioSerializer
from materias.serializers import MateriaGestionCursoSerializer

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
    
    #se le manda la ficha de inscripcion en el endpoint: GET /alumnos/fichas/1/materias-inscritas/
    @action(detail=True, methods=['get'], url_path='materias-inscritas')
    def materias_inscritas(self, request, pk=None):
        ficha = self.get_object()
        materias = MateriasInscritasGestion.objects.filter(ficha=ficha)
        serializer = MateriasInscritasGestionSerializer(materias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
 
class NotaViewSet(viewsets.ModelViewSet):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer
    permission_classes = [IsAdminUser]

#permisos para solo profesores
class EsProfesor(BasePermission):
    def has_permission(self, request,view):
        return request.user.is_authenticated and request.user.tipo_usuario == 'prof'
    
    def has_object_permission(self, request, view, obj):
        return request.user == obj.profesor

#funciones para los profesores
class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    permission_classes = [IsAuthenticated, EsProfesor]

    def get_queryset(self):
        profe = self.request.user
        materias_dictadas = MateriaGestionCurso.objects.filter(profesor=profe)
        return Asistencia.objects.filter(
            materia__in=[m.materia for m in materias_dictadas],
            curso__in=[m.curso for m in materias_dictadas],
            gestion__in=[m.gestion for m in materias_dictadas]
        )
    
    def perform_create(self, serializer):
        data = serializer.validated_data
        profe = self.request.user
        permitido = MateriaGestionCurso.objects.filter(
            profesor=profe,
            materia=data['materia'],
            curso=data['curso'],
            gestion=data['gestion']
        ).exists()
        if not permitido:
            raise serializers.ValidationError("No está autorizado para registrar asistencia en esta materia.")
        serializer.save()

class ParticipacionViewSet(viewsets.ModelViewSet):
    queryset = Participacion.objects.all()
    serializer_class = ParticipacionSerializer
    permission_classes = [IsAuthenticated, EsProfesor]

    def get_queryset(self):
        profe = self.request.user
        materias_dictadas = MateriaGestionCurso.objects.filter(profesor=profe)
        return Participacion.objects.filter(
            materia__in=[m.materia for m in materias_dictadas],
            curso__in=[m.curso for m in materias_dictadas],
            gestion__in=[m.gestion for m in materias_dictadas]
        )

    def perform_create(self, serializer):
        data = serializer.validated_data
        profe = self.request.user
        permitido = MateriaGestionCurso.objects.filter(
            profesor=profe,
            materia=data['materia'],
            curso=data['curso'],
            gestion=data['gestion']
        ).exists()
        if not permitido:
            raise serializers.ValidationError("No está autorizado para registrar participación en esta materia.")
        serializer.save()

#vistas restringidas para profesores
class ProfesorViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, EsProfesor]

    @action(detail=True, methods=['get'], url_path='alumnos')
    def ver_alumnos_inscritos(self, request, pk=None):
        profe = request.user

        try:
            mgc = MateriaGestionCurso.objects.get(pk=pk, profesor=profe)
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No tenés acceso a esta asignación"}, status=403)

        materias_inscritas = MateriasInscritasGestion.objects.filter(
            materia=mgc.materia,
            gestion_curso=mgc.gestion_curso
        )

        alumnos = [mi.ficha.matricula.alumno for mi in materias_inscritas]
        serializer = UsuarioSerializer(alumnos, many=True)

        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='mis-materias')
    def mis_materias(self, request):
        profe = request.user
        asignaciones = MateriaGestionCurso.objects.filter(profesor=profe)
        serializer = MateriaGestionCursoSerializer(asignaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='calificar')
    def calificar(self, request):
        serializer = CalificacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        profe = request.user

        try:
            # Validar que el profe tenga esa asignación
            asignacion = MateriaGestionCurso.objects.get(
                profesor=profe,
                materia_id=data['materia_id'],
                gestion_curso_id=data['gestion_curso'],
            )
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No estás asignado a esa materia."}, status=403)

        try:
            alumno = Usuario.objects.get(id=data['alumno_id'], tipo_usuario='alum')
            matricula = Matricula.objects.get(alumno=alumno)
            ficha = FichaInscripcion.objects.get(matricula=matricula)
            materia_inscrita = MateriasInscritasGestion.objects.get(
                ficha=ficha,
                materia_id=data['materia_id'],
                gestion_curso_id=data['gestion_curso']
            )
        except Exception as e:
            return Response({"error": "No se encontró la inscripción del alumno."}, status=404)

        nota = materia_inscrita.nota
        if data.get('ser') is not None:
            nota.ser = data['ser']
        if data.get('saber') is not None:
            nota.saber = data['saber']
        if data.get('hacer') is not None:
            nota.hacer = data['hacer']
        if data.get('decidir') is not None:
            nota.decidir = data['decidir']
        if data.get('nota_final') is not None:
            nota.nota_final = data['nota_final']
        nota.save()

        return Response({"mensaje": "Nota actualizada correctamente."})
    
    @action(detail=False, methods=['POST'], url_path='registrar-asistencia')
    def registrar_asistencia(self, request):
        serializer = AsistenciaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data
        profe = request.user
        try:
            MateriaGestionCurso.objects.get(
                profesor=profe,
                materia_id=data['materia_id'],
                gestion_curso_id=data['gestion_curso_id'],
            )
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No estás asignado a esa materia."}, status=403)
        
        try:
            alumno = Usuario.objects.get(id=data['alumno_id'], tipo_usuario='alum')
            matricula = Matricula.objects.get(alumno=alumno)
            ficha = FichaInscripcion.objects.get(matricula=matricula)
        except Exception:
            return Response({"error": "Alumno no encontrado o no inscrito."}, status=404)

        Asistencia.objects.create(
            ficha=ficha,
            materia_id=data['materia_id'],
            gestion_curso_id=data['gestion_curso_id'],
            fecha=data['fecha'],
            asistio=data['asistio']
        )
        return Response({"mensaje": "Asistencia registrada correctamente."})
    
    @action(detail=False, methods=['post'], url_path='registrar-participacion')
    def registrar_participacion(self, request):
        serializer = ParticipacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        profe = request.user

        try:
            MateriaGestionCurso.objects.get(
                profesor=profe,
                materia_id=data['materia_id'],
                gestion_curso_id=data['gestion_curso_id'],
            )
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No estás asignado a esa materia."}, status=403)

        try:
            alumno = Usuario.objects.get(id=data['alumno_id'], tipo_usuario='alum')
            matricula = Matricula.objects.get(alumno=alumno)
            ficha = FichaInscripcion.objects.get(matricula=matricula)
        except Exception:
            return Response({"error": "Alumno no encontrado o no inscrito."}, status=404)

        Participacion.objects.create(
            ficha=ficha,
            materia_id=data['materia_id'],
            gestion_curso_id=data['gestion_curso_id'],
            fecha=data['fecha'],
            descripcion=data['descripcion']
        )

        return Response({"mensaje": "Participación registrada correctamente."})
    
    @action(detail=False, methods=['get'], url_path='ver-asistencias')
    def ver_asistencias(self, request):
        profe = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        if not materia_id or not gestion_curso_id:
            return Response({"error": "Faltan parámetros requeridos"}, status=400)

        try:
            asignacion = MateriaGestionCurso.objects.get(
                profesor=profe,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No estás asignado a esa materia."}, status=403)

        asistencias = Asistencia.objects.filter(
            materia_id=materia_id,
            gestion_curso_id=gestion_curso_id
        ).select_related('ficha__matricula__alumno')

        resultado = [
            {
                "alumno": f"{a.ficha.matricula.alumno.nombre} {a.ficha.matricula.alumno.apellidos}",
                "fecha": a.fecha,
                "asistio": a.asistio
            }
            for a in asistencias
        ]

        return Response(resultado, status=200)
    
    @action(detail=False, methods=['get'], url_path='ver-participaciones')
    def ver_participaciones(self, request):
        profe = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        if not materia_id or not gestion_curso_id:
            return Response({"error": "Faltan parámetros requeridos"}, status=400)

        try:
            asignacion = MateriaGestionCurso.objects.get(
                profesor=profe,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )
        except MateriaGestionCurso.DoesNotExist:
            return Response({"error": "No estás asignado a esa materia."}, status=403)

        participaciones = Participacion.objects.filter(
            materia_id=materia_id,
            gestion_curso_id=gestion_curso_id
        ).select_related('ficha__matricula__alumno')

        resultado = [
            {
                "alumno": f"{p.ficha.matricula.alumno.nombre} {p.ficha.matricula.alumno.apellidos}",
                "fecha": p.fecha,
                "descripcion": p.descripcion
            }
            for p in participaciones
        ]

        return Response(resultado, status=200)
    
    @action(detail=False, methods=['get'], url_path='ver-nota')
    def ver_nota(self, request):
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        if not (alumno_id and materia_id and gestion_curso_id):
            return Response({"error": "Faltan parámetros requeridos"}, status=400)

        try:
            alumno = Usuario.objects.get(id=alumno_id, tipo_usuario='alum')
            matricula = Matricula.objects.get(alumno=alumno)
            ficha = FichaInscripcion.objects.get(matricula=matricula)
            materia_inscrita = MateriasInscritasGestion.objects.get(
                ficha=ficha,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )

            nota = materia_inscrita.nota
            data = {
                "ser": nota.ser,
                "saber": nota.saber,
                "hacer": nota.hacer,
                "decidir": nota.decidir,
                "nota_final": nota.nota_final
            }
            return Response(data, status=200)

        except Usuario.DoesNotExist:
            return Response({"error": "Alumno no encontrado."}, status=404)
        except MateriasInscritasGestion.DoesNotExist:
            return Response({"error": "El alumno no está inscrito en esa materia."}, status=404)
        except Exception as e:
            return Response({"error": "Error inesperado."}, status=500)


#vistas para alumnos
class EsAlumno(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo_usuario == 'alum'
    
class AlumnoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, EsAlumno]

    @action(detail=False, methods=['get'], url_path='mis-materias')
    def mis_materias(self, request):
        alumno = request.user
        try:
            ficha = FichaInscripcion.objects.get(matricula__alumno=alumno)
            materias = MateriasInscritasGestion.objects.filter(ficha=ficha)
            serializer = MateriasInscritasGestionSerializer(materias, many=True)
            return Response(serializer.data)
        except:
            return Response({"error": "No estás inscrito en ninguna materia."}, status=404)

    @action(detail=False, methods=['get'], url_path='mis-notas')
    def ver_nota_materia(self, request):
        alumno = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        try:
            ficha = FichaInscripcion.objects.get(matricula__alumno=alumno)
            materia_inscrita = MateriasInscritasGestion.objects.get(
                ficha=ficha,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )
            nota = materia_inscrita.nota
            return Response({
            "ser": nota.ser,
            "saber": nota.saber,
            "hacer": nota.hacer,
            "decidir": nota.decidir,
            "nota_final": nota.nota_final
            })
        except:
            return Response({"error": "No se encontró la nota para esta materia."}, status=404)

    @action(detail=False, methods=['get'], url_path='mis-asistencias')
    def ver_asistencias(self, request):
        alumno = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        try:
            ficha = FichaInscripcion.objects.get(matricula__alumno=alumno)
            asistencias = Asistencia.objects.filter(
                ficha=ficha,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )
            data = [
                {"fecha": a.fecha, "asistio": a.asistio}
                for a in asistencias
            ]
            return Response(data)
        except:
            return Response({"error": "No se encontraron asistencias."}, status=404)

    @action(detail=False, methods=['get'], url_path='mis-participaciones')
    def ver_participaciones(self, request):
        alumno = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        try:
            ficha = FichaInscripcion.objects.get(matricula__alumno=alumno)
            participaciones = Participacion.objects.filter(
                ficha=ficha,
                materia_id=materia_id,
                gestion_curso_id=gestion_curso_id
            )
            data = [
                {"fecha": p.fecha, "descripcion": p.descripcion}
                for p in participaciones
            ]
            return Response(data)
        except:
            return Response({"error": "No se encontraron participaciones."}, status=404)
