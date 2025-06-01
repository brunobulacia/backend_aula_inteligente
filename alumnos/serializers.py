from rest_framework import serializers
from usuarios.models import Usuario
from .models import Matricula, FichaInscripcion, Nota, MateriasInscritasGestion
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
    
