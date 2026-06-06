from datetime import datetime
from nicegui import ui, events
from models import Indicaciones
from Errores import log_error_and_notify
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    HC_CARD_PROFESSIONAL,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
)


class HistoriaClinicaIndicacionesMixin:
    @ui.refreshable
    def indicaciones(self):

        with ui.column().classes('w-full q-pa-sm q-pa-md-md q-gutter-y-lg'):

            # HEADER
            with ui.row().classes('w-full justify-between items-center wrap q-col-gutter-md q-px-sm'):

                with ui.column().classes('q-gutter-y-xs'):

                    ui.label('Plan Terapéutico e Indicaciones').classes(
                        HEADER_TITLE_CLASSES
                    )

                    ui.label(
                        'Gestión de tratamientos y diagnóstico de diabetes'
                    ).classes('text-slate-400 text-sm')

                if tiene_permiso("indicaciones_manage"):

                    ui.button(
                        'Nueva Indicación',
                        icon='add_moderator',
                        on_click=self.agregar_indicaciones
                    ).classes(
                        PRIMARY_BUTTON_CLASSES + ' shadow-lg'
                    ).props('unelevated')

            # CONTENIDO PRINCIPAL RESPONSIVE QUASAR
            with ui.row().classes('w-full q-col-gutter-lg wrap'):

                # =========================================================
                # COLUMNA IZQUIERDA
                # =========================================================
                with ui.column().classes('col-12 col-lg-6 q-gutter-y-md'):

                    with ui.card().classes(
                        HC_CARD_PROFESSIONAL +
                        ' border-left-4 border-blue-600'
                    ):

                        ui.label(
                            'Resumen del Tratamiento Vigente'
                        ).classes(
                            'text-xs font-bold text-slate-400 uppercase tracking-widest mb-4'
                        )

                        indicaciones_list = [
                            ind for ind in self.paciente.indicaciones
                            if ind.fecha_registro
                        ]

                        ultima = max(
                            indicaciones_list,
                            key=lambda x: x.fecha_registro,
                            default=None
                        )

                        if ultima:

                            with ui.column().classes('w-full q-gutter-y-md'):

                                with ui.row().classes('items-center wrap q-gutter-sm'):

                                    ui.icon(
                                        'event_note',
                                        color='primary',
                                        size='sm'
                                    )

                                    ui.label(
                                        f'Actualizado el: {ultima.fecha_registro.strftime("%d/%m/%Y")}'
                                    ).classes(
                                        'text-sm font-bold text-blue-800'
                                    )

                                # TIPO DIABETES
                                with ui.column().classes('''
                                    w-full
                                    q-pa-md
                                    rounded-xl
                                    bg-indigo-1
                                    border border-indigo-2
                                '''):

                                    with ui.row().classes(
                                        'items-center wrap q-gutter-xs mb-1'
                                    ):

                                        ui.icon(
                                            'emergency',
                                            color='indigo-5',
                                            size='xs'
                                        )

                                        ui.label(
                                            'Tipo de Diabetes'
                                        ).classes(
                                            'text-[10px] font-bold text-indigo-400 uppercase'
                                        )

                                    ui.label(
                                        ultima.tipo_diabetes
                                    ).classes(
                                        'text-h5 text-weight-black text-indigo-10 q-ml-md'
                                    )

                                # PRESCRIPCIÓN
                                with ui.column().classes('''
                                    w-full
                                    q-pa-lg
                                    rounded-xl
                                    bg-slate-1
                                    border border-slate-3
                                    shadow-1
                                '''):

                                    with ui.row().classes(
                                        'items-center wrap q-gutter-xs mb-3'
                                    ):

                                        ui.icon(
                                            'assignment',
                                            color='grey-6',
                                            size='xs'
                                        )

                                        ui.label(
                                            'Prescripción Médica'
                                        ).classes(
                                            'text-[10px] font-bold text-slate-500 uppercase'
                                        )

                                    ui.markdown(
                                        f"**{ultima.tratamiento}**"
                                    ).classes(
                                        'text-slate-700 leading-relaxed q-ml-md'
                                    )

                        else:

                            with ui.column().classes('''
                                w-full
                                items-center
                                q-pa-xl
                                bg-slate-1
                                rounded-xl
                                border-2 border-dashed border-slate-3
                            '''):

                                ui.icon(
                                    'description',
                                    size='56px',
                                    color='grey-4'
                                )

                                ui.label(
                                    'No hay indicaciones activas'
                                ).classes(
                                    'text-slate-400 font-medium q-mt-sm'
                                )

                # =========================================================
                # COLUMNA DERECHA
                # =========================================================
                with ui.column().classes('col-12 col-lg-5 q-gutter-y-md'):

                    with ui.card().classes(HC_CARD_PROFESSIONAL):

                        with ui.row().classes(
                            'items-center wrap q-gutter-sm mb-4'
                        ):

                            ui.icon('history', color='grey-5')

                            ui.label(
                                'Historial de Cambios'
                            ).classes(
                                'text-h6 text-weight-bold text-slate-700'
                            )

                        with ui.scroll_area().classes(
                            'w-full'
                        ).style(
                            'height: 500px;'
                        ):

                            if self.paciente.indicaciones:

                                mens_ord = sorted(
                                    self.paciente.indicaciones,
                                    key=lambda x: x.fecha_registro,
                                    reverse=True
                                )

                                for ind in mens_ord:

                                    with ui.card().classes('''
                                        w-full
                                        q-mb-md
                                        q-pa-none
                                        border border-slate-2
                                        shadow-1
                                        hover:border-blue-3
                                    '''):

                                        # HEADER CARD
                                        with ui.row().classes('''
                                            w-full
                                            bg-slate-1
                                            q-pa-sm
                                            justify-between
                                            items-center
                                            wrap
                                            q-col-gutter-sm
                                        '''):

                                            with ui.row().classes(
                                                'items-center wrap q-gutter-sm'
                                            ):

                                                ui.label(
                                                    ind.fecha_registro.strftime("%d/%m/%Y")
                                                ).classes(
                                                    'text-sm font-bold text-slate-700'
                                                )

                                                ui.badge(
                                                    ind.tipo_diabetes,
                                                    color='blue-1'
                                                ).classes(
                                                    'text-blue-8 text-[10px] border border-blue-2'
                                                )

                                            with ui.row().classes(
                                                'wrap q-gutter-xs'
                                            ):

                                                if tiene_permiso("indicaciones_manage"):

                                                    ui.button(
                                                        icon='edit',
                                                        on_click=lambda e, i=ind:
                                                        self.editar_indicacion(i)
                                                    ).props(
                                                        'flat dense size=sm color=primary'
                                                    ).classes(
                                                        PRIMARY_BUTTON_CLASSES
                                                    )

                                                    ui.button(
                                                        icon='delete',
                                                        on_click=lambda e, i=ind:
                                                        self.eliminar_indicaciones(i)
                                                    ).props(
                                                        'flat dense size=sm color=error'
                                                    ).classes(
                                                        DANGER_BUTTON_CLASSES
                                                    )

                                        # CONTENIDO
                                        with ui.column().classes('q-pa-md'):

                                            ui.label(
                                                ind.tratamiento
                                            ).classes(
                                                'text-sm text-slate-600 italic'
                                            )

                            else:

                                ui.label(
                                    'Sin registros previos'
                                ).classes(
                                    'text-slate-300 text-center w-full q-py-xl'
                                )
    def agregar_indicaciones(self):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes(HC_CARD_PROFESSIONAL):
            ui.label('Nuevas Indicaciones').classes(HEADER_TITLE_CLASSES)
            with ui.input('Fecha').classes('w-full mb-4') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(
                        f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'
                    ).classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            tipo_diabetes = ui.select(
                [
                    'Diabetes Mellitus Tipo 1 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 1 Con Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Con Evidencias de Complicaciones',
                ],
                with_input=True,
                label='Diagnostico Definitivo',
            ).classes('w-102')
            indicaciones = ui.textarea(label='Indicaciones').props('autogrow').classes('w-full mb-4')

            def guardar():
                if not fecha_input.value:
                    ui.notify('La fecha es obligatoria', type='negative')
                    return
                try:
                    nuevo_registro = Indicaciones(
                        paciente_id=self.paciente.id,
                        fecha_registro=datetime.strptime(fecha_input.value, '%Y-%m-%d').date(),
                        tipo_diabetes=tipo_diabetes.value if tipo_diabetes.value is not None else "No Registrado",
                        tratamiento=indicaciones.value if indicaciones.value is not None else "No Registrado",
                    )
                    self.session.add(nuevo_registro)
                    self.session.commit()
                    ui.notify('Registro guardado exitosamente', type='positive')
                    dialog.close()
                    self.indicaciones.refresh()
                except Exception as e:
                    self.session.rollback()
                    log_error_and_notify(e, 'Error al guardar nuevas indicaciones')
                    ui.notify(f'Error al guardar: {str(e)}', type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')

                def key_handler(event: events.KeyEventArguments):
                    if event.action.keydown and event.key == "Enter":
                        guardar()

                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                ui.keyboard(key_handler)
            dialog.open()

    def editar_indicacion(self, registro):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6'):
            ui.label('Editar Indicaciones ').classes(HEADER_TITLE_CLASSES)
            fecha_valor = registro.fecha_registro.strftime('%Y-%m-%d') if registro.fecha_registro else ''
            with ui.input('Fecha ', value=fecha_valor).classes('w-full mb-4') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(
                        f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'
                    ).classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            tipo_diabetes = ui.select(
                [
                    'Diabetes Mellitus Tipo 1 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 1 Con Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Con Evidencias de Complicaciones',
                    "No Registrado",
                ],
                value=registro.tipo_diabetes,
                label='Diagnostico Definitivo',
            ).classes(INPUT_CLASSES)
            indicaciones = ui.textarea(label='Indicaciones', value=registro.tratamiento or '').props('autogrow').classes('w-full mb-4')

            def actualizar():
                if not fecha_input.value:
                    ui.notify('La fecha es obligatoria', type='negative')
                    return
                try:
                    registro.fecha_registro = datetime.strptime(fecha_input.value, '%Y-%m-%d').date()
                    registro.tipo_diabetes = tipo_diabetes.value if tipo_diabetes.value is not None else "No Registrado"
                    registro.tratamiento = indicaciones.value if indicaciones.value is not None else "No Registrado"
                    self.session.commit()
                    ui.notify('Registro actualizado exitosamente', type='positive')
                    dialog.close()
                    self.indicaciones.refresh()
                except Exception as e:
                    self.session.rollback()
                    log_error_and_notify(e, 'Error al actualizar indicaciones')
                    ui.notify(f'Error al actualizar: {str(e)}', type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')

                def key_handler(event: events.KeyEventArguments):
                    if event.action.keydown and event.key == "Enter":
                        actualizar()

                ui.button('Guardar Cambios', on_click=actualizar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                ui.keyboard(key_handler)
            dialog.open()

    def eliminar_indicaciones(self, examen):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar estas Indicaciones?')
            with ui.row().classes('w-full justify-end gap-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props(' color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_indicaciones(examen, dialog)).classes(
                    DANGER_BUTTON_CLASSES
                ).props('color="error"')
        dialog.open()

    def confirmar_eliminacion_indicaciones(self, examen, dialog):
        try:
            self.session.delete(examen)
            self.session.commit()
            ui.notify('Indicaciones eliminadas correctamente', type='positive')
            self.indicaciones.refresh()
        except Exception as e:
            log_error_and_notify(e, f'Error al eliminar las indicaciones ID {examen.id}')
            ui.notify(f'Error al eliminar las Indicaciones: {str(e)}', type='negative')
        finally:
            dialog.close()
