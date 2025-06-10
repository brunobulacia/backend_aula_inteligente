from django.db import models
from usuarios.models import Usuario


class Matricula(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False, unique=True)
    alumno = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo_usuario': 'alum'},
        related_name='matriculas'
    )
    fecha = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            ultimo = Matricula.objects.order_by('-id').first()
            if ultimo:
                self.id = ultimo.id + 1
            else:
                self.id = 219000000  # primer ID con 9 dígitos
        super().save(*args, **kwargs)


class FichaInscripcion(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)

class Nota(models.Model):
    ser = models.FloatField()
    saber = models.FloatField()
    hacer = models.FloatField()
    decidir = models.FloatField()
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
