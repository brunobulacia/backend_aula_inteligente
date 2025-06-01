from rest_framework import serializers
from usuarios.models import Usuario
from .models import Matricula, FichaInscripcion, Nota, Asistencia, MateriasInscritasGestion, Participacion
from materias.models import Materia, Curso, Gestion

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
            curso = Curso.objects.get(id=item['curso_id'])
            gestion = Gestion.objects.get(id=item['gestion_id'])
            nota = Nota.objects.create(nota1=0, nota2=0, nota_final=0)

            MateriasInscritasGestion.objects.get_or_create(
                ficha=ficha,
                materia=materia,
                curso=curso,
                gestion=gestion,
                defaults={'nota': nota}
            ) 

        return ficha
    
class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = ['nota1','nota2','nota_final']

class MateriasInscritasGestionSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre',read_only=True)
    periodo = serializers.CharField(source='gestion.periodo', read_only=True)
    nota = NotaSerializer(read_only=True)

    class Meta:
        model = MateriasInscritasGestion
        fields = ['materia_nombre', 'curso_nombre', 'periodo', 'nota']

class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = '__all__'

class ParticipacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacion
        fields = '__all__'

#calificar para el profesor 
class CalificacionSerializer(serializers.Serializer):
    alumno_id = serializers.IntegerField()
    materia_id = serializers.IntegerField()
    curso_id = serializers.IntegerField()
    gestion_id = serializers.IntegerField()
    nota1 = serializers.FloatField(required=False)
    nota2 = serializers.FloatField(required=False)
    nota_final = serializers.FloatField(required=False)

    def validate(self, data):
        if not any([data.get('nota1'), data.get('nota2'), data.get('nota_final')]):
            raise serializers.ValidationError("Debés enviar al menos una nota.")
        return data