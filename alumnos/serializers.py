from rest_framework import serializers
from usuarios.models import Usuario
from .models import Matricula, FichaInscripcion, Nota, Asistencia, MateriasInscritasGestion, Participacion
from materias.models import Materia, GestionCurso

class FichaInscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FichaInscripcion
        fields = '__all__'

class InscripcionSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField()
    materias = serializers.ListField(child=serializers.DictField(), write_only=True)

    def validate_alumno_id(self, value):
        try:
            Usuario.objects.get(id=value, tipo_usuario='alum')
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Alumno no encontrado.")
        return value

    def create(self, validated_data):
        alumno_id=validated_data['alumno_id']
        materias_data = validated_data['materias']

        alumno = Usuario.objects.get(id=alumno_id)
        matricula, _ = Matricula.objects.get_or_create(alumno=alumno)
        ficha, _ = FichaInscripcion.objects.get_or_create(matricula=matricula)

        for item in materias_data:
            materia = Materia.objects.get(id=item['materia_id'])
            gestion_curso = GestionCurso.objects.get(id=item['gestion_curso_id'])
            nota = Nota.objects.create(ser=0, saber=0, hacer=0, decidir=0, nota_final=0)

            MateriasInscritasGestion.objects.get_or_create(
                ficha=ficha,
                materia=materia,
                gestion_curso=gestion_curso,
                defaults={'nota': nota}
            ) 

        return ficha
    
class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = ['ser','saber','hacer','decidir','nota_final']

class MateriasInscritasGestionSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='gestion_curso.curso.nombre',read_only=True)
    periodo = serializers.CharField(source='gestion_curso.gestion.periodo', read_only=True)
    nota = NotaSerializer(read_only=True)

    class Meta:
        model = MateriasInscritasGestion
        fields = ['materia_nombre', 'curso_nombre', 'periodo', 'nota']


#calificar para el profesor 
class CalificacionSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField()
    materia_id = serializers.IntegerField()
    gestion_curso = serializers.IntegerField();
    ser = serializers.FloatField(required=False)
    saber = serializers.FloatField(required=False)
    hacer = serializers.FloatField(required=False)
    decidir = serializers.FloatField(required=False)
    nota_final = serializers.FloatField(required=False)

    def validate(self, data):
        if not any([data.get('ser'), data.get('saber'), data.get('hacer'), data.get('decidir'), data.get('nota_final')]):
            raise serializers.ValidationError("Debés enviar al menos una nota.")
        return data

class AsistenciaSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField()
    materia_id = serializers.IntegerField()
    gestion_curso_id = serializers.IntegerField()
    fecha = serializers.DateField()
    asistio = serializers.BooleanField()

class ParticipacionSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField()
    materia_id = serializers.IntegerField()
    gestion_curso_id = serializers.IntegerField()
    fecha = serializers.DateField()
    descripcion = serializers.CharField()