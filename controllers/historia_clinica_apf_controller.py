# controllers/historia_clinica_apf_controller.py
from datetime import datetime
from models import AntecedentePatologicoFamiliarNoDiabetesMellitus, PatologiaFamiliarNoDiabetes
from Errores import log_error_and_notify

class AntecedentesFamiliaresController:
    def __init__(self, session):
        # Mantenemos la sesión activa de la aplicación para preservar el scope del paciente
        self.session = session

    def obtener_antecedentes_procesados(self, paciente):
        """Procesa la colección de antecedentes familiares, extrayendo el último y ordenando cronológicamente."""
        if not paciente or not hasattr(paciente, 'antecedentes_familiares') or not paciente.antecedentes_familiares:
            return [], None
        
        # Filtrar registros válidos que posean fecha de registro y patologías
        antecedentes_validos = [
            ant for ant in paciente.antecedentes_familiares
            if ant.fecha_registro and ant.patologias
        ]
        
        ultimo = max(
            antecedentes_validos,
            key=lambda x: x.fecha_registro,
            default=None
        )
        
        ant_ordenados = sorted(
            paciente.antecedentes_familiares,
            key=lambda x: x.fecha_registro,
            reverse=True
        )
        return ant_ordenados, ultimo

    def guardar_antecedente(self, paciente_id, fecha_str, nombres_patologias):
        """Valida las reglas médicas e inserta un nuevo bloque de APF con sus relaciones."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
            
            if not nombres_patologias:
                return False, 'Debe seleccionar o escribir al menos una patología'

            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            nuevo_antecedente = AntecedentePatologicoFamiliarNoDiabetesMellitus(
                paciente_id=paciente_id, 
                fecha_registro=fecha_registro
            )
            
            # Construcción dinámica de la colección relacional
            for nombre in nombres_patologias:
                nuevo_antecedente.patologias.append(
                    PatologiaFamiliarNoDiabetes(tipo_patologia=nombre)
                )
                
            self.session.add(nuevo_antecedente)
            self.session.commit()
            return True, 'Antecedente familiar guardado correctamente'
            
        except Exception as e:
            self.session.rollback()
            return False, f'Error en base de datos: {str(e)}'

    def actualizar_antecedente(self, antecedente_id, fecha_str, nombres_patologias):
        """Actualiza la fecha y reconstruye de manera limpia la matriz de patologías asociadas."""
        try:
            if not fecha_str:
                return False, 'Debe seleccionar una fecha'
                
            if not nombres_patologias:
                return False, 'Debe seleccionar al menos una patología'

            antecedente = self.session.get(AntecedentePatologicoFamiliarNoDiabetesMellitus, antecedente_id)
            if not antecedente:
                return False, 'El registro clínico solicitado ya no existe'

            antecedente.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Reemplazo atómico de la colección
            antecedente.patologias = [
                PatologiaFamiliarNoDiabetes(tipo_patologia=nombre) for nombre in nombres_patologias
            ]
            
            self.session.commit()
            return True, 'Antecedente familiar actualizado con éxito'
            
        except Exception as e:
            self.session.rollback()
            return False, f'Error al actualizar: {str(e)}'

    def eliminar_antecedente(self, antecedente_id):
        """Remueve físicamente el registro de la base de datos por su Identificador Único."""
        try:
            antecedente = self.session.get(AntecedentePatologicoFamiliarNoDiabetesMellitus, antecedente_id)
            if not antecedente:
                return False, 'El antecedente ya ha sido removido del sistema'
                
            self.session.delete(antecedente)
            self.session.commit()
            return True, 'Antecedente eliminado correctamente'
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el antecedente familiar ID {antecedente_id}')
            return False, f'Error al eliminar el antecedente: {str(e)}'