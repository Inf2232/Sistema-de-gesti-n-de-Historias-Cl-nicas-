# controllers/historia_clinica_app_controller.py
from datetime import datetime
from models import AntecedentePatologicoPersonal, PatologiaPersonal
from Errores import log_error_and_notify

class AntecedentesPersonalesController:
    def __init__(self, session):
        # Recibe la sesión compartida de la aplicación para mantener el contexto del objeto paciente
        self.session = session

    def obtener_antecedentes_procesados(self, paciente):
        """Filtra, extrae el último diagnóstico y ordena cronológicamente el historial."""
        if not paciente or not hasattr(paciente, 'antecedentes_personales') or not paciente.antecedentes_personales:
            return [], None
        
        antecedentes = [
            ant for ant in paciente.antecedentes_personales
            if ant.fecha_registro and ant.patologias
        ]
        
        ultimo = max(
            antecedentes,
            key=lambda x: x.fecha_registro,
            default=None
        )
        
        ant_sorted = sorted(
            paciente.antecedentes_personales,
            key=lambda x: x.fecha_registro,
            reverse=True
        )
        return ant_sorted, ultimo

    def guardar_antecedente(self, paciente_id, fecha_str, patologias_data):
        """Valida las reglas de negocio e inserta un antecedente con sus patologías."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
            
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            antecedente = AntecedentePatologicoPersonal(paciente_id=paciente_id, fecha_registro=fecha_registro)
            
            if not patologias_data:
                return False, 'Debe seleccionar al menos una patología'
            
            for pat in patologias_data:
                tipo = pat['tipo']
                anios = pat['anios']
                meses = pat['meses']
                
                # Validaciones de reglas de negocio
                if tipo != 'No tiene' and not (anios or meses):
                    return False, f'Debe completar el tiempo para: {tipo}'
                if meses and meses > 11:
                    return False, 'Los meses deben ser un valor entre 0 y 11'
                
                antecedente.patologias.append(
                    PatologiaPersonal(tipo_patologia=tipo, tiempo_anios=anios or 0, tiempo_meses=meses or 0)
                )
            
            self.session.add(antecedente)
            self.session.commit()
            return True, 'Antecedente guardado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al guardar nuevo antecedente personal')
            return False, f'Error al guardar: {str(e)}'

    def actualizar_antecedente(self, antecedente_id, fecha_str, patologias_data):
        """Modifica un antecedente existente reemplazando su colección de patologías."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
            
            antecedente = self.session.get(AntecedentePatologicoPersonal, antecedente_id)
            if not antecedente:
                return False, 'El antecedente clínico solicitado no existe'
            
            antecedente.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Limpiamos las patologías previas de la relación
            antecedente.patologias = []
            
            if not patologias_data:
                return False, 'Debe seleccionar al menos una patología'
            
            for pat in patologias_data:
                tipo = pat['tipo']
                anios = pat['anios']
                meses = pat['meses']
                
                if tipo != 'No tiene' and not (anios or meses):
                    return False, f'Debe completar el tiempo para: {tipo}'
                if meses and meses > 11:
                    return False, 'Los meses deben estar entre 0 y 11'
                
                antecedente.patologias.append(
                    PatologiaPersonal(tipo_patologia=tipo, tiempo_anios=anios or 0, tiempo_meses=meses or 0)
                )
            
            self.session.commit()
            return True, 'Actualizado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar antecedente personal')
            return False, f'Error al actualizar: {str(e)}'

    def eliminar_antecedente(self, antecedente_id):
        """Elimina físicamente el registro de antecedentes por ID."""
        try:
            antecedente = self.session.get(AntecedentePatologicoPersonal, antecedente_id)
            if not antecedente:
                return False, 'El antecedente ya no existe en el sistema'
            
            self.session.delete(antecedente)
            self.session.commit()
            return True, 'Antecedente eliminado correctamente'
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el antecedente ID {antecedente_id}')
            return False, f'Error al eliminar el antecedente: {str(e)}'