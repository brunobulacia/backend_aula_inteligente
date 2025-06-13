import base64
import json
from datetime import datetime, date
from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAdminUser, BasePermission, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FichaInscripcion, MateriasInscritasGestion, Nota, Asistencia, Participacion, Matricula
from materias.models import MateriaGestionCurso
from usuarios.models import Usuario, PadreAlumno
from .serializers import FichaInscripcionSerializer,AsistenciaQrSerializer,InscripcionSerializer, MateriasInscritasGestionSerializer, NotaSerializer, AsistenciaSerializer, ParticipacionSerializer, CalificacionSerializer, PrediccionRendimientoSerializer
from usuarios.serializers import UsuarioSerializer
from materias.serializers import MateriaGestionCursoSerializer
from .ml.ml_utils import entrenar_modelo_rendimiento, predecir_rendimiento_grupal, predecir_rendimiento_individual
from .utils.fcm import enviar_notificacion_push


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
        gestion_id = request.query_params.get('gestion_id')

        if not gestion_id:
            return Response({"error": "Debés enviar el parámetro 'gestion_id'"}, status=400)

        asignaciones = MateriaGestionCurso.objects.filter(
            profesor=profe,
            gestion_curso__gestion_id=gestion_id
        )
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
            ficha = FichaInscripcion.objects.filter(
                matricula=matricula,
                materiasinscritasgestion__gestion_curso_id=data['gestion_curso'],
                materiasinscritasgestion__materia_id=data['materia_id']
            ).first()

            if not ficha:
                return Response({"error": "No se encontró la ficha del alumno para esa materia y gestión."}, status=404)

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
        nota.nota_final = (nota.ser or 0) + (nota.saber or 0) + (nota.hacer or 0) + (nota.decidir or 0)
        nota.save()

        # 🧠 Comparar contra la predicción
        try:
            from .ml.ml_utils import predecir_rendimiento_individual

            resultados = predecir_rendimiento_individual(alumno, gestion_id=asignacion.gestion_curso.gestion.id)
            resultado_materia = next((r for r in resultados if r['materia_id'] == data['materia_id']), None)

            if resultado_materia:
                nota_real = nota.nota_final
                nota_predicha = resultado_materia.get('nota_final_predicha', 0)
                materia_nombre = resultado_materia.get('materia', 'Materia')

                if nota_real < nota_predicha:
                    titulo = "📉 Rendimiento bajo"
                    cuerpo = f"En {materia_nombre}, la nota real del alumno fue {nota_real:.1f}, menor a la esperada ({nota_predicha:.1f})."

                    # ➤ Notificar al alumno
                    if alumno.fcm_token:
                        enviar_notificacion_push(alumno.fcm_token, titulo, cuerpo)

                    # ➤ Notificar a los padres
                    padres = alumno.padres.all()
                    for p in alumno.padres.all():  # p es un objeto PadreAlumno
                        padre = p.padre
                        if padre.fcm_token:
                            enviar_notificacion_push(padre.fcm_token, titulo, cuerpo)

        except Exception as e:
            print(f"⚠️ Error en predicción o envío de notificación: {e}")

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
            fichas = FichaInscripcion.objects.filter(matricula=matricula)
            ficha = None
            for f in fichas:
                if MateriasInscritasGestion.objects.filter(ficha=f, gestion_curso_id=data['gestion_curso_id'], materia_id=data['materia_id']).exists():
                    ficha = f
                    break
            if not ficha:
                return Response({"error": "Alumno no está inscrito en esa materia en esta gestión."}, status=404)
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
            fichas = FichaInscripcion.objects.filter(matricula=matricula)
            ficha = None
            for f in fichas:
                if MateriasInscritasGestion.objects.filter(ficha=f, gestion_curso_id=data['gestion_curso_id'], materia_id=data['materia_id']).exists():
                    ficha = f
                    break
            if not ficha:
                return Response({"error": "Alumno no está inscrito en esa materia en esta gestión."}, status=404)
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

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        profe = request.user
        materias = MateriaGestionCurso.objects.filter(profesor=profe)

        total_materias = materias.count()

        total_alumnos = 0
        gestion_curso_ids = []
        for m in materias:
            gestion_curso_ids.append(m.gestion_curso.id)
            inscritos = MateriasInscritasGestion.objects.filter(gestion_curso=m.gestion_curso).count()
            total_alumnos += inscritos

        hoy = timezone.now().date()
        asistencias_hoy = Asistencia.objects.filter(gestion_curso_id__in=gestion_curso_ids, fecha=hoy).count()
        participaciones_total = Participacion.objects.filter(gestion_curso_id__in=gestion_curso_ids).count()


        return Response({
            "total_materias": total_materias,
            "total_alumnos": total_alumnos,
            "asistencias_hoy": asistencias_hoy,
            "participaciones_total": participaciones_total
        })

    @action(detail=False, methods=['get'], url_path='entrenar-modelo')
    def entrenar_modelo(self, request):
        try:
            ruta = entrenar_modelo_rendimiento()
            return Response({"mensaje": "Modelo entrenado y guardado exitosamente", "ruta": ruta})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['get'], url_path='predecir-rendimiento')
    def predecir_rendimiento(self, request):
        profesor = request.user
        gestion_id = request.query_params.get('gestion_id')
        curso_id = request.query_params.get('curso_id')

        resultados = predecir_rendimiento_grupal(
            profesor,
            gestion_id=int(gestion_id) if gestion_id else None,
            curso_id=int(curso_id) if curso_id else None
        )   
        return Response(resultados)

    
    @action(detail=False, methods=['get'], url_path='generar-qr-asistencia')
    def generar_qr_asistencia(self, request):
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        if not materia_id or not gestion_curso_id:
            return Response({'error': 'Faltan parámetros'}, status=400)

        payload = {
            'materia_id': int(materia_id),
            'gestion_curso_id': int(gestion_curso_id),
            'fecha': str(date.today())
        }

        qr_string = base64.b64encode(json.dumps(payload).encode()).decode()

        return Response({'qr_data': qr_string})



    


