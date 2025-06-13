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

class Command(BaseCommand):
    help = "Pobla la gestión 1-2024 para todos los alumnos del curso Primero B"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        gestion = Gestion.objects.get(periodo="1-2024")
        curso = Curso.objects.get(nombre="Primero B")
        gc = GestionCurso.objects.get(gestion=gestion, curso=curso)

        asignaciones = MateriaGestionCurso.objects.filter(gestion_curso=gc)
        if not asignaciones.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay materias asignadas para Primero B en 1-2024"))
            return

        # Solo alumnos de Primero B (id 41 al 60)
        alumnos = Usuario.objects.filter(
            tipo_usuario='alum',
            id__gte=41,
            id__lt=61
        ).distinct()

        total = 0
        for alumno in alumnos:
            matricula = alumno.matriculas.first()

            if FichaInscripcion.objects.filter(
                matricula=matricula,
                materiasinscritasgestion__gestion_curso=gc
            ).exists():
                continue

            self.stdout.write(f"👦 Poblando gestión 1-2024 para: {alumno.nombre} {alumno.apellidos}")
            ficha = FichaInscripcion.objects.create(matricula=matricula)

            for asignacion in asignaciones:
                materia = asignacion.materia

                asistencias = random.randint(10, 20)
                participaciones = random.randint(4, 10)

                ser = min(25, max(0, asistencias + random.uniform(-3, 3)))
                hacer = min(25, max(0, participaciones + random.uniform(-2, 2)))
                decidir = min(25, max(0, participaciones + random.uniform(-2, 2)))
                saber = random.uniform(8, 25)

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
                        fecha=date(2024, 3, 1) + timedelta(days=random.randint(0, 90)),
                        asistio=True
                    )

                for _ in range(participaciones):
                    Participacion.objects.create(
                        ficha=ficha,
                        materia=materia,
                        gestion_curso=gc,
                        fecha=date(2024, 3, 1) + timedelta(days=random.randint(0, 90)),
                        descripcion=f"Participación en {fake.word()}"
                    )

            total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Gestión 1-2024 poblada para {total} alumno(s) de Primero B."))
