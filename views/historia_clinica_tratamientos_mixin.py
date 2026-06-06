from datetime import datetime

from nicegui import ui
from Errores import log_error_and_notify
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)
from seguridad_roles import tiene_permiso


class HistoriaClinicaTratamientosMixin:

    # =========================================================
    # MOSTRAR
    # =========================================================

    @ui.refreshable
    def mostrar_tratamientos(self):

        with ui.column().classes('w-full md:p-6 gap-6 max-w-7xl mx-auto'):

            # =========================================================
            # HEADER
            # =========================================================

            with ui.row().classes(
                'w-full justify-between items-center px-2 q-col-gutter-md wrap'
            ):

                with ui.column().classes('gap-1 col-12 col-md'):

                    ui.label(
                        'Esquema Terapéutico'
                    ).classes(
                        HEADER_TITLE_CLASSES
                    )

                    ui.label(
                        'Control de medicación específica y tratamientos concomitantes'
                    ).classes(
                        'text-slate-400 text-sm pl-0 md:pl-2'
                    )

            # =========================================================
            # GRID
            # =========================================================

            with ui.row().classes('w-full q-col-gutter-lg'):

                # =====================================================
                # TRATAMIENTO DIABETES
                # =====================================================

                with ui.element('div').classes('col-12 p-0 col-lg-6'):

                    with ui.card().classes(
                        HC_CARD_PROFESSIONAL +
                        ' border-l-4 border-blue-600 w-full'
                    ):

                        with ui.row().classes(
                            'justify-between items-center mb-4 w-full wrap gap-2'
                        ):

                            ui.label(
                                'Tratamiento Diabetes'
                            ).classes(
                                'text-sm font-bold text-slate-500 uppercase tracking-wider'
                            )

                            if tiene_permiso("tratamiento_actual_manage"):

                                ui.button(
                                    icon='add',
                                    on_click=self.agregar_tratamiento_actual
                                ).props(
                                    'flat round dense color="primary"'
                                ).classes(
                                    'bg-blue-50 hover:bg-blue-100'
                                )

                        reciente = self.controlador_tratamientos.obtener_tratamiento_actual_reciente(self.paciente)

                        if reciente:

                            with ui.column().classes('w-full gap-2'):

                                ui.label(
                                    reciente.fecha_registro.strftime("%d/%m/%Y")
                                ).classes(
                                    '''
                                    text-xs font-black text-blue-700
                                    bg-blue-50 px-3 py-1 rounded-md w-fit
                                    '''
                                )

                                color_via = (
                                    'green'
                                    if reciente.sigue_via_clinica == "Si"
                                    else 'orange'
                                )

                                ui.badge(
                                    f'Vía Clínica: {reciente.sigue_via_clinica}',
                                    color=color_via
                                ).props('outline')

                                with ui.column().classes(
                                    '''
                                    w-full p-4
                                    bg-gradient-to-br from-blue-50 to-white
                                    rounded-xl border border-blue-100 shadow-sm
                                    '''
                                ):

                                    esquema = self.controlador_tratamientos.obtener_esquema_visual(
                                        reciente
                                    )

                                    for med in esquema:

                                        with ui.card().classes(
                                            '''
                                            w-full p-3
                                            bg-white border border-slate-200
                                            rounded-lg shadow-none
                                            '''
                                        ):

                                            with ui.row().classes(
                                                'items-center gap-2'
                                            ):

                                                ui.icon(
                                                    'medication',
                                                    color='blue-600',
                                                    size='sm'
                                                )

                                                ui.label(
                                                    med.get(
                                                        'tratamiento',
                                                        ''
                                                    )
                                                ).classes(
                                                    '''
                                                    text-md font-bold
                                                    text-slate-700
                                                    '''
                                                )

                                            ui.label(
                                                f"Dosis: {med.get('dosis', '')}"
                                            ).classes(
                                                'text-sm text-slate-600 mt-2'
                                            )

                                            if med.get('anio_inicio'):

                                                ui.label(
                                                    f"Inicio: {med.get('anio_inicio')}"
                                                ).classes(
                                                    'text-xs text-slate-500'
                                                )

                        else:

                            with ui.column().classes(
                                '''
                                w-full items-center py-10
                                bg-slate-50 rounded-xl
                                border-2 border-dashed border-slate-200
                                '''
                            ):

                                ui.icon(
                                    'medical_services',
                                    size='48px',
                                    color='slate-300'
                                )

                                ui.label(
                                    'Sin tratamiento registrado'
                                ).classes(
                                    'text-slate-400 text-sm mt-2'
                                )

                # =====================================================
                # OTROS TRATAMIENTOS
                # =====================================================

                with ui.element('div').classes('col-12 col-lg-6'):

                    with ui.card().classes(
                        HC_CARD_PROFESSIONAL +
                        ' border-l-4 border-purple-500 w-full'
                    ):

                        with ui.row().classes(
                            'justify-between items-center mb-4 w-full wrap gap-2'
                        ):

                            ui.label(
                                'Otros Tratamientos'
                            ).classes(
                                'text-sm font-bold text-slate-500 uppercase tracking-wider'
                            )

                            if tiene_permiso(
                                "otros_tratamientos_manage"
                            ):

                                ui.button(
                                    icon='add',
                                    on_click=self.agregar_otro_tratamiento
                                ).props(
                                    'flat round dense color="secondary"'
                                ).classes(
                                    'bg-purple-50 hover:bg-purple-100'
                                )

                        otros_sorted = self.controlador_tratamientos.obtener_otros_tratamientos_ordenados(self.paciente)

                        if otros_sorted:

                            with ui.column().classes('w-full gap-2'):

                                for trat in otros_sorted:

                                    with ui.row().classes(
                                        '''
                                        items-center justify-between
                                        p-3 bg-slate-50 rounded-lg
                                        border border-slate-100
                                        hover:bg-white transition-colors
                                        w-full wrap gap-3
                                        '''
                                    ):

                                        with ui.row().classes(
                                            'items-center gap-3 flex-wrap'
                                        ):

                                            ui.icon(
                                                'pill',
                                                color='purple-400',
                                                size='xs'
                                            )

                                            with ui.column().classes(
                                                'gap-0'
                                            ):

                                                ui.label(
                                                    trat.tratamiento
                                                ).classes(
                                                    '''
                                                    text-sm font-bold
                                                    text-slate-700 leading-tight
                                                    '''
                                                )

                                                ui.label(
                                                    f"Dosis: {trat.dosis}"
                                                ).classes(
                                                    'text-[11px] text-slate-500'
                                                )

                                        with ui.row().classes(
                                            'gap-1 justify-end'
                                        ):

                                            if tiene_permiso(
                                                "otros_tratamientos_manage"
                                            ):

                                                ui.button(
                                                    icon='edit',
                                                    on_click=lambda e, t=trat:
                                                    self.editar_otro_tratamiento(t)
                                                ).props(
                                                    'flat dense size=sm color=primary'
                                                ).classes(
                                                    PRIMARY_BUTTON_CLASSES
                                                )

                                                ui.button(
                                                    icon='delete',
                                                    on_click=lambda e, t=trat:
                                                    self.eliminar_otro_tratamiento(t)
                                                ).props(
                                                    'flat dense size=sm color=error'
                                                ).classes(
                                                    DANGER_BUTTON_CLASSES
                                                )

            # =========================================================
            # HISTORIAL
            # =========================================================

            with ui.expansion(
                'Historial de Cambios en Tratamiento Diabetes',
                icon='history'
            ).classes(
                '''
                w-full bg-white border border-slate-200
                rounded-xl shadow-none mt-4
                '''
            ):

                historial = self.controlador_tratamientos.obtener_historial_tratamientos(self.paciente)

                if historial:

                    with ui.column().classes(
                        'w-full p-2 md:p-4 gap-4'
                    ):

                        for h in historial:

                            with ui.card().classes(
                                'w-full border border-slate-200'
                            ):

                                with ui.column().classes(
                                    'w-full gap-3 p-4'
                                ):

                                    with ui.row().classes(
                                        'justify-between items-center wrap'
                                    ):

                                        ui.label(
                                            h.fecha_registro.strftime(
                                                "%d/%m/%Y"
                                            )
                                        ).classes(
                                            'text-xs font-bold text-slate-400'
                                        )

                                        ui.label(
                                            f"Vía: {h.sigue_via_clinica}"
                                        ).classes(
                                            'text-xs font-bold'
                                        )

                                    esquema = self.controlador_tratamientos.obtener_esquema_visual(h)

                                    for med in esquema:

                                        with ui.card().classes(
                                            '''
                                            w-full p-3
                                            bg-slate-50 border
                                            rounded-lg shadow-none
                                            '''
                                        ):

                                            ui.label(
                                                med.get(
                                                    'tratamiento',
                                                    ''
                                                )
                                            ).classes(
                                                'font-bold text-slate-700'
                                            )

                                            ui.label(
                                                f"Dosis: {med.get('dosis', '')}"
                                            ).classes(
                                                'text-sm text-slate-600'
                                            )

                                            if med.get('anio_inicio'):

                                                ui.label(
                                                    f"Inicio: {med.get('anio_inicio')}"
                                                ).classes(
                                                    'text-xs text-slate-500'
                                                )

                                    with ui.row().classes(
                                        'justify-end gap-2'
                                    ):

                                        if tiene_permiso(
                                            "tratamiento_actual_manage"
                                        ):

                                            ui.button(
                                                icon='edit',
                                                on_click=lambda e, t=h:
                                                self.editar_tratamiento_actual(t)
                                            ).props(
                                                'flat dense size=sm color=primary'
                                            ).classes(
                                                PRIMARY_BUTTON_CLASSES
                                            )

                                            ui.button(
                                                icon='delete',
                                                on_click=lambda e, t=h:
                                                self.eliminar_tratamiento_actual(t)
                                            ).props(
                                                'flat dense size=sm color=error'
                                            ).classes(
                                                DANGER_BUTTON_CLASSES
                                            )

                else:

                    ui.label(
                        'Sin historial disponible'
                    ).classes(
                        'p-4 text-slate-400 italic'
                    )

    # =========================================================
    # AGREGAR TRATAMIENTO ACTUAL
    # =========================================================

    def agregar_tratamiento_actual(self):

        with ui.dialog() as dialog, ui.card().classes(
            'w-full max-w-4xl p-4'
        ):

            ui.label(
                'Agregar Tratamiento Actual'
            ).classes(
                HEADER_TITLE_CLASSES
            )

            # =====================================================
            # FECHA
            # =====================================================

            with ui.input('Fecha').classes('w-full') as fecha_input:

                with ui.menu().props('no-parent-event') as menu:

                    with ui.date().bind_value(fecha_input).props(
                        f'locale="es" '
                        f'default-year-month={self.current_month} '
                        f':options="date => date <= \'{self.today}\'"'
                    ):

                        with ui.row().classes('justify-end'):

                            ui.button(
                                'Cerrar',
                                on_click=menu.close
                            ).props(
                                'flat'
                            ).classes(
                                DANGER_BUTTON_CLASSES
                            )

                    with fecha_input.add_slot('append'):

                        ui.icon(
                            'edit_calendar'
                        ).on(
                            'click',
                            menu.open
                        ).classes(
                            'cursor-pointer'
                        )

            # =====================================================
            # CONTENEDOR MEDICAMENTOS
            # =====================================================

            medicamentos_container = ui.column().classes(
                'w-full gap-3 mt-4'
            )

            opciones = [
                "Tratamiento No Farmacologico",
                "SUR",
                "Metformina",
                "Insulina",
                "Otros"
            ]

            # =====================================================
            # AGREGAR MEDICAMENTO
            # =====================================================

            def agregar_medicamento(
                tratamiento_valor=None,
                dosis_valor='',
                anio_valor=''
            ):

                with medicamentos_container:

                    with ui.card().classes(
                        'w-full p-4 border rounded-xl'
                    ) as card:

                        tratamiento_input = ui.select(
                            options=opciones,
                            label='Medicamento',
                            value=tratamiento_valor
                        ).classes('w-full')

                        otros_input = ui.input(
                            label='Otro medicamento'
                        ).classes(INPUT_CLASSES)

                        # Oculto por defecto al agregar uno nuevo
                        otros_input.set_visibility(False)

                        # Control del cambio de valor y vaciado del input
                        def manejar_cambio(e):
                            if e.value == "Otros":
                                otros_input.set_visibility(True)
                                otros_input.value = ""  # <-- Garantiza que aparezca vacío
                            else:
                                otros_input.set_visibility(False)
                                otros_input.value = ""

                        tratamiento_input.on_value_change(manejar_cambio)

                        dosis_input = ui.input(
                            label='Dosis',
                            value=dosis_valor
                        ).classes(INPUT_CLASSES)

                        anio_input = ui.input(
                            label='Año inicio',
                            value=anio_valor
                        ).classes(INPUT_CLASSES)

                        ui.button(
                            'Eliminar',
                            icon='delete',
                            on_click=card.delete
                        ).props(
                            'flat color=red'
                        ).classes(
                            DANGER_BUTTON_CLASSES
                        )

            agregar_medicamento()

            ui.button(
                'Agregar medicamento',
                icon='add',
                on_click=agregar_medicamento
            ).classes(
                PRIMARY_BUTTON_CLASSES
            ).props(
                'color="primary"'
            )

            # =====================================================
            # VIA CLINICA
            # =====================================================

            via_clinica_input = ui.select(
                options=["Si", "No"],
                label='¿Sigue lo establecido por la Vía Clínica?',
                value="Si"
            ).classes('w-full mt-4')

            # =====================================================
            # GUARDAR
            # =====================================================

            def guardar():

                try:

                    if not fecha_input.value:

                        ui.notify(
                            'Debe seleccionar una fecha',
                            type='negative'
                        )

                        return

                    fecha_registro = datetime.strptime(
                        fecha_input.value,
                        '%Y-%m-%d'
                    ).date()

                    cards = medicamentos_container.default_slot.children

                    esquema = []

                    nombres_tratamientos = []

                    for card in cards:

                        children = card.default_slot.children

                        tratamiento_input = children[0]
                        otros_input = children[1]
                        dosis_input = children[2]
                        anio_input = children[3]

                        if not tratamiento_input.value:
                            continue

                        nombre = (
                            otros_input.value
                            if tratamiento_input.value == "Otros"
                            else tratamiento_input.value
                        )

                        esquema.append({
                            "tratamiento": nombre,
                            "dosis": (
                                dosis_input.value
                                or "No registrado"
                            ),
                            "anio_inicio": (
                                anio_input.value or ""
                            )
                        })

                        nombres_tratamientos.append(nombre)

                    if not esquema:

                        ui.notify(
                            'Debe agregar al menos un medicamento',
                            type='negative'
                        )

                        return

                    self.controlador_tratamientos.guardar_tratamiento_actual(
                        paciente=self.paciente,
                        fecha_registro=fecha_registro,
                        tratamiento_str=' + '.join(nombres_tratamientos),
                        esquema=esquema,
                        sigue_via_clinica=via_clinica_input.value
                    )

                    ui.notify(
                        'Tratamiento agregado correctamente',
                        type='positive'
                    )

                    dialog.close()

                    self.mostrar_tratamientos.refresh()

                except Exception as e:

                    ui.notify(
                        f'Error al agregar: {str(e)}',
                        type='negative'
                    )

            # =====================================================
            # BOTONES
            # =====================================================

            with ui.row().classes(
                'w-full justify-end gap-4 mt-4'
            ):

                ui.button(
                    'Cancelar',
                    on_click=dialog.close
                ).classes(
                    DANGER_BUTTON_CLASSES
                ).props(
                    'color="warning"'
                )

                ui.button(
                    'Guardar',
                    on_click=guardar
                ).classes(
                    SUCCESS_BUTTON_CLASSES
                ).props(
                    'color="success"'
                )

            dialog.open()

    def editar_tratamiento_actual(self, tratamiento):

        with ui.dialog() as dialog, ui.card().classes(
            'w-full max-w-4xl p-4'
        ):

            ui.label(
                'Editar Tratamiento Actual'
            ).classes(
                HEADER_TITLE_CLASSES
            )

            # =====================================================
            # FECHA
            # =====================================================

            fecha_valor = (
                tratamiento.fecha_registro.strftime('%Y-%m-%d')
                if tratamiento.fecha_registro
                else ''
            )

            with ui.input(
                'Fecha',
                value=fecha_valor
            ).classes('w-full') as fecha_input:

                with ui.menu().props('no-parent-event') as menu:

                    with ui.date().bind_value(fecha_input).props(
                        f'locale="es" '
                        f'default-year-month={self.current_month} '
                        f':options="date => date <= \'{self.today}\'"'
                    ):

                        with ui.row().classes('justify-end'):

                            ui.button(
                                'Cerrar',
                                on_click=menu.close
                            ).props(
                                'flat'
                            ).classes(
                                DANGER_BUTTON_CLASSES
                            )

                    with fecha_input.add_slot('append'):

                        ui.icon(
                            'edit_calendar'
                        ).on(
                            'click',
                            menu.open
                        ).classes(
                            'cursor-pointer'
                        )

            # =====================================================
            # CONTENEDOR MEDICAMENTOS
            # =====================================================

            medicamentos_container = ui.column().classes(
                'w-full gap-3 mt-4'
            )

            opciones = [
                "Tratamiento No Farmacologico",
                "SUR",
                "Metformina",
                "Insulina",
                "Otros"
            ]

            # =====================================================
            # FUNCIÓN AGREGAR MEDICAMENTO
            # =====================================================

            def agregar_medicamento(
                tratamiento_valor=None,
                dosis_valor='',
                anio_valor=''
            ):

                with medicamentos_container:

                    with ui.card().classes(
                        'w-full p-4 border rounded-xl'
                    ) as card:

                        es_otro = (
                            tratamiento_valor not in opciones
                            and tratamiento_valor is not None
                        )

                        valor_inicial_select = "Otros" if es_otro else tratamiento_valor

                        tratamiento_input = ui.select(
                            options=opciones,
                            label='Medicamento',
                            value=valor_inicial_select
                        ).classes('w-full')

                        otros_input = ui.input(
                            label='Otro medicamento',
                            value=tratamiento_valor if es_otro else ''
                        ).classes(INPUT_CLASSES)

                        otros_input.set_visibility(es_otro)

                        # Manejador reactivo para la edición
                        def manejar_cambio_edit(e):
                            if e.value == "Otros":
                                otros_input.set_visibility(True)
                                # Solo vaciamos si realmente se cambió la opción actual del select
                                if tratamiento_input.value != valor_inicial_select:
                                    otros_input.value = ""
                            else:
                                otros_input.set_visibility(False)
                                otros_input.value = ""

                        tratamiento_input.on_value_change(manejar_cambio_edit)

                        dosis_input = ui.input(
                            label='Dosis',
                            value=dosis_valor
                        ).classes(INPUT_CLASSES)

                        anio_input = ui.input(
                            label='Año inicio',
                            value=anio_valor
                        ).classes(INPUT_CLASSES)

                        ui.button(
                            'Eliminar',
                            icon='delete',
                            on_click=card.delete
                        ).props(
                            'flat color=red'
                        ).classes(
                            DANGER_BUTTON_CLASSES
                        )
            # =====================================================
            # CARGAR DATOS VIEJOS O NUEVOS
            # =====================================================

            if tratamiento.esquema_json and len(tratamiento.esquema_json) > 0:

                for med in tratamiento.esquema_json:

                    agregar_medicamento(
                        tratamiento_valor=med.get(
                            'tratamiento',
                            ''
                        ),
                        dosis_valor=med.get(
                            'dosis',
                            ''
                        ),
                        anio_valor=med.get(
                            'anio_inicio',
                            ''
                        )
                    )

            else:

                # COMPATIBILIDAD CON REGISTROS VIEJOS

                agregar_medicamento(
                    tratamiento_valor=tratamiento.tratamiento,
                    dosis_valor=tratamiento.dosis,
                    anio_valor=''
                )

            # =====================================================
            # BOTÓN AGREGAR MEDICAMENTO
            # =====================================================

            ui.button(
                'Agregar medicamento',
                icon='add',
                on_click=agregar_medicamento
            ).classes(
                PRIMARY_BUTTON_CLASSES
            ).props(
                'color="primary"'
            )

            # =====================================================
            # VÍA CLÍNICA
            # =====================================================

            via_clinica_input = ui.select(
                options=["Si", "No"],
                label='¿Sigue lo establecido por la Vía Clínica?',
                value=tratamiento.sigue_via_clinica or "Si"
            ).classes('w-full mt-4')

            # =====================================================
            # GUARDAR
            # =====================================================

            def guardar():

                try:

                    if not fecha_input.value:

                        ui.notify(
                            'Debe seleccionar una fecha',
                            type='negative'
                        )

                        return

                    fecha_registro = datetime.strptime(
                        fecha_input.value,
                        '%Y-%m-%d'
                    ).date()

                    cards = medicamentos_container.default_slot.children

                    esquema = []

                    nombres_tratamientos = []

                    for card in cards:

                        children = card.default_slot.children

                        tratamiento_input = children[0]
                        otros_input = children[1]
                        dosis_input = children[2]
                        anio_input = children[3]

                        if not tratamiento_input.value:
                            continue

                        nombre = (
                            otros_input.value
                            if tratamiento_input.value == "Otros"
                            else tratamiento_input.value
                        )

                        if not nombre:
                            continue

                        esquema.append({
                            "tratamiento": nombre,
                            "dosis": (
                                dosis_input.value
                                or "No registrado"
                            ),
                            "anio_inicio": (
                                anio_input.value or ""
                            )
                        })

                        nombres_tratamientos.append(nombre)

                    if not esquema:

                        ui.notify(
                            'Debe agregar al menos un medicamento',
                            type='negative'
                        )

                        return

                    # =============================================
                    # ACTUALIZAR DESDE EL CONTROLADOR
                    # =============================================

                    self.controlador_tratamientos.actualizar_tratamiento_actual(
                        tratamiento=tratamiento,
                        fecha_registro=fecha_registro,
                        tratamiento_str=' + '.join(nombres_tratamientos),
                        esquema=esquema,
                        sigue_via_clinica=via_clinica_input.value
                    )

                    ui.notify(
                        'Tratamiento actualizado correctamente',
                        type='positive'
                    )

                    dialog.close()

                    self.mostrar_tratamientos.refresh()

                except Exception as e:

                    ui.notify(
                        f'Error al actualizar: {str(e)}',
                        type='negative'
                    )

            # =====================================================
            # BOTONES
            # =====================================================

            with ui.row().classes(
                'w-full justify-end gap-4 mt-4'
            ):

                ui.button(
                    'Cancelar',
                    on_click=dialog.close
                ).classes(
                    DANGER_BUTTON_CLASSES
                ).props(
                    'color="warning"'
                )

                ui.button(
                    'Guardar',
                    on_click=guardar
                ).classes(
                    SUCCESS_BUTTON_CLASSES
                ).props(
                    'color="success"'
                )

            dialog.open()
    def eliminar_tratamiento_actual(self, tratamiento):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este registro del historial?').classes('text-xl font-bold mb-4 text-red-600')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_tratamiento_actual(tratamiento, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()


    def confirmar_eliminacion_tratamiento_actual(self, tratamiento, dialog):
        try:
            if tratamiento is None:
                ui.notify('Error: El tratamiento ya no existe', type='negative')
                dialog.close()
                return
            
            self.controlador_tratamientos.eliminar_tratamiento_actual(tratamiento)
            ui.notify('Registro eliminado correctamente', type='positive')
            dialog.close()
            self.mostrar_tratamientos.refresh()
        except Exception as e:
            ui.notify(f'Error al eliminar el registro: {str(e)}', type='negative')

    def agregar_otro_tratamiento(self):
        # Crear una nueva ventana para el formulario
        with ui.dialog() as dialog, ui.card().classes('p-3 w-full max-w-4xl').style("width:760px; max-width:none;"):
            
            ui.label('Agregar Tratamientos').classes(HEADER_TITLE_CLASSES)
            
            # Contenedor para los tratamientos
            tratamientos_container = ui.row().classes('w-full flex-wrap gap-4')
            
            # Función para crear un nuevo campo de tratamiento
            def agregar_campo_tratamiento(tratamiento=None, dosis=None, fecha=None):
                with tratamientos_container:
                     with ui.card().classes(HC_SECTION_CARD) as card:
                        # Fecha
                        
                        with ui.input('Fecha').classes('w-full') as fecha_input:
                            with ui.menu().props('no-parent-event') as menu:
                                with ui.date().bind_value(fecha_input).props(
                                        f'locale="es" '
                                        f'default-year-month={self.current_month} '
                                        f':options="date => date <= \'{self.today}\'"'
                                    ):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                                with fecha_input.add_slot('append'):
                                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                        
                        # Campos del formulario
                        tratamiento_input = ui.input(
                            label='Tratamiento', 
                            placeholder='Nombre del medicamento',
                            value=tratamiento if tratamiento else ''
                        ).classes(INPUT_CLASSES)
                        
                        dosis_input = ui.input(
                            label='Dosis', 
                            placeholder='Dosis del medicamento',
                            value=dosis if dosis else ''
                        ).classes(INPUT_CLASSES)
                        
                        # Botón para eliminar este tratamiento
                        ui.button('Eliminar', on_click=card.delete).props('flat color=red').classes(DANGER_BUTTON_CLASSES + ' mt-2').props('color="error"')
            
            # Agregar primer tratamiento vacío
            agregar_campo_tratamiento()
            
            # Botón para agregar más tratamientos
            ui.button('Agregar otro tratamiento', on_click=agregar_campo_tratamiento, icon='add').classes(PRIMARY_BUTTON_CLASSES ).props('color="primary"')
            
            # Botones principales
            with ui.row().classes('justify-end gap-2 w-full'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar todos', on_click=lambda: guardar_todos()).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            def guardar_todos():
                # Obtener todos los tratamientos del contenedor
                cards = tratamientos_container.default_slot.children
                
                if not cards:
                    ui.notify('No hay tratamientos para guardar', color='negative')
                    return
                    
                tratamientos_guardados = 0
                errores = 0
                
                for card in cards:
                    try:
                        # Obtener los inputs de cada card
                        inputs = card.default_slot.children
                        fecha_input = inputs[0]
                        tratamiento_input = inputs[1]
                        dosis_input = inputs[2]
                        
                        # Validar campos
                        if not tratamiento_input.value:
                            errores += 1
                            continue
                            
                        if not fecha_input.value:
                            errores += 1
                            continue
                            
                        # Convertir la fecha
                        fecha_registro = datetime.strptime(fecha_input.value, '%Y-%m-%d').date()
                        
                        # Agregar de manera individual a la sesión vía el controlador
                        self.controlador_tratamientos.agregar_otro_tratamiento_individual(
                            paciente=self.paciente,
                            tratamiento_val=tratamiento_input.value,
                            dosis_val=dosis_input.value,
                            fecha_registro=fecha_registro
                        )
                        tratamientos_guardados += 1
                        
                    except Exception as e:
                        self.controlador_tratamientos.rollback()
                        log_error_and_notify(e, 'Error al guardar tratamiento')
                        errores += 1
                        print(f"Error al guardar tratamiento: {str(e)}")
                
                try:
                    self.controlador_tratamientos.commit()
                    self.controlador_tratamientos.refresh(self.paciente)
                    
                    if tratamientos_guardados > 0:
                        msg = f"Se guardaron {tratamientos_guardados} tratamientos"
                        if errores > 0:
                            msg += f", {errores} no se pudieron guardar"
                        ui.notify(msg, color='positive' if errores == 0 else 'warning')
                    else:
                        ui.notify('No se pudo guardar ningún tratamiento', color='negative')
                    
                    dialog.close()
                    self.mostrar_tratamientos.refresh()
                    
                except Exception as e:
                    log_error_and_notify(e, 'Error al guardar tratamientos')
                    self.controlador_tratamientos.rollback()
                    ui.notify(f'Error al guardar: {str(e)}', color='negative')
        
        dialog.open()
    
    def editar_otro_tratamiento(self, tratamiento):
        # Crear una nueva ventana para el formulario
        with ui.dialog() as dialog, ui.card().classes('p-4 w-96'):
            ui.label('Editar Tratamiento').classes(HEADER_TITLE_CLASSES)

              # Fecha
            fecha_valor = tratamiento.fecha_registro.strftime('%Y-%m-%d') if tratamiento.fecha_registro else ''
            with ui.input('Fecha', value=fecha_valor).classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(
                            f'locale="es" '
                            f'default-year-month={self.current_month} '
                            f':options="date => date <= \'{self.today}\'"'
                        ):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            
            # Campos del formulario con valores actuales
            tratamiento_input = ui.input(label='Tratamiento', value=tratamiento.tratamiento).classes(INPUT_CLASSES)
            dosis_input = ui.input(label='Dosis', value=tratamiento.dosis if hasattr(tratamiento, "dosis") else "").classes(INPUT_CLASSES)
            
            
            # Botones
            with ui.row().classes('justify-end gap-2'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=lambda: guardar()).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            def guardar():
                try:
                    # Convertir fecha si es string
                    fecha = fecha_input.value
                    if isinstance(fecha, str):
                        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                    
                    # Actualizar a través del controlador
                    self.controlador_tratamientos.actualizar_otro_tratamiento(
                        tratamiento=tratamiento,
                        fecha_registro=fecha,
                        tratamiento_val=tratamiento_input.value,
                        dosis_val=dosis_input.value
                    )
                    ui.notify('Tratamiento actualizado correctamente', color='positive')
                except Exception as e:
                    ui.notify(f'Error: {str(e)}', color='negative')
                
                dialog.close()
                self.mostrar_tratamientos.refresh()
    
        dialog.open()
    
    def eliminar_otro_tratamiento(self, tratamiento):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este tratamiento?').classes('text-xl font-bold mb-4 text-red-600')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_otro_tratamiento(tratamiento, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()

    def confirmar_eliminacion_otro_tratamiento(self, tratamiento, dialog):
        try:
            if tratamiento is None:
                ui.notify('Error: El tratamiento ya no existe', type='negative')
                dialog.close()
                return
            
            self.controlador_tratamientos.eliminar_otro_tratamiento(tratamiento)
            ui.notify('Tratamiento eliminado correctamente', type='positive')
            dialog.close()
            self.mostrar_tratamientos.refresh()
        except Exception as e:
            ui.notify(f'Error al eliminar el tratamiento: {str(e)}', type='negative')

    
    def actualizar_campo_otros(self):
        self.mostrar_campo_otros = (self.forma_presentacion_diagnostico_input.value == 'Otros')

    def actualizar_campo_otros_tratamiento(self):
        self.mostrar_campo_otros_tratamiento = (self.tratamiento_inicial_input.value == 'Otros')
        self.otros_tratamiento_input.update()