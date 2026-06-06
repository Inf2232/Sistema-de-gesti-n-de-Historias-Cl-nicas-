from datetime import datetime
from models import Estomatologia, DiagnosticosClinico
from Errores import log_error_and_notify
from nicegui import ui

class EstomatologiaController:
    def __init__(self, session, paciente):
        self.session = session
        self.paciente = paciente

    def guardar_examen(self, fecha_str, examen_funcional, diag_epidemiologicos, pronostico, tratamiento, diag_clinico_vals):
        if not fecha_str:
            ui.notify('La fecha es obligatoria', type='negative')
            return False
            
        try:
            nuevo_registro = Estomatologia(
                paciente_id=self.paciente.id,
                fecha_registro=datetime.strptime(fecha_str, '%Y-%m-%d').date(),
                examen_funcional=examen_funcional,
                diagnosticos_epidemiologicos=diag_epidemiologicos,
                pronostico=pronostico,
                tratamiento=tratamiento
            )
            
            self.session.add(nuevo_registro)
            self.session.flush()  
            
            if diag_clinico_vals:
                for diagnostico in diag_clinico_vals:
                    nuevo_diagnostico = DiagnosticosClinico(
                        examen_id=nuevo_registro.id,
                        diagnostico=diagnostico
                    )
                    self.session.add(nuevo_diagnostico)
            
            self.session.commit()
            ui.notify('Registro guardado exitosamente', type='positive')
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al guardar el examen estomatológico: {str(e)}')
            ui.notify(f'Error al guardar: {str(e)}', type='negative')
            return False

    def actualizar_examen(self, registro, fecha_str, examen_funcional, diag_epidemiologicos, pronostico, tratamiento, diag_clinico_vals):
        if not fecha_str:
            ui.notify('La fecha es obligatoria', type='negative')
            return False
            
        try:
            registro.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            registro.examen_funcional = examen_funcional
            registro.diagnosticos_epidemiologicos = diag_epidemiologicos
            registro.pronostico = pronostico
            registro.tratamiento = tratamiento
            
            # Eliminar diagnósticos antiguos
            for diagnostico in registro.diagnosticos_clinico:
                self.session.delete(diagnostico)
            
            # Agregar nuevos diagnósticos
            if diag_clinico_vals:
                for diagnostico in diag_clinico_vals:
                    nuevo_diagnostico = DiagnosticosClinico(
                        examen_id=registro.id,
                        diagnostico=diagnostico
                    )
                    self.session.add(nuevo_diagnostico)
            
            self.session.commit()
            ui.notify('Registro actualizado exitosamente', type='positive')
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al actualizar el examen estomatológico: {str(e)}')
            ui.notify(f'Error al actualizar: {str(e)}', type='negative')
            return False

    def eliminar_examen(self, examen):
        try:
            self.session.delete(examen)
            self.session.commit()
            ui.notify('Examen de estomatologia eliminado correctamente', type='positive')
            return True
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el examen de estomatologia: {str(e)}')  
            ui.notify(f'Error al eliminar el examen: {str(e)}', type='negative')
            return False