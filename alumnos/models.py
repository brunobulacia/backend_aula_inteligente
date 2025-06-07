from django.db import models
from usuarios.models import Usuario


class Matricula(models.Model):
    alumno = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo_usuario': 'alum'},
        related_name='matriculas'
    )
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.alumno}"


class FichaInscripcion(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)

class Nota(models.Model):
    nota1 = models.FloatField()
    nota2 = models.FloatField()
    nota_final = models.FloatField()

class MateriasInscritasGestion(models.Model):
    ficha = models.ForeignKey(FichaInscripcion, on_delete=models.CASCADE)
    materia = models.ForeignKey('materias.Materia', on_delete=models.CASCADE)
    gestion_curso = models.ForeignKey('materias.GestionCurso', on_delete=models.CASCADE)
    nota = models.ForeignKey(Nota, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('ficha', 'materia', 'gestion_curso')

    def __str__(self):
        return f"{self.ficha} inscrita a {self.materia}-{self.gestion_curso}"


class Participacion(models.Model):
    ficha = models.ForeignKey(FichaInscripcion, on_delete=models.CASCADE)
    materia = models.ForeignKey('materias.Materia', on_delete=models.CASCADE)
    gestion_curso = models.ForeignKey('materias.GestionCurso', on_delete=models.CASCADE)
    fecha = models.DateField()
    descripcion = models.TextField()


class Asistencia(models.Model):
    ficha = models.ForeignKey(FichaInscripcion, on_delete=models.CASCADE)
    materia = models.ForeignKey('materias.Materia', on_delete=models.CASCADE)
    gestion_curso = models.ForeignKey('materias.GestionCurso', on_delete=models.CASCADE)
    fecha = models.DateField()
    asistio = models.BooleanField()
