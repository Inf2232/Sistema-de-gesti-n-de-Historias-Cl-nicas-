from datetime import datetime
from models import TratamientoActual, OtrosTratamientos
from Errores import log_error_and_notify

class ControladorTratamientos:

    def __init__(self, session):
        self.session = session


    # =========================================================
    # UTILIDADES / CONSULTAS
    # =========================================================

    def obtener_esquema_visual(self, tratamiento):
        """
        Compatibilidad:
        - Nuevos -> esquema_json
        - Viejos -> tratamiento + dosis
        """
        if tratamiento.esquema_json and len(tratamiento.esquema_json) > 0:
            return tratamiento.esquema_json

        return [{
            "tratamiento": tratamiento.tratamiento or "No registrado",
            "dosis": tratamiento.dosis or "No registrado",
            "anio_inicio": ""
        }]


    def obtener_tratamiento_actual_reciente(self, paciente):
        if not paciente.tratamiento_actual:
            return None
        return max(
            paciente.tratamiento_actual,
            key=lambda x: x.fecha_registro
        )


    def obtener_otros_tratamientos_ordenados(self, paciente):
        if not paciente.otros_tratamientos:
            return []
        return sorted(
            paciente.otros_tratamientos,
            key=lambda x: x.fecha_registro,
            reverse=True
        )


    def obtener_historial_tratamientos(self, paciente):
        if not paciente.tratamiento_actual:
            return []
        return sorted(
            paciente.tratamiento_actual,
            key=lambda x: x.fecha_registro,
            reverse=True
        )


    # =========================================================
    # ACCIONES / PERSISTENCIA
    # =========================================================

    def guardar_tratamiento_actual(self, paciente, fecha_registro, tratamiento_str, esquema, sigue_via_clinica):
        nuevo_tratamiento = TratamientoActual(
            paciente_id=paciente.id,
            fecha_registro=fecha_registro,
            tratamiento=tratamiento_str,
            dosis='Ver esquema',
            esquema_json=esquema,
            sigue_via_clinica=sigue_via_clinica
        )
        self.session.add(nuevo_tratamiento)
        self.session.commit()
        self.session.refresh(paciente)


    def actualizar_tratamiento_actual(self, tratamiento, fecha_registro, tratamiento_str, esquema, sigue_via_clinica):
        tratamiento.fecha_registro = fecha_registro
        tratamiento.tratamiento = tratamiento_str
        tratamiento.dosis = 'Ver esquema'
        tratamiento.esquema_json = esquema
        tratamiento.sigue_via_clinica = sigue_via_clinica
        self.session.commit()

    def eliminar_tratamiento_actual(self, tratamiento):
        self.session.delete(tratamiento)
        self.session.commit()
    def agregar_otro_tratamiento_individual(self, paciente, tratamiento_val, dosis_val, fecha_registro):
        nuevo_tratamiento = OtrosTratamientos(
            paciente_id=paciente.id,
            tratamiento=tratamiento_val,
            dosis=dosis_val,
            fecha_registro=fecha_registro
        )
        self.session.add(nuevo_tratamiento)


    def actualizar_otro_tratamiento(self, tratamiento, fecha_registro, tratamiento_val, dosis_val):
        tratamiento.tratamiento = tratamiento_val
        tratamiento.dosis = dosis_val
        tratamiento.fecha_registro = fecha_registro
        self.session.commit()


    def eliminar_otro_tratamiento(self, tratamiento):
        self.session.delete(tratamiento)
        self.session.commit()


    def rollback(self):
        self.session.rollback()


    def commit(self):
        self.session.commit()


    def refresh(self, objeto):
        self.session.refresh(objeto)