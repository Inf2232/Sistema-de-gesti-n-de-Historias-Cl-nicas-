# controllers/historia_clinica_apf_diabetes_controller.py
from datetime import datetime
from models import AntecedentePatologicoFamiliarDiabetes, GradoParentezco
from Errores import log_error_and_notify

class AntecedentesDiabetesController:
    def __init__(self, session):
        # Mantenemos la sesión activa provista por el entorno principal
        self.session = session

    def obtener_antecedentes_procesados(self, paciente):
        """Procesa, calcula el último registro y ordena el historial de diabetes genético."""
        if not paciente or not hasattr(paciente, 'antecedentes_familiares_diabetes') or not paciente.antecedentes_familiares_diabetes:
            return [], None
        
        antecedentes_validos = [
            ant for ant in paciente.antecedentes_familiares_diabetes
            if ant.fecha_registro
        ]
        
        ultimo = max(
            antecedentes_validos,
            key=lambda x: x.fecha_registro,
            default=None
        )
        
        ordenados = sorted(
            paciente.antecedentes_familiares_diabetes,
            key=lambda x: x.fecha_registro,
            reverse=True
        )
        return ordenados, ultimo

    def guardar_antecedente(self, paciente_id, fecha_str, grados_seleccionados):
        """Valida e inserta un nuevo bloque de carga hereditaria de diabetes."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
            if not grados_seleccionados:
                return False, 'Debe especificar el parentesco'
            
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            antecedente = AntecedentePatologicoFamiliarDiabetes(
                paciente_id=paciente_id, 
                fecha_registro=fecha_registro
            )
            
            for grado in grados_seleccionados:
                antecedente.grados_parentezco.append(GradoParentezco(grado=grado))
                
            self.session.add(antecedente)
            self.session.commit()
            return True, 'Antecedente familiar de diabetes agregado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al agregar antecedente familiar de diabetes')
            return False, f'Error al agregar el antecedente familiar de diabetes: {str(e)}'

    def actualizar_antecedente(self, antecedente_id, fecha_str, grados_nuevos):
        """Ejecuta la lógica de negocio para actualizar fechas y realizar el diffing de relaciones hijo."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
            if not grados_nuevos:
                return False, 'Debe especificar al menos un grado de parentesco'
            
            antecedente = self.session.get(AntecedentePatologicoFamiliarDiabetes, antecedente_id)
            if not antecedente:
                return False, 'El registro clínico ya no existe en el sistema'
                
            antecedente.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            nuevos_grados_set = set(grados_nuevos)
            
            # =========================================================================
            # REGLA DE NEGOCIO: Aplicada directamente sobre los datos de entrada
            # Si viene "Ninguno" acompañado de otros grados reales, lo eliminamos del set
            # =========================================================================
            if "Ninguno" in nuevos_grados_set and len(nuevos_grados_set) > 1:
                nuevos_grados_set.remove("Ninguno")
            
            grados_existentes = {g.grado for g in antecedente.grados_parentezco}
            
            # 1. Remover grados que el médico desmarcó (si tenía "Ninguno" guardado y ahora marcó "Madre", aquí se eliminará)
            for grado in list(antecedente.grados_parentezco):
                if grado.grado not in nuevos_grados_set:
                    self.session.delete(grado)
            
            # 2. Insertar nuevos grados seleccionados (ya libre de "Ninguno" inconsistente)
            for grado in nuevos_grados_set:
                if grado not in grados_existentes:
                    antecedente.grados_parentezco.append(GradoParentezco(grado=grado))
         
            self.session.commit()
            return True, 'Antecedente familiar actualizado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar antecedente familiar de diabetes')
            return False, f'Error al actualizar: {str(e)}'

    def eliminar_antecedente(self, antecedente_id):
        """Elimina de manera segura un registro y limpia en cascada las claves hijas."""
        try:
            antecedente = self.session.get(AntecedentePatologicoFamiliarDiabetes, antecedente_id)
            if not antecedente:
                return False, 'El antecedente solicitado ya fue eliminado'
                
            self.session.delete(antecedente)
            self.session.commit()
            return True, 'Antecedente familiar de diabetes eliminado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el antecedente familiar de diabetes ID {antecedente_id}')
            return False, f'Error al eliminar el antecedente: {str(e)}'