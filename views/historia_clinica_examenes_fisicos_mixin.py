from datetime import datetime

from nicegui import ui
from Errores import log_error_and_notify
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL, 
    HC_SECTION_CARD
)
from seguridad_roles import tiene_permiso


class HistoriaClinicaExamenesFisicosMixin:

    # =========================================================
    # VISTA PRINCIPAL / RENDERIZADO
    # =========================================================

    @ui.refreshable
    def mostrar_examenes_fisicos(self):
        with ui.column().classes('w-full gap-6'):
            # Layout de dos columnas
            with ui.row().classes('full-width p-0 q-col-gutter-md'):

                
                # --- COLUMNA IZQUIERDA: RESUMEN DEL ÚLTIMO EXAMEN ---
                with ui.column().classes('col-12 p-0 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('justify-between items-center mb-6'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('monitor_heart', color='primary', size='md')
                                ui.label('Estado Físico Actual').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso("examen_fisico_manage"):
                                ui.button('Nuevo Examen', icon='add', on_click=self.agregar_examen_fisico)\
                                    .classes(PRIMARY_BUTTON_CLASSES)
                            
                        examenes = self.paciente.examen_fisico
                        if examenes:
                            ultimo = max(examenes, key=lambda x: x.fecha_registro)
                            
                            # Panel de Signos Vitales con diseño limpio
                            with ui.column().classes('w-full gap-3'):
                                # Fecha destacada
                                with ui.row().classes('w-full justify-end'):
                                    ui.label(f'Evaluado el: {ultimo.fecha_registro.strftime("%d/%m/%Y")}').classes('text-xs font-bold text-slate-400 uppercase')

                                # Grid de indicadores rápidos
                                with ui.grid(columns=2).classes('w-full gap-4'):
                                    # Presión Arterial
                                    if ultimo.sistolica_sentado and ultimo.diastolica_sentado:
                                        pa_color = 'red-500' if ultimo.sistolica_sentado > 130 or ultimo.diastolica_sentado > 80 else 'green-600'
                                        with ui.column().classes(f'p-4 rounded-xl border-l-4 border-{pa_color} bg-slate-50'):
                                            ui.label('Presión Arterial con el paciente Sentado').classes('text-xs font-medium text-slate-500')
                                            ui.label(f'{ultimo.sistolica_sentado}/{ultimo.diastolica_sentado}').classes(f'text-2xl font-bold text-{pa_color}')
                                            ui.label('mmHg').classes('text-[10px] text-slate-400 font-bold')
                                            ui.label(f'FC: {ultimo.frecuencia_cardiaca_sentado} lpm').classes('text-xs font-medium text-slate-500 mt-1')
                                    else:
                                        with ui.column().classes('p-4 rounded-xl border-l-4 border-red-400 bg-slate-50'):
                                            ui.label('No hay datos de Presión Arterial con el paciente Sentado').classes('text-xs font-medium text-slate-500')
                                    
                                    if ultimo.sistolica_de_pie and ultimo.diastolica_de_pie:
                                        pa_color = 'red-500' if ultimo.sistolica_de_pie > 130 or ultimo.diastolica_de_pie > 80 else 'green-600'
                                        with ui.column().classes(f'p-4 rounded-xl border-l-4 border-{pa_color} bg-slate-50'):
                                            ui.label('Presión Arterial con el paciente De Pie').classes('text-xs font-medium text-slate-500')
                                            ui.label(f'{ultimo.sistolica_de_pie}/{ultimo.diastolica_de_pie}').classes(f'text-2xl font-bold text-{pa_color}')
                                            ui.label('mmHg').classes('text-[10px] text-slate-400 font-bold')
                                    else:
                                        with ui.column().classes('p-4 rounded-xl border-l-4 border-red-400 bg-slate-50'):
                                            ui.label('No hay datos de Presión Arterial con el paciente De Pie').classes('text-xs font-medium text-slate-500')
                                    
                                    if ultimo.sistolica_acostado and ultimo.diastolica_acostado:
                                        pa_color = 'red-500' if ultimo.sistolica_acostado > 130 or ultimo.diastolica_acostado > 80 else 'green-600'
                                        with ui.column().classes(f'p-4 rounded-xl border-l-4 border-{pa_color} bg-slate-50'):
                                            ui.label('Presión Arterial con el paciente Acostado').classes('text-xs font-medium text-slate-500')
                                            ui.label(f'{ultimo.sistolica_acostado}/{ultimo.diastolica_acostado}').classes(f'text-2xl font-bold text-{pa_color}')
                                            ui.label('mmHg').classes('text-[10px] text-slate-400 font-bold')
                                            ui.label(f'FC: {ultimo.frecuencia_cardiaca_acostado} lpm').classes('text-xs font-medium text-slate-500 mt-1')
                                    else:
                                        with ui.column().classes('p-4 rounded-xl border-l-4 border-red-400 bg-slate-50'):
                                            ui.label('No hay datos de Presión Arterial con el paciente Acostado').classes('text-xs font-medium text-slate-500')

                                    # Bocio
                                    with ui.column().classes('p-4 rounded-xl border-l-4 border-blue-400 bg-slate-50'):
                                        ui.label('Bocio').classes('text-xs font-medium text-slate-500')
                                        ui.label(f'Grado {ultimo.bocio}').classes('text-2xl font-bold text-slate-800')
                                        ui.label('Escala Médica').classes('text-[10px] text-slate-400 font-bold')

                                # Acantosis Nigricans (Alerta visual)
                                ac_bg = 'bg-red-50 border-red-100' if ultimo.acantosis_nigricans == "Si" else 'bg-green-50 border-green-100'
                                ac_text = 'Presente' if ultimo.acantosis_nigricans == "Si" else 'Ausente'
                                ac_icon = 'warning' if ultimo.acantosis_nigricans == "Si" else 'check_circle'
                                ac_color = 'red-600' if ultimo.acantosis_nigricans == "Si" else 'green-600'

                                with ui.row().classes(f'w-full {ac_bg} border p-3 rounded-lg items-center justify-between'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon(ac_icon, color=ac_color)
                                        ui.label('Acantosis Nigricans').classes('font-medium text-slate-700')
                                    ui.label(ac_text).classes(f'font-bold text-{ac_color}')
                        else:
                            with ui.column().classes('col-12'):
                                ui.icon('analytics', size='50px').classes('text-slate-200')
                                ui.label('Sin registros físicos').classes()


                # --- COLUMNA DERECHA: HISTORIAL CRONOLÓGICO ---
                with ui.column().classes('col-12 p-0 col-md-5'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        ui.label('Historial de Mediciones').classes(HEADER_TITLE_CLASSES + ' mb-4')
                        
                        # Solución al scroll: Altura definida y ancho total
                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            if examenes:
                                examenes_ordenados = sorted(examenes, key=lambda x: x.fecha_registro, reverse=True)
                                with ui.column().classes('w-full gap-3'):
                                    for examen in examenes_ordenados:
                                        # Card de historial simplificada (sin sombra excesiva)
                                        with ui.card().classes('w-full p-0 border border-slate-100 shadow-none'):
                                            # Header de la fila de historial
                                            with ui.row().classes('w-full bg-slate-50 p-2 justify-between items-center'):
                                                ui.label(examen.fecha_registro.strftime("%d/%m/%Y")).classes('text-sm font-bold text-slate-700')
                                                with ui.row().classes('gap-1'):
                                                    if tiene_permiso("examen_fisico_manage"):   
                                                        ui.button(icon='edit', on_click=lambda e, ex=examen: self.editar_examen_fisico(ex)).props('flat dense size=sm ').classes(PRIMARY_BUTTON_CLASSES)
                                                        ui.button(icon='delete', on_click=lambda e, ex=examen: self.eliminar_examen_fisico(ex)).props('flat dense size=sm color="error"').classes(DANGER_BUTTON_CLASSES)
                                            
                                            # Datos en una sola línea horizontal para ahorrar espacio
                                            with ui.row().classes('w-full p-3 justify-between items-center gap-2'):
                                                # PA
                                                with ui.row().classes('items-baseline gap-1'):
                                                    ui.label('PA Sentado:').classes('text-[10px] text-slate-400 font-bold')
                                                    ui.label(f'{examen.sistolica_sentado}/{examen.diastolica_sentado}').classes('text-sm font-semibold')
                                                    if examen.frecuencia_cardiaca_sentado is not None:
                                                        ui.label(f'FC: {examen.frecuencia_cardiaca_sentado} lpm').classes('text-xs text-slate-500 ml-2')
                                                with ui.row().classes('items-baseline gap-1'):
                                                    ui.label('PA De Pie:').classes('text-[10px] text-slate-400 font-bold')
                                                    ui.label(f'{examen.sistolica_de_pie}/{examen.diastolica_de_pie}').classes('text-sm font-semibold')
                                                with ui.row().classes('items-baseline gap-1'):
                                                    ui.label('PA Acostado:').classes('text-[10px] text-slate-400 font-bold')
                                                    ui.label(f'{examen.sistolica_acostado}/{examen.diastolica_acostado}').classes('text-sm font-semibold')
                                                    if examen.frecuencia_cardiaca_acostado is not None:
                                                        ui.label(f'FC: {examen.frecuencia_cardiaca_acostado} lpm').classes('text-xs text-slate-500 ml-2')
                                                
                                                # Bocio
                                                with ui.row().classes('items-baseline gap-1'):
                                                    ui.label('BOCIO:').classes('text-[10px] text-slate-400 font-bold')
                                                    ui.label(f'G{examen.bocio}').classes('text-sm font-semibold')
                                                
                                                # Acantosis
                                                ac_status = 'Si' if examen.acantosis_nigricans == "Si" else 'No'
                                                ac_status_color = 'red-600' if examen.acantosis_nigricans == "Si" else 'slate-400'
                                                with ui.row().classes('items-baseline gap-1'):
                                                    ui.label('ACANT:').classes('text-[10px] text-slate-400 font-bold')
                                                    ui.label(ac_status).classes(f'text-sm font-bold text-{ac_status_color}')
                            else:
                                ui.label('No hay registros previos').classes('text-gray-400 italic text-center w-full py-10')


    # =========================================================
    # DIÁLOGOS Y FORMULARIOS (ALTAS Y EDICIÓN)
    # =========================================================

    def agregar_examen_fisico(self):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl p-6 rounded-2xl'):
            ui.label('Nuevo Examen Físico').classes(HEADER_TITLE_CLASSES + ' mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # --- SECCIÓN FECHA ---
                with ui.card().classes('w-full p-4 bg-blue-50 shadow-none border border-blue-100'):
                    with ui.input('Fecha del Examen').classes('w-full') as fecha_input:
                        with ui.menu().props('no-parent-event') as menu:
                            ui.date().bind_value(fecha_input).on('change', menu.close).props(
                                f'locale="es" :options="date => date <= \'{self.today}\'"'
                            )
                        with fecha_input.add_slot('append'):
                            ui.icon('calendar_month').on('click', menu.open).classes('cursor-pointer text-blue-600')

                # --- SECCIÓN TENSIÓN ARTERIAL (TRIPLE COLUMNA) ---
                ui.label('Tensión Arterial (mmHg)').classes('text-sm font-bold text-slate-600 uppercase mt-2')
                
                with ui.row().classes('w-full gap-3 no-wrap'):
                    # 1. Acostado
                    with ui.card().classes('p-3 border-t-4 border-indigo-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('hotel', size='xs').classes('text-indigo-500')
                            ui.label('Acostado').classes('font-bold text-xs')
                        sist_acostado = self.input_clinico('Sist.', 50, 250, None).classes('w-full')
                        diast_acostado = self.input_clinico('Diast.', 30, 150, None).classes('w-full')
                        ui.separator().classes('my-2')
                        fc_acostado = self.input_clinico('FC (lpm)', 30, 200, None).classes('w-full')

                    # 2. Sentado 
                    with ui.card().classes('p-3 border-t-4 border-orange-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('chair', size='xs').classes('text-orange-500')
                            ui.label('Sentado').classes('font-bold text-xs')
                        sist_sentado = self.input_clinico('Sist.', 50, 250, None).classes('w-full')
                        diast_sentado = self.input_clinico('Diast.', 30, 150, None).classes('w-full')
                        ui.separator().classes('my-2')
                        fc_sentado = self.input_clinico('FC (lpm)', 30, 200, None).classes('w-full')

                    # 3. De Pie
                    with ui.card().classes('p-3 border-t-4 border-green-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('accessibility_new', size='xs').classes('text-green-500')
                            ui.label('De Pie').classes('font-bold text-xs')
                        sist_pie = self.input_clinico('Sist.', 50, 250, None).classes('w-full')
                        diast_pie = self.input_clinico('Diast.', 30, 150, None).classes('w-full')

                # --- OTROS HALLAZGOS ---
                with ui.row().classes('w-full gap-4 mt-2'):
                    bocio_input = ui.select(options=['0', 'I', 'II', 'III'], label='Bocio', value='0').classes('flex-1')
                    acantosis_input = ui.select(options=['Si', 'No'], label='Acantosis', value='No').classes('flex-1')

                def guardar_examen_fisico():
                    try:
                        fecha = datetime.strptime(fecha_input.value, '%Y-%m-%d').date()
                        
                        datos = {
                            'sistolica_acostado': sist_acostado.value if sist_acostado.value is not None else None,
                            'diastolica_acostado': diast_acostado.value if diast_acostado.value is not None else None,
                            'sistolica_sentado': sist_sentado.value if sist_sentado.value is not None else None,
                            'diastolica_sentado': diast_sentado.value if diast_sentado.value is not None else None,
                            'sistolica_de_pie': sist_pie.value if sist_pie.value is not None else None,
                            'diastolica_de_pie': diast_pie.value if diast_pie.value is not None else None,
                            'bocio': bocio_input.value,  
                            'acantosis_nigricans': acantosis_input.value,
                            'frecuencia_cardiaca_acostado': fc_acostado.value if fc_acostado.value is not None else None,
                            'frecuencia_cardiaca_sentado': fc_sentado.value if fc_sentado.value is not None else None
                        }
                        
                        self.controlador_examenes_fisicos.crear_examen_fisico(self.paciente.id, fecha, datos)
                        ui.notify('Registro guardado correctamente', type='positive')
                        dialog.close()
                        self.mostrar_examenes_fisicos.refresh()
                        
                    except Exception as e:
                        self.session.rollback()
                        log_error_and_notify(e, 'Error al guardar examen físico')

                with ui.row().classes('w-full justify-end gap-3 mt-6'):
                    ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                    ui.button('Guardar', on_click=guardar_examen_fisico).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()


    def editar_examen_fisico(self, examen):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl p-6 rounded-2xl'):
            ui.label('Editar Examen Físico').classes(HEADER_TITLE_CLASSES + ' mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # --- SECCIÓN FECHA ---
                with ui.card().classes('w-full p-4 bg-blue-50 shadow-none border border-blue-100'):
                    fecha_str = examen.fecha_registro.strftime('%Y-%m-%d') if examen.fecha_registro else self.today
                    with ui.input('Fecha del Examen', value=fecha_str).classes('w-full') as fecha_input:
                        with ui.menu().props('no-parent-event') as menu:
                            ui.date().bind_value(fecha_input).on('change', menu.close).props(
                                f'locale="es" :options="date => date <= \'{self.today}\'"'
                            )
                        with fecha_input.add_slot('append'):
                            ui.icon('calendar_month').on('click', menu.open).classes('cursor-pointer text-blue-600')

                # --- SECCIÓN TENSIÓN ARTERIAL (TRIPLE COLUMNA) ---
                ui.label('Tensión Arterial (mmHg)').classes('text-sm font-bold text-slate-600 uppercase mt-2')
                
                with ui.row().classes('w-full gap-3 no-wrap'):
                    # 1. Acostado
                    with ui.card().classes('p-3 border-t-4 border-indigo-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('hotel', size='xs').classes('text-indigo-500')
                            ui.label('Acostado').classes('font-bold text-xs')
                        sist_acostado = self.input_clinico('Sist.', 50, 250, examen.sistolica_acostado).classes('w-full')
                        diast_acostado = self.input_clinico('Diast.', 30, 150, examen.diastolica_acostado).classes('w-full')
                        ui.separator().classes('my-2')
                        fc_acostado = self.input_clinico('FC (lpm)', 30, 200, examen.frecuencia_cardiaca_acostado).classes('w-full')

                    # 2. Sentado
                    with ui.card().classes('p-3 border-t-4 border-orange-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('chair', size='xs').classes('text-orange-500')
                            ui.label('Sentado').classes('font-bold text-xs')
                        sist_sentado = self.input_clinico('Sist.', 50, 250, examen.sistolica_sentado).classes('w-full')
                        diast_sentado = self.input_clinico('Diast.', 30, 150, examen.diastolica_sentado).classes('w-full')
                        ui.separator().classes('my-2')
                        fc_sentado = self.input_clinico('FC (lpm)', 30, 200, examen.frecuencia_cardiaca_sentado).classes('w-full')

                    # 3. De Pie
                    with ui.card().classes('p-3 border-t-4 border-green-400 shadow-sm flex-1'):
                        with ui.row().classes('items-center gap-2 mb-2'):
                            ui.icon('accessibility_new', size='xs').classes('text-green-500')
                            ui.label('De Pie').classes('font-bold text-xs')
                        sist_pie = self.input_clinico('Sist.', 50, 250, examen.sistolica_de_pie).classes('w-full')
                        diast_pie = self.input_clinico('Diast.', 30, 150, examen.diastolica_de_pie).classes('w-full')

                # --- OTROS HALLAZGOS ---
                with ui.row().classes('w-full gap-4 mt-2'):
                    bocio_input = ui.select(
                        options=['0', 'I', 'II', 'III'], 
                        label='Bocio', 
                        value=str(examen.bocio) if examen.bocio else '0'
                    ).classes('flex-1')
                    
                    acantosis_input = ui.select(
                        options=['Si', 'No'], 
                        label='Acantosis', 
                        value='Si' if examen.acantosis_nigricans == "Si" else 'No'
                    ).classes('flex-1')

                def guardar_edicion():
                    try:
                        fecha = datetime.strptime(fecha_input.value, '%Y-%m-%d').date()
                        
                        datos = {
                            'sistolica_acostado': sist_acostado.value if sist_acostado.value is not None else None,
                            'diastolica_acostado': diast_acostado.value if diast_acostado.value is not None else None,
                            'sistolica_sentado': sist_sentado.value if sist_sentado.value is not None else None,
                            'diastolica_sentado': diast_sentado.value if diast_sentado.value is not None else None,
                            'sistolica_de_pie': sist_pie.value if sist_pie.value is not None else None,
                            'diastolica_de_pie': diast_pie.value if diast_pie.value is not None else None,
                            'bocio': bocio_input.value,
                            'acantosis_nigricans': acantosis_input.value,
                            'frecuencia_cardiaca_acostado': fc_acostado.value if fc_acostado.value is not None else None,
                            'frecuencia_cardiaca_sentado': fc_sentado.value if fc_sentado.value is not None else None
                        }
                        
                        self.controlador_examenes_fisicos.actualizar_examen_fisico(examen, fecha, datos)
                        ui.notify('Registro actualizado con éxito', type='positive', icon='update')
                        dialog.close()
                        self.mostrar_examenes_fisicos.refresh()
                        
                    except Exception as e:
                        self.session.rollback()
                        log_error_and_notify(e, 'Error al actualizar examen físico')

                with ui.row().classes('w-full justify-end gap-3 mt-6'):
                    ui.button('Cancelar', on_click=dialog.close).props('flat color=grey')
                    ui.button('Actualizar', on_click=guardar_edicion).classes(SUCCESS_BUTTON_CLASSES)

        dialog.open()


    def eliminar_examen_fisico(self, examen):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Está seguro que desea eliminar este examen físico?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_examen(examen, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()


    def confirmar_eliminacion_examen(self, examen, dialog):
        try:
            if examen is None:
                ui.notify('Error: El examen ya no existe', type='negative')
                dialog.close()
                return
            
            self.controlador_examenes_fisicos.eliminar_examen_fisico(examen)
            ui.notify('Examen físico eliminado correctamente', type='positive')
            dialog.close()  
            self.mostrar_examenes_fisicos.refresh()  
            
        except Exception as e:
            log_error_and_notify(e, 'Error al eliminar examen físico')  
            self.session.rollback()
            ui.notify(f'Error al eliminar: {str(e)}', type='negative')