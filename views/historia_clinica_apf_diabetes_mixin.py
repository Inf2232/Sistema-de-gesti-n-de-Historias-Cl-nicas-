# views/historia_clinica_apf_diabetes_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    HC_CARD_PROFESSIONAL,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
)

class HistoriaClinicaApfDiabetesMixin:
    
    def _inicializar_controlador_diabetes(self):
        """Lazy loading del controlador inyectándole la sesión activa."""
        if not hasattr(self, 'controlador_diabetes'):
            from controllers.historia_clinica_apf_diabetes_controller import AntecedentesDiabetesController
            self.controlador_diabetes = AntecedentesDiabetesController(self.session)

    @ui.refreshable
    def mostrar_apf_diabetes(self):
        self._inicializar_controlador_diabetes()
        
        # Consumo de datos crudos formateados desde el controlador lógico
        ordenados, ultimo = self.controlador_diabetes.obtener_antecedentes_procesados(self.paciente)

        with ui.column().classes('w-full p-6 gap-6 max-w-7xl mx-auto'):

            # HEADER RESPONSIVE
            with ui.row().classes('w-full justify-between items-center wrap q-col-gutter-md px-2'):
                with ui.column().classes('gap-1'):
                    ui.label('Antecedentes Familiares de Diabetes').classes(HEADER_TITLE_CLASSES)
                    ui.label('Mapeo genético y grados de parentesco con diagnóstico de DM').classes('text-slate-400 text-sm pl-4')

                if tiene_permiso("ant_fam_diabetes_manage"):
                    ui.button(
                        'Registrar Familiar',
                        icon='add_moderator',
                        on_click=self.agregar_antecedente_familiar_diabetes
                    ).classes(PRIMARY_BUTTON_CLASSES + ' px-6 shadow-lg')

            # GRID RESPONSIVE QUASAR
            with ui.row().classes('w-full q-col-gutter-lg wrap'):

                # ====================================================
                # COLUMNA IZQUIERDA: RESUMEN DE CARGA
                # ====================================================
                with ui.element('div').classes('col-12 col-lg-6'):
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_CARD_PROFESSIONAL + ' border-l-4 border-indigo-500'):
                            ui.label('Resumen de Carga Hereditaria').classes('text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4')

                            if ultimo:
                                with ui.column().classes('w-full gap-4'):
                                    with ui.row().classes('items-center justify-between wrap q-col-gutter-sm w-full'):
                                        ui.label(ultimo.fecha_registro.strftime("%d/%m/%Y")).classes('text-sm font-bold text-indigo-700 bg-indigo-50 px-4 py-1 rounded-full')
                                        ui.badge('Registro Activo', color='indigo-100').classes('text-indigo-800 shadow-none text-[10px]')

                                    with ui.column().classes('w-full gap-3 mt-2'):
                                        if ultimo.grados_parentezco:
                                            for grado in ultimo.grados_parentezco:
                                                with ui.row().classes('items-center gap-4 wrap q-col-gutter-md p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-indigo-200 transition-all'):
                                                    with ui.avatar('family_restroom', color='indigo-500', text_color='white').props('size=md'):
                                                        pass
                                                    with ui.column().classes('gap-0'):
                                                        ui.label('Grado de Parentesco').classes('text-[10px] text-slate-400 uppercase font-bold')
                                                        ui.label(grado.grado).classes('text-lg font-bold text-slate-700')
                            else:
                                with ui.column().classes('w-full items-center py-12 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200'):
                                    ui.icon('family_restroom', size='56px', color='slate-200')
                                    ui.label('Sin antecedentes de DM registrados').classes('text-slate-400 font-medium mt-2')

                # ====================================================
                # COLUMNA DERECHA: EVOLUCIÓN CRONOLÓGICA
                # ====================================================
                with ui.element('div').classes('col-12 col-lg-6'):
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_CARD_PROFESSIONAL):
                            with ui.row().classes('items-center gap-2 mb-4 wrap'):
                                ui.icon('history', color='slate-400')
                                ui.label('Evolución de Antecedentes').classes('text-lg font-bold text-slate-700')

                            with ui.scroll_area().classes('h-[500px] pr-4 bg-slate-50/20 rounded-lg p-2'):
                                if ordenados:
                                    for ant in ordenados:
                                        with ui.card().classes('w-full mb-4 p-0 border border-slate-100 shadow-none hover:shadow-sm transition-shadow'):
                                            with ui.row().classes('w-full bg-slate-50 p-3 justify-between items-center wrap q-col-gutter-sm border-b border-indigo-50'):
                                                ui.label(ant.fecha_registro.strftime("%d/%m/%Y")).classes('text-xs font-bold text-indigo-600')

                                                with ui.row().classes('gap-1 wrap'):
                                                    if tiene_permiso("ant_fam_diabetes_manage"):
                                                        ui.button(icon='edit', on_click=lambda e, a=ant: self.editar_antecedente_familiar_diabetes(a)).props('flat dense size=sm color=primary').classes(PRIMARY_BUTTON_CLASSES)
                                                        ui.button(icon='delete', on_click=lambda e, a=ant: self.eliminar_antecedente_familiar_diabetes(a)).props('flat dense size=sm color=error').classes(DANGER_BUTTON_CLASSES)

                                            with ui.column().classes('p-3 gap-2'):
                                                if ant.grados_parentezco:
                                                    for g in ant.grados_parentezco:
                                                        with ui.row().classes('items-center gap-2 wrap'):
                                                            ui.icon('fiber_manual_record', size='8px', color='indigo-300')
                                                            ui.label(g.grado).classes('text-sm text-slate-600 font-medium')
                                else:
                                    ui.label('No hay historial disponible').classes('text-slate-300 text-center w-full py-10')

    def agregar_antecedente_familiar_diabetes(self):
        self._inicializar_controlador_diabetes()
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Agregar Antecedente Familiar de Diabetes').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            
            parentesco_opciones = ["Ninguno", "Grado 1", "Grado 2", "Diabetes Gestacional"]
            parentesco_input = ui.select(options=parentesco_opciones, label='Parentesco', with_input=True, multiple=True).classes(INPUT_CLASSES)

            def guardar():
               
                exito, msg = self.controlador_diabetes.guardar_antecedente(
                    paciente_id=self.paciente.id,
                    fecha_str=fecha_input.value,
                    grados_seleccionados=parentesco_input.value  # <-- Aquí estaba el cambio necesario
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_apf_diabetes.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            dialog.open()

    def editar_antecedente_familiar_diabetes(self, antecedente):
        self._inicializar_controlador_diabetes()
        with ui.dialog().classes('w-full max-w-md') as dialog, ui.card().classes('w-full p-6 gap-4'):
            ui.label('Editar Antecedente Familiar de Diabetes').classes(HEADER_TITLE_CLASSES)
            
            fecha_valor = antecedente.fecha_registro.strftime('%Y-%m-%d') if antecedente.fecha_registro else ''
            with ui.input('Fecha', value=fecha_valor).classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"').classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            
            parentesco_opciones = ["Ninguno", "Grado 1", "Grado 2", "Diabetes Gestacional"]
            grados_actuales = [g.grado for g in antecedente.grados_parentezco] if antecedente.grados_parentezco else []
            if not grados_actuales and antecedente.id:
                grados_actuales = ["Ninguno"]
                
            parentesco_input = ui.select(
                options=parentesco_opciones, label='Grados de Parentesco', value=grados_actuales, multiple=True, with_input=True
            ).classes(INPUT_CLASSES).props('use-chips clearable')

            def guardar():
                exito, msg = self.controlador_diabetes.actualizar_antecedente(
                    antecedente_id=antecedente.id,
                    fecha_str=fecha_input.value,
                    grados_nuevos=parentesco_input.value
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    if hasattr(self, 'mostrar_apf_diabetes'):
                        self.mostrar_apf_diabetes.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar Cambios', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            dialog.open()

    def eliminar_antecedente_familiar_diabetes(self, antecedente):
        self._inicializar_controlador_diabetes()
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este antecedente familiar de diabetes?').classes('text-xl font-bold mb-4 text-red-600')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def confirmar():
                    exito, msg = self.controlador_diabetes.eliminar_antecedente(antecedente.id)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_apf_diabetes.refresh()
                    else:
                        ui.notify(msg, type='negative')
                        
                ui.button('Eliminar', on_click=confirmar).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            dialog.open()