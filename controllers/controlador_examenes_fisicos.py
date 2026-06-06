from models import ExamenFisico


class ControladorExamenesFisicos:

    def __init__(self, session):
        self.session = session


    # =========================================================
    # ACCIONES / PERSISTENCIA
    # =========================================================

    def crear_examen_fisico(self, paciente_id, fecha, datos):
        nuevo_examen = ExamenFisico(
            paciente_id=paciente_id,
            fecha_registro=fecha,
            sistolica_acostado=datos.get('sistolica_acostado'),
            diastolica_acostado=datos.get('diastolica_acostado'),
            sistolica_sentado=datos.get('sistolica_sentado'),
            diastolica_sentado=datos.get('diastolica_sentado'),
            sistolica_de_pie=datos.get('sistolica_de_pie'),
            diastolica_de_pie=datos.get('diastolica_de_pie'),
            bocio=datos.get('bocio'),
            acantosis_nigricans=datos.get('acantosis_nigricans'),
            frecuencia_cardiaca_acostado=datos.get('frecuencia_cardiaca_acostado'),
            frecuencia_cardiaca_sentado=datos.get('frecuencia_cardiaca_sentado')
        )
        self.session.add(nuevo_examen)
        self.session.commit()
        return nuevo_examen


    def actualizar_examen_fisico(self, examen, fecha, datos):
        examen.fecha_registro = fecha
        examen.sistolica_acostado = datos.get('sistolica_acostado')
        examen.diastolica_acostado = datos.get('diastolica_acostado')
        examen.sistolica_sentado = datos.get('sistolica_sentado')
        examen.diastolica_sentado = datos.get('diastolica_sentado')
        examen.sistolica_de_pie = datos.get('sistolica_de_pie')
        examen.diastolica_de_pie = datos.get('diastolica_de_pie')
        examen.bocio = datos.get('bocio')
        examen.acantosis_nigricans = datos.get('acantosis_nigricans')
        examen.frecuencia_cardiaca_acostado = datos.get('frecuencia_cardiaca_acostado')
        examen.frecuencia_cardiaca_sentado = datos.get('frecuencia_cardiaca_sentado')
        
        self.session.commit()


    def eliminar_examen_fisico(self, examen):
        self.session.delete(examen)
        self.session.commit()