import pandas as pd
import numpy as np
import os
from django.conf import settings
import joblib
from sklearn.ensemble import RandomForestRegressor
from alumnos.models import MateriasInscritasGestion, Asistencia, Participacion, FichaInscripcion
from materias.models import MateriaGestionCurso

def entrenar_modelo_rendimiento():
    dataset = []
    saber_data = []

    for inscripcion in MateriasInscritasGestion.objects.all():
        ficha = inscripcion.ficha
        alumno = ficha.matricula.alumno
        materia = inscripcion.materia
        gestion_curso = inscripcion.gestion_curso
        nota = inscripcion.nota

        if not nota:
            continue

        asistencias = Asistencia.objects.filter(
            ficha=ficha,
            materia=materia,
            gestion_curso=gestion_curso,
            asistio=True
        ).count()

        participaciones = Participacion.objects.filter(
            ficha=ficha,
            materia=materia,
            gestion_curso=gestion_curso
        ).count()

        dataset.append({
            "asistencias": asistencias,
            "participaciones": participaciones,
            "ser": nota.ser,
            "hacer": nota.hacer,
            "decidir": nota.decidir
        })

        anteriores = MateriasInscritasGestion.objects.filter(
            ficha__matricula__alumno=alumno
        ).exclude(id=inscripcion.id)

        notas_saber_previas = [
            i.nota.saber for i in anteriores if i.nota and i.nota.saber is not None
        ]

        if notas_saber_previas:
            promedio_saber_pasado = sum(notas_saber_previas) / len(notas_saber_previas)
            saber_data.append({
                "saber_pasado": promedio_saber_pasado,
                "saber": nota.saber
            })

    if not dataset:
        raise ValueError("No hay datos suficientes para entrenar.")

    df = pd.DataFrame(dataset)

    modelo_ser = RandomForestRegressor()
    modelo_ser.fit(df[["asistencias"]], df["ser"])

    modelo_hacer = RandomForestRegressor()
    modelo_hacer.fit(df[["participaciones"]], df["hacer"])

    modelo_decidir = RandomForestRegressor()
    modelo_decidir.fit(df[["participaciones"]], df["decidir"])

    modelos = {
        "ser": modelo_ser,
        "hacer": modelo_hacer,
        "decidir": modelo_decidir
    }

    if saber_data:
        df_saber = pd.DataFrame(saber_data)
        modelo_saber = RandomForestRegressor()
        modelo_saber.fit(df_saber[["saber_pasado"]], df_saber["saber"])
        modelos["saber"] = modelo_saber

    ruta_salida = os.path.join("alumnos", "modelo_rendimiento.pkl")
    joblib.dump(modelos, ruta_salida)

    return ruta_salida

def predecir_rendimiento_grupal(profesor, gestion_id=None):
    modelo_path = os.path.join(settings.BASE_DIR, 'alumnos', 'ml', 'modelo_rendimiento.pkl')
    modelos = joblib.load(modelo_path)

    resultados = []

    asignaciones = MateriaGestionCurso.objects.filter(profesor=profesor)
    if gestion_id:
        asignaciones = asignaciones.filter(gestion_curso__gestion_id=gestion_id)

    for asignacion in asignaciones:
        gestion_curso = asignacion.gestion_curso
        materia = asignacion.materia
        inscritos = MateriasInscritasGestion.objects.filter(
            gestion_curso=gestion_curso, materia=materia
        )

        if not inscritos.exists():
            continue

        suma_ser_predicho = 0
        suma_saber_predicho = 0
        suma_hacer_predicho = 0
        suma_decidir_predicho = 0
        suma_total_predicha = 0

        suma_total_real = 0
        suma_ser_real = 0
        suma_saber_real = 0
        suma_hacer_real = 0
        suma_decidir_real = 0

        total_estudiantes = 0

        for ins in inscritos:
            alumno = ins.ficha.matricula.alumno
            asistencias = Asistencia.objects.filter(
                ficha=ins.ficha, materia=materia, gestion_curso=gestion_curso, asistio=True
            ).count()
            participaciones = Participacion.objects.filter(
                ficha=ins.ficha, materia=materia, gestion_curso=gestion_curso
            ).count()

            ser = modelos["ser"].predict(pd.DataFrame([[asistencias]], columns=["asistencias"]))[0]
            hacer = modelos["hacer"].predict(pd.DataFrame([[participaciones]], columns=["participaciones"]))[0]
            decidir = modelos["decidir"].predict(pd.DataFrame([[participaciones]], columns=["participaciones"]))[0]

            anteriores = MateriasInscritasGestion.objects.filter(
                ficha__matricula__alumno=alumno
            ).exclude(id=ins.id)

            notas_saber_previas = [
                i.nota.saber for i in anteriores if i.nota and i.nota.saber is not None
            ]

            if "saber" in modelos and notas_saber_previas:
                promedio_saber_pasado = sum(notas_saber_previas) / len(notas_saber_previas)
                saber = modelos["saber"].predict(pd.DataFrame([[promedio_saber_pasado]], columns=["saber_pasado"]))[0]
            else:
                saber = 0.0

            nota_predicha = ser + saber + hacer + decidir

            suma_ser_predicho += ser
            suma_saber_predicho += saber
            suma_hacer_predicho += hacer
            suma_decidir_predicho += decidir
            suma_total_predicha += nota_predicha

            if ins.nota:
                suma_ser_real += ins.nota.ser
                suma_saber_real += ins.nota.saber
                suma_hacer_real += ins.nota.hacer
                suma_decidir_real += ins.nota.decidir
                suma_total_real += ins.nota.nota_final

            total_estudiantes += 1

        resultados.append({
            "materia": materia.nombre,
            "gestion": gestion_curso.gestion.periodo,
            "curso": gestion_curso.curso.nombre,
            "ser_predicho": round(suma_ser_predicho / total_estudiantes, 2),
            "saber_predicho": round(suma_saber_predicho / total_estudiantes, 2),
            "hacer_predicho": round(suma_hacer_predicho / total_estudiantes, 2),
            "decidir_predicho": round(suma_decidir_predicho / total_estudiantes, 2),
            "nota_final_predicha": round(suma_total_predicha / total_estudiantes, 2),
            "ser_real": round(suma_ser_real / total_estudiantes, 2),
            "saber_real": round(suma_saber_real / total_estudiantes, 2),
            "hacer_real": round(suma_hacer_real / total_estudiantes, 2),
            "decidir_real": round(suma_decidir_real / total_estudiantes, 2),
            "nota_final_real": round(suma_total_real / total_estudiantes, 2),
        })

    return resultados




