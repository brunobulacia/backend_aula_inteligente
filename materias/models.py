from django.db import models
from usuarios.models import Usuario


class Materia(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre 
    

class Gestion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.periodo} - {self.curso}"


class Horario(models.Model):
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.hora_inicio}-{self.hora_fin}"

class Dia(models.Model):
    dia = models.CharField(max_length=15)

    def __str__(self):
        return self.dia
    
class Dia_Horario(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE)
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('dia', 'horario')

    def __str__(self):
        return f"{self.dia} - {self.horario}"


class MateriaGestionCurso(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE)
    dia_horarios = models.ManyToManyField(Dia_Horario, blank=True)
    profesor = models.ForeignKey(Usuario, on_delete=models.CASCADE,limit_choices_to={'tipo_usuario': 'prof'})

    class Meta:
        unique_together = ('materia', 'curso', 'gestion')

    def __str__(self):
        return f"{self.materia} - {self.curso} - {self.gestion}"
