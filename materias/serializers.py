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
    class Meta:
        model = MateriaGestionCurso
        fields = '__all__'
