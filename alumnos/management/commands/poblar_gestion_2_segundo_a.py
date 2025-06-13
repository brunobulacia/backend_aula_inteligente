import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.db import transaction
from datetime import timedelta, date
from usuarios.models import Usuario
from alumnos.models import (
    FichaInscripcion, Nota,
    MateriasInscritasGestion, Asistencia, Participacion
)
from materias.models import Gestion, Curso, GestionCurso, MateriaGestionCurso

fake = Faker('es_ES')

def fecha_aleatoria_segundo_semestre():
    inicio = date(2024, 7, 1)
    fin = date(2024, 11, 30)
    delta = fin - inicio
    return inicio + timedelta(days=random.randint(0, delta.days))

class Command(BaseCommand):
    help = "Pobla la gestión 2-2024 para todos los alumnos del curso Segundo A"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        gestion = Gestion.objects.get(periodo="2-2024")
        curso = Curso.objects.get(nombre="Segundo A")
        gc = GestionCurso.objects.get(gestion=gestion, curso=curso)

        asignaciones = MateriaGestionCurso.objects.filter(gestion_curso=gc)
        if not asignaciones.exists():
            self.stdout.write(self.style.WARNING("\u26a0\ufe0f No hay materias asignadas para Segundo A en 2-2024"))
            return

        alumnos = Usuario.objects.filter(tipo_usuario='alum', id__gte=61, id__lt=81)
        total = 0

        for alumno in alumnos:
            matricula = alumno.matriculas.first()

            # Saltar si ya tiene ficha con materias en esta gestión
            if FichaInscripcion.objects.filter(
                matricula=matricula,
                materiasinscritasgestion__gestion_curso=gc
            ).exists():
                continue

            self.stdout.write(f"👦 Poblando gestión 2-2024 para: {alumno.nombre} {alumno.apellidos}")
            ficha = FichaInscripcion.objects.create(matricula=matricula)

            for asignacion in asignaciones:
                materia = asignacion.materia

                asistencias = random.randint(13, 22)
                participaciones = random.randint(6, 12)

                ser = min(25, max(0, asistencias + random.uniform(-2, 2)))
                hacer = min(25, max(0, participaciones + random.uniform(-1.5, 1.5)))
                decidir = min(25, max(0, participaciones + random.uniform(-1.5, 1.5)))
                saber = random.uniform(15, 25)

                nota_final = round(ser + hacer + decidir + saber, 2)
                nota = Nota.objects.create(
                    ser=round(ser, 2),
                    saber=round(saber, 2),
                    hacer=round(hacer, 2),
                    decidir=round(decidir, 2),
                    nota_final=nota_final
                )

                MateriasInscritasGestion.objects.create(
                    ficha=ficha,
                    materia=materia,
                    gestion_curso=gc,
                    nota=nota
                )

                for _ in range(asistencias):
                    Asistencia.objects.create(
                        ficha=ficha,
                        materia=materia,
                        gestion_curso=gc,
                        fecha=fecha_aleatoria_segundo_semestre(),
                        asistio=True
                    )

                for _ in range(participaciones):
                    Participacion.objects.create(
                        ficha=ficha,
                        materia=materia,
                        gestion_curso=gc,
                        fecha=fecha_aleatoria_segundo_semestre(),
                        descripcion=f"Participación en {fake.word()}"
                    )

            total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Gestión 2-2024 poblada para {total} alumno(s) de Segundo A."))
