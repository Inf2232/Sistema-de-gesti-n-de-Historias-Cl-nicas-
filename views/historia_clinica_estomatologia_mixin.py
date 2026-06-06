

from datetime import datetime

from nicegui import ui
from seguridad_roles import tiene_permiso
# Importas el controlador desde la ruta donde lo guardes
from controllers.historia_clinica_estomatologia_controller import EstomatologiaController 

from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)

class HistoriaClinicaEstomatologiaMixin:
    
    def _get_controller(self):
        # Devuelve el controlador asegurando que use la sesión y paciente actuales de la vista
        return EstomatologiaController(self.session, self.paciente)

    @ui.refreshable
    def mostrar_estomatologia(self):
        with ui.column().classes('w-full p-4'):
            with ui.element('div').classes('row q-col-gutter-lg w-full'):
                                
                with ui.element('div').classes('col-12 col-md-6'):
                    # Resumen de Exámenes Estomatológicos
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('justify-between items-center'):
                            ui.label('Exámenes Estomatológicos').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso('estomatologia_manage'):
                                ui.button('Agregar Nuevo', icon='add', on_click=self.agregar_estomatologia).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                        
                        examenes = self.paciente.estomatologia
                        if examenes:
                            # Obtener el último examen
                            ultimo_examen = max(examenes, key=lambda x: x.fecha_registro)
                            with ui.card().classes(HC_SECTION_CARD):
                                with ui.column().classes('gap-4'):
                                    ui.label(f'Último examen: {ultimo_examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-700 font-medium')
                                    
                                    # Sección de Examen Funcional
                                    with ui.grid(columns=2):
                                        ui.label('Examen Funcional').classes('text-sm font-medium text-gray-600')
                                        ui.label(ultimo_examen.examen_funcional or "No registrado").classes('text-gray-600')

                                        ui.label('Diagnósticos Epidemiológicos').classes('text-sm font-medium text-gray-600')
                                        ui.label(ultimo_examen.diagnosticos_epidemiologicos or "No registrado").classes('text-gray-600')

                                        ui.label('Diagnóstico Clínico').classes('text-sm font-medium text-gray-600')
                                        with ui.column().classes("border rounded-lg"):  
                                            if ultimo_examen.diagnosticos_clinico:
                                                for diagnostico in ultimo_examen.diagnosticos_clinico:
                                                    ui.label(diagnostico.diagnostico or "No registrado").classes('text-gray-600')
                                            else:
                                                ui.label("No registrado").classes('text-gray-600')
                                        ui.label('Pronóstico').classes('text-sm font-medium text-gray-600')
                                        ui.label(ultimo_examen.pronostico or "No registrado").classes('text-gray-600')

                                        ui.label('Tratamiento').classes('text-sm font-medium text-gray-600')
                                        ui.label(ultimo_examen.tratamiento or "No registrado").classes('text-gray-600')
                        else:
                            ui.label('No hay exámenes estomatológicos registrados').classes('text-gray-500 italic')

                with ui.element('div').classes('col-12 col-md-6'):                         
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        ui.label('Historial Completo').classes(HEADER_TITLE_CLASSES)
                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            with ui.card().classes(HC_SECTION_CARD):
                                if examenes:
                                    examenes_ordenados = sorted(examenes, key=lambda x: x.fecha_registro, reverse=True)
                                    with ui.column().classes('w-full gap-4'):
                                        for examen in examenes_ordenados:
                                            with ui.card().classes(HC_SECTION_CARD):
                                                with ui.row().classes('justify-between items-center'):
                                                    ui.label(f'Fecha: {examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-700 font-medium')
                                                    with ui.row().classes('gap-2'):
                                                        if tiene_permiso('estomatologia_manage'):
                                                            ui.button(icon='edit', on_click=lambda e, ex=examen: self.editar_estomatologia(ex)).props('flat round dense').classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                                                            ui.button(icon='delete', on_click=lambda e, ex=examen: self.eliminar_estomatologia(ex)).props('flat round dense').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                                                    
                                                with ui.column().classes('gap-4'):
                                                    with ui.grid(columns=2):
                                                        ui.label('Examen Funcional').classes('text-sm font-medium text-gray-600')
                                                        ui.label(examen.examen_funcional or "No registrado").classes('text-gray-600')

                                                        ui.label('Diagnósticos Epidemiológicos').classes('text-sm font-medium text-gray-600')
                                                        ui.label(examen.diagnosticos_epidemiologicos or "No registrado").classes('text-gray-600')

                                                        ui.label('Diagnóstico Clínico').classes('text-sm font-medium text-gray-600')
                                                        with ui.column().classes("border rounded-lg"):  
                                                            if examen.diagnosticos_clinico:
                                                                for diagnostico in examen.diagnosticos_clinico:
                                                                    ui.label(diagnostico.diagnostico or "No registrado").classes('text-gray-600')
                                                            else:
                                                                ui.label("No registrado").classes('text-gray-600')

                                                        ui.label('Pronóstico').classes('text-sm font-medium text-gray-600')
                                                        ui.label(examen.pronostico or "No registrado").classes('text-gray-600')

                                                        ui.label('Tratamiento').classes('text-sm font-medium text-gray-600')
                                                        ui.label(examen.tratamiento or "No registrado").classes('text-gray-600')
                                else:
                                    ui.icon('info').classes('text-gray-400 text-4xl mb-2')
                                    ui.label('No hay registros de exámenes estomatológicos').classes('text-gray-500 italic')

    def agregar_estomatologia(self):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6'):
            ui.label('Nuevo Examen Estomatológico').classes(HEADER_TITLE_CLASSES)
            
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
            
            examen_funcional = ui.select(['Sin Alteraciones', 'Con Alteraciones'], label='Examen Funcional').classes(INPUT_CLASSES + ' w-64').props('stack-label outlined dense')
            diag_epidemiologicos = ui.select(['Enfermo', 'Sano C. Riesgo','Sano','Discapacitado'], label='Diagnostico Epidemiologico').classes(INPUT_CLASSES + ' w-64').props('stack-label outlined dense')
            diag_clinico = ui.select(['Caries', 'Periodontopatia','Disfuncion Masticatoria'], label='Diagnostico Clinico', multiple=True).classes(INPUT_CLASSES + ' w-64').props('stack-label outlined dense')
            pronostico = ui.select(['Favorable', 'No favorable'], label='Pronostico').classes(INPUT_CLASSES + ' w-64').props('stack-label outlined dense')
            tratamiento = ui.textarea(label='Tratamiento', value="Remisión APS").props('autogrow').classes('w-full mb-4').props('stack-label outlined dense')
            
            def guardar():
                ctrl = self._get_controller()
                exito = ctrl.guardar_examen(
                    fecha_str=fecha_input.value,
                    examen_funcional=examen_funcional.value,
                    diag_epidemiologicos=diag_epidemiologicos.value,
                    pronostico=pronostico.value,
                    tratamiento=tratamiento.value,
                    diag_clinico_vals=diag_clinico.value
                )
                if exito:
                    dialog.close()
                    self.mostrar_estomatologia.refresh()
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def editar_estomatologia(self, registro):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6'):
            ui.label('Editar Examen Estomatológico').classes(HEADER_TITLE_CLASSES)
            
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
            
            examen_funcional = ui.select(['Sin Alteraciones', 'Con Alteraciones'], label='Examen Funcional', value=registro.examen_funcional).classes(INPUT_CLASSES+ ' w-64').props('stack-label outlined')
            diag_epidemiologicos = ui.select(['Enfermo', 'Sano C. Riesgo','Sano','Discapacitado'], label='Diagnostico Epidemiologico', value=registro.diagnosticos_epidemiologicos).classes(INPUT_CLASSES+ ' w-64').props('stack-label outlined')

            diagnosticos_actuales = [d.diagnostico for d in registro.diagnosticos_clinico]
            diag_clinico = ui.select(['Caries', 'Periodontopatia','Disfuncion Masticatoria'], 
                                label='Diagnostico Clinico', 
                                value=diagnosticos_actuales or "No Registrado",
                                multiple=True).classes(INPUT_CLASSES+ ' w-64').props('stack-label outlined')

            pronostico = ui.select(['Favorable', 'No favorable'], label='Pronostico', value=registro.pronostico).classes(INPUT_CLASSES+ ' w-64').props('stack-label outlined')
            tratamiento = ui.textarea(label='Tratamiento', value=registro.tratamiento).props('autogrow').classes('w-full mb-4').props('stack-label outlined')
            
            def actualizar():
                ctrl = self._get_controller()
                exito = ctrl.actualizar_examen(
                    registro=registro,
                    fecha_str=fecha_input.value,
                    examen_funcional=examen_funcional.value,
                    diag_epidemiologicos=diag_epidemiologicos.value,
                    pronostico=pronostico.value,
                    tratamiento=tratamiento.value,
                    diag_clinico_vals=diag_clinico.value
                )
                if exito:
                    dialog.close()
                    self.mostrar_estomatologia.refresh()
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar Cambios', on_click=actualizar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def eliminar_estomatologia(self, examen):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar este examen de estomatologia?')
            
            def confirmar():
                ctrl = self._get_controller()
                if ctrl.eliminar_examen(examen):
                    self.mostrar_estomatologia.refresh()
                dialog.close()

            with ui.row().classes('w-full justify-end gap-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=confirmar).classes(DANGER_BUTTON_CLASSES).props('color="error"')
        
        dialog.open()