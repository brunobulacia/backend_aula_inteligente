import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.db import transaction
from datetime import timedelta, date
from usuarios.models import Usuario
from alumnos.models import (
    Matricula, FichaInscripcion, Nota,
    MateriasInscritasGestion, Asistencia, Participacion
)
from materias.models import Gestion, Curso, GestionCurso, MateriaGestionCurso

fake = Faker('es_ES')

class Command(BaseCommand):
    help = "Pobla la gestión 2-2024 para todos los alumnos de Primero A inscritos en gestión 1."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        gestion1 = Gestion.objects.get(periodo="1-2024")
        gestion2 = Gestion.objects.get(periodo="2-2024")
        curso = Curso.objects.get(nombre="Primero A")
        gc1 = GestionCurso.objects.get(gestion=gestion1, curso=curso)
        gc2 = GestionCurso.objects.get(gestion=gestion2, curso=curso)

        asignaciones2 = MateriaGestionCurso.objects.filter(gestion_curso=gc2)
        if not asignaciones2.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay materias asignadas en la gestión 2 para Primero A"))
            return

        # Obtener todas las fichas con materias inscritas en gestión 1
        fichas_g1 = FichaInscripcion.objects.filter(
            materiasinscritasgestion__gestion_curso=gc1
        ).distinct()

        total = 0
        for ficha1 in fichas_g1:
            matricula = ficha1.matricula
            alumno = matricula.alumno

            # Saltar si ya fue poblado
            if FichaInscripcion.objects.filter(
                matricula=matricula,
                materiasinscritasgestion__gestion_curso=gc2
            ).exists():
                continue

            self.stdout.write(f"👨 Poblando gestión 2-2024 para: {alumno.nombre} {alumno.apellidos}")
            ficha2 = FichaInscripcion.objects.create(matricula=matricula)

            for asignacion in asignaciones2:
                materia = asignacion.materia

                mig1 = MateriasInscritasGestion.objects.filter(
                    ficha=ficha1, gestion_curso=gc1, materia=materia
                ).first()

                asistencias_prev = 14
                participaciones_prev = 7

                if mig1:
                    asistencias_prev = Asistencia.objects.filter(
                        ficha=ficha1, gestion_curso=gc1, materia=materia, asistio=True
                    ).count()
                    participaciones_prev = Participacion.objects.filter(
                        ficha=ficha1, gestion_curso=gc1, materia=materia
                    ).count()

                asistencias = max(8, int(asistencias_prev * random.uniform(0.8, 1.2)))
                participaciones = max(3, int(participaciones_prev * random.uniform(0.8, 1.3)))

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
                    ficha=ficha2,
                    materia=materia,
                    gestion_curso=gc2,
                    nota=nota
                )

                for _ in range(asistencias):
                    Asistencia.objects.create(
                        ficha=ficha2,
                        materia=materia,
                        gestion_curso=gc2,
                        fecha=date.today() - timedelta(days=random.randint(1, 60)),
                        asistio=True
                    )

                for _ in range(participaciones):
                    Participacion.objects.create(
                        ficha=ficha2,
                        materia=materia,
                        gestion_curso=gc2,
                        fecha=date.today() - timedelta(days=random.randint(1, 60)),
                        descripcion=f"Participación en {fake.word()}"
                    )

            total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Gestión 2-2024 poblada para {total} alumno(s)."))
