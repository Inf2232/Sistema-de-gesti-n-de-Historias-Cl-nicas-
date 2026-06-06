from datetime import datetime
from nicegui import ui
from models import Ingreso
from Errores import log_error_and_notify
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
)


class HistoriaClinicaIngresosMixin:
    @ui.refreshable
    def mostrar_ingresos(self):

        ingresos = (
            self.session.query(Ingreso)
            .filter_by(paciente_id=self.paciente.id)
            .order_by(Ingreso.fecha_ingreso.desc())
            .all()
        )

        # HEADER
        with ui.row().classes('w-full items-center justify-between wrap q-col-gutter-md mb-4'):

            ui.label('Ingresos del paciente').classes(HEADER_TITLE_CLASSES)

            if not any(i.fecha_egreso is None for i in ingresos):

                ui.button(
                    'Nuevo ingreso',
                    icon='add',
                    on_click=lambda: self.nuevo_ingreso()
                ).props('color=primary unelevated').classes(PRIMARY_BUTTON_CLASSES)

        # GRID RESPONSIVE QUASAR
        with ui.row().classes('w-full q-col-gutter-lg wrap'):

            for ingreso in ingresos:

                ingresado = ingreso.fecha_egreso is None

                card_color = (
                    'bg-yellow-1 border-yellow-4'
                    if ingresado
                    else 'bg-grey-1 border-grey-4'
                )

                # COLUMNA RESPONSIVE
                with ui.column().classes('col-12 col-md-6 col-xl-4'):

                    with ui.card().classes(f'''
                        w-full
                        q-pa-md
                        rounded-xl
                        shadow-2
                        border-left-4
                        {card_color}
                    '''):

                        # HEADER CARD
                        with ui.row().classes('w-full items-start justify-between wrap q-col-gutter-sm'):

                            with ui.column().classes('q-gutter-y-xs'):

                                ui.label(
                                    ingreso.fecha_ingreso.strftime("%Y-%m-%d")
                                ).classes('text-h6 text-weight-bold text-primary')

                                ui.label(
                                    f'Motivo: {ingreso.motivo or "-"}'
                                ).classes('text-body2 text-grey-8')

                            # BADGE ESTADO
                            estado = 'Ingresado' if ingresado else 'Egresado'

                            estado_color = 'warning' if ingresado else 'positive'

                            ui.badge(
                                estado,
                                color=estado_color
                            ).props('rounded')

                        ui.separator().classes('q-my-md')

                        # DATOS
                        with ui.column().classes('q-gutter-y-sm'):

                            if ingreso.fecha_egreso:

                                with ui.row().classes('items-center q-gutter-sm'):
                                    ui.icon('event_available').classes('text-green')
                                    ui.label(
                                        f'Egreso: {ingreso.fecha_egreso.strftime("%Y-%m-%d")}'
                                    ).classes('text-body2')

                                with ui.column().classes('q-gutter-y-xs'):

                                    ui.label(
                                        'Observaciones de egreso'
                                    ).classes('text-caption text-grey-6')

                                    ui.label(
                                        ingreso.observaciones_egreso or '-'
                                    ).classes('text-body2')

                            else:

                                with ui.row().classes('items-center q-gutter-sm'):
                                    ui.icon('local_hospital').classes('text-orange')
                                    ui.label(
                                        'Paciente actualmente ingresado'
                                    ).classes('text-body2 text-orange-8')

                        ui.separator().classes('q-my-md')

                        # BOTONES
                        with ui.row().classes('w-full justify-end wrap q-gutter-sm'):

                            if ingresado:

                                ui.button(
                                    'Dar egreso',
                                    icon='logout',
                                    on_click=lambda i=ingreso: self.dar_egreso(i)
                                ).props(
                                    'color=primary unelevated'
                                ).classes(PRIMARY_BUTTON_CLASSES)

                            ui.button(
                                'Editar',
                                icon='edit',
                                on_click=lambda i=ingreso: self.editar_ingreso(i)
                            ).props(
                                'color=primary flat'
                            ).classes(PRIMARY_BUTTON_CLASSES)

                            ui.button(
                                'Eliminar',
                                icon='delete',
                                on_click=lambda i=ingreso: self.eliminar_ingreso(i)
                            ).props(
                                'color=error flat'
                            ).classes(DANGER_BUTTON_CLASSES)

    def nuevo_ingreso(self):
        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6'):
            ui.label('Nuevo ingreso').classes('text-lg font-bold mb-2')
            with ui.input('Fecha de ingreso').classes() as fecha:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha).props(
                        f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'
                    ).classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            motivo = ui.input('Motivo', value='').classes(INPUT_CLASSES)

            def guardar():
                try:
                    if not fecha.value:
                        ui.notify('La fecha es obligatoria', type='negative')
                        return
                    ingreso = Ingreso(
                        paciente_id=self.paciente.id,
                        fecha_ingreso=datetime.strptime(fecha.value, '%Y-%m-%d').date(),
                        motivo=motivo.value,
                    )
                    self.session.add(ingreso)
                    self.session.commit()
                    ui.notify('Ingreso registrado', type='positive')
                    dialog.close()
                    self.mostrar_ingresos.refresh()
                except Exception as e:
                    log_error_and_notify(e, f'Error al guardar el ingreso: {str(e)}')
                    ui.notify(f'Error: {e}', type='negative')

            ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            ui.button('Cancelar', on_click=dialog.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="warning"')
            dialog.open()

    def dar_egreso(self, ingreso):
        with ui.dialog() as dialog, ui.card().classes('w-[400px] p-4'):
            ui.label('Dar egreso').classes(HEADER_TITLE_CLASSES)
            with ui.input('Fecha de egreso').classes() as fecha:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha).props(
                        f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'
                    ).classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            observaciones = ui.input('Observaciones', value='').classes(INPUT_CLASSES)

            def guardar():
                try:
                    if not fecha.value:
                        ui.notify('La fecha es obligatoria', type='negative')
                        return
                    ingreso.fecha_egreso = datetime.strptime(fecha.value, '%Y-%m-%d').date()
                    ingreso.observaciones_egreso = observaciones.value
                    self.session.commit()
                    ui.notify('Egreso registrado', type='positive')
                    dialog.close()
                    self.mostrar_ingresos.refresh()
                except Exception as e:
                    log_error_and_notify(e, f'Error al guardar el egreso: {str(e)}')
                    ui.notify(f'Error: {e}', type='negative')

            ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            ui.button('Cancelar', on_click=dialog.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="warning"')
            dialog.open()

    def editar_ingreso(self, ingreso):
        with ui.dialog() as dialog, ui.card().classes('w-[400px] p-4'):
            ui.label('Editar ingreso').classes('text-lg font-bold mb-2')
            fecha_valor = ingreso.fecha_ingreso.strftime('%Y-%m-%d') if ingreso.fecha_ingreso else ''
            with ui.input('Fecha de ingreso', value=fecha_valor).classes('w-full mb-4') as fecha:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha).props(
                        f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'
                    ).classes('shadow-lg'):
                        with ui.row().classes('justify-end p-2'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')
            motivo = ui.input('Motivo', value=ingreso.motivo or '').classes(INPUT_CLASSES)

            def guardar():
                try:
                    ingreso.fecha_ingreso = datetime.strptime(fecha.value, '%Y-%m-%d').date()
                    ingreso.motivo = motivo.value
                    self.session.commit()
                    ui.notify('Ingreso actualizado', type='positive')
                    dialog.close()
                    self.mostrar_ingresos.refresh()
                except Exception as e:
                    log_error_and_notify(e, f'Error al actualizar el ingreso: {str(e)}')
                    ui.notify(f'Error: {e}', type='negative')

            ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            ui.button('Cancelar', on_click=dialog.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="warning"')
            dialog.open()

    def eliminar_ingreso(self, ingreso):
        with ui.dialog() as dialog, ui.card().classes('w-[400px] p-4'):
            ui.label('¿Eliminar ingreso?').classes('text-lg font-bold mb-2')
            ui.label('Esta acción no se puede deshacer.')

            def confirmar():
                try:
                    self.paciente = ingreso.paciente
                    self.session.delete(ingreso)
                    self.session.commit()
                    ui.notify('Ingreso eliminado', type='positive')
                    dialog.close()
                    self.mostrar_ingresos.refresh()
                except Exception as e:
                    log_error_and_notify(e, f'Error al eliminar el ingreso: {str(e)}')
                    ui.notify(f'Error: {e}', type='negative')

            ui.button('Eliminar', on_click=confirmar).props('color="error"').classes(DANGER_BUTTON_CLASSES)
            ui.button('Cancelar', on_click=dialog.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="warning"')
            dialog.open()
