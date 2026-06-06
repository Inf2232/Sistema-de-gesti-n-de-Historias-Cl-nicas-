# views/historia_clinica_apf_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    HC_CARD_PROFESSIONAL,
    HC_SECTION_CARD,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
)

class HistoriaClinicaApfMixin:
    
    def _inicializar_controlador_apf(self):
        """Garantiza la instanciación perezosa (lazy) del controlador usando la sesión de la vista."""
        if not hasattr(self, 'controlador_familiares'):
            from controllers.historia_clinica_apf_controller import AntecedentesFamiliaresController
            self.controlador_familiares = AntecedentesFamiliaresController(self.session)

    @ui.refreshable
    def mostrar_antecedentes_familiares(self):
        self._inicializar_controlador_apf()
        
        # Recuperamos datos puros procesados cronológicamente desde el controlador
        ant_ordenados, ultimo = self.controlador_familiares.obtener_antecedentes_procesados(self.paciente)

        with ui.column().classes('w-full p-6 gap-6 max-w-7xl mx-auto'):

            # HEADER RESPONSIVE
            with ui.row().classes('w-full justify-between items-center wrap q-col-gutter-md px-2'):
                with ui.column().classes('gap-1'):
                    ui.label('Antecedentes Patológicos Familiares').classes(HEADER_TITLE_CLASSES)
                    ui.label('Registro de enfermedades hereditarias y factores de riesgo familiar').classes('text-slate-400 text-sm pl-4')

                if tiene_permiso("ant_familiares_manage"):
                    ui.button(
                        'Añadir',
                        icon='group_add',
                        on_click=self.agregar_antecedente_familiar
                    ).classes(PRIMARY_BUTTON_CLASSES + ' px-6 shadow-lg')

            # GRID RESPONSIVE QUASAR
            with ui.row().classes('w-full q-col-gutter-lg wrap'):

                # =====================================================
                # COLUMNA IZQUIERDA: DIAGNÓSTICO CLAVE
                # =====================================================
                with ui.column().classes('col-12 col-lg-5 gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL + ' border-l-4 border-orange-400'):
                        ui.label('Diagnósticos Familiares Clave').classes('text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4')

                        if ultimo:
                            with ui.column().classes('w-full gap-4'):
                                with ui.row().classes('items-center gap-2 wrap'):
                                    ui.icon('calendar_today', color='orange-500', size='xs')
                                    ui.label(f'{ultimo.fecha_registro.strftime("%d/%m/%Y")}').classes('text-sm font-bold text-orange-800')

                                with ui.column().classes('w-full gap-3'):
                                    for pat in ultimo.patologias:
                                        with ui.row().classes('items-center justify-between wrap q-col-gutter-md p-4 bg-orange-50/30 rounded-xl border border-orange-100 hover:bg-orange-50 transition-colors'):
                                            with ui.row().classes('items-center gap-3 wrap'):
                                                ui.icon('family_restroom', color='orange-400', size='sm')
                                                with ui.column().classes('gap-0'):
                                                    ui.label(pat.tipo_patologia).classes('text-gray-700 font-bold leading-tight')
                                                    ui.label('Antecedente Directo').classes('text-[10px] text-orange-600 uppercase font-medium')
                                            ui.icon('chevron_right', color='orange-200')
                        else:
                            with ui.column().classes('w-full items-center py-12 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200'):
                                ui.icon('diversity_3', size='56px', color='slate-200')
                                ui.label('No hay datos familiares').classes('text-slate-400 font-medium mt-2')

                # =====================================================
                # COLUMNA DERECHA: HISTORIAL DE REGISTROS
                # =====================================================
                with ui.column().classes('col-12 col-lg-5 gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('items-center gap-2 mb-4 wrap'):
                            ui.icon('history', color='slate-400')
                            ui.label('Historial de Registros').classes('text-lg font-bold text-slate-700')

                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            if ant_ordenados:
                                for ant in ant_ordenados:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        # HEADER DE TARJETA CRONOLÓGICA
                                        with ui.row().classes('w-full bg-slate-50 p-2 px-4 justify-between items-center wrap q-col-gutter-sm'):
                                            ui.label(ant.fecha_registro.strftime("%d/%m/%Y")).classes('text-xs font-bold text-slate-600')

                                            with ui.row().classes('gap-1 wrap'):
                                                if tiene_permiso("ant_familiares_manage"):
                                                    ui.button(icon='edit', on_click=lambda e, a=ant: self.editar_antecedente_familiar(a)).props('flat dense size=sm color=primary').classes(PRIMARY_BUTTON_CLASSES)
                                                    ui.button(icon='delete', on_click=lambda e, a=ant: self.eliminar_antecedente_familiar(a)).props('flat dense size=sm color=error').classes(DANGER_BUTTON_CLASSES)

                                        # CONTENIDO DE PATOLOGÍAS
                                        with ui.column().classes('p-3 gap-2'):
                                            for p in ant.patologias:
                                                with ui.row().classes('items-center gap-2 wrap'):
                                                    ui.icon('fiber_manual_record', size='8px', color='orange-300')
                                                    ui.label(p.tipo_patologia).classes('text-sm text-slate-600')
                            else:
                                ui.label('Sin historial familiar').classes('text-slate-300 text-center w-full py-10')

    def agregar_antecedente_familiar(self):
        self._inicializar_controlador_apf()
        with ui.dialog() as dialog, ui.card().classes('w-[500px] p-4'):
            ui.label('Agregar Antecedente Patológico Familiar').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            
            checkboxes = {}
            otros_inputs = []
            
            with ui.column().classes('w-full gap-3 mt-4'):
                for patologia in self.patologias:
                    if patologia != 'Otros':
                        with ui.row().classes('items-center gap-2 w-full'):
                            checkboxes[patologia] = ui.checkbox(patologia).classes('mr-4')
                
                with ui.column().classes('gap-4 w-full mt-4'):
                    ui.label('Otros').classes('font-semibold text-gray-700')
                    contenedor_otros = ui.column().classes('gap-2 p-4 border border-gray-300 rounded-lg max-h-[150px] overflow-y-auto')

                    def agregar_input_otros():
                        with contenedor_otros:
                            with ui.row().classes('items-center gap-2 w-full') as fila:
                                input_nuevo = ui.input('Especifique').classes(f'flex-grow {INPUT_CLASSES}')
                                ui.button(icon='delete', on_click=lambda: (contenedor_otros.remove(fila), otros_inputs.remove(input_nuevo))).props('flat round dense color="negative"')
                                otros_inputs.append(input_nuevo)

                    ui.button('Agregar otro', icon='add', on_click=agregar_input_otros).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                    agregar_input_otros()

            def guardar():
                # Empaquetamos los nombres seleccionados en una lista pura de strings
                patologias_seleccionadas = [nombre for nombre, cb in checkboxes.items() if cb.value]
                
                for inp in otros_inputs:
                    valor = inp.value.strip()
                    if valor:
                        # Fragmentar si el médico ingresa elementos separados por coma
                        patologias_seleccionadas.extend([x.strip() for x in valor.split(',') if x.strip()])

                exito, msg = self.controlador_familiares.guardar_antecedente(
                    paciente_id=self.paciente.id,
                    fecha_str=fecha_input.value,
                    nombres_patologias=patologias_seleccionadas
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_antecedentes_familiares.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
        dialog.open()

    def editar_antecedente_familiar(self, antecedente):
        self._inicializar_controlador_apf()
        with ui.dialog() as dialog, ui.card().classes('w-[500px] p-4'):
            ui.label('Editar Antecedente Patológico Familiar').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha', value=antecedente.fecha_registro.strftime('%Y-%m-%d')) as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            
            checkboxes = {}
            otros_inputs = []
            
            with ui.column().classes('w-full gap-3 mt-4'):
                for patologia in self.patologias:
                    if patologia != 'Otros':
                        existente = next((p for p in antecedente.patologias if p.tipo_patologia == patologia), None)
                        checkboxes[patologia] = ui.checkbox(patologia, value=existente is not None).classes('mr-4')
                
                ui.label('Otros').classes('font-semibold text-gray-700 mt-2')
                contenedor_otros = ui.column().classes('gap-2 p-4 border border-gray-300 rounded-lg max-h-[150px] overflow-y-auto')

                def agregar_input_otros(valor_inicial=''):
                    with contenedor_otros:
                        with ui.row().classes('items-center gap-2 w-full') as fila:
                            input_nuevo = ui.input('Especifique', value=valor_inicial).classes(f'flex-grow {INPUT_CLASSES}')
                            ui.button(icon='delete', on_click=lambda: (contenedor_otros.remove(fila), otros_inputs.remove(input_nuevo))).props('flat round dense color="negative"')
                            otros_inputs.append(input_nuevo)

                patologias_otros_existentes = [p for p in antecedente.patologias if p.tipo_patologia not in self.patologias]
                for p_existente in patologias_otros_existentes:
                    agregar_input_otros(p_existente.tipo_patologia)
                    
                if not patologias_otros_existentes:
                    agregar_input_otros()
                    
                ui.button('Agregar otro', icon='add', on_click=lambda: agregar_input_otros()).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

            def guardar():
                patologias_seleccionadas = [nombre for nombre, cb in checkboxes.items() if cb.value]
                for inp in otros_inputs:
                    valor = inp.value.strip()
                    if valor:
                        patologias_seleccionadas.extend([x.strip() for x in valor.split(',') if x.strip()])

                # Pasamos el ID del antecedente para que el controlador lo recupere en su propio scope transaccional
                exito, msg = self.controlador_familiares.actualizar_antecedente(
                    antecedente_id=antecedente.id,
                    fecha_str=fecha_input.value,
                    nombres_patologias=patologias_seleccionadas
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_antecedentes_familiares.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
        dialog.open()

    def eliminar_antecedente_familiar(self, antecedente):
        self._inicializar_controlador_apf()
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este antecedente?').classes('text-xl font-bold mb-4')
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def confirmar():
                    exito, msg = self.controlador_familiares.eliminar_antecedente(antecedente.id)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_antecedentes_familiares.refresh()
                    else:
                        ui.notify(msg, type='negative')

                ui.button('Eliminar', on_click=confirmar).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            dialog.open()