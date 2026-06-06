from datetime import datetime
from models import Oftalmologia
from Errores import log_error_and_notify

class HistoriaClinicaOftalmologiaController:
    def __init__(self, session):
        self.session = session

    def guardar_examen(self, paciente_id, fecha_registro, **variables_formulario):
        try:
            if fecha_registro:
                if isinstance(fecha_registro, str):
                    fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
                
                nuevo_examen = Oftalmologia(
                    paciente_id=paciente_id,
                    fecha_registro=fecha_registro,
                    **variables_formulario  # Recibe tus variables originales exactas
                )
                
                self.session.add(nuevo_examen)
                self.session.commit()
                return True, "Examen oftalmológico guardado correctamente"
            else:
                return False, "Debe introducir la fecha"
                
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, "Error al guardar examen oftalmológico")
            return False, f"Error al guardar: {str(e)}"

    def actualizar_examen(self, examen, fecha_registro, **variables_formulario):
        try:
            if fecha_registro:
                if isinstance(fecha_registro, str):
                    examen.fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
                else:
                    examen.fecha_registro = fecha_registro

                # Actualiza dinámicamente usando tus variables originales
                for clave, valor in variables_formulario.items():
                    if hasattr(examen, clave):
                        setattr(examen, clave, valor)

                self.session.commit()
                return True, "Examen oftalmológico actualizado correctamente"
            else:
                return False, "Debe introducir la fecha"
                
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, "Error al actualizar examen oftalmológico")
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_examen(self, examen):
        try:
            self.session.delete(examen)
            self.session.commit()
            return True, "Examen oftalmológico eliminado correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f"Error al eliminar examen oftalmológico: {str(e)}")
            return False, f"Error al eliminar el examen: {str(e)}"