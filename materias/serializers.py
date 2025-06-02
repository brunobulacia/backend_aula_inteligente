from rest_framework import serializers
from .models import Curso, Materia, Horario, Dia, Dia_Horario, Gestion, MateriaGestionCurso

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


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = '__all__'

class DiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia
        fields = '__all__'

class DiaHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia_Horario
        fields = '__all__'

class MateriaGestionCursoSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    profesor_nombre = serializers.CharField(source='profesor.nombre', read_only=True)
    gestion_periodo = serializers.CharField(source='gestion.periodo', read_only=True)
    
    dia_horarios = serializers.PrimaryKeyRelatedField(
        queryset=Dia_Horario.objects.all(), many=True
    )
    
    class Meta:
        model = MateriaGestionCurso
        fields = '__all__'