#vistas para alumnos
class EsAlumno(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo_usuario == 'alum'
    
class AlumnoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, EsAlumno]

    @action(detail=False, methods=['get'], url_path='mis-materias')
    def mis_materias(self, request):
        alumno = request.user
        gestion_id = request.query_params.get('gestion_id')

        if not gestion_id:
            return Response({"error": "Debés enviar el parámetro 'gestion_id'"}, status=400)

        try:
            ficha = self.obtener_ficha_por_gestion(alumno, gestion_id)
            if not ficha:
                return Response({"error": "No estás inscrito en ninguna materia para esa gestión."}, status=404)

            materias = MateriasInscritasGestion.objects.filter(
                ficha=ficha,
                gestion_curso__gestion_id=gestion_id
            )
            serializer = MateriasInscritasGestionSerializer(materias, many=True)
            return Response(serializer.data)
        except FichaInscripcion.DoesNotExist:
            return Response({"error": "No estás inscrito en ninguna materia."}, status=404)


    @action(detail=False, methods=['get'], url_path='mis-notas')
    def ver_nota_materia(self, request):
        alumno = request.user
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')

        try:
            ficha = self.obtener_ficha_por_gestion(alumno, gestion_curso_id)
            if not ficha:
                return Response({"error": "No se encontró ficha para esa gestión."}, status=404)

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
            ficha = self.obtener_ficha_por_gestion(alumno, gestion_curso_id)
            if not ficha:
                return Response({"error": "No se encontró ficha para esa gestión."}, status=404)

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
            ficha = self.obtener_ficha_por_gestion(alumno, gestion_curso_id)
            if not ficha:
                return Response({"error": "No se encontró ficha para esa gestión."}, status=404)

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
        
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        alumno = request.user
        gestion_id = request.query_params.get('gestion_id')
        if not gestion_id:
            return Response({"error": "Debés enviar el parámetro 'gestion_id'"}, status=400)
        try:
            ficha = self.obtener_ficha_por_gestion(alumno, gestion_id)
            if not ficha:
                return Response({"error": "No tenés ficha para esa gestión."}, status=404)
            materias_inscritas = MateriasInscritasGestion.objects.filter(
                ficha=ficha,
                gestion_curso__gestion_id=gestion_id
            )
            total_materias = materias_inscritas.count()

            total_participaciones = Participacion.objects.filter(ficha=ficha).count()
            total_asistencias = Asistencia.objects.filter(ficha=ficha).count()

            promedio_general = 0
            suma_notas = 0
            total_con_notas = 0

            for ins in materias_inscritas:
                if ins.nota:
                    n = ins.nota
                    promedio = (n.ser + n.saber + n.hacer + n.decidir + n.nota_final) / 5
                    suma_notas += promedio
                    total_con_notas += 1

            if total_con_notas > 0:
                promedio_general = round(suma_notas / total_con_notas, 2)

            return Response({
                "total_materias": total_materias,
                "total_participaciones": total_participaciones,
                "total_asistencias": total_asistencias,
                "promedio_general": promedio_general
            })

        except FichaInscripcion.DoesNotExist:
            return Response({"error": "No tenés ficha de inscripción."}, status=404)
    
    @action(detail=False, methods=['get'], url_path='predecir-rendimiento')
    def predecir_rendimiento(self, request):
        alumno = request.user
        gestion_id = request.query_params.get('gestion_id')

        if not gestion_id:
            return Response({"error": "Debés enviar el parámetro 'gestion_id'"}, status=400)

        resultados = predecir_rendimiento_individual(alumno, gestion_id=int(gestion_id))
        return Response(resultados)
    
    def obtener_ficha_por_gestion(self, alumno, gestion_id):
        try:
            fichas = FichaInscripcion.objects.filter(matricula__alumno=alumno)
            for ficha in fichas:
                if MateriasInscritasGestion.objects.filter(ficha=ficha, gestion_curso__gestion_id=gestion_id).exists():
                    return ficha
            return None
        except:
            return None

    
    @action(detail=False, methods=['post'], url_path='registrar-asistencia-qr')
    def registrar_asistencia_qr(self, request):
        user = request.user
        qr_data = request.data.get('qr_data')

        if not qr_data:
            return Response({'error': 'Falta el campo qr_data'}, status=400)

        try:
            decoded = json.loads(base64.b64decode(qr_data).decode())
            materia_id = decoded['materia_id']
            gestion_curso_id = decoded['gestion_curso_id']
            fecha = decoded['fecha']
        except Exception as e:
            return Response({'error': 'QR inválido'}, status=400)

        
        fichas = FichaInscripcion.objects.filter(matricula__alumno=user)
        ficha = None
        for f in fichas:
            if MateriasInscritasGestion.objects.filter(ficha=f, gestion_curso_id=gestion_curso_id, materia_id=materia_id).exists():
                ficha = f
                break

        if not ficha:
            return Response({'error': 'No tenés ficha válida para esta materia y gestión'}, status=404)

        asistencia_data = {
            'ficha': ficha.id,
            'materia_id': materia_id,
            'gestion_curso_id': gestion_curso_id,
            'fecha': fecha,
            'asistio': True
        }

        serializer = AsistenciaQrSerializer(data=asistencia_data)
        if serializer.is_valid():
            return Response({'mensaje': 'Asistencia registrada'})
        return Response(serializer.errors, status=400)


