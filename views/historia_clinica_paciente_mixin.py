from nicegui import ui
from seguridad_roles import tiene_permiso
from Errores import log_error_and_notify
from .historia_clinica_constants import DANGER_BUTTON_CLASSES


class HistoriaClinicaPacienteMixin:
    @ui.refreshable
    def mostrar_lista_ingresos(self):
        with ui.column().classes('w-full gap-2 mb-4'):
            if not self.ingresos_temporales:
                ui.label('No hay ingresos registrados.').classes('text-xs italic text-slate-400')
            else:
                for index, ing in enumerate(self.ingresos_temporales):
                    with ui.row().classes('w-full items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-100'):
                        with ui.column().classes('gap-0'):
                            ui.label(f"Motivo: {ing['motivo']}").classes('text-sm font-bold text-blue-800')
                            ui.label(f"Fecha: {ing['fecha']}").classes('text-[10px] text-slate-500')
                            if ing['especificacion']:
                                ui.label(f"Detalle: {ing['especificacion']}").classes('text-[11px] text-slate-600')

                        ui.button(icon='delete', on_click=lambda i=index: self.eliminar_ingreso_diab(i)).props(
                            'flat round dense color="red"'
                        ).classes('hover:bg-red-100')

    def eliminar_ingreso_diab(self, index):
        self.ingresos_temporales.pop(index)
        self.mostrar_lista_ingresos.refresh()

    def procesar_ingreso(self):
        if not self.motivo_sel.value or not self.fecha_ing.value:
            ui.notify('Complete motivo y fecha', type='warning')
            return

        datos = {
            'motivo': self.motivo_sel.value,
            'fecha': self.fecha_ing.value,
            'especificacion': self.otros_det.value if self.motivo_sel.value == 'Otros' else ''
        }

        if self.edit_index is None:
            self.ingresos_temporales.append(datos)
            ui.notify('Ingreso añadido')
        else:
            self.ingresos_temporales[self.edit_index] = datos
            ui.notify('Ingreso actualizado')

        self.limpiar_formulario_ingreso()
        self.mostrar_lista_ingresos.refresh()

    def cargar_ingreso_para_editar(self, index):
        self.edit_index = index
        ingreso = self.ingresos_temporales[index]

        self.motivo_sel.set_value(ingreso['motivo'])
        self.fecha_ing.set_value(ingreso['fecha'])
        self.otros_det.set_value(ingreso.get('especificacion', ''))

        if self.btn_accion:
            self.btn_accion.set_text('GUARDAR CAMBIOS')
            self.btn_accion.props('color="green" icon="check"')

        if self.btn_cancelar_edit:
            self.btn_cancelar_edit.set_visibility(True)

    def limpiar_formulario_ingreso(self):
        self.edit_index = None
        for attr in ['motivo_sel', 'fecha_ing', 'otros_det']:
            field = getattr(self, attr, None)
            if field:
                field.set_value(None)

        if hasattr(self, 'btn_accion') and self.btn_accion:
            self.btn_accion.set_text('AÑADIR INGRESO')
            self.btn_accion.props('color="primary" icon="add"')

        if hasattr(self, 'btn_cancelar_edit') and self.btn_cancelar_edit:
            self.btn_cancelar_edit.set_visibility(False)
        self.mostrar_lista_ingresos.refresh()
    def guardar_cambios_paciente(self):
            print(self.esquema_inicial_temporal)  # Debug: Ver el esquema antes de enviar
            if not tiene_permiso('pacientes_edit'):
                ui.notify('No tienes permiso para modificar datos', type='negative')
                return

            try:
                campos_requeridos = {
                    "Número HC": self.no_hc_input.value,
                    "Carnet de Identidad": self.ci_input.value,
                    "Nombres": self.nombres_input.value,
                    "Apellidos": self.apellidos_input.value,
                    "Fecha de Historia Clínica": self.fecha_hc_input.value,
                    "Sexo": self.sexo_input.value,
                    "Color de Piel": self.color_piel.value,
                    "Provincia": self.provincia_input.value,
                    "Municipio": self.municipio_input.value,
                    "Institución": self.institucion_input.value,
                }
                campos_faltantes = [nombre for nombre, valor in campos_requeridos.items() if not valor]
                if campos_faltantes:
                    ui.notify(f'Los siguientes campos son requeridos: {", ".join(campos_faltantes)}', type='negative')
                    return

                payload = {
                    "no_hc": self.no_hc_input.value,
                    "ci": self.ci_input.value,
                    "nombres": self.nombres_input.value,
                    "apellidos": self.apellidos_input.value,
                    "telefono": self.telefono_input.value,
                    "tel_emergencia": self.tel_emergencia.value,
                    "area_salud": self.area_salud_input.value,
                    "fecha_hc": self.fecha_hc_input.value,
                    "estado_actual": self.estado_actual_input.value,
                    "calle": self.calle_input.value,
                    "numero": self.numero_input.value,
                    "entre_calles": self.entre_calles_input.value,
                    "municipio": self.municipio_input.value,
                    "provincia": self.provincia_input.value,
                    "sexo": self.sexo_input.value,
                    "color_piel": self.color_piel.value,
                    "escolaridad": self.escolaridad_input.value,
                    "ocupacion": self.ocupacion_input.value,
                    "estado_civil": self.estado_civil_input.value,
                    "tiempo_evolucion_anios": self.tiempo_evolucion_anios.value,
                    "tiempo_evolucion_meses": self.tiempo_evolucion_meses.value,
                    "tiempo_evolucion_dias": self.tiempo_evolucion_dias.value,
                    "forma_presentacion_diagnostico": self.forma_presentacion_diagnostico_input.value,
                    "otros_forma_presentacion_diagnostico": self.otros_forma_presentacion_diagnostico_input.value,
                    "glucemia_debut": self.glucemia_debut_input.value,
                    "exceso_peso_diagnostico": self.exceso_peso_diagnostico.value,
                    "tiempo_exceso_peso_anios": self.tiempo_exceso_peso_anios.value,
                    "tiempo_exceso_peso_meses": self.tiempo_exceso_peso_meses.value,
                    "remision": self.remision_input.value,

                    # ═════════════════════════════════════════════════════════════════════════
                    # ENVIAR ESQUEMA DINÁMICO DE MEDICAMENTOS (JSON)
                    # ═════════════════════════════════════════════════════════════════════════
                    "tratamiento_inicial_json": self.esquema_inicial_temporal,
                    # ═════════════════════════════════════════════════════════════════════════

                    "prediabetes": self.prediabetes_input.value,
                    "tiempo_prediabetes_anios": self.tiempo_prediabetes_anios.value,
                    "tiempo_prediabetes_meses": self.tiempo_prediabetes_meses.value,
                    "causa_fallecimiento": self.causa_fallecimiento_input.value,
                    "institucion": self.institucion_input.value,
                }

                resultado = self.controller.actualizar_paciente_desde_payload(
                    paciente=self.paciente,
                    payload=payload,
                    ingresos_temporales=self.ingresos_temporales,
                    mapa_instituciones=self.mapa_instituciones,
                    original_hc=self.original_hc,
                )
                hc_cambio = resultado["hc_cambio"]
                if hc_cambio:
                    ui.notify('Número de HC modificado - Volviendo a la página anterior', type='positive')
                    ui.navigate.to('/principal')
                else:
                    ui.notify('Paciente actualizado correctamente', type='positive')
                self.dialog_editar.close()

            except ValueError as e:
                ui.notify(str(e), type='negative')
            except Exception as e:
                self.session.rollback()
                log_error_and_notify(e, f'Error Actualizando paciente en HC {self.no_hc_input.value}')
                ui.notify(f'Error al actualizar el paciente: {str(e)}', type='negative')

    def actualizar_municipios_edicion(self):
        nombre_prov = self.provincia_input.value
        self.municipio_input.options = self.controller.obtener_municipios_por_provincia(nombre_prov)
        self.municipio_input.value = None
        self.area_salud_input.options = []
        self.area_salud_input.value = None
        self.municipio_input.update()
        self.area_salud_input.update()

    def actualizar_areas_edicion(self):
        nombre_muni = self.municipio_input.value
        nombre_prov = self.provincia_input.value
        self.area_salud_input.options = self.controller.obtener_areas_por_municipio(nombre_muni, nombre_prov)
        self.area_salud_input.value = None
        self.area_salud_input.update()

    async def confirmar_eliminacion(self):
        if not self.paciente:
            return
        no_hc = self.paciente.no_hc
        nombre_completo = f"{self.paciente.nombres} {self.paciente.apellidos}"
        with ui.dialog() as confirm_dialog, ui.card():
            ui.label(f'¿Está seguro de que desea eliminar al paciente {nombre_completo} (HC: {no_hc})?').classes('text-lg mb-4')
            ui.label('Esta acción no se puede deshacer.').classes('text-red-600 mb-4')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=confirm_dialog.close).props('flat color="warning"').classes(DANGER_BUTTON_CLASSES)
                ui.button('Eliminar Definitivamente', on_click=lambda: self.eliminar_paciente(no_hc, confirm_dialog)).props(
                    'color=error'
                ).classes(DANGER_BUTTON_CLASSES)
        await confirm_dialog

    def confirmar_desactivacion(self, paciente):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Confirmar desactivación?').classes('text-lg font-bold')
            ui.label('El paciente no aparecerá en las listas activas, pero sus datos se conservarán.')
            with ui.row():
                ui.button('SÍ, ARCHIVAR', on_click=lambda: [self.toggle_estado_paciente(paciente), dialog.close()]).props('color=red')
                ui.button('CANCELAR', on_click=dialog.close).props('flat')
        dialog.open()

    def eliminar_paciente(self, no_hc, dialog):
        dialog.close()
        try:
            eliminado = self.controller.eliminar_paciente(no_hc)
            if eliminado:
                ui.notify('Paciente eliminado correctamente')
                return ui.navigate.to('/principal')
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar el paciente {no_hc}')
            ui.notify(f'Error al eliminar el paciente: {str(e)}', type='negative', color='red')
