# controllers/historia_clinica_mensuraciones_controller.py
from datetime import datetime
from Errores import log_error_and_notify
from models import Mensuraciones

class MensuracionesController:
    def __init__(self, session):
        self.session = session

    def obtener_mensuraciones_procesadas(self, paciente):
        """
        Retorna el historial de mediciones ordenadas cronológicamente (descendente)
        y la última medición registrada (vigente).
        """
        if not paciente or not hasattr(paciente, 'mensuraciones') or not paciente.mensuraciones:
            return [], None
            
        # Ordenamos de la más reciente a la más antigua
        mens_ord = sorted(paciente.mensuraciones, key=lambda x: x.fecha_registro, reverse=True)
        ultima = mens_ord[0] if mens_ord else None
        
        return mens_ord, ultima

    def guardar_mensuracion(self, paciente_id, fecha_str, peso, talla, cintura, cadera, cuello, dieta):
        """Crea y persiste un nuevo registro de mensuración antropométrica."""
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            nueva_mensuracion = Mensuraciones(
                paciente_id=paciente_id,
                fecha_registro=fecha,
                peso=float(peso) if peso is not None and peso != '' else None,
                talla=float(talla) if talla is not None and talla != '' else None,
                cintura=float(cintura) if cintura is not None and cintura != '' else None,
                cadera=float(cadera) if cadera is not None and cadera != '' else None,
                cuello=float(cuello) if cuello is not None and cuello != '' else None,
                dieta=dieta if dieta is not None else None
            )
            
            self.session.add(nueva_mensuracion)
            self.session.commit()
            return True, "Mensuración guardada correctamente"
            
        except ValueError as e:
            self.session.rollback()
            return False, f"Error en los valores numéricos: {str(e)}"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al guardar mensuracion')
            return False, f"Error al guardar: {str(e)}"

    def actualizar_mensuracion(self, mensuracion, fecha_str, peso, talla, cintura, cadera, cuello, dieta):
        """Actualiza un registro de mensuración existente."""
        try:
            mensuracion.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            mensuracion.talla = float(talla) if talla is not None and talla != '' else None
            mensuracion.peso = float(peso) if peso is not None and peso != '' else None
            mensuracion.cintura = float(cintura) if cintura is not None and cintura != '' else None
            mensuracion.cadera = float(cadera) if cadera is not None and cadera != '' else None
            mensuracion.cuello = float(cuello) if cuello is not None and cuello != '' else None
            mensuracion.dieta = dieta if dieta is not None else None
            
            self.session.commit()
            return True, "Mensuración actualizada correctamente"
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar mensuracion')
            return False, f"Error: {str(e)}"

    def eliminar_mensuracion(self, mensuracion):
        """Elimina físicamente la medición de la base de datos."""
        try:
            if mensuracion is None:
                return False, "Error: La mensuración ya no existe"
                
            self.session.delete(mensuracion)
            self.session.commit()
            return True, "Mensuración eliminada correctamente"
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al eliminar mensuracion')
            return False, f"Error al eliminar: {str(e)}"