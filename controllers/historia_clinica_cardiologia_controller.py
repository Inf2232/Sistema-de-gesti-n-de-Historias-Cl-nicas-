# controllers/historia_clinica_cardiologia_controller.py
from datetime import datetime
from models import Cardiologia
from Errores import log_error_and_notify
from nicegui import ui

class HistoriaClinicaCardiologiaController:
    def __init__(self, session):
        self.session = session

    def guardar_examen(self, paciente, fecha_str, ekg_options, eac_suboptions, taquiarritmia_suboptions, otras_alteraciones_val, formulario_riesgo):
        """Procesa y guarda un nuevo examen cardiológico."""
        if not fecha_str:
            ui.notify('La fecha es obligatoria', type='negative')
            return False
            
        try:
            # Construir descripción del EKG
            descripcion_ekg = []
            
            if ekg_options['eac']:
                eac_desc = []
                if eac_suboptions['st_elevado']: eac_desc.append("Aumento ST")
                if eac_suboptions['st_deprimido']: eac_desc.append("Disminución ST")
                if eac_suboptions['t_negativo']: eac_desc.append("T negativo")
                descripcion_ekg.append(f"Alteraciones compatibles con EAC: {', '.join(eac_desc)}")
            
            if ekg_options['conduccion']:
                descripcion_ekg.append("Alteraciones conducción AV")
            
            if ekg_options['taquiarritmia']:
                taqui_desc = []
                if taquiarritmia_suboptions['supraventricular']: taqui_desc.append("Supraventricular")
                if taquiarritmia_suboptions['ventricular']: taqui_desc.append("Ventricular")
                descripcion_ekg.append(f"Taquiarritmia: {', '.join(taqui_desc)}")
            
            if ekg_options['normal']:
                descripcion_ekg.append("Normal")
            
            if ekg_options['otras'] and otras_alteraciones_val:
                descripcion_ekg.append(f"Otras: {otras_alteraciones_val}")
            
            ekg_final = ". ".join(descripcion_ekg)

            # Crear el registro utilizando los parámetros pasados
            nuevo_registro = Cardiologia(
                paciente_id=paciente.id,
                fecha_registro=datetime.strptime(fecha_str, '%Y-%m-%d').date(),
                ekg=ekg_final,
                sexo=formulario_riesgo['sexo'],
                edad=formulario_riesgo['edad'],
                colesterol_total=formulario_riesgo['colesterol_total'],
                presion_sistolica=formulario_riesgo['presion_sistolica'],
                fuma=formulario_riesgo['fuma'],
                diabetes=formulario_riesgo['diabetes']
            )
            
            # Calcular riesgo si está marcado
            if formulario_riesgo['calcular_riesgo']:
                resultado_riesgo = nuevo_registro.calcular_riesgo_coronario()
                if resultado_riesgo and resultado_riesgo["riesgo"] is not None:
                    nuevo_registro.riesgo_oms = resultado_riesgo["riesgo"]
                    nuevo_registro.color_riesgo = resultado_riesgo["color"]
            
            self.session.add(nuevo_registro)
            self.session.commit()
            ui.notify('Registro guardado exitosamente', type='positive')
            return True
        
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al guardar el examen cardiológico: {str(e)}')
            ui.notify(f'Error al guardar: {str(e)}', type='negative')
            return False

    def actualizar_examen(self, registro, fecha_str, ekg_options, eac_suboptions, taquiarritmia_suboptions, otras_alteraciones_val, formulario_riesgo):
        """Procesa los cambios y actualiza un registro cardiológico existente."""
        if not fecha_str:
            ui.notify('La fecha es obligatoria', type='negative')
            return False
            
        try:
            # Construir descripción del EKG actualizada
            descripcion_ekg = []
            
            if ekg_options['eac']:
                eac_desc = []
                if eac_suboptions['st_elevado']: eac_desc.append("Aumento ST")
                if eac_suboptions['st_deprimido']: eac_desc.append("Disminución ST")
                if eac_suboptions['t_negativo']: eac_desc.append("T negativo")
                if eac_desc:
                    descripcion_ekg.append(f"Alteraciones compatibles con EAC: {', '.join(eac_desc)}")
            
            if ekg_options['conduccion']:
                descripcion_ekg.append("Alteraciones conducción AV")
            
            if ekg_options['taquiarritmia']:
                taqui_desc = []
                if taquiarritmia_suboptions['supraventricular']: taqui_desc.append("Supraventricular")
                if taquiarritmia_suboptions['ventricular']: taqui_desc.append("Ventricular")
                if taqui_desc:
                    descripcion_ekg.append(f"Taquiarritmia: {', '.join(taqui_desc)}")
            
            if ekg_options['normal']:
                descripcion_ekg.append("Normal")
            
            if ekg_options['otras'] and otras_alteraciones_val:
                descripcion_ekg.append(f"Otras: {otras_alteraciones_val}")
            
            ekg_final = ". ".join(descripcion_ekg)

            # Actualizar campos del registro
            registro.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            registro.ekg = ekg_final
            registro.sexo = formulario_riesgo['sexo']
            registro.edad = formulario_riesgo['edad']
            registro.colesterol_total = formulario_riesgo['colesterol_total']
            registro.presion_sistolica = formulario_riesgo['presion_sistolica']
            registro.fuma = formulario_riesgo['fuma']
            registro.diabetes = formulario_riesgo['diabetes']
            
            # Recalcular riesgo si está marcado
            if formulario_riesgo['recalcular_riesgo']:
                resultado_riesgo = registro.calcular_riesgo_coronario()
                if resultado_riesgo and resultado_riesgo["riesgo"] is not None:
                    registro.riesgo_oms = resultado_riesgo["riesgo"]
                    registro.color_riesgo = resultado_riesgo["color"]
            
            self.session.commit()
            ui.notify('Examen cardiológico actualizado', type='positive')
            return True
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al actualizar el examen cardiológico: {str(e)}')
            ui.notify(f'Error al actualizar: {str(e)}', type='negative')
            return False

    def eliminar_examen(self, examen):
        """Elimina un examen de la base de datos."""
        try:
            self.session.delete(examen)
            self.session.commit()
            ui.notify('Examen de cardiología eliminado correctamente', type='positive')
            return True
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el examen cardiológico: {str(e)}')  
            ui.notify(f'Error al eliminar el examen: {str(e)}', type='negative')
            return False