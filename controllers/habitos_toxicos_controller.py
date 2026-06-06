# controllers/habitos_toxicos_controller.py
from datetime import datetime
from models import HabitosToxicos
from Errores import log_error_and_notify

class HabitosToxicosController:
    def __init__(self, session):
        self.session = session

    def obtener_habitos_procesados(self, paciente):
        """Retorna la lista ordenada descendentemente y el último registro válido."""
        if not paciente or not paciente.habitos_toxicos:
            return [], None
            
        habitos_sorted = sorted(
            paciente.habitos_toxicos,
            key=lambda x: x.fecha_registro,
            reverse=True
        )
        ultimo = habitos_sorted[0] if habitos_sorted else None
        return habitos_sorted, ultimo

    def guardar_habito(self, paciente_id, fecha_str, fuma, cant_cigarros=None, cant_tabacos=None, tiempo_sin_fumar=None, consumo_alcohol=None):
        try:
            if not fecha_str:
                return False, "La fecha de registro es obligatoria."
                
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()

            # Consistencia de lógica de negocio: Limpieza de datos condicionales
            if fuma != "Si":
                cant_cigarros = None
                cant_tabacos = None
            if fuma != "Ex Fumador":
                tiempo_sin_fumar = None

            nuevo_habito = HabitosToxicos(
                paciente_id=paciente_id,
                fecha_registro=fecha_registro,
                fuma=fuma,
                cant_cigarros=cant_cigarros,
                cant_tabacos=cant_tabacos,
                tiempo_sin_fumar=tiempo_sin_fumar,
                consumo_excesivo_alcohol=consumo_alcohol
            )
            
            self.session.add(nuevo_habito)
            self.session.commit()
            return True, "Evaluación de hábitos registrada correctamente."
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, "Error al insertar registro de hábitos tóxicos")
            return False, f"Error al guardar: {str(e)}"

    def actualizar_habito(self, habito, fecha_str, fuma, cant_cigarros=None, cant_tabacos=None, tiempo_sin_fumar=None, consumo_alcohol=None):
        try:
            if not fecha_str:
                return False, "La fecha de registro es obligatoria."
                
            habito.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            habito.fuma = fuma
            
            # Limpieza estricta de campos según el nuevo estado seleccionado
            if fuma == "Si":
                habito.cant_cigarros = cant_cigarros
                habito.cant_tabacos = cant_tabacos
                habito.tiempo_sin_fumar = None
            elif fuma == "Ex Fumador":
                habito.cant_cigarros = None
                habito.cant_tabacos = None
                habito.tiempo_sin_fumar = tiempo_sin_fumar
            else:
                habito.cant_cigarros = None
                habito.cant_tabacos = None
                habito.tiempo_sin_fumar = None
            
            habito.consumo_excesivo_alcohol = consumo_alcohol
            
            self.session.commit()
            return True, "Cambios de la evaluación actualizados con éxito."
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f"Error al actualizar hábitos tóxicos ID {habito.id}")
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_habito(self, habito):
        try:
            self.session.delete(habito)
            self.session.commit()
            return True, "Registro de hábito tóxico eliminado correctamente."
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f"Error al eliminar hábito tóxico ID {habito.id}")
            return False, f"Error al eliminar: {str(e)}"