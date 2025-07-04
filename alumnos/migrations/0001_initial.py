# Generated by Django 5.2.1 on 2025-06-06 21:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('materias', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FichaInscripcion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Nota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nota1', models.FloatField()),
                ('nota2', models.FloatField()),
                ('nota_final', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('asistio', models.BooleanField()),
                ('gestion_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.gestioncurso')),
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.materia')),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alumnos.fichainscripcion')),
            ],
        ),
        migrations.CreateModel(
            name='Matricula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_now_add=True)),
                ('alumno', models.ForeignKey(limit_choices_to={'tipo_usuario': 'alum'}, on_delete=django.db.models.deletion.CASCADE, related_name='matriculas', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='fichainscripcion',
            name='matricula',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alumnos.matricula'),
        ),
        migrations.CreateModel(
            name='Participacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('descripcion', models.TextField()),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alumnos.fichainscripcion')),
                ('gestion_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.gestioncurso')),
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.materia')),
            ],
        ),
        migrations.CreateModel(
            name='MateriasInscritasGestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alumnos.fichainscripcion')),
                ('gestion_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.gestioncurso')),
                ('materia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='materias.materia')),
                ('nota', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='alumnos.nota')),
            ],
            options={
                'unique_together': {('ficha', 'materia', 'gestion_curso')},
            },
        ),
    ]
