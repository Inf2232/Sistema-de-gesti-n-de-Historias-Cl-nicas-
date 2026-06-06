# historia_clinica_cardiologia_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
# Importamos el controlador correspondiente
from controllers.historia_clinica_cardiologia_controller import HistoriaClinicaCardiologiaController

from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)

class HistoriaClinicaCardiologiaMixin:

    @property
    def controlador_cardiologia(self):
        """Inicializa de forma bajo demanda el controlador con la sesión activa."""
        if not hasattr(self, '_controlador_cardiologia'):
            self._controlador_cardiologia = HistoriaClinicaCardiologiaController(self.session)
        return self._controlador_cardiologia

    @ui.refreshable
    def mostrar_cardiologia(self):
        with ui.column().classes('w-full'):
            # Header principal con estadísticas
            with ui.card().classes(HC_CARD_PROFESSIONAL):
                with ui.row().classes('justify-between items-center p-6'):
                    with ui.column().classes('space-y-2'):
                        ui.label('Cardiología').classes(HEADER_TITLE_CLASSES)
                        ui.label('Gestión de exámenes cardiológicos y evaluación de riesgo coronario').classes('text-gray-600')
                    
                    with ui.row().classes('items-center space-x-4'):
                        # Estadísticas rápidas
                        examenes = self.paciente.cardiologia
                        total_examenes = len(examenes) if examenes else 0
                        
                        with ui.card().classes(HC_SECTION_CARD):
                            with ui.column().classes('items-center'):
                                ui.label(str(total_examenes)).classes('text-2xl font-bold text-red-600')
                                ui.label('Exámenes').classes('text-xs text-gray-500 uppercase tracking-wide')
                        if tiene_permiso('cardiologia_manage'):
                            ui.button('Nuevo Examen', icon='add_circle', on_click=self.agregar_cardiologia).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

            # Layout principal
            with ui.element('div').classes('row q-col-gutter-lg w-full'):
                                
                with ui.element('div').classes('col-12 col-md-6'):
                    # Tarjeta de último examen
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('Último Examen Cardiológico').classes('text-white font-semibold text-lg')
                        
                        if examenes:
                            ultimo_examen = max(examenes, key=lambda x: x.fecha_registro)
                            with ui.column().classes('p-6 space-y-4'):
                                # Fecha destacada
                                with ui.row().classes('items-center justify-between bg-gray-50 p-3 rounded-lg'):
                                    ui.icon('event').classes('text-red-500 text-xl')
                                    ui.label(f'{ultimo_examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-700 font-medium')
                                    ui.badge('Último', color='red').classes('text-xs')
                                
                                # Información del EKG
                                with ui.card().classes(HC_SECTION_CARD):
                                    with ui.row().classes('items-center mb-2'):
                                        ui.icon('monitor_heart').classes('text-blue-600 mr-2')
                                        ui.label('Electrocardiograma').classes('text-blue-800 font-semibold')
                                    
                                    ui.label(ultimo_examen.ekg or "No registrado").classes('text-gray-700')
                                
                                # Riesgo coronario con indicador visual
                                resultado_riesgo = ultimo_examen.calcular_riesgo_coronario()
                                if resultado_riesgo and resultado_riesgo["riesgo"] is not None:
                                    riesgo_color = resultado_riesgo["color"]
                                    with ui.card().classes(f'bg-{riesgo_color}-50 border-l-4 border-{riesgo_color}-400 p-4'):
                                        with ui.row().classes('items-center justify-between mb-2'):
                                            ui.label('Riesgo Coronario a 10 años').classes(f'text-{riesgo_color}-800 font-semibold')
                                            ui.icon('warning').classes(f'text-{riesgo_color}-600')
                                        
                                        with ui.row().classes('items-center space-x-3'):
                                            ui.icon('favorite').classes(f'text-{riesgo_color}-500 text-2xl')
                                            ui.label(f"{resultado_riesgo['riesgo']}%").classes(f'text-{riesgo_color}-700 text-2xl font-bold')
                                            
                                            # Indicador de nivel de riesgo
                                            riesgo_nivel = (
                                                "Bajo" if 1 <= resultado_riesgo['riesgo'] <= 4 else
                                                "Moderado" if 5 <= resultado_riesgo['riesgo'] <= 9 else
                                                "Alto" if 10 <= resultado_riesgo['riesgo'] <= 19 else
                                                "Muy Alto" if 20 <= resultado_riesgo['riesgo'] <= 30 else
                                                "Crítico" if resultado_riesgo['riesgo'] > 30 else
                                                "Fuera de rango"
                                            )
                                            ui.badge(riesgo_nivel, color=riesgo_color).classes('text-xs')
                                else:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        ui.label('Riesgo Coronario').classes('text-gray-800 font-semibold mb-2')
                                        ui.label(resultado_riesgo["error"] ).classes('text-gray-600 italic')
                        else:
                            # Estado vacío mejorado
                            with ui.column().classes('p-6 items-center text-center space-y-4'):
                                ui.icon('monitor_heart_off').classes('text-gray-400 text-6xl')
                                ui.label('No hay exámenes registrados').classes('text-gray-600 text-lg font-medium')
                                ui.label('Agrega el primer examen cardiológico para comenzar').classes('text-gray-500 text-sm')

                # Panel derecho - Historial completo
                with ui.element('div').classes('col-12 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.card().classes(HC_SECTION_CARD):
                            with ui.row().classes('items-center justify-between'):
                                ui.label('Historial Completo').classes(HEADER_TITLE_CLASSES)
                                ui.badge(f'{total_examenes} registros', color='white').classes('bg-white/20 text-white')
                        
                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            if examenes:
                                examenes_ordenados = sorted(examenes, key=lambda x: x.fecha_registro, reverse=True)
                                with ui.column().classes('space-y-4'):
                                    for i, examen in enumerate(examenes_ordenados):
                                        with ui.card().classes(HC_SECTION_CARD):
                                            # Header de la tarjeta
                                            with ui.row().classes('justify-between items-center p-4 bg-gradient-to-r from-indigo-50 to-purple-50'):
                                                with ui.row().classes('items-center space-x-3'):
                                                    ui.icon('event_note').classes('text-indigo-600')
                                                    ui.label(f'Examen #{len(examenes_ordenados) - i}').classes('text-indigo-800 font-semibold')
                                                    ui.label(f'{examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-600')
                                                
                                                with ui.row().classes('space-x-1'):
                                                    if tiene_permiso('cardiologia_manage'):
                                                        ui.button(icon='edit', on_click=lambda e, ex=examen: self.editar_cardiologia(ex)).props('flat round dense').classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                                                        ui.button(icon='delete', on_click=lambda e, ex=examen: self.eliminar_cardiologia(ex)).props('flat round dense').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                                            
                                            # Contenido de la tarjeta
                                            with ui.column().classes('p-4 space-y-3'):
                                                # EKG
                                                with ui.grid(columns=2).classes('gap-4'):
                                                    with ui.card().classes(HC_SECTION_CARD):
                                                        ui.label('EKG').classes('text-blue-800 font-medium text-sm mb-1')
                                                        ui.label(examen.ekg or "No registrado").classes('text-gray-700')
                                                
                                                # Riesgo coronario
                                                resultado_riesgo = examen.calcular_riesgo_coronario()
                                                if resultado_riesgo and resultado_riesgo["riesgo"] is not None:
                                                    riesgo_color = resultado_riesgo["color"]
                                                    with ui.card().classes(f'bg-{riesgo_color}-50 p-3 rounded-lg'):
                                                        with ui.row().classes('items-center justify-between'):
                                                            ui.label('Riesgo Coronario').classes(f'text-{riesgo_color}-800 font-medium text-sm')
                                                            ui.label(f"{resultado_riesgo['riesgo']}%").classes(f'text-{riesgo_color}-700 font-bold')
                            else:
                                # Estado vacío del historial
                                with ui.column().classes('items-center justify-center h-64 text-center space-y-4'):
                                    ui.icon('history').classes('text-gray-400 text-5xl')
                                    ui.label('Sin historial').classes('text-gray-600 text-lg font-medium')
                                    ui.label('Los exámenes aparecerán aquí').classes('text-gray-500 text-sm')

    def agregar_cardiologia(self):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6').style("width:760px; max-width:none;"):
            ui.label('Nuevo Examen Cardiológico').classes(HEADER_TITLE_CLASSES)
            
            # Sección 1: Datos básicos del EKG
            with ui.grid(columns=2):
                with ui.card().classes(HC_CARD_PROFESSIONAL):
                    ui.label('Datos del Electrocardiograma').classes('text-lg font-medium text-blue-800 mb-2')
                    
                    # Fecha del examen
                    with ui.input('Fecha ').classes('w-full mb-4') as fecha_input:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(fecha_input).props(
                                    f'locale="es" '
                                    f'default-year-month={self.current_month} '
                                    f':options="date => date <= \'{self.today}\'"'
                                ).classes('shadow-lg'):
                                with ui.row().classes('justify-end p-2'):
                                    ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                            with fecha_input.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
                    
                    # Campo EKG
                    ekg_options = {
                        'eac': ui.checkbox('Alteraciones compatibles con EAC'),
                        'conduccion': ui.checkbox('Alteraciones en la conducción AV'),
                        'taquiarritmia': ui.checkbox('Taquiarritmia'),
                        'normal': ui.checkbox('Normal'),
                        'otras': ui.checkbox('Otras alteraciones')
                    }
                    
                    # Subopciones para EAC
                    with ui.column().bind_visibility_from(ekg_options['eac'], 'value').classes('ml-8 gap-2 bg-blue-100 p-2 rounded'):
                        ui.label('Tipo de alteración EAC:').classes('text-sm font-medium')
                        eac_suboptions = {
                            'st_elevado': ui.checkbox('Aumento ST'),
                            'st_deprimido': ui.checkbox('Disminución ST'),
                            't_negativo': ui.checkbox('T negativo')
                        }
                    
                    # Subopciones para Taquiarritmia
                    with ui.column().bind_visibility_from(ekg_options['taquiarritmia'], 'value').classes('ml-8 gap-2 bg-blue-100 p-2 rounded'):
                        ui.label('Tipo de taquiarritmia:').classes('text-sm font-medium')
                        taquiarritmia_suboptions = {
                            'supraventricular': ui.checkbox('Supraventricular'),
                            'ventricular': ui.checkbox('Ventricular')
                        }
                    
                    # Campo para otras alteraciones
                    otras_alteraciones = ui.textarea('Especifique otras alteraciones').props('autogrow').classes('w-full mt-2')
                    otras_alteraciones.bind_visibility_from(ekg_options['otras'], 'value')

                # Sección de riesgo coronario
                with ui.card().classes(HC_SECTION_CARD):
                    ui.label('Cálculo de Riesgo Coronario').classes('text-lg font-medium text-green-800 mb-2')
                    
                    # Obtener datos del paciente
                    examenes_complementarios = self.paciente.complementarios
                    ultimo_examen_complementario = max(examenes_complementarios, key=lambda x: x.fecha_registro) if examenes_complementarios else None
                    ultimo_habito = next(iter(sorted(self.paciente.habitos_toxicos, 
                                                    key=lambda x: x.fecha_registro, 
                                                    reverse=True)), None) if self.paciente.habitos_toxicos else None
                    
                    with ui.column().classes('gap-4'):
                        ui.label('Parámetros para cálculo de riesgo OMS').classes('text-sm font-medium text-gray-700')
                        
                        # Campos para el cálculo de riesgo
                        sexo = ui.select(['Masculino', 'Femenino'], label='Sexo', value=self.paciente.sexo).classes(INPUT_CLASSES).props('stack-label outlined')
                        edad = ui.number(
                            label='Edad', 
                            value=self.paciente.edad_actual if isinstance(self.paciente.edad_actual, int) else 50,
                            validation={
                                'Fuera de rango (40-74)': lambda v: 40 <= v <= 74 if v is not None else True
                            }
                        ).classes(INPUT_CLASSES).props('stack-label outlined')
                        colesterol_total = ui.number(
                            label='Colesterol Total (mmol/L)', 
                            value=ultimo_examen_complementario.colesterol if ultimo_examen_complementario else 5.0,
                            validation={
                                'Rango permitido: 2 - 10': lambda v: 2 <= v <= 10 if v is not None else True
                            }
                        ).classes(INPUT_CLASSES).props('stack-label outlined')
                        presion_sistolica = ui.number(label='Presión Sistólica (mmHg)', min=90, max=200, value=120).classes(INPUT_CLASSES).props('stack-label outlined')
                        fuma = ui.select(['Si', 'No',"Ex Fumador"], label='Fumador', value=ultimo_habito.fuma if ultimo_habito  else 'No').classes(INPUT_CLASSES).props('stack-label outlined')
                        diabetes = ui.select(['Si', 'No'], label='Diabetes', value='Si' if self.paciente.tiempo_evolucion_anios > 0 else 'No').classes(INPUT_CLASSES + 'w-64').props('stack-label outlined')
                        calcular_riesgo = ui.checkbox('Calcular riesgo coronario', value=False).classes(INPUT_CLASSES).props('stack-label outlined')
            
            def guardar():
                # Reunir datos estructurados de opciones EKG
                opciones_ekg_dict = {k: v.value for k, v in ekg_options.items()}
                sub_eac_dict = {k: v.value for k, v in eac_suboptions.items()}
                sub_taqui_dict = {k: v.value for k, v in taquiarritmia_suboptions.items()}
                
                # Campos de cálculo estructurados
                formulario_riesgo = {
                    'sexo': sexo.value,
                    'edad': edad.value,
                    'colesterol_total': colesterol_total.value,
                    'presion_sistolica': presion_sistolica.value,
                    'fuma': fuma.value,
                    'diabetes': diabetes.value,
                    'calcular_riesgo': calcular_riesgo.value
                }

                # Llamada delegada al controlador
                exito = self.controlador_cardiologia.guardar_examen(
                    paciente=self.paciente,
                    fecha_str=fecha_input.value,
                    ekg_options=opciones_ekg_dict,
                    eac_suboptions=sub_eac_dict,
                    taquiarritmia_suboptions=sub_taqui_dict,
                    otras_alteraciones_val=otras_alteraciones.value,
                    formulario_riesgo=formulario_riesgo
                )
                
                if exito:
                    dialog.close()
                    self.mostrar_cardiologia.refresh()
            
            # Botones de acción
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color=warning')
                ui.button('Guardar Examen', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                
            dialog.open()

    def editar_cardiologia(self, registro):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6').style("width:760px; max-width:none;"):
            ui.label('Editar Examen Cardiológico').classes(HEADER_TITLE_CLASSES)
            with ui.grid(columns=2):
                with ui.card().classes(HC_CARD_PROFESSIONAL):
                    ui.label('Datos del Electrocardiograma').classes('text-lg font-medium text-blue-800 mb-2')
                    # Parsear el EKG existente para cargar los checkboxes
                    ekg_data = registro.ekg if registro.ekg else ""
                    ekg_normal = "Normal" in ekg_data
                    ekg_eac = "EAC:" in ekg_data
                    eac_st_elevado = "Aumento ST" in ekg_data if ekg_eac else False
                    eac_st_deprimido = "Disminución ST" in ekg_data if ekg_eac else False
                    eac_t_negativo = "T negativo" in ekg_data if ekg_eac else False
                    ekg_conduccion = "conducción AV" in ekg_data
                    ekg_taquiarritmia = "Taquiarritmia:" in ekg_data
                    taqui_supra = "Supraventricular" in ekg_data if ekg_taquiarritmia else False
                    taqui_ventricular = "Ventricular" in ekg_data if ekg_taquiarritmia else False
                    ekg_otras = "Otras:" in ekg_data
                    otras_text = ekg_data.split("Otras:")[1].strip() if ekg_otras else ""

                    # Fecha del examen
                    fecha_valor = registro.fecha_registro.strftime('%Y-%m-%d') if registro.fecha_registro else ''
                    with ui.input('Fecha del Examen', value=fecha_valor).classes('w-full mb-4') as fecha_input:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(fecha_input).props(
                                    f'locale="es" '
                                    f'default-year-month={self.current_month} '
                                    f':options="date => date <= \'{self.today}\'"'
                                ).classes('shadow-lg'):
                                with ui.row().classes('justify-end p-2'):
                                    ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                            with fecha_input.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
                    
                    # Opciones principales del EKG con valores existentes
                    ekg_options = {
                        'eac': ui.checkbox('Alteraciones compatibles con EAC', value=ekg_eac),
                        'conduccion': ui.checkbox('Alteraciones en la conducción AV', value=ekg_conduccion),
                        'taquiarritmia': ui.checkbox('Taquiarritmia', value=ekg_taquiarritmia),
                        'normal': ui.checkbox('Normal', value=ekg_normal),
                        'otras': ui.checkbox('Otras alteraciones', value=ekg_otras)
                    }
                    
                    # Subopciones para EAC
                    with ui.column().bind_visibility_from(ekg_options['eac'], 'value').classes('ml-8 gap-2 bg-blue-100 p-2 rounded'):
                        ui.label('Tipo de alteración EAC:').classes('text-sm font-medium')
                        eac_suboptions = {
                            'st_elevado': ui.checkbox('Aumento ST', value=eac_st_elevado),
                            'st_deprimido': ui.checkbox('Disminución ST', value=eac_st_deprimido),
                            't_negativo': ui.checkbox('T negativo', value=eac_t_negativo)
                        }
                    
                    # Subopciones para Taquiarritmia
                    with ui.column().bind_visibility_from(ekg_options['taquiarritmia'], 'value').classes('ml-8 gap-2 bg-blue-100 p-2 rounded'):
                        ui.label('Tipo de taquiarritmia:').classes('text-sm font-medium')
                        taquiarritmia_suboptions = {
                            'supraventricular': ui.checkbox('Supraventricular', value=taqui_supra),
                            'ventricular': ui.checkbox('Ventricular', value=taqui_ventricular)
                        }
                    
                    # Campo para otras alteraciones
                    otras_alteraciones = ui.textarea('Especifique otras alteraciones', value=otras_text).props('autogrow').classes('w-full mt-2')
                    otras_alteraciones.bind_visibility_from(ekg_options['otras'], 'value')
                
                # Sección de riesgo coronario
                with ui.card().classes(HC_SECTION_CARD):
                    ui.label('Cálculo de Riesgo Coronario').classes('text-lg font-medium text-green-800 mb-2')
                    
                    with ui.column().classes('gap-4'):
                        ui.label('Parámetros para cálculo de riesgo OMS').classes('text-sm font-medium text-gray-700')
                        
                        # Campos para el cálculo de riesgo con valores existentes
                        sexo = ui.select(['Masculino', 'Femenino'], label='Sexo', value=registro.sexo or 'Masculino').classes(INPUT_CLASSES).props('stack-label outlined')
                        edad = ui.number(
                            label='Edad', 
                            value=registro.edad if isinstance(registro.edad, int) else 50,
                            validation={
                                'Fuera de rango (40-74)': lambda v: 40 <= v <= 74 if v is not None else True
                            }
                        ).classes(INPUT_CLASSES).props('stack-label outlined')
                        colesterol_total = ui.number(
                            label='Colesterol Total (mmol/L)', 
                            value=registro.colesterol_total if isinstance(registro.colesterol_total, (int, float)) else 5.0,
                            validation={
                                'Rango permitido: 2 - 10': lambda v: 2 <= v <= 10 if v is not None else True
                            }
                        ).classes(INPUT_CLASSES).props('stack-label outlined')
                        presion_sistolica = ui.number(label='Presión Sistólica (mmHg)', min=90, max=200, value=registro.presion_sistolica or 120).classes(INPUT_CLASSES).props('stack-label outlined')
                        fuma = ui.select(['Si', 'No' ,"Ex Fumador"], label='Fumador', value=registro.fuma or 'No').classes(INPUT_CLASSES).props('stack-label outlined')
                        diabetes = ui.select(['Si', 'No'], label='Diabetes', value=registro.diabetes or 'Si').classes(INPUT_CLASSES + 'w-64').props('stack-label outlined')
                        
                        recalcular_riesgo = ui.checkbox('Recalcular riesgo coronario', value=True).classes('w-full')
                        
                        # Mostrar resultados existentes si los hay
                        if registro.riesgo_oms is not None:
                            with ui.grid(columns=2).classes('w-full bg-blue-50 p-4 rounded-lg'):
                                ui.label('Riesgo actual:').classes('text-sm font-medium text-gray-600')
                                with ui.row().classes('items-center'):
                                    ui.icon('circle').classes(f'text-{registro.color_riesgo}-600 mr-2')
                                    ui.label(f"{registro.riesgo_oms}%").classes('text-lg font-bold')
                
                def actualizar():
                    # Mapeo estructurado para enviar al controlador
                    opciones_ekg_dict = {k: v.value for k, v in ekg_options.items()}
                    sub_eac_dict = {k: v.value for k, v in eac_suboptions.items()}
                    sub_taqui_dict = {k: v.value for k, v in taquiarritmia_suboptions.items()}
                    
                    formulario_riesgo = {
                        'sexo': sexo.value,
                        'edad': edad.value,
                        'colesterol_total': colesterol_total.value,
                        'presion_sistolica': presion_sistolica.value,
                        'fuma': fuma.value,
                        'diabetes': diabetes.value,
                        'recalcular_riesgo': recalcular_riesgo.value
                    }

                    # Ejecución delegada al controlador
                    exito = self.controlador_cardiologia.actualizar_examen(
                        registro=registro,
                        fecha_str=fecha_input.value,
                        ekg_options=opciones_ekg_dict,
                        eac_suboptions=sub_eac_dict,
                        taquiarritmia_suboptions=sub_taqui_dict,
                        otras_alteraciones_val=otras_alteraciones.value,
                        formulario_riesgo=formulario_riesgo
                    )
                    
                    if exito:
                        dialog.close()
                        self.mostrar_cardiologia.refresh()

            # Botones de acción
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color=warning')
                ui.button('Guardar Cambios', on_click=actualizar).props('color=primary').classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def eliminar_cardiologia(self, examen):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar este examen de cardiología?')
            
            with ui.row().classes('w-full justify-end gap-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color=warning')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_cardilogia(examen, dialog))\
                    .classes(DANGER_BUTTON_CLASSES).props('color="error"')
        
        dialog.open()

    def confirmar_eliminacion_cardilogia(self, examen, dialog):
        # El controlador se encarga de eliminar, manejar excepciones y enviar notificaciones
        if self.controlador_cardiologia.eliminar_examen(examen):
            self.mostrar_cardiologia.refresh()
        dialog.close()