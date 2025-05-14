from django.db import models
from alumnos.models import Nota

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
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE)
    dia = models.CharField(max_length=10) 
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        unique_together = ('materia', 'curso', 'gestion')

    def __str__(self):
        return f"{self.materia} - {self.dia} {self.hora_inicio}-{self.hora_fin}"

class MateriaGestionCurso(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE)
    nota = models.ForeignKey(Nota, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('materia', 'curso', 'gestion')

    def __str__(self):
        return f"{self.materia} - {self.curso} - {self.gestion}"