def predecir_rendimiento_individual(alumno, gestion_id=None):
    modelo_path = os.path.join(settings.BASE_DIR, 'alumnos', 'ml', 'modelo_rendimiento.pkl')
    modelos = joblib.load(modelo_path)

    resultados = []

    try:
        ficha = FichaInscripcion.objects.get(matricula__alumno=alumno)
    except FichaInscripcion.DoesNotExist:
        return resultados

    materias_inscritas = MateriasInscritasGestion.objects.filter(ficha=ficha)
    if gestion_id:
        materias_inscritas = materias_inscritas.filter(gestion_curso__gestion_id=gestion_id)

    for ins in materias_inscritas:
        materia = ins.materia
        gestion_curso = ins.gestion_curso
        nota = ins.nota if ins.nota else None

        asistencias = Asistencia.objects.filter(
            ficha=ficha,
            materia=materia,
            gestion_curso=gestion_curso,
            asistio=True
        ).count()

        participaciones = Participacion.objects.filter(
            ficha=ficha,
            materia=materia,
            gestion_curso=gestion_curso
        ).count()

        ser = modelos["ser"].predict(pd.DataFrame([[asistencias]], columns=["asistencias"]))[0]
        hacer = modelos["hacer"].predict(pd.DataFrame([[participaciones]], columns=["participaciones"]))[0]
        decidir = modelos["decidir"].predict(pd.DataFrame([[participaciones]], columns=["participaciones"]))[0]

        anteriores = MateriasInscritasGestion.objects.filter(
            ficha__matricula__alumno=alumno
        ).exclude(id=ins.id)

        notas_saber_previas = [
            i.nota.saber for i in anteriores if i.nota and i.nota.saber is not None
        ]

        if "saber" in modelos and notas_saber_previas:
            promedio_saber_pasado = sum(notas_saber_previas) / len(notas_saber_previas)
            saber = modelos["saber"].predict(pd.DataFrame([[promedio_saber_pasado]], columns=["saber_pasado"]))[0]
        else:
            saber = 0.0

        nota_predicha = ser + saber + hacer + decidir

        resultados.append({
            "materia": materia.nombre,
            "materia_id": materia.id,
            "gestion": gestion_curso.gestion.periodo,
            "curso": gestion_curso.curso.nombre,
            "ser_real": round(nota.ser, 2) if nota else None,
            "saber_real": round(nota.saber, 2) if nota else None,
            "hacer_real": round(nota.hacer, 2) if nota else None,
            "decidir_real": round(nota.decidir, 2) if nota else None,
            "nota_final_real": round(nota.nota_final, 2) if nota else None,
            "ser_predicho": round(ser, 2),
            "saber_predicho": round(saber, 2),
            "hacer_predicho": round(hacer, 2),
            "decidir_predicho": round(decidir, 2),
            "nota_final_predicha": round(nota_predicha, 2)
        })

    return resultados
