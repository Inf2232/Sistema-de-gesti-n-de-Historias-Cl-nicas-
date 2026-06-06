# views/historia_clinica_habitos_mixin.py
from nicegui import ui
from controllers.habitos_toxicos_controller import HabitosToxicosController
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL
)
from seguridad_roles import tiene_permiso


class HistoriaClinicaHabitosMixin:
    @property
    def controlador_habitos(self):
        """Inicializa el controlador bajo demanda al acceder a la pestaña."""
        if not hasattr(self, '_controlador_habitos'):
            # self.session ya existe en la instancia principal de HistoriaClinicaApp
            self._controlador_habitos = HabitosToxicosController(self.session)
        return self._controlador_habitos

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialización del controlador inyectando la sesión activa de la app
        self._inicializar_controlador_habitos()

    @ui.refreshable
    def mostrar_habitos_toxicos(self):
        # Al evaluar self.controlador_habitos, se ejecutará el método @property de arriba
        habitos_sorted, ultimo = self.controlador_habitos.obtener_habitos_procesados(self.paciente)

        with ui.column().classes('w-full p-6 gap-6 max-w-7xl mx-auto'):

            # --- CABECERA ---
            with ui.row().classes('w-full justify-between items-center wrap q-col-gutter-md px-2'):
                with ui.column().classes('gap-1'):
                    ui.label('Hábitos Tóxicos').classes(HEADER_TITLE_CLASSES)
                    ui.label('Evaluación de tabaquismo, alcohol y tiempo de abandono').classes(
                        'text-slate-400 text-sm pl-4'
                    )

                if tiene_permiso("habitos_toxicos_manage"):
                    ui.button(
                        'Registrar Evaluación',
                        icon='Assignment_add',
                        on_click=self.agregar_habito_toxico
                    ).classes(PRIMARY_BUTTON_CLASSES + ' px-6 shadow-lg')

            # --- CONTENIDO PRINCIPAL ---
            with ui.row().classes('w-full q-col-gutter-lg'):

                # COLUMNA IZQUIERDA: Perfil Actual
                with ui.element('div').classes('col-12 col-lg-6'):
                    with ui.column().classes('gap-4'):

                        with ui.card().classes(HC_CARD_PROFESSIONAL + ' border-l-4 border-rose-500'):
                            ui.label('Perfil de Riesgo Actual').classes(
                                'text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4'
                            )

                            if ultimo:
                                with ui.column().classes('w-full gap-4'):
                                    # Fecha y alerta
                                    with ui.row().classes('items-center justify-between w-full wrap q-col-gutter-sm'):
                                        ui.label(ultimo.fecha_registro.strftime("%d/%m/%Y")).classes(
                                            'text-sm font-bold text-rose-700 bg-rose-50 px-4 py-1 rounded-full'
                                        )

                                        if (ultimo.fuma != "No" or ultimo.consumo_excesivo_alcohol == "Si"):
                                            ui.icon('warning', color='rose-400', size='sm')
                                        else:
                                            ui.icon('verified_user', color='green-400', size='sm')

                                    # INDICADOR TABACO
                                    with ui.row().classes(
                                        'items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 shadow-sm wrap q-col-gutter-md'
                                    ):
                                        with ui.row().classes('items-center gap-3 wrap'):
                                            ui.icon(
                                                'smoking_rooms',
                                                color='slate-500' if ultimo.fuma == "No" else 'rose-600'
                                            )
                                            with ui.column().classes('gap-0'):
                                                ui.label('Tabaquismo').classes('font-bold text-slate-700')

                                                if ultimo.fuma == "Si":
                                                    if ultimo.cant_cigarros:
                                                        ui.label(f'{ultimo.cant_cigarros} cigarros/día').classes('text-xs text-rose-500')
                                                    if ultimo.cant_tabacos:
                                                        ui.label(f'{ultimo.cant_tabacos} tabacos/día').classes('text-xs text-rose-500')
                                                elif ultimo.fuma == "Ex Fumador":
                                                    ui.label(f'Abandono: {ultimo.tiempo_sin_fumar or "No especificado"}').classes('text-xs text-blue-500 font-medium')

                                        color_fuma = 'green-600' if ultimo.fuma == "No" else ('orange-600' if ultimo.fuma == "Ex Fumador" else 'red-600')
                                        bg_fuma = 'bg-green-50' if ultimo.fuma == "No" else ('bg-orange-50' if ultimo.fuma == "Ex Fumador" else 'bg-red-50')
                                        ui.label(ultimo.fuma).classes(f'font-black px-4 py-1 rounded-md {color_fuma} {bg_fuma} text-xs')

                                    # INDICADOR ALCOHOL
                                    with ui.row().classes(
                                        'items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 shadow-sm wrap q-col-gutter-md'
                                    ):
                                        with ui.row().classes('items-center gap-3 wrap'):
                                            ui.icon(
                                                'local_bar',
                                                color='slate-500' if ultimo.consumo_excesivo_alcohol == "No" else 'rose-600'
                                            )
                                            ui.label('Alcohol Excesivo').classes('font-bold text-slate-700')

                                        color_alc = 'green-600' if ultimo.consumo_excesivo_alcohol == "No" else 'red-600'
                                        bg_alc = 'bg-green-50' if ultimo.consumo_excesivo_alcohol == "No" else 'bg-red-50'
                                        ui.label(ultimo.consumo_excesivo_alcohol).classes(f'font-black px-4 py-1 rounded-md {color_alc} {bg_alc} text-xs')
                            else:
                                ui.label('Sin registros').classes('text-slate-400 text-center py-10')

                # COLUMNA DERECHA: Evolución Histórica
                with ui.element('div').classes('col-12 col-lg-6'):
                    with ui.column().classes('gap-4'):

                        with ui.card().classes(HC_CARD_PROFESSIONAL):
                            ui.label('Evolución Histórica').classes('text-lg font-bold text-slate-700 mb-4')

                            with ui.scroll_area().classes('h-[500px] pr-4'):
                                if habitos_sorted:
                                    for hab in habitos_sorted:
                                        with ui.card().classes('mb-3 border-none shadow-sm bg-slate-50 overflow-hidden'):

                                            # Header miniatura
                                            with ui.row().classes('w-full bg-slate-200/50 p-2 px-4 justify-between items-center wrap q-col-gutter-sm'):
                                                ui.label(hab.fecha_registro.strftime("%d/%m/%Y")).classes('text-xs font-bold text-slate-600')

                                                with ui.row().classes('gap-1 wrap'):
                                                    if tiene_permiso("habitos_toxicos_manage"):
                                                        ui.button(icon='edit', on_click=lambda e, h=hab: self.editar_habito_toxico(h)).props('flat dense size=sm color=primary')
                                                        ui.button(icon='delete', on_click=lambda e, h=hab: self.eliminar_habito_toxico(h)).props('flat dense size=sm color=error')

                                            # Contenido del historial
                                            with ui.row().classes('p-3 w-full justify-around items-start wrap q-col-gutter-lg'):
                                                # Info Tabaco
                                                with ui.column().classes('items-center'):
                                                    ui.label(hab.fuma).classes('text-[10px] font-black uppercase text-slate-400')

                                                    with ui.row().classes('items-center gap-1 wrap'):
                                                        ui.icon('smoking_rooms', size='14px', color='red-400' if hab.fuma != "No" else 'green-400')

                                                        detalle = ""
                                                        if hab.fuma == "Si":
                                                            partes = []
                                                            if hab.cant_cigarros: partes.append(f"{hab.cant_cigarros} cig")
                                                            if hab.cant_tabacos: partes.append(f"{hab.cant_tabacos} tab")
                                                            detalle = " + ".join(partes)
                                                        elif hab.fuma == "Ex Fumador":
                                                            detalle = hab.tiempo_sin_fumar or "Abandono"

                                                        ui.label(detalle if detalle else hab.fuma).classes('text-xs font-medium text-slate-600')

                                                # Info Alcohol
                                                with ui.column().classes('items-center border-l border-slate-200 pl-6'):
                                                    ui.label('Alcohol').classes('text-[10px] font-black uppercase text-slate-400')

                                                    with ui.row().classes('items-center gap-1 wrap'):
                                                        ui.icon('local_bar', size='14px', color='red-400' if hab.consumo_excesivo_alcohol == "Si" else 'green-400')
                                                        ui.label(hab.consumo_excesivo_alcohol).classes('text-xs font-medium text-slate-600')
                                else:
                                    ui.label('Historial vacío').classes('text-slate-300 text-center w-full py-10')

    def agregar_habito_toxico(self):
        with ui.dialog() as dialog, ui.card().classes('w-[450px] p-6'):
            ui.label('Nueva Evaluación de Hábitos').classes(HEADER_TITLE_CLASSES)
            
            # Fecha
            with ui.input('Fecha').classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')  
            
            # Selector de Estado
            with ui.column().classes('w-full gap-4 mt-2'):
                ui.label("Estado de tabaquismo:").classes('font-bold text-slate-700')
                fuma_status = ui.radio(["Si", "No", "Ex Fumador"], value=None).props('inline color="rose"')

                # SECCIÓN PARA FUMADORES ACTIVOS
                with ui.column().classes('w-full bg-rose-50 p-4 rounded-lg gap-2').bind_visibility_from(fuma_status, 'value', backward=lambda v: v == 'Si'):
                    ui.label('Consumo Actual').classes('text-xs font-black text-rose-700 uppercase')
                    cigarros_input = ui.input(label='Cigarrillos al día').classes('w-full bg-white').props('outlined dense')
                    tabacos_input = ui.input(label='Tabacos (Puros) al día').classes('w-full bg-white').props('outlined dense')

                # SECCIÓN PARA EX-FUMADORES
                with ui.column().classes('w-full bg-blue-50 p-4 rounded-lg gap-2').bind_visibility_from(fuma_status, 'value', backward=lambda v: v == 'Ex Fumador'):
                    ui.label('Tiempo de Abandono').classes('text-xs font-black text-blue-700 uppercase')
                    tiempo_input = ui.input(label='¿Hace cuánto dejó de fumar?', placeholder='Ej: 3 años y 2 meses').classes('w-full bg-white').props('outlined dense')

            # Alcohol
            ui.label("Consumo excesivo de alcohol:").classes('font-bold text-slate-700 mt-2')
            alcohol_value = ui.radio(["Si", "No", "No Precisado"], value="No").props('inline color="indigo"')
            
            # ETIQUETA INFORMATIVA DE CRITERIOS
            with ui.column().classes('w-full bg-indigo-50/50 p-3 rounded-lg border border-indigo-100 mt-1'):
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.icon('info', size='xs', color='indigo-500')
                    ui.label('Criterios de Consumo Excesivo :').classes('text-[10px] font-black text-indigo-700 uppercase')
                
                with ui.grid(columns=2).classes('w-full gap-2'):
                    with ui.column().classes('gap-0'):
                        ui.label('♂ Hombres').classes('text-[10px] font-bold text-indigo-900')
                        ui.label('5+ bebidas/día o 15+/semana').classes('text-[10px] text-indigo-800')
                    with ui.column().classes('gap-0 border-l border-indigo-200 pl-2'):
                        ui.label('♀ Mujeres').classes('text-[10px] font-bold text-indigo-900')
                        ui.label('4+ bebidas/día o 8+/semana').classes('text-[10px] text-indigo-800')

            # Acción de guardado delegando al Controlador
            def procesar_guardado():
                exito, msg = self.controlador_habitos.guardar_habito(
                    paciente_id=self.paciente.id,
                    fecha_str=fecha_input.value,
                    fuma=fuma_status.value,
                    cant_cigarros=cigarros_input.value,
                    cant_tabacos=tabacos_input.value,
                    tiempo_sin_fumar=tiempo_input.value,
                    consumo_alcohol=alcohol_value.value
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_habitos_toxicos.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end mt-6'):
                ui.button('Guardar', on_click=procesar_guardado).classes(SUCCESS_BUTTON_CLASSES)
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')

        dialog.open()

    def editar_habito_toxico(self, habito):
        with ui.dialog() as dialog, ui.card().classes('w-[450px] p-6'):
            ui.label('Editar Evaluación de Hábitos').classes(HEADER_TITLE_CLASSES)
            
            # Fecha de Registro
            with ui.input('Fecha', value=habito.fecha_registro.strftime('%Y-%m-%d')) as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes('text-rose-500')
                with fecha_input.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            # Sección de Tabaquismo
            with ui.column().classes('w-full gap-4 mt-4'):
                ui.label("Estado de tabaquismo:").classes('font-bold text-slate-700')
                fuma_status = ui.radio(["Si", "No", "Ex Fumador"], value=habito.fuma).props('inline color="rose"')

                # CAMPOS PARA FUMADORES ACTIVOS
                with ui.column().classes('w-full bg-rose-50 p-4 rounded-lg gap-2').bind_visibility_from(fuma_status, 'value', backward=lambda v: v == 'Si'):
                    ui.label('Consumo Actual').classes('text-[10px] font-black text-rose-700 uppercase')
                    cigarros_input = ui.input(label='Cigarrillos al día', value=habito.cant_cigarros).classes('w-full bg-white').props('outlined dense')
                    tabacos_input = ui.input(label='Tabacos (Puros) al día', value=habito.cant_tabacos).classes('w-full bg-white').props('outlined dense')

                # CAMPOS PARA EX-FUMADORES
                with ui.column().classes('w-full bg-blue-50 p-4 rounded-lg gap-2').bind_visibility_from(fuma_status, 'value', backward=lambda v: v == 'Ex Fumador'):
                    ui.label('Tiempo de Abandono').classes('text-[10px] font-black text-blue-700 uppercase')
                    tiempo_input = ui.input(label='¿Hace cuánto dejó?', value=habito.tiempo_sin_fumar).classes('w-full bg-white').props('outlined dense')

            # Sección de Alcohol
            ui.label("Consumo excesivo de alcohol:").classes('font-bold text-slate-700 mt-4')
            alcohol_value = ui.radio(["Si", "No", "No Precisado"], value=habito.consumo_excesivo_alcohol).props('inline color="indigo"')

            # ETIQUETA DE AYUDA (CRITERIOS)
            with ui.column().classes('w-full bg-indigo-50/50 p-3 rounded-lg border border-indigo-100 mt-1'):
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.icon('info', size='xs', color='indigo-500')
                    ui.label('Criterios de Consumo Excesivo:').classes('text-[10px] font-black text-indigo-700 uppercase')
                with ui.grid(columns=2).classes('w-full'):
                    ui.label('♂ Hombres: 5+ día / 15+ sem').classes('text-[9px] text-indigo-800')
                    ui.label('♀ Mujeres: 4+ día / 8+ sem').classes('text-[9px] text-indigo-800 pl-2 border-l border-indigo-200')

            # Acción de edición delegando al Controlador
            def guardar_edicion():
                exito, msg = self.controlador_habitos.actualizar_habito(
                    habito=habito,
                    fecha_str=fecha_input.value,
                    fuma=fuma_status.value,
                    cant_cigarros=cigarros_input.value,
                    cant_tabacos=tabacos_input.value,
                    tiempo_sin_fumar=tiempo_input.value,
                    consumo_alcohol=alcohol_value.value
                )
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_habitos_toxicos.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-3 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).props('flat').classes(DANGER_BUTTON_CLASSES)
                ui.button('Guardar Cambios', on_click=guardar_edicion).classes(SUCCESS_BUTTON_CLASSES)

        dialog.open()

    def eliminar_habito_toxico(self, habito):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este hábito tóxico?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_habito(habito, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()

    def confirmar_eliminacion_habito(self, habito, dialog):
        exito, msg = self.controlador_habitos.eliminar_habito(habito)
        if exito:
            ui.notify(msg, type='positive')
            dialog.close()
            self.mostrar_habitos_toxicos.refresh()
        else:
            ui.notify(msg, type='negative')