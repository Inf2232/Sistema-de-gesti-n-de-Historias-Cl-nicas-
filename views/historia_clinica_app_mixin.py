# views/historia_clinica_app_mixin.py
from datetime import datetime
from nicegui import ui, events
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

class HistoriaClinicaAppMixin:
    
    def _inicializar_controlador(self):
        """Garantiza la carga del controlador usando la sesión activa del Mixin."""
        if not hasattr(self, 'controlador_antecedentes'):
            from controllers.historia_clinica_app_controller import AntecedentesPersonalesController
            self.controlador_antecedentes = AntecedentesPersonalesController(self.session)

    @ui.refreshable
    def mostrar_antecedentes_personales(self):
        self._inicializar_controlador()
        
        # Consumimos los datos ordenados y calculados desde el controlador puro
        ant_sorted, ultimo = self.controlador_antecedentes.obtener_antecedentes_procesados(self.paciente)

        with ui.column().classes('w-full p-6 gap-6 max-w-7xl mx-auto'):

            # HEADER RESPONSIVE
            with ui.row().classes('w-full justify-between items-center wrap q-col-gutter-md px-2'):
                with ui.column().classes('gap-1'):
                    ui.label('Antecedentes Patológicos Personales').classes(HEADER_TITLE_CLASSES)
                    ui.label('Registro histórico de diagnósticos y condiciones crónicas').classes('text-slate-400 text-sm pl-4')

                if tiene_permiso("ant_personales_manage"):
                    ui.button(
                        'Agregar Nuevo',
                        icon='add_moderator',
                        on_click=self.agregar_antecedente_personal
                    ).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

            # GRID -> RESPONSIVE CON QUASAR
            with ui.row().classes('w-full q-col-gutter-lg wrap'):

                # =====================================================
                # COLUMNA IZQUIERDA: ÚLTIMO DIAGNÓSTICO
                # =====================================================
                with ui.column().classes('col-12 col-lg-6 gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('items-center gap-2 mb-2 wrap'):
                            ui.icon('assignment_late', color='primary', size='sm')
                            ui.label('Último Diagnóstico Registrado').classes('text-xs font-bold text-slate-500 uppercase tracking-tight')

                        if ultimo:
                            ui.label(ultimo.fecha_registro.strftime("%d/%m/%Y")).classes('text-sm font-bold text-blue-600 bg-blue-50 px-4 py-1 rounded-full w-fit mb-4')
                            with ui.column().classes('w-full gap-3'):
                                for pat in ultimo.patologias:
                                    with ui.row().classes('items-center justify-between wrap q-col-gutter-md p-4 bg-slate-50 rounded-xl border border-slate-100 hover:bg-blue-50/50 transition-colors'):
                                        with ui.row().classes('items-center gap-3 wrap'):
                                            ui.icon('medical_services', color='blue-500', size='xs')
                                            ui.label(pat.tipo_patologia).classes('text-gray-700 font-semibold text-lg')

                                        if pat.tipo_patologia != 'No tiene':
                                            t_partes = []
                                            if pat.tiempo_anios: t_partes.append(f"{pat.tiempo_anios} años")
                                            if pat.tiempo_meses: t_partes.append(f"{pat.tiempo_meses} meses")
                                            if t_partes:
                                                ui.label(" - ".join(t_partes)).classes('text-xs font-medium bg-white text-blue-800 px-3 py-1 rounded-lg border border-blue-100 shadow-sm')
                        else:
                            with ui.column().classes('w-full items-center py-10 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200'):
                                ui.icon('info', size='48px', color='slate-300')
                                ui.label('No hay antecedentes registrados').classes('text-slate-400 font-medium mt-2')

                # =====================================================
                # COLUMNA DERECHA: HISTORIAL CRONOLÓGICO
                # =====================================================
                with ui.column().classes('col-12 col-lg-6 gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('items-center gap-2 mb-4 wrap'):
                            ui.icon('history', color='slate-400')
                            ui.label('Historial Cronológico').classes('text-lg font-bold text-slate-700')

                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            if ant_sorted:
                                for ant in ant_sorted:
                                    with ui.card().classes(HC_SECTION_CARD + ' mb-3 p-0 shadow-sm'):
                                        with ui.row().classes('w-full bg-white/80 p-3 justify-between items-center wrap q-col-gutter-sm border-b border-blue-50'):
                                            ui.label(ant.fecha_registro.strftime("%d/%m/%Y")).classes('text-xs font-bold text-blue-600')

                                            with ui.row().classes('gap-1 wrap'):
                                                if tiene_permiso("ant_personales_manage"):
                                                    ui.button(icon='edit', on_click=lambda e, a=ant: self.editar_antecedente(a)).props('flat dense size=sm color="primary"').classes(PRIMARY_BUTTON_CLASSES.replace('bg-blue-600',''))
                                                    ui.button(icon='delete', on_click=lambda e, a=ant: self.eliminar_antecedente(a)).props('flat dense size=sm color="error"').classes(DANGER_BUTTON_CLASSES)

                                        with ui.column().classes('p-3 gap-2'):
                                            for p in ant.patologias:
                                                with ui.row().classes('items-center gap-2 wrap'):
                                                    ui.icon('check_circle', size='14px', color='blue-300')
                                                    ui.label(p.tipo_patologia).classes('text-sm text-gray-600 font-medium')
                                                    
                                                    t_str = f"({p.tiempo_anios or 0}a {p.tiempo_meses or 0}m)" if p.tipo_patologia != 'No tiene' else ""
                                                    if t_str != "(0a 0m)":
                                                        ui.label(t_str).classes('text-[10px] text-gray-400')
                            else:
                                ui.label('Sin registros previos').classes('text-slate-300 text-center w-full py-10 italic')

    def agregar_antecedente_personal(self):
        self._inicializar_controlador()
        with ui.dialog() as dialog, ui.card().classes(HC_CARD_PROFESSIONAL).style("width:760px; max-width:none;"):
            ui.label('Agregar Antecedente Patológico Personal').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes(INPUT_CLASSES) as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            checkboxes = {}
            otros_inputs = []
            
            with ui.card().classes(HC_SECTION_CARD):
                ui.label('Patologías').classes('text-lg font-semibold text-gray-700 mb-4')

                def update_checkboxes():
                    no_tiene_checked = checkboxes.get('No tiene', (None,))[0].value if 'No tiene' in checkboxes else False
                    for key, (chk, _, _) in checkboxes.items():
                        if key != 'No tiene':
                            chk.enabled = not no_tiene_checked
                            if no_tiene_checked: chk.value = False

                for patologia in self.patologias:
                    if patologia != 'Otros':
                        with ui.row().classes('items-center gap-4 w-full p-2 rounded-lg hover:bg-blue-50'):
                            checkbox = ui.checkbox(patologia, on_change=update_checkboxes).classes('flex-shrink-0')
                            with ui.row().classes('items-center gap-2 flex-grow'):
                                ui.label('Tiempo:').classes('text-sm text-gray-600')
                                tiempo_anios = ui.number(label='Años', min=0, max=100, format='%.0f', value=0).classes(INPUT_CLASSES).props('dense')
                                tiempo_meses = ui.number(label='Meses', min=0, max=11, format='%.0f', value=0).classes(INPUT_CLASSES).props('dense')
                            checkboxes[patologia] = (checkbox, tiempo_anios, tiempo_meses)

                with ui.column().classes('gap-4 w-full mt-4'):
                    ui.label('Otros').classes('font-semibold text-gray-700')
                    contenedor_otros = ui.column().classes('gap-2 p-4 border border-gray-300 rounded-lg max-height: 150px; ')

                    def agregar_input_otros():
                        with contenedor_otros:
                            with ui.row().classes('items-center gap-2') as fila:
                                input_nuevo = ui.input('Especifique').classes(f'flex-grow {INPUT_CLASSES}')
                                tiempo_anios_otro = ui.number(label='Años', min=0, max=100, format='%.0f', value=0).classes(INPUT_CLASSES).props('dense')
                                tiempo_meses_otro = ui.number(label='Meses', min=0, max=11, format='%.0f', value=0).classes(INPUT_CLASSES).props('dense')
                                ui.button(icon='delete', on_click=lambda: (contenedor_otros.remove(fila), otros_inputs.remove(input_nuevo))).props('flat round dense color="negative"')
                                otros_inputs.append((input_nuevo, tiempo_anios_otro, tiempo_meses_otro))

                    ui.button('Agregar otro', icon='add', on_click=agregar_input_otros).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                    agregar_input_otros()

            def guardar():
                # Empaquetamos la interfaz en una estructura de datos nativa limpia de Python
                patologias_para_enviar = []
                checked_keys = [key for key, (chk, _, _) in checkboxes.items() if chk.value]
                
                if 'No tiene' in checked_keys:
                    patologias_para_enviar.append({'tipo': 'No tiene', 'anios': 0, 'meses': 0})
                else:
                    for key in checked_keys:
                        _, anios, meses = checkboxes[key]
                        patologias_para_enviar.append({'tipo': key, 'anios': anios.value, 'meses': meses.value})
                
                for input_otros, anios_otro, meses_otro in otros_inputs:
                    texto = input_otros.value.strip()
                    if texto:
                        for pat_individual in [p.strip() for p in texto.split(',') if p.strip()]:
                            patologias_para_enviar.append({'tipo': pat_individual, 'anios': anios_otro.value, 'meses': meses_otro.value})

                # Delegamos al controlador de datos
                exito, msg = self.controlador_antecedentes.guardar_antecedente(
                    paciente_id=self.paciente.id,
                    fecha_str=fecha_input.value,
                    patologias_data=patologias_para_enviar
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_antecedentes_personales.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end mt-4 gap-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')

                def key_handler(event: events.KeyEventArguments):
                    if event.action.keydown and event.key == "Enter": guardar()

                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                ui.keyboard(key_handler)
        dialog.open()

    def editar_antecedente(self, antecedente):
        self._inicializar_controlador()
        with ui.dialog() as dialog, ui.card().classes(HC_CARD_PROFESSIONAL).style("width:760px; max-width:none;"):
            ui.label('Editar Antecedente Patológico Personal').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha', value=antecedente.fecha_registro.strftime('%Y-%m-%d')).classes(INPUT_CLASSES) as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        ui.button('Calendario', on_click=menu.open).props('flat')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            checkboxes = {}
            otros_inputs = []
            
            with ui.card().classes(HC_SECTION_CARD):
                ui.label('Patologías').classes('text-lg font-semibold text-gray-700 mb-4')

                def update_checkboxes():
                    no_tiene_checked = checkboxes.get('No tiene', (None,))[0].value if 'No tiene' in checkboxes else False
                    for key, (chk, _, _) in checkboxes.items():
                        if key != 'No tiene':
                            chk.enabled = not no_tiene_checked
                            if no_tiene_checked: chk.value = False

                for patologia in self.patologias:
                    if patologia != 'Otros':
                        existente = next((p for p in antecedente.patologias if p.tipo_patologia == patologia), None)
                        with ui.row().classes('items-center gap-4 w-full p-2 rounded-lg hover:bg-blue-50'):
                            checkbox = ui.checkbox(patologia, value=bool(existente), on_change=update_checkboxes).classes('flex-shrink-0')
                            with ui.row().classes('items-center gap-2 flex-grow'):
                                ui.label('Tiempo:').classes('text-sm text-gray-600')
                                anios = ui.number(label='Años', min=0, max=100, format='%.0f', value=existente.tiempo_anios if existente else 0).classes(INPUT_CLASSES).props('dense')
                                meses = ui.number(label='Meses', min=0, max=11, format='%.0f', value=existente.tiempo_meses if existente else 0).classes(INPUT_CLASSES).props('dense')
                                checkboxes[patologia] = (checkbox, anios, meses)
                update_checkboxes()

                with ui.column().classes('gap-4 w-full mt-4'):
                    ui.label('Otros').classes('font-semibold text-gray-700')
                    contenedor_otros = ui.column().classes('gap-2 p-4 border border-gray-300 rounded-lg max-height: 150px; ')

                    def agregar_input_otros(valor_texto='', anios_val=0, meses_val=0):
                        with contenedor_otros:
                            with ui.row().classes('items-center gap-2') as fila:
                                input_nuevo = ui.input('Especifique', value=valor_texto).classes(f'flex-grow {INPUT_CLASSES}')
                                tiempo_anios_otro = ui.number(label='Años', min=0, max=100, format='%.0f', value=anios_val).classes(INPUT_CLASSES).props('dense')
                                tiempo_meses_otro = ui.number(label='Meses', min=0, max=11, format='%.0f', value=meses_val).classes(INPUT_CLASSES).props('dense')
                                ui.button(icon='delete', on_click=lambda: (contenedor_otros.remove(fila), otros_inputs.remove(input_nuevo))).props('flat round dense color="negative"')
                                otros_inputs.append((input_nuevo, tiempo_anios_otro, tiempo_meses_otro))

                    ui.button('Agregar otro', icon='add', on_click=agregar_input_otros).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                    
                    otros_existentes = [p for p in antecedente.patologias if p.tipo_patologia not in self.patologias]
                    if otros_existentes:
                        for pat in otros_existentes:
                            agregar_input_otros(pat.tipo_patologia, pat.tiempo_anios, pat.tiempo_meses)
                    else:
                        agregar_input_otros()

            def guardar():
                patologias_para_enviar = []
                checked_keys = [key for key, (chk, _, _) in checkboxes.items() if chk.value]
                
                if 'No tiene' in checked_keys:
                    patologias_para_enviar.append({'tipo': 'No tiene', 'anios': 0, 'meses': 0})
                else:
                    for key in checked_keys:
                        _, anios, meses = checkboxes[key]
                        patologias_para_enviar.append({'tipo': key, 'anios': anios.value, 'meses': meses.value})
                
                for input_nuevo, anios_otro, meses_otro in otros_inputs:
                    texto = input_nuevo.value.strip()
                    if texto:
                        for pat_individual in [p.strip() for p in texto.split(',') if p.strip()]:
                            patologias_para_enviar.append({'tipo': pat_individual, 'anios': anios_otro.value, 'meses': meses_otro.value})

                # Delegamos la edición por ID al controlador
                exito, msg = self.controlador_antecedentes.actualizar_antecedente(
                    antecedente_id=antecedente.id,
                    fecha_str=fecha_input.value,
                    patologias_data=patologias_para_enviar
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_antecedentes_personales.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')

                def key_handler(event: events.KeyEventArguments):
                    if event.action.keydown and event.key == "Enter": guardar()

                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                ui.keyboard(key_handler)
        dialog.open()

    def eliminar_antecedente(self, antecedente):
        self._inicializar_controlador()
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este antecedente?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props(' color="warning"')
                
                def confirmar():
                    exito, msg = self.controlador_antecedentes.eliminar_antecedente(antecedente.id)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_antecedentes_personales.refresh()
                    else:
                        ui.notify(msg, type='negative')
                        
                ui.button('Eliminar', on_click=confirmar).classes(DANGER_BUTTON_CLASSES).props(' color="error"')
            dialog.open()