class EsPadre(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo_usuario == 'padre'
    

class PadreViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, EsPadre]

    @action(detail=False, methods=['get'], url_path='mis-hijos')
    def mis_hijos(self, request):
        padre = request.user
        hijos = Usuario.objects.filter(padres__padre=padre)
        serializer = UsuarioSerializer(hijos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='ver-materias')
    def ver_materias(self, request):
        alumno_id = request.query_params.get('alumno_id')
        gestion_id = request.query_params.get('gestion_id')
        if not alumno_id or not gestion_id:
            return Response({"error": "Faltan parámetros"}, status=400)

        try:
            ficha = self.obtener_ficha_por_gestion(alumno_id, gestion_id)
            if not ficha:
                return Response({"error": "No se encontró la ficha de inscripción para esa gestión."}, status=404)

            materias = MateriasInscritasGestion.objects.filter(ficha=ficha, gestion_curso__gestion_id=gestion_id)
            serializer = MateriasInscritasGestionSerializer(materias, many=True)
            return Response(serializer.data)
        except:
            return Response({"error": "No se encontraron materias"}, status=404)

    @action(detail=False, methods=['get'], url_path='ver-nota')
    def ver_nota(self, request):
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')
        gestion_id = request.query_params.get('gestion_id')
        ficha = self.obtener_ficha_por_gestion(alumno_id, gestion_id)
        if not ficha:
            return Response({"error": "No se encontró la ficha de inscripción para esa gestión."}, status=404)
        try:

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
            return Response({"error": "No se encontró la nota"}, status=404)

    @action(detail=False, methods=['get'], url_path='ver-asistencias')
    def ver_asistencias(self, request):
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')
        gestion_id = request.query_params.get('gestion_id')

        try:
            ficha = self.obtener_ficha_por_gestion(alumno_id, gestion_id)
            if not ficha:
                return Response({"error": "No se encontró la ficha de inscripción para esa gestión."}, status=404)

            asistencias = Asistencia.objects.filter(ficha=ficha, materia_id=materia_id, gestion_curso_id=gestion_curso_id)
            data = [{"fecha": a.fecha, "asistio": a.asistio} for a in asistencias]
            return Response(data)
        except:
            return Response({"error": "No se encontraron asistencias"}, status=404)

    @action(detail=False, methods=['get'], url_path='ver-participaciones')
    def ver_participaciones(self, request):
        alumno_id = request.query_params.get('alumno_id')
        materia_id = request.query_params.get('materia_id')
        gestion_curso_id = request.query_params.get('gestion_curso_id')
        gestion_id = request.query_params.get('gestion_id')

        try:
            ficha = self.obtener_ficha_por_gestion(alumno_id, gestion_id)
            if not ficha:
                return Response({"error": "No se encontró la ficha de inscripción para esa gestión."}, status=404)

            participaciones = Participacion.objects.filter(ficha=ficha, materia_id=materia_id, gestion_curso_id=gestion_curso_id)
            data = [{"fecha": p.fecha, "descripcion": p.descripcion} for p in participaciones]
            return Response(data)
        except:
            return Response({"error": "No se encontraron participaciones"}, status=404)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        alumno_id = request.query_params.get('alumno_id')
        gestion_id = request.query_params.get('gestion_id')

        if not alumno_id or not gestion_id:
            return Response({"error": "Faltan parámetros"}, status=400)

        ficha = self.obtener_ficha_por_gestion(alumno_id, gestion_id)
        if not ficha:
            return Response({"error": "No se encontró la ficha de inscripción para esa gestión."}, status=404)

        total_materias = MateriasInscritasGestion.objects.filter(ficha=ficha).count()
        total_asistencias = Asistencia.objects.filter(ficha=ficha).count()
        total_participaciones = Participacion.objects.filter(ficha=ficha).count()

        materias_inscritas = MateriasInscritasGestion.objects.filter(ficha=ficha)
        suma = 0
        n_materias = 0
        for ins in materias_inscritas:
            if ins.nota:
                n = ins.nota
                suma += (n.ser + n.saber + n.hacer + n.decidir + n.nota_final) / 5
                n_materias += 1

        promedio_general = round(suma / n_materias, 2) if n_materias > 0 else 0

        return Response({
            "total_materias": total_materias,
            "total_asistencias": total_asistencias,
            "total_participaciones": total_participaciones,
            "promedio_general": promedio_general
        })

    @action(detail=False, methods=['get'], url_path='predecir-rendimiento')
    def predecir_rendimiento(self, request):
        padre = request.user
        alumno_id = request.query_params.get('alumno_id')
        gestion_id = request.query_params.get('gestion_id')

        if not alumno_id or not gestion_id:
            return Response({"error": "Faltan parámetros requeridos"}, status=400)

        try:
            alumno = Usuario.objects.get(id=alumno_id, tipo_usuario='alum')
            if not PadreAlumno.objects.filter(padre=padre, alumno=alumno).exists():
                return Response({"error": "Este alumno no está vinculado a tu cuenta"}, status=403)

            resultados = predecir_rendimiento_individual(alumno, gestion_id=int(gestion_id))
            return Response(resultados)

        except Usuario.DoesNotExist:
            return Response({"error": "Alumno no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=500)

    def obtener_ficha_por_gestion(self, alumno_id, gestion_id):
        try:
            return FichaInscripcion.objects.filter(
                matricula__alumno_id=alumno_id,
                materiasinscritasgestion__gestion_curso__gestion_id=gestion_id
            ).distinct().first()
        except:
            return None

    @action(detail=False, methods=['get'], url_path='predecir-rendimiento')
    def predecir_rendimiento(self, request):
        padre = request.user
        alumno_id = request.query_params.get('alumno_id')
        gestion_id = request.query_params.get('gestion_id')

        if not alumno_id or not gestion_id:
            return Response({"error": "Faltan parámetros requeridos"}, status=400)

        try:
            alumno = Usuario.objects.get(id=alumno_id, tipo_usuario='alum')
            # Verificar si es hijo del padre actual
            if not PadreAlumno.objects.filter(padre=padre, alumno=alumno).exists():
                return Response({"error": "Este alumno no está vinculado a tu cuenta"}, status=403)

            resultados = predecir_rendimiento_individual(alumno, gestion_id=int(gestion_id))
            return Response(resultados)

        except Usuario.DoesNotExist:
            return Response({"error": "Alumno no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=500)
        
    def obtener_ficha_por_gestion(self, alumno_id, gestion_id):
        try:
            return FichaInscripcion.objects.filter(
                matricula__alumno_id=alumno_id,
                materiasinscritasgestion__gestion_curso__gestion_id=gestion_id
            ).distinct().first()
        except:
         return None




