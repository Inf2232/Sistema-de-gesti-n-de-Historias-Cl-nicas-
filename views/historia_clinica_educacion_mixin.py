# views/historia_clinica_educacion_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES, HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)
from controllers.historia_clinica_educacion_controller import EducacionDiabetologicaController

class HistoriaClinicaEducacionMixin:
    
    @property
    def controlador_educacion(self):
        """Lazy loading del controlador para garantizar la carga segura de dependencias."""
        if not hasattr(self, '_controlador_educacion'):
            self._controlador_educacion = EducacionDiabetologicaController(self.session)
        return self._controlador_educacion

    @ui.refreshable
    def mostrar_educacion_diabetica(self):
        # Delegamos la consulta compleja al controlador
        ultimo_registro, ultimo_estado, historial = self.controlador_educacion.obtener_datos_educacion(self.paciente.id)

        with ui.column().classes('w-full p-6 gap-6 max-w-7xl mx-auto'):
            # --- CABECERA ---
            with ui.row().classes('w-full justify-between items-center px-2'):
                with ui.column().classes('gap-1'):
                    ui.label('Educación Diabetológica').classes(HEADER_TITLE_CLASSES)
                    ui.label('Evaluación de conocimientos y empoderamiento del paciente').classes('text-slate-400 text-sm pl-4')

            with ui.grid(columns=2).classes('w-full gap-6'):
                
                # --- COLUMNA IZQUIERDA: ÚLTIMA EVALUACIÓN ---
                with ui.column().classes('gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL + ' border-l-4 border-indigo-500'):
                        with ui.row().classes('justify-between items-center mb-6 w-full'):
                            ui.label('Nivel de Conocimiento').classes('text-sm font-bold text-slate-500 uppercase tracking-wider')
                            if tiene_permiso("educacion_diab_manage"):
                                ui.button('Evaluar', icon='quiz', on_click=self.agregar_evaluacion_diabetologica)\
                                    .props('flat round dense color="primary"').classes('bg-indigo-50 hover:bg-indigo-100')

                        if ultimo_registro:
                            with ui.column().classes('w-full items-center gap-4'):
                                ui.label(f'Evaluado el {ultimo_registro.fecha_registro.strftime("%d/%m/%Y")}')\
                                    .classes('text-[10px] font-bold text-indigo-400 uppercase')
                                
                                with ui.row().classes('w-full justify-around bg-slate-50 p-4 rounded-xl border border-slate-100'):
                                    with ui.column().classes('items-center'):
                                        ui.label('INICIAL').classes('text-[10px] font-bold text-slate-400')
                                        ui.label(str(ultimo_registro.inicio)).classes('text-xl font-black text-slate-700')
                                    
                                    ui.icon('trending_flat').classes('text-indigo-300 self-center text-2xl')
                                    
                                    with ui.column().classes('items-center'):
                                        ui.label('ACTUAL').classes('text-[10px] font-bold text-slate-400')
                                        ui.label(str(ultimo_registro.final)).classes('text-xl font-black text-indigo-600')
                        else:
                            with ui.column().classes('w-full items-center py-8 gap-2'):
                                ui.icon('history_edu', size='32px').classes('text-slate-200')
                                ui.label('Sin evaluaciones registradas').classes('text-slate-400 text-xs italic')
                           
                # --- COLUMNA DERECHA: ESTADO DE MANTENIMIENTO ---
                with ui.column().classes('gap-4'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL + ' border-l-4 border-emerald-500'):
                        with ui.row().classes('justify-between items-center mb-6 w-full'):
                            ui.label('Adherencia y Seguimiento').classes('text-sm font-bold text-slate-500 uppercase tracking-wider')
                            if tiene_permiso("educacion_diab_manage"):
                                ui.button('Actualizar', icon='update', on_click=self.agregar_estado_diabetologico)\
                                    .props('flat round dense color="positive"').classes('bg-emerald-50 hover:bg-emerald-100')

                        if ultimo_estado:
                            mantiene = ultimo_estado.mantiene_educacion
                            color_status = 'emerald' if mantiene else 'rose'
                            
                            with ui.column().classes('w-full items-center gap-4 py-2'):
                                ui.icon('verified' if mantiene else 'warning', size='48px').classes(f'text-{color_status}-500')
                                
                                with ui.column().classes('items-center gap-0'):
                                    ui.label('Mantiene Educación').classes('text-xs text-slate-400 font-bold uppercase')
                                    ui.label('ACTIVO' if mantiene else 'REQUIERE REFUERZO')\
                                        .classes(f'text-lg font-black text-{color_status}-600')
                                
                                ui.label(f'Último control: {ultimo_estado.fecha_registro.strftime("%d/%m/%Y")}')\
                                    .classes('text-[10px] text-slate-400')
                        else:
                            with ui.column().classes('w-full items-center py-8 gap-2'):
                                ui.icon('history_edu', size='32px').classes('text-slate-200')
                                ui.label('Sin estado de seguimiento').classes('text-slate-400 text-xs italic')

            # --- HISTORIAL UNIFICADO ---
            with ui.expansion('Cronología de Aprendizaje', icon='auto_stories').classes('w-full bg-slate-50 border border-slate-200 rounded-xl mt-4'):
                if historial:
                    with ui.column().classes('w-full p-4 gap-2'):
                        for item in historial:
                            # Lógica visual segura para diferenciar modelos
                            es_evaluacion = hasattr(item, 'inicio')
                            with ui.row().classes('w-full items-center justify-between p-3 bg-white rounded-lg border border-slate-100'):
                                
                                with ui.row().classes('items-center gap-4'):
                                    ui.label(item.fecha_registro.strftime("%d/%m/%Y")).classes('text-xs font-bold text-slate-400 w-20')
                                    
                                    if es_evaluacion:
                                        ui.badge('EVALUACIÓN').props('color="indigo" text-color="white"').classes('text-[10px]')
                                        ui.label(f'Progreso: {item.inicio} → {item.final}').classes('text-sm font-bold text-slate-700')
                                    else:
                                        ui.badge('SEGUIMIENTO').props('color="emerald" text-color="white"').classes('text-[10px]')
                                        ui.label('Continúa educado' if item.mantiene_educacion else 'Perdió seguimiento').classes('text-sm text-slate-600')
                                
                                with ui.row().classes('gap-1'):
                                    if es_evaluacion:
                                        if tiene_permiso("educacion_diab_manage"):
                                            ui.button(icon='edit', on_click=lambda e, i=item: self.editar_evaluacion_diabetologica(i)).props('flat dense size=sm').classes(PRIMARY_BUTTON_CLASSES)
                                            ui.button(icon='delete', on_click=lambda e, i=item: self.eliminar_evaluacion_diabetologica(i)).props('flat dense size=sm color=error').classes(DANGER_BUTTON_CLASSES)
                                    else:
                                        if tiene_permiso("educacion_diab_manage"):
                                            ui.button(icon='edit', on_click=lambda e, i=item: self.editar_estado_diabetologico(i)).props('flat dense size=sm').classes(PRIMARY_BUTTON_CLASSES)
                                            ui.button(icon='delete', on_click=lambda e, i=item: self.eliminar_estado_diabetologico(i)).props('flat dense size=sm color=error').classes(DANGER_BUTTON_CLASSES)
                else:
                    ui.label('No hay registros históricos').classes('p-6 text-center text-slate-400 italic')

    # ========================= MODALES DE ESTADO =========================

    def agregar_estado_diabetologico(self):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Agregar Estado de Educación Diabetológica').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')   

            mantiene_input = ui.select(options=['Si', 'No'], label='Mantiene Educación', value='Si').classes('w-58 ' + INPUT_CLASSES)

            def guardar():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='negative')
                    return
                    
                exito, msg = self.controlador_educacion.guardar_estado(
                    self.paciente.id, 
                    fecha_input.value, 
                    mantiene_input.value == 'Si'
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_educacion_diabetica.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()

    def editar_estado_diabetologico(self, estado):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Editar Estado de Educación Diabetológica').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha', value=estado.fecha_registro.strftime('%Y-%m-%d')).classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            mantiene_input = ui.select(
                options=['Si', 'No'], label='Mantiene Educación', value='Si' if estado.mantiene_educacion else 'No'
            ).classes(INPUT_CLASSES)

            def guardar():
                if not fecha_input.value:
                    ui.notify('La fecha es obligatoria', type='negative')
                    return

                exito, msg = self.controlador_educacion.actualizar_estado(estado, fecha_input.value, mantiene_input.value == 'Si')
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_educacion_diabetica.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()

    def eliminar_estado_diabetologico(self, estado):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Está seguro de eliminar este estado?').classes('text-xl font-bold mb-4 text-red-600')
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def ejecutar_confirmacion():
                    exito, msg = self.controlador_educacion.eliminar_estado(estado)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_educacion_diabetica.refresh()
                    else:
                        ui.notify(msg, type='negative')

                ui.button('Eliminar', on_click=ejecutar_confirmacion).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            dialog.open()

    # ========================= MODALES DE EVALUACIÓN (SCORES) =========================

    def agregar_evaluacion_diabetologica(self):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Evaluación Diabetológica').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')   
            
            inicio_input = ui.select(['Excelente', 'Notable', 'Suficiente', 'Insuficiente'], label='Inicio', value='Excelente').classes(INPUT_CLASSES)
            final_input = ui.select(['Excelente', 'Notable', 'Suficiente', 'Insuficiente'], label='Final', value='Excelente').classes(INPUT_CLASSES)

            def guardar():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='negative')
                    return
                    
                exito, msg = self.controlador_educacion.guardar_evaluacion(
                    self.paciente.id, fecha_input.value, inicio_input.value, final_input.value
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_educacion_diabetica.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()

    def editar_evaluacion_diabetologica(self, evaluacion):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Editar Evaluación Diabetológica').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha', value=evaluacion.fecha_registro.strftime('%Y-%m-%d')).classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            inicio_input = ui.select(options=['Excelente', 'Notable', 'Suficiente', 'Insuficiente'], label='Inicio', value=evaluacion.inicio).classes(INPUT_CLASSES)
            final_input = ui.select(options=['Excelente', 'Notable', 'Suficiente', 'Insuficiente'], label='Final', value=evaluacion.final).classes(INPUT_CLASSES)

            def guardar():
                if not fecha_input.value:
                    ui.notify('La fecha es obligatoria', type='negative')
                    return
                
                exito, msg = self.controlador_educacion.actualizar_evaluacion(
                    evaluacion, fecha_input.value, inicio_input.value, final_input.value
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_educacion_diabetica.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()

    def eliminar_evaluacion_diabetologica(self, evaluacion):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Está seguro de eliminar esta evaluación?').classes('text-xl font-bold mb-4 text-red-600')
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def ejecutar_confirmacion():
                    exito, msg = self.controlador_educacion.eliminar_evaluacion(evaluacion)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_educacion_diabetica.refresh()
                    else:
                        ui.notify(msg, type='negative')

                ui.button('Eliminar', on_click=ejecutar_confirmacion).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            dialog.open()