# controllers/historia_clinica_educacion_controller.py
from datetime import datetime
from Errores import log_error_and_notify
from models import ResultadoEducacionDiabetologica, EstadoEducacionDiabetologica

class EducacionDiabetologicaController:
    def __init__(self, session):
        self.session = session

    def obtener_datos_educacion(self, paciente_id):
        """
        Replica la lógica original: obtiene el último registro de evaluación, 
        el último estado de seguimiento, y unifica ambos en un historial cronológico.
        """
        # 1. Obtener evaluaciones
        evaluaciones = self.session.query(ResultadoEducacionDiabetologica).filter(
            ResultadoEducacionDiabetologica.paciente_id == paciente_id
        ).order_by(ResultadoEducacionDiabetologica.fecha_registro.desc()).all()
        
        # 2. Obtener estados de seguimiento (Nota: usa educacion_id según el código original)
        estados = self.session.query(EstadoEducacionDiabetologica).filter(
            EstadoEducacionDiabetologica.educacion_id == paciente_id
        ).order_by(EstadoEducacionDiabetologica.fecha_registro.desc()).all()

        ultimo_registro = evaluaciones[0] if evaluaciones else None
        ultimo_estado = estados[0] if estados else None
        
        # Unificar cronología
        historial = sorted(evaluaciones + estados, key=lambda x: x.fecha_registro, reverse=True)
        
        return ultimo_registro, ultimo_estado, historial

    # ================= CRUD ESTADOS DE SEGUIMIENTO =================

    def guardar_estado(self, paciente_id, fecha_str, mantiene):
        try:
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            nuevo_estado = EstadoEducacionDiabetologica(
                educacion_id=paciente_id, # Se usa educacion_id según el modelo original
                fecha_registro=fecha_registro,
                mantiene_educacion=mantiene
            )
            self.session.add(nuevo_estado)
            self.session.commit()
            return True, "Estado de seguimiento guardado correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al guardar estado diabetológico')
            return False, f"Error al guardar: {str(e)}"

    def actualizar_estado(self, estado, fecha_str, mantiene):
        try:
            estado.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            estado.mantiene_educacion = mantiene
            self.session.commit()
            return True, "Estado actualizado correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar estado diabetológico')
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_estado(self, estado):
        try:
            self.session.delete(estado)
            self.session.commit()
            return True, "Estado eliminado correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al eliminar estado diabetológico')   
            return False, f"Error al eliminar: {str(e)}"

    # ================= CRUD EVALUACIONES (SCORES) =================

    def guardar_evaluacion(self, paciente_id, fecha_str, inicio, final):
        try:
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            nueva_evaluacion = ResultadoEducacionDiabetologica(
                paciente_id=paciente_id,
                fecha_registro=fecha_registro,
                inicio=inicio,
                final=final
            )
            self.session.add(nueva_evaluacion)
            self.session.commit()
            return True, "Evaluación guardada correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al guardar evaluación diabetológica')
            return False, f"Error al guardar: {str(e)}"

    def actualizar_evaluacion(self, evaluacion, fecha_str, inicio, final):
        try:
            evaluacion.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            evaluacion.inicio = inicio
            evaluacion.final = final
            self.session.commit()
            return True, "Evaluación actualizada correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar evaluación diabetológica')
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_evaluacion(self, evaluacion):
        try:
            self.session.delete(evaluacion)
            self.session.commit()
            return True, "Evaluación eliminada correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al eliminar evaluación diabetológica')
            return False, f"Error al eliminar: {str(e)}"