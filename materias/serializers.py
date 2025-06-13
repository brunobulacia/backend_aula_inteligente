from rest_framework import serializers
from .models import Curso, Materia, Horario, Dia, Dia_Horario, Gestion, MateriaGestionCurso, GestionCurso

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = '__all__'

class GestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gestion
        fields = '__all__'

class GestionCursoSerializer(serializers.ModelSerializer):
    gestion_periodo = serializers.CharField(source='gestion.periodo')
    curso_nombre = serializers.CharField(source='curso.nombre')

    class Meta:
        model = GestionCurso
        fields = ['id', 'gestion_periodo', 'curso_nombre']

    def validate(self, attrs):
        # Buscar la gestión por periodo
        periodo = attrs.get('gestion', {}).get('periodo') or attrs.get('gestion_periodo')
        try:
            gestion = Gestion.objects.get(periodo=periodo)
        except Gestion.DoesNotExist:
            raise serializers.ValidationError({'gestion_periodo': 'No existe una gestión con ese periodo.'})

        # Buscar el curso por nombre
        nombre = attrs.get('curso', {}).get('nombre') or attrs.get('curso_nombre')
        try:
            curso = Curso.objects.get(nombre=nombre)
        except Curso.DoesNotExist:
            raise serializers.ValidationError({'curso_nombre': 'No existe un curso con ese nombre.'})

        attrs['gestion'] = gestion
        attrs['curso'] = curso
        return attrs

    def update(self, instance, validated_data):
        instance.gestion = validated_data.get('gestion', instance.gestion)
        instance.curso = validated_data.get('curso', instance.curso)
        instance.save()
        return instance

class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = '__all__'

class DiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia
        fields = '__all__'

class DiaHorarioSerializer(serializers.ModelSerializer):
    dia = serializers.CharField(source='dia.dia', read_only=True)
    hora_inicio = serializers.TimeField(source='horario.hora_inicio', read_only=True)
    hora_fin = serializers.TimeField(source='horario.hora_fin', read_only=True)

    class Meta:
        model = Dia_Horario
        fields = ['id', 'dia', 'hora_inicio', 'hora_fin']


class MateriaGestionCursoSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='gestion_curso.curso.nombre', read_only=True)
    profesor_nombre = serializers.CharField(source='profesor.nombre', read_only=True)
    gestion_periodo = serializers.CharField(source='gestion_curso.gestion.periodo', read_only=True)
    
    dia_horarios = DiaHorarioSerializer(many=True, read_only=True)
    
    class Meta:
        model = MateriaGestionCurso
        fields = '__all__'
