import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction
from usuarios.models import Usuario, Direccion
from alumnos.models import Matricula, FichaInscripcion
from materias.models import Gestion, Curso, GestionCurso

fake = Faker('es_ES')

class Command(BaseCommand):
    help = "Pobla el curso Segundo A con 20 alumnos para la gestión 1-2024."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        gestion = Gestion.objects.get(periodo="1-2024")
        curso = Curso.objects.get(nombre="Segundo A")
        gestion_curso = GestionCurso.objects.get(gestion=gestion, curso=curso)

        total = 0
        for i in range(20):
            nombre = fake.first_name()
            apellidos = fake.last_name()
            email = f"{nombre.lower()}.{apellidos.lower()}{random.randint(100, 999)}@example.com"
            ci = str(random.randint(9000000, 9999999))

            # Crear dirección
            direccion = Direccion.objects.create(
                ciudad=fake.city(),
                zona=fake.street_name(),
                calle=fake.street_name(),
                numero=fake.building_number(),
                referencia=fake.sentence(nb_words=5)
            )

            # Crear usuario alumno
            usuario = Usuario.objects.create_user(
                nombre=nombre,
                apellidos=apellidos,
                email=email,
                password='12345678',
                ci=ci,
                tipo_usuario='alum',
                direccion=direccion
            )

            # Crear matrícula y ficha
            matricula = Matricula.objects.create(alumno=usuario)
            FichaInscripcion.objects.create(matricula=matricula)

            self.stdout.write(f"✅ Alumno creado: {nombre} {apellidos} - CI: {ci}")
            total += 1

        self.stdout.write(self.style.SUCCESS(f"🎉 Se crearon {total} alumnos para Segundo A en gestión 1-2024."))
