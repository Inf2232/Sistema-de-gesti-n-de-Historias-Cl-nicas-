# En: app/controllers/historia_clinica_obstetrica_controller.py
from datetime import datetime
from models import HistoriaObstetrica

class HistoriaClinicaObstetricaController:
    def __init__(self, session):
        self.session = session

    def obtener_historias_procesadas(self, paciente):
        """Devuelve la lista ordenada por fecha (descendente) y el último registro."""
        historias = [h for h in paciente.historia_obstetrica if h.fecha_registro is not None]
        historias_ordenadas = sorted(historias, key=lambda x: x.fecha_registro, reverse=True)
        ultima = historias_ordenadas[0] if historias_ordenadas else None
        return historias_ordenadas, ultima

    def guardar_registro(self, paciente_id, datos):
        """Crea y persiste un nuevo registro de historia obstétrica."""
        try:
            nueva_historia = HistoriaObstetrica(
                paciente_id=paciente_id,
                fecha_registro=datetime.strptime(datos['fecha_registro'], '%Y-%m-%d').date(),
                edad_menarca=datos['edad_menarca'],
                edad_primera_relacion_sexual=datos['edad_primera_relacion_sexual'],
                gestaciones=datos['gestaciones'] or 0,
                partos=datos['partos'] or 0,
                abortos_espontaneos=datos['abortos_espontaneos'] or 0,
                abortos_provocados=datos['abortos_provocados'] or 0,
                anticoncepcion_actual=datos['anticoncepcion_actual'],
                tiempo_anticoncepcion_actual_anos=int(datos['tiempo_act_anos'] or 0),
                tiempo_anticoncepcion_actual_meses=int(datos['tiempo_act_meses'] or 0),
                anticoncepcion_previa=datos['anticoncepcion_previa'],
                tiempo_anticoncepcion_prev_anos=int(datos['tiempo_prev_anos'] or 0),
                tiempo_anticoncepcion_prev_meses=int(datos['tiempo_prev_meses'] or 0),
                diabetes_gestacional=datos['diabetes_gestacional'],
                diabetes_insulina=datos['diabetes_insulina'],
                diabetes_gestacional_historial=datos['historial_diabetes'],
                edad_materna_al_diagnostico=datos['edad_materna_al_diagnostico'],
                fecha_diabetes_gestacionaria=datetime.strptime(datos['fecha_db_input'], '%Y-%m-%d').date() if datos['fecha_db_input'] else None,
                ehe=datos['ehe'],
                ehe_historial=datos['historial_ehe'],
                macrofetos=datos['macrofetos'],
                macrofetos_historial=datos['historial_macrofetos'],
                malformaciones=datos['malformaciones'],
                malformaciones_cuales=datos['malformaciones_cuales'],
                muertes_perinatales=datos['muertes_perinatales'],
                edad_menopausia=datos['edad_menopausia'],
                tipo_menopausia=datos['tipo_menopausia']
            )
            self.session.add(nueva_historia)
            self.session.commit()
            return True, "Historia Obstétrica guardada correctamente"
        except Exception as e:
            self.session.rollback()
            return False, str(e)

    def actualizar_registro(self, historia, datos):
        """Actualiza un registro existente."""
        try:
            historia.fecha_registro = datetime.strptime(datos['fecha_registro'], '%Y-%m-%d').date()
            historia.edad_menarca = datos['edad_menarca']
            historia.edad_primera_relacion_sexual = datos['edad_primera_relacion_sexual']
            historia.gestaciones = datos['gestaciones'] or 0
            historia.partos = datos['partos'] or 0
            historia.abortos_espontaneos = datos['abortos_espontaneos'] or 0
            historia.abortos_provocados = datos['abortos_provocados'] or 0
            historia.anticoncepcion_actual = datos['anticoncepcion_actual']
            historia.tiempo_anticoncepcion_actual_anos = int(datos['tiempo_act_anos'] or 0)
            historia.tiempo_anticoncepcion_actual_meses = int(datos['tiempo_act_meses'] or 0)
            historia.anticoncepcion_previa = datos['anticoncepcion_previa']
            historia.tiempo_anticoncepcion_prev_anos = int(datos['tiempo_prev_anos'] or 0)
            historia.tiempo_anticoncepcion_prev_meses = int(datos['tiempo_prev_meses'] or 0)
            historia.diabetes_gestacional = datos['diabetes_gestacional']
            historia.diabetes_insulina = datos['diabetes_insulina']
            historia.diabetes_gestacional_historial = datos['historial_diabetes']
            historia.edad_materna_al_diagnostico = datos['edad_materna_al_diagnostico']
            historia.fecha_diabetes_gestacionaria = datetime.strptime(datos['fecha_db_input'], '%Y-%m-%d').date() if datos['fecha_db_input'] else None
            historia.ehe = datos['ehe']
            historia.ehe_historial = datos['historial_ehe']
            historia.macrofetos = datos['macrofetos']
            historia.macrofetos_historial = datos['historial_macrofetos']
            historia.malformaciones = datos['malformaciones']
            historia.malformaciones_cuales = datos['malformaciones_cuales']
            historia.muertes_perinatales = datos['muertes_perinatales']
            historia.edad_menopausia = datos['edad_menopausia']
            historia.tipo_menopausia = datos['tipo_menopausia']

            self.session.commit()
            return True, "Historia Obstétrica actualizada correctamente"
        except Exception as e:
            self.session.rollback()
            return False, str(e)

    def eliminar_registro(self, historia):
        """Elimina un registro de la base de datos."""
        try:
            self.session.delete(historia)
            self.session.commit()
            return True, "Historia obstétrica eliminada correctamente"
        except Exception as e:
            self.session.rollback()
            return False, str(e)