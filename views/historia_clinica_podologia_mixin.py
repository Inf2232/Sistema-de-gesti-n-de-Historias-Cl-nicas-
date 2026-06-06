from datetime import datetime
from nicegui import ui
from models import ExamenMiembrosInferiores ,EnfermedadesPodalicasDerecho,EnfermedadesPodalicasIzquierdo,LesionesDermatologicasIzquierdo,LesionesDermatologicasDerecho,LesionesUñasDerecho,LesionesUñasIzquierdo
from Errores import log_error_and_notify
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)
from seguridad_roles import tiene_permiso
from controllers.historia_clinica_podologia_controller import HistoriaClinicaPodologiaController

class HistoriaClinicaPodologiaMixin:
    @property
    def controlador_podologia(self):
        """Inicializa de forma segura el controlador bajo demanda."""
        if not hasattr(self, '_controlador_podologia'):
            self._controlador_podologia = HistoriaClinicaPodologiaController(self.session)
        return self._controlador_podologia
    #examenes miembros inferiores
    @ui.refreshable
    def mostrar_examenes_podologicos(self):

        with ui.column().classes('w-full p-2 md:p-4 gap-6'):

            # =========================================================
            # HEADER
            # =========================================================
            with ui.card().classes(HC_CARD_PROFESSIONAL):

                with ui.row().classes('w-full justify-between items-center flex-wrap gap-4'):

                    with ui.row().classes('items-center gap-3'):
                        with ui.column().classes('gap-1'):
                            ui.label('Exámenes Miembros Inferiores').classes(HEADER_TITLE_CLASSES)
                            ui.label(
                                'Evaluación integral de miembros inferiores'
                            ).classes('text-sm text-teal-600')

                    if tiene_permiso("miembros_inf_manage"):
                        ui.button(
                            'Agregar Nuevo',
                            icon='add',
                            on_click=self.agregar_examen_miembro_inferior
                        ).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

                

                # =========================================================
                # ÚLTIMO EXAMEN
                # =========================================================
                ultimo_examen = self.controlador_podologia.obtener_ultimo_examen(self.paciente)
                if ultimo_examen:
                    with ui.card().classes(HC_SECTION_CARD + ' mt-4'):

                        with ui.column().classes('w-full gap-4'):

                            # FECHA
                            with ui.row().classes('items-center gap-2 flex-wrap'):
                                ui.icon('event', size='lg').classes('text-teal-500')

                                ui.label(
                                    f'Último examen: '
                                    f'{ultimo_examen.fecha_registro.strftime("%d/%m/%Y")}'
                                ).classes(
                                    'text-lg font-semibold text-gray-700'
                                )

                            # =================================================
                            # PIES
                            # =================================================
                            with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):

                                # =============================================
                                # PIE IZQUIERDO
                                # =============================================
                                with ui.element('div').classes(
                                    'col-12 col-md-5'
                                ):

                                    with ui.card().classes(HC_SECTION_CARD):

                                        with ui.column().classes('gap-4'):

                                            ui.label(
                                                'Pie Izquierdo'
                                            ).classes(
                                                'text-lg font-bold text-blue-800'
                                            )

                                            # =====================================
                                            # GRID INTERNO
                                            # =====================================
                                            with ui.element('div').classes(
                                                'row q-col-gutter-md'
                                            ):

                                                # =================================
                                                # COLUMNA 1
                                                # =================================
                                                with ui.element('div').classes(
                                                    'col-12 col-md-6'
                                                ):

                                                    with ui.column().classes('gap-3'):

                                                        # Enfermedades
                                                        with ui.expansion(
                                                            'Enfermedades Podálicas',
                                                            icon='medical_services'
                                                        ).classes('w-full'):

                                                            for enfermedad_podalica in ultimo_examen.defromidades_podalicas_izquierdo:
                                                                ui.label(
                                                                    f'• {enfermedad_podalica.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                        # Lesiones Dermatológicas
                                                        with ui.expansion(
                                                            'Lesiones Dermatológicas',
                                                            icon='healing'
                                                        ).classes('w-full'):

                                                            for lesion_dermatologica in ultimo_examen.lesiones_dermatologicas_izquierdo:
                                                                ui.label(
                                                                    f'• {lesion_dermatologica.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                        # Lesiones uñas
                                                        with ui.expansion(
                                                            'Lesiones Uñas',
                                                            icon='back_hand'
                                                        ).classes('w-full'):

                                                            for lesion_uña in ultimo_examen.lesiones_uñas_izquierdo:
                                                                ui.label(
                                                                    f'• {lesion_uña.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                # =================================
                                                # COLUMNA 2
                                                # =================================
                                                with ui.element('div').classes(
                                                    'col-12 col-md-6'
                                                ):

                                                    with ui.column().classes('gap-3'):

                                                        # Arterial
                                                        with ui.expansion(
                                                            'Examen Arterial',
                                                            icon='favorite',
                                                            value=False
                                                        ).classes('w-full'):

                                                            with ui.column().classes(
                                                                'gap-2 p-2'
                                                            ):

                                                                self._create_medical_info_row(
                                                                    "Pulso Femoral",
                                                                    ultimo_examen.pulso_femoral_izquierdo,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Popliteo",
                                                                    ultimo_examen.pulso_popliteo_izquierdo,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Tibial Posterior",
                                                                    ultimo_examen.pulso_tibial_posterior_izquierdo,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Pedeo",
                                                                    ultimo_examen.pulso_pedeo_izquierdo,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "ITB",
                                                                    f"{ultimo_examen.ITB_izquierdo} ({ultimo_examen.itb_clasificacion_izquierdo})",
                                                                    'trending_up',
                                                                    'blue'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "EAP",
                                                                    ultimo_examen.EAP_izquierdo,
                                                                    'speed',
                                                                    'orange'
                                                                )
                                                                self._create_medical_info_row(
                                                                    "Venoso periférico",
                                                                    ultimo_examen.venoso_periferico_izquierdo,
                                                                    'speed',
                                                                    'orange'
                                                                )
                                                                self._create_medical_info_row(
                                                                    "Linfático",
                                                                    ultimo_examen.linfatico_izquierdo,
                                                                    'speed',
                                                                    'orange'
                                                                )

                                                        # Neurológico
                                                        with ui.expansion(
                                                            'Examen Neurológico',
                                                            icon='psychology',
                                                            value=False
                                                        ).classes('w-full'):

                                                            with ui.column().classes(
                                                                'gap-2 p-2'
                                                            ):

                                                                self._create_medical_info_row(
                                                                    "Táctil",
                                                                    ultimo_examen.tactil_izquierdo,
                                                                    'touch_app',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Térmica",
                                                                    ultimo_examen.termica_izquierdo,
                                                                    'thermostat',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Dolorosa",
                                                                    ultimo_examen.dolorosa_izquierdo,
                                                                    'warning',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Palestesia",
                                                                    ultimo_examen.palestesia_izquierdo,
                                                                    'vibration',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Patelar",
                                                                    ultimo_examen.patelar_izquierdo,
                                                                    'flash_on',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Aquileano",
                                                                    ultimo_examen.aquileano_izquierdo,
                                                                    'flash_on',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "LOPS",
                                                                    ultimo_examen.LOPS_izquierdo,
                                                                    'psychology',
                                                                    'purple'
                                                                )

                                # =============================================
                                # PIE DERECHO
                                # =============================================
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):

                                    with ui.card().classes(HC_SECTION_CARD):

                                        with ui.column().classes('gap-4'):

                                            ui.label(
                                                'Pie Derecho'
                                            ).classes(
                                                'text-lg font-bold text-green-800'
                                            )

                                            with ui.element('div').classes(
                                                'row q-col-gutter-md'
                                            ):

                                                # =================================
                                                # COLUMNA 1
                                                # =================================
                                                with ui.element('div').classes(
                                                    'col-12 col-md-6'
                                                ):

                                                    with ui.column().classes('gap-3'):

                                                        with ui.expansion(
                                                            'Enfermedades Podálicas',
                                                            icon='medical_services'
                                                        ).classes('w-full'):

                                                            for enfermedad_podalica in ultimo_examen.defromidades_podalicas_derecho:
                                                                ui.label(
                                                                    f'• {enfermedad_podalica.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                        with ui.expansion(
                                                            'Lesiones Dermatológicas',
                                                            icon='healing'
                                                        ).classes('w-full'):

                                                            for lesion_dermatologica in ultimo_examen.lesiones_dermatologicas_derecho:
                                                                ui.label(
                                                                    f'• {lesion_dermatologica.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                        with ui.expansion(
                                                            'Lesiones Uñas',
                                                            icon='back_hand'
                                                        ).classes('w-full'):

                                                            for lesion_uña in ultimo_examen.lesiones_uñas_derecho:
                                                                ui.label(
                                                                    f'• {lesion_uña.padecimiento}'
                                                                ).classes(
                                                                    'text-sm text-gray-600'
                                                                )

                                                # =================================
                                                # COLUMNA 2
                                                # =================================
                                                with ui.element('div').classes(
                                                    'col-12 col-md-6'
                                                ):

                                                    with ui.column().classes('gap-3'):

                                                        with ui.expansion(
                                                            'Examen Arterial',
                                                            icon='favorite',
                                                            value=False
                                                        ).classes('w-full'):

                                                            with ui.column().classes(
                                                                'gap-2 p-2'
                                                            ):

                                                                self._create_medical_info_row(
                                                                    "Pulso Femoral",
                                                                    ultimo_examen.pulso_femoral_derecho,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Popliteo",
                                                                    ultimo_examen.pulso_popliteo_derecho,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Tibial Posterior",
                                                                    ultimo_examen.pulso_tibial_posterior_derecho,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Pulso Pedeo",
                                                                    ultimo_examen.pulso_pedeo_derecho,
                                                                    'favorite',
                                                                    'red'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "ITB",
                                                                    f"{ultimo_examen.ITB_derecho} ({ultimo_examen.itb_clasificacion_derecho})",
                                                                    'trending_up',
                                                                    'blue'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "EAP",
                                                                    ultimo_examen.EAP_derecho,
                                                                    'speed',
                                                                    'orange'
                                                                )
                                                                self._create_medical_info_row(
                                                                    "Venoso periférico",
                                                                    ultimo_examen.venoso_periferico_derecho,
                                                                    'speed',
                                                                    'orange'
                                                                )
                                                                self._create_medical_info_row(
                                                                    "Linfático",
                                                                    ultimo_examen.linfatico_derecho,
                                                                    'speed',
                                                                    'orange'
                                                                )


                                                        with ui.expansion(
                                                            'Examen Neurológico',
                                                            icon='psychology',
                                                            value=False
                                                        ).classes('w-full'):

                                                            with ui.column().classes(
                                                                'gap-2 p-2'
                                                            ):

                                                                self._create_medical_info_row(
                                                                    "Táctil",
                                                                    ultimo_examen.tactil_derecho,
                                                                    'touch_app',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Térmica",
                                                                    ultimo_examen.termica_derecho,
                                                                    'thermostat',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Dolorosa",
                                                                    ultimo_examen.dolorosa_derecho,
                                                                    'warning',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Palestesia",
                                                                    ultimo_examen.palestesia_derecho,
                                                                    'vibration',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Patelar",
                                                                    ultimo_examen.patelar_derecho,
                                                                    'flash_on',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "Aquileano",
                                                                    ultimo_examen.aquileano_derecho,
                                                                    'flash_on',
                                                                    'purple'
                                                                )

                                                                self._create_medical_info_row(
                                                                    "LOPS",
                                                                    ultimo_examen.LOPS_derecho,
                                                                    'psychology',
                                                                    'purple'
                                                                )

                            # =================================================
                            # IMPRESIÓN DIAGNÓSTICA
                            # =================================================
                            with ui.card().classes(HC_SECTION_CARD):

                                with ui.row().classes(
                                    'items-start gap-3 flex-wrap'
                                ):

                                    ui.icon(
                                        'medical_services',
                                        size='lg'
                                    ).classes('text-amber-600')

                                    with ui.column().classes('gap-1'):

                                        ui.label(
                                            "Impresión Diagnóstica"
                                        ).classes(
                                            'font-bold text-amber-800'
                                        )

                                        ui.label(
                                            f'{ultimo_examen.impresion_diagnostica}'
                                        ).classes(
                                            'text-gray-700'
                                        )

                # =========================================================
                # SIN EXÁMENES
                # =========================================================
                else:

                    with ui.card().classes(HC_SECTION_CARD):

                        with ui.column().classes(
                            'items-center text-center gap-4 py-10'
                        ):

                            ui.icon(
                                'info',
                                size='4xl'
                            ).classes('text-gray-400')

                            ui.label(
                                'No hay exámenes de miembros inferiores registrados'
                            ).classes(
                                'text-gray-500 text-lg'
                            )

                            ui.label(
                                'Agregue el primer examen para comenzar el seguimiento'
                            ).classes(
                                'text-gray-400 text-sm'
                            )

            # =============================================================
            # HISTORIAL
            # =============================================================
            with ui.expansion(
                'Ver historial completo',
                icon='history'
            ).classes(
                'w-full mt-4 bg-white rounded-lg'
            ):

                with ui.card().classes(HC_CARD_PROFESSIONAL):
                    examenes = self.controlador_podologia.obtener_examenes_paciente(self.paciente)
                    if examenes:

                        examenes_ordenados = sorted(
                            examenes,
                            key=lambda x: x.fecha_registro,
                            reverse=True
                        )

                        with ui.column().classes('w-full gap-4'):

                            for examen in examenes_ordenados:

                                with ui.expansion(
                                    f'Examen {examen.fecha_registro.strftime("%d/%m/%Y")}',
                                    icon='calendar_month'
                                ).classes('w-full'):

                                    with ui.card().classes(HC_SECTION_CARD):

                                        with ui.row().classes(
                                            'justify-end items-center flex-wrap gap-2'
                                        ):

                                            if tiene_permiso("miembros_inf_manage"):

                                                ui.button(
                                                    icon='edit',
                                                    on_click=lambda e, ex=examen:
                                                    self.editar_examen_miembro_inferior(ex)
                                                ).props(
                                                    'flat round dense color="primary"'
                                                ).classes(PRIMARY_BUTTON_CLASSES)

                                                ui.button(
                                                    icon='delete',
                                                    on_click=lambda e, ex=examen:
                                                    self.eliminar_examen_miembro_inferior(ex)
                                                ).props(
                                                    'flat round dense color="error"'
                                                ).classes(DANGER_BUTTON_CLASSES)

                                        with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):

                                            # =============================================
                                            # PIE IZQUIERDO
                                            # =============================================
                                            with ui.element('div').classes(
                                                'col-12 col-md-6'
                                            ):

                                                with ui.card().classes(HC_SECTION_CARD):

                                                    with ui.column().classes('gap-4'):

                                                        ui.label(
                                                            'Pie Izquierdo'
                                                        ).classes(
                                                            'text-lg font-bold text-blue-800'
                                                        )

                                                        # =====================================
                                                        # GRID INTERNO
                                                        # =====================================
                                                        with ui.element('div').classes(
                                                            'row q-col-gutter-md'
                                                        ):

                                                            # =================================
                                                            # COLUMNA 1
                                                            # =================================
                                                            with ui.element('div').classes(
                                                                'col-12 col-md-6'
                                                            ):

                                                                with ui.column().classes('gap-3'):

                                                                    # Enfermedades
                                                                    with ui.expansion(
                                                                        'Enfermedades Podálicas',
                                                                        icon='medical_services'
                                                                    ).classes('w-full'):

                                                                        for enfermedad_podalica in examen.defromidades_podalicas_izquierdo:
                                                                            ui.label(
                                                                                f'• {enfermedad_podalica.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                                    # Lesiones Dermatológicas
                                                                    with ui.expansion(
                                                                        'Lesiones Dermatológicas',
                                                                        icon='healing'
                                                                    ).classes('w-full'):

                                                                        for lesion_dermatologica in examen.lesiones_dermatologicas_izquierdo:
                                                                            ui.label(
                                                                                f'• {lesion_dermatologica.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                                    # Lesiones uñas
                                                                    with ui.expansion(
                                                                        'Lesiones Uñas',
                                                                        icon='back_hand'
                                                                    ).classes('w-full'):

                                                                        for lesion_uña in examen.lesiones_uñas_izquierdo:
                                                                            ui.label(
                                                                                f'• {lesion_uña.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                            # =================================
                                                            # COLUMNA 2
                                                            # =================================
                                                            with ui.element('div').classes(
                                                                'col-12 col-md-6'
                                                            ):

                                                                with ui.column().classes('gap-3'):

                                                                    # Arterial
                                                                    with ui.expansion(
                                                                        'Examen Arterial',
                                                                        icon='favorite',
                                                                        value=False
                                                                    ).classes('w-full'):

                                                                        with ui.column().classes(
                                                                            'gap-2 p-2'
                                                                        ):

                                                                            self._create_medical_info_row(
                                                                                "Pulso Femoral",
                                                                                examen.pulso_femoral_izquierdo,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Popliteo",
                                                                                ultimo_examen.pulso_popliteo_izquierdo,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Tibial Posterior",
                                                                                examen.pulso_tibial_posterior_izquierdo,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Pedeo",
                                                                                examen.pulso_pedeo_izquierdo,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "ITB",
                                                                                f"{examen.ITB_izquierdo} ({examen.itb_clasificacion_izquierdo})",
                                                                                'trending_up',
                                                                                'blue'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "EAP",
                                                                                examen.EAP_izquierdo,
                                                                                'speed',
                                                                                'orange'
                                                                            )
                                                                            self._create_medical_info_row(
                                                                                "Venoso periférico",
                                                                                examen.venoso_periferico_izquierdo,
                                                                                'speed',
                                                                                'orange'
                                                                            )
                                                                            self._create_medical_info_row(
                                                                                "Linfático",
                                                                                examen.linfatico_izquierdo,
                                                                                'speed',
                                                                                'orange'
                                                                            )

                                                                    # Neurológico
                                                                    with ui.expansion(
                                                                        'Examen Neurológico',
                                                                        icon='psychology',
                                                                        value=False
                                                                    ).classes('w-full'):

                                                                        with ui.column().classes(
                                                                            'gap-2 p-2'
                                                                        ):

                                                                            self._create_medical_info_row(
                                                                                "Táctil",
                                                                                examen.tactil_izquierdo,
                                                                                'touch_app',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Térmica",
                                                                                examen.termica_izquierdo,
                                                                                'thermostat',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Dolorosa",
                                                                                examen.dolorosa_izquierdo,
                                                                                'warning',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Palestesia",
                                                                                examen.palestesia_izquierdo,
                                                                                'vibration',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Patelar",
                                                                                examen.patelar_izquierdo,
                                                                                'flash_on',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Aquileano",
                                                                                examen.aquileano_izquierdo,
                                                                                'flash_on',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "LOPS",
                                                                                examen.LOPS_izquierdo,
                                                                                'psychology',
                                                                                'purple'
                                                                            )

                                            # =============================================
                                            # PIE DERECHO
                                            # =============================================
                                            with ui.element('div').classes(
                                                'col-12 col-md-6'
                                            ):

                                                with ui.card().classes(HC_SECTION_CARD):

                                                    with ui.column().classes('gap-4'):

                                                        ui.label(
                                                            'Pie Derecho'
                                                        ).classes(
                                                            'text-lg font-bold text-green-800'
                                                        )

                                                        with ui.element('div').classes(
                                                            'row q-col-gutter-md'
                                                        ):

                                                            # =================================
                                                            # COLUMNA 1
                                                            # =================================
                                                            with ui.element('div').classes(
                                                                'col-12 col-md-6'
                                                            ):

                                                                with ui.column().classes('gap-3'):

                                                                    with ui.expansion(
                                                                        'Enfermedades Podálicas',
                                                                        icon='medical_services'
                                                                    ).classes('w-full'):

                                                                        for enfermedad_podalica in examen.defromidades_podalicas_derecho:
                                                                            ui.label(
                                                                                f'• {enfermedad_podalica.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                                    with ui.expansion(
                                                                        'Lesiones Dermatológicas',
                                                                        icon='healing'
                                                                    ).classes('w-full'):

                                                                        for lesion_dermatologica in examen.lesiones_dermatologicas_derecho:
                                                                            ui.label(
                                                                                f'• {lesion_dermatologica.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                                    with ui.expansion(
                                                                        'Lesiones Uñas',
                                                                        icon='back_hand'
                                                                    ).classes('w-full'):

                                                                        for lesion_uña in examen.lesiones_uñas_derecho:
                                                                            ui.label(
                                                                                f'• {lesion_uña.padecimiento}'
                                                                            ).classes(
                                                                                'text-sm text-gray-600'
                                                                            )

                                                            # =================================
                                                            # COLUMNA 2
                                                            # =================================
                                                            with ui.element('div').classes(
                                                                'col-12 col-md-6'
                                                            ):

                                                                with ui.column().classes('gap-3'):

                                                                    with ui.expansion(
                                                                        'Examen Arterial',
                                                                        icon='favorite',
                                                                        value=False
                                                                    ).classes('w-full'):

                                                                        with ui.column().classes(
                                                                            'gap-2 p-2'
                                                                        ):

                                                                            self._create_medical_info_row(
                                                                                "Pulso Femoral",
                                                                                examen.pulso_femoral_derecho,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Popliteo",
                                                                                examen.pulso_popliteo_derecho,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Tibial Posterior",
                                                                                examen.pulso_tibial_posterior_derecho,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Pulso Pedeo",
                                                                                examen.pulso_pedeo_derecho,
                                                                                'favorite',
                                                                                'red'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "ITB",
                                                                                f"{examen.ITB_derecho} ({examen.itb_clasificacion_derecho})",
                                                                                'trending_up',
                                                                                'blue'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "EAP",
                                                                                examen.EAP_derecho,
                                                                                'speed',
                                                                                'orange'
                                                                            )
                                                                            self._create_medical_info_row(
                                                                                "Venoso periférico",
                                                                                examen.venoso_periferico_derecho,
                                                                                'speed',
                                                                                'orange'
                                                                            )
                                                                            self._create_medical_info_row(
                                                                                "Linfático",
                                                                                examen.linfatico_derecho,
                                                                                'speed',
                                                                                'orange'
                                                                            )

                                                                    with ui.expansion(
                                                                        'Examen Neurológico',
                                                                        icon='psychology',
                                                                        value=False
                                                                    ).classes('w-full'):

                                                                        with ui.column().classes(
                                                                            'gap-2 p-2'
                                                                        ):

                                                                            self._create_medical_info_row(
                                                                                "Táctil",
                                                                                examen.tactil_derecho,
                                                                                'touch_app',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Térmica",
                                                                                examen.termica_derecho,
                                                                                'thermostat',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Dolorosa",
                                                                                examen.dolorosa_derecho,
                                                                                'warning',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Palestesia",
                                                                                examen.palestesia_derecho,
                                                                                'vibration',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Patelar",
                                                                                examen.patelar_derecho,
                                                                                'flash_on',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "Aquileano",
                                                                                examen.aquileano_derecho,
                                                                                'flash_on',
                                                                                'purple'
                                                                            )

                                                                            self._create_medical_info_row(
                                                                                "LOPS",
                                                                                examen.LOPS_derecho,
                                                                                'psychology',
                                                                                'purple'
                                                                            )

                                        # =================================================
                                        # IMPRESIÓN DIAGNÓSTICA
                                        # =================================================
                                        with ui.card().classes(HC_SECTION_CARD):

                                            with ui.row().classes(
                                                'items-start gap-3 flex-wrap'
                                            ):

                                                ui.icon(
                                                    'medical_services',
                                                    size='lg'
                                                ).classes('text-amber-600')

                                                with ui.column().classes('gap-1'):

                                                    ui.label(
                                                        "Impresión Diagnóstica"
                                                    ).classes(
                                                        'font-bold text-amber-800'
                                                    )

                                                    ui.label(
                                                        f'{examen.impresion_diagnostica}'
                                                    ).classes(
                                                        'text-gray-700'
                                                    )

                    else:
                        ui.label(
                            'No hay registros de exámenes físicos'
                        ).classes(
                            'text-gray-500 italic'
                        )
    def agregar_examen_miembro_inferior(self):
        # Diccionario interno para encapsular la referencia de los inputs y radios dinámicos
        campos_dinamicos = {}

        def crear_campo_dinamico(label, valor_inicial="N"):
            """
            Fábrica interna: Se encarga de leer el estado, renderizar el Radio (N, AN, NE)
            y enlazar un input de texto que reacciona de forma automática si se elige 'AN'.
            """
            # Mapeo de compatibilidad con datos viejos o formatos previos para evitar errores
            radio_defecto = 'N'
            texto_defecto = ''
            
            if valor_inicial:
                if valor_inicial.startswith('AN:'):
                    partes = valor_inicial.split(':', 1)
                    radio_defecto = 'AN'
                    texto_defecto = partes[1]
                elif valor_inicial == 'AN':
                    radio_defecto = 'AN'
                elif valor_inicial in ['Presente', 'Conservada', 'N']:
                    radio_defecto = 'N'
                elif valor_inicial in ['Ausente', 'No Conservada', 'NE']:
                    radio_defecto = 'NE'
                else:
                    # Si contiene texto libre sin prefijo, asumimos que era Anormal
                    radio_defecto = 'AN'
                    texto_defecto = valor_inicial

            contenedor = ui.column().classes('w-full gap-1 mb-2')
            with contenedor:
                ui.label(label).classes('text-xs font-semibold text-blue-700')
                # Radio con los 3 nuevos estados requeridos
                radio = ui.radio({'N': 'N', 'AN': 'AN', 'NE': 'NE'}, value=radio_defecto).props('inline dense')
                # Input de texto para la especificación
                input_texto = ui.input(label='Especifique anomalía...', value=texto_defecto).classes('w-full text-xs').props('dense')
                # Vinculación mágica: si radio != 'AN', el input permanece oculto de forma automática
                input_texto.bind_visibility_from(radio, 'value', lambda v: v == 'AN')
            
            return {'radio': radio, 'input': input_texto}

        with ui.dialog().classes('maximized') as dialog, ui.card().classes('w-full max-w-6xl shadow-lg rounded-lg').style("width:100%; max-width:none;"):
            ui.label('Agregar Examen de Miembro Inferior').classes(HEADER_TITLE_CLASSES)
            
            # Fecha input with modern styling
            with ui.row().classes('w-full mb-6'):
                with ui.input('Fecha').classes('w-64') as fecha_input:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.date().bind_value(fecha_input).props(
                                f'locale="es" '
                                f'default-year-month={self.current_month} '
                                f':options="date => date <= \'{self.today}\'"'
                            ).classes('shadow-lg rounded-lg'):
                            with ui.row().classes('justify-end p-2 bg-gray-100'):
                                ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                        with fecha_input.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer text-primary')

            with ui.element('div').classes('row q-col-gutter-lg w-full'):
                
                # ==================== COLUMNA 1: PIE IZQUIERDO (Dermatología/Pulsos) ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Izquierdo').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Enfermedades Podálicas').classes('text-lg font-semibold text-blue-700')
                    defromidades_podalicas_izquierdo = ui.select(
                        ['Pie Plano, cavo , supinado', 'Hallux Valgus', 'Dedos En Garra', 'Pie de Charcot', 
                        'Amp Menores', 'Dedos en martillo', 'Otras'], 
                        value=[], multiple=True
                    ).classes(INPUT_CLASSES+ ' w-64').props('use-chips')
                    
                    otra_enf_pod_izq = ui.input('Especifique otra enfermedad').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(defromidades_podalicas_izquierdo, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Dermatológicas').classes('text-lg font-semibold text-blue-700')
                    lesiones_dermatologicas_izquierdo = ui.select(
                        ['Epidermofitosis', 'Piel seca y Callosa' , 'Hiperpigmentación', 'Dermatitis', 
                        'Celulitis', 'Úlceras', 'Palidez', 'Cianosis','Rubicundez', 'Dedos con necrosis', 'Otras'], 
                        value=[], multiple=True
                    ).classes(INPUT_CLASSES+ ' w-64').props('use-chips')

                    otra_les_derm_izq = ui.input('Especifique otra lesión').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(lesiones_dermatologicas_izquierdo, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Uñas').classes('text-lg font-semibold text-blue-700')
                    lesiones_uñas_izquierdo = ui.select(['Onimicosis', 'Paroniquia'], value=[], multiple=True).classes(INPUT_CLASSES+ ' w-64').props('use-chips')
                    
                    ui.label('Pulso Femoral').classes('text-lg font-semibold text-blue-700')
            
                    campos_dinamicos['pulso_femoral_izquierdo'] = crear_campo_dinamico('Pulso Femoral', 'Presente')
                    ui.label('Pulso Popliteo').classes('text-lg font-semibold text-blue-700')
                   
                    campos_dinamicos['pulso_popliteo_izquierdo'] = crear_campo_dinamico('Pulso Popliteo', 'Presente')

                    ui.label('Pulso Tibial Posterior').classes('text-lg font-semibold text-blue-700')
                    
                    campos_dinamicos['pulso_tibial_posterior_izquierdo'] = crear_campo_dinamico('Pulso Tibial Posterior', 'Presente')
                    
                    ui.label('Pulso Pedeo').classes('text-lg font-semibold text-blue-700')
                 
                    campos_dinamicos['pulso_pedeo_izquierdo'] = crear_campo_dinamico('Pulso Pedeo', 'Presente')

                    ui.label('EAP').classes('text-lg font-semibold text-blue-700')
                    EAP_izquierdo = ui.radio(['Si', 'No'], value='No').props('inline').classes('w-full')

                    # Campos Dinámicos Nuevos (Formato N/AN/NE)
                    campos_dinamicos['venoso_periferico_izquierdo'] = crear_campo_dinamico('Veno Periférico', 'Presente')
                    campos_dinamicos['linfatico_izquierdo'] = crear_campo_dinamico('Linfático', 'Presente')

                # ==================== COLUMNA 2: PIE IZQUIERDO (Presiones/Sensibilidad) ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Izquierdo...').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Presión Tibial (mmHg)').classes('text-lg font-semibold text-blue-700')
                    tibial_izquierdo = self.input_clinico('Tibial Izquierdo', min_val=50, max_val=250, valor_inicial=None).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Pedia (mmHg)').classes('text-lg font-semibold text-blue-700')
                    pedia_izquierdo = self.input_clinico('Pedia Izquierdo', min_val=30, max_val=300, valor_inicial=None).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Humeral (mmHg)').classes('text-lg font-semibold text-blue-700')
                    humeral_izquierdo = self.input_clinico('Humeral Izquierdo', min_val=20, max_val=300, valor_inicial=None).classes(INPUT_CLASSES)
                    
                    ui.label('LOPS').classes('text-lg font-semibold text-blue-700')
                    LOPS_izquierdo = ui.radio(['Si', 'No'], value='No').props('inline').classes('w-full')
                    
                    # Campos Dinámicos Nuevos (Formato N/AN/NE)
                    campos_dinamicos['patelar_izquierdo'] = crear_campo_dinamico('Patelar', 'Presente')
                    campos_dinamicos['aquileano_izquierdo'] = crear_campo_dinamico('Aquileano', 'Presente')
                    campos_dinamicos['palestesia_izquierdo'] = crear_campo_dinamico('Palestesia (Profunda)', 'Conservada')
                    
                    ui.label('Sensibilidad Superficial').classes('text-base font-bold text-gray-800 mt-2 mb-1')
                    campos_dinamicos['tactil_izquierdo'] = crear_campo_dinamico('Táctil', 'Presente')
                    campos_dinamicos['termica_izquierdo'] = crear_campo_dinamico('Térmica', 'Presente')
                    campos_dinamicos['dolorosa_izquierdo'] = crear_campo_dinamico('Dolorosa', 'Presente')


                # ==================== COLUMNA 3: PIE DERECHO (Dermatología/Pulsos) ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Derecho').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Enfermedades Podálicas').classes('text-lg font-semibold text-blue-700')
                    defromidades_podalicas_derecho = ui.select(
                        ['Pie Plano, cavo , supinado', 'Hallux Valgus', 'Dedos En Garra', 'Pie de Charcot', 
                        'Amp Menores', 'Dedos en martillo', 'Otras'], 
                        value=[], multiple=True
                    ).classes(INPUT_CLASSES+' w-64').props('use-chips')

                    otra_enf_pod_der = ui.input('Especifique otra enfermedad').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(defromidades_podalicas_derecho, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Dermatológicas').classes('text-lg font-semibold text-blue-700')
                    lesiones_dermatologicas_derecho = ui.select(
                        ['Epidermofitosis', 'Piel seca y Callosa' , 'Hiperpigmentación', 'Dermatitis', 
                        'Celulitis', 'Úlceras', 'Palidez', 'Cianosis','Rubicundez', 'Dedos con necrosis', 'Otras'], 
                        value=[], multiple=True
                    ).classes(INPUT_CLASSES+' w-64').props('use-chips')

                    otra_les_derm_der = ui.input('Especifique otra lesión').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(lesiones_dermatologicas_derecho, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Uñas').classes('text-lg font-semibold text-blue-700')
                    lesiones_uñas_derecho = ui.select(['Onimicosis', 'Paroniquia'], value=[], multiple=True).classes(INPUT_CLASSES+' w-64').props('use-chips')
                    
                    ui.label('Pulso Femoral').classes('text-lg font-semibold text-blue-700')
                  
                    campos_dinamicos['pulso_femoral_derecho'] = crear_campo_dinamico('Pulso Femoral', 'Presente')
                    ui.label('Pulso Popliteo').classes('text-lg font-semibold text-blue-700')
                
                    campos_dinamicos['pulso_popliteo_derecho'] = crear_campo_dinamico('Pulso Popliteo', 'Presente')
                    ui.label('Pulso Tibial Posterior').classes('text-lg font-semibold text-blue-700')
                   
                    campos_dinamicos['pulso_tibial_posterior_derecho'] = crear_campo_dinamico('Pulso Tibial Posterior', 'Presente')
                    
                    ui.label('Pulso Pedeo').classes('text-lg font-semibold text-blue-700')
                  
                    campos_dinamicos['pulso_pedeo_derecho'] = crear_campo_dinamico('Pulso Pedeo', 'Presente')
                    
                    ui.label('EAP').classes('text-lg font-semibold text-blue-700')
                    EAP_derecho = ui.radio(['Si', 'No'], value='No').props('inline').classes('w-full')
                    
                    # Campos Dinámicos Nuevos (Formato N/AN/NE)
                    campos_dinamicos['venoso_periferico_derecho'] = crear_campo_dinamico('Veno Periférico', 'Presente')
                    campos_dinamicos['linfatico_derecho'] = crear_campo_dinamico('Linfático', 'Presente')


                # ==================== COLUMNA 4: PIE DERECHO (Presiones/Sensibilidad) ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Derecho...').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Presión Tibial (mmHg)').classes('text-lg font-semibold text-blue-700')
                    tibial_derecho = self.input_clinico('Tibial Derecho', min_val=50, max_val=250, valor_inicial=None).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Pedia (mmHg)').classes('text-lg font-semibold text-blue-700')
                    pedia_derecho = self.input_clinico('Pedia Derecho', min_val=30, max_val=250, valor_inicial=None).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Humeral (mmHg)').classes('text-lg font-semibold text-blue-700')
                    humeral_derecho = self.input_clinico('Humeral Derecho', min_val=20, max_val=250, valor_inicial=None).classes(INPUT_CLASSES)

                    ui.label('LOPS').classes('text-lg font-semibold text-blue-700')
                    LOPS_derecho = ui.radio(['Si', 'No'], value='No').props('inline').classes('w-full')
                    
                    # Campos Dinámicos Nuevos (Formato N/AN/NE)
                    campos_dinamicos['patelar_derecho'] = crear_campo_dinamico('Patelar', 'Presente')
                    campos_dinamicos['aquileano_derecho'] = crear_campo_dinamico('Aquileano', 'Presente')
                    campos_dinamicos['palestesia_derecho'] = crear_campo_dinamico('Palestesia (Profunda)', 'Conservada')
                    
                    ui.label('Sensibilidad Superficial').classes('text-base font-bold text-gray-800 mt-2 mb-1')
                    campos_dinamicos['tactil_derecho'] = crear_campo_dinamico('Táctil', 'Presente')
                    campos_dinamicos['termica_derecho'] = crear_campo_dinamico('Térmica', 'Presente')
                    campos_dinamicos['dolorosa_derecho'] = crear_campo_dinamico('Dolorosa', 'Presente')

            
            with ui.column().classes('w-full gap-4 mt-6'):
                ui.label('Impresión Diagnóstica').classes('text-xl font-bold text-blue-700 border-b-2 border-blue-200 pb-2')
                impresion_diagnostica = ui.select(
                    options=['Pie de Riesgo Grado 0', 'Pie de Riesgo Grado 1', 'Pie de Riesgo Grado 2', 
                             'Pie de Riesgo Grado 3', 'Pie de Riesgo Grado 4'],
                    label='Seleccione la impresión diagnóstica'
                ).classes(INPUT_CLASSES+' w-64')
                
            
            def procesar_y_guardar():
                # Lógica interna para empaquetar el string compuesto: "AN:Texto"
                def obtener_valor_final(campo_dict):
                    r_val = campo_dict['radio'].value
                    i_val = campo_dict['input'].value
                    if r_val == 'AN':
                        return f"AN:{i_val.strip()}" if i_val and i_val.strip() else "AN"
                    return r_val

                # Sustituir 'Otras' por el valor escrito en el input
                enf_izq = [otra_enf_pod_izq.value if x == 'Otras' and otra_enf_pod_izq.value else x for x in defromidades_podalicas_izquierdo.value]
                enf_izq = [x for x in enf_izq if x != 'Otras']
                
                les_izq = [otra_les_derm_izq.value if x == 'Otras' and otra_les_derm_izq.value else x for x in lesiones_dermatologicas_izquierdo.value]
                les_izq = [x for x in les_izq if x != 'Otras']

                enf_der = [otra_enf_pod_der.value if x == 'Otras' and otra_enf_pod_der.value else x for x in defromidades_podalicas_derecho.value]
                enf_der = [x for x in enf_der if x != 'Otras']
                
                les_der = [otra_les_derm_der.value if x == 'Otras' and otra_les_derm_der.value else x for x in lesiones_dermatologicas_derecho.value]
                les_der = [x for x in les_der if x != 'Otras']

                # Ejecución de almacenamiento mediante el controlador de Podología
                exito, msg = self.controlador_podologia.guardar_examen_miembro_inferior(
                    self.paciente.id,
                    fecha_input.value,
                    enf_izq, les_izq, lesiones_uñas_izquierdo.value,
                    obtener_valor_final(campos_dinamicos['pulso_femoral_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['pulso_popliteo_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['pulso_tibial_posterior_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['pulso_pedeo_izquierdo']), 
                    EAP_izquierdo.value, tibial_izquierdo.value, pedia_izquierdo.value,
                    humeral_izquierdo.value, 
                    obtener_valor_final(campos_dinamicos['patelar_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['aquileano_izquierdo']), 
                    LOPS_izquierdo.value, 
                    obtener_valor_final(campos_dinamicos['palestesia_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['tactil_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['termica_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['dolorosa_izquierdo']),
                    enf_der, les_der, lesiones_uñas_derecho.value,
                    obtener_valor_final(campos_dinamicos['pulso_femoral_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_popliteo_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_tibial_posterior_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_pedeo_derecho']), 
                    EAP_derecho.value, tibial_derecho.value, pedia_derecho.value,
                    humeral_derecho.value, 
                    obtener_valor_final(campos_dinamicos['patelar_derecho']), 
                    obtener_valor_final(campos_dinamicos['aquileano_derecho']),
                    LOPS_derecho.value, 
                    obtener_valor_final(campos_dinamicos['palestesia_derecho']), 
                    obtener_valor_final(campos_dinamicos['tactil_derecho']), 
                    obtener_valor_final(campos_dinamicos['termica_derecho']), 
                    obtener_valor_final(campos_dinamicos['dolorosa_derecho']),
                    impresion_diagnostica.value,
                    obtener_valor_final(campos_dinamicos['venoso_periferico_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['venoso_periferico_derecho']),
                    obtener_valor_final(campos_dinamicos['linfatico_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['linfatico_derecho']), 
                    dialog
                )
                if exito:
                    self.mostrar_examenes_podologicos.refresh()
                    ui.notify(msg, color='green') 
                else:
                    ui.notify(f"Error: {msg}", color='red')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=procesar_y_guardar).props('flat').classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    

    def editar_examen_miembro_inferior(self, examen):
        # Diccionario para encapsular la referencia de inputs y radios dinámicos en edición
        campos_dinamicos = {}

        def crear_campo_dinamico(label, valor_inicial="N"):
            """
            Fábrica interna adaptada para leer datos históricos de la BD.
            Mapea "Presente/Conservada" -> N, "Ausente/No Registrado" -> NE.
            Cualquier texto no reconocido o con prefijo "AN:" activa el estado "AN".
            """
            radio_defecto = 'N'
            texto_defecto = ''
            
            if valor_inicial:
                valor_str = str(valor_inicial)
                if valor_str.startswith('AN:'):
                    partes = valor_str.split(':', 1)
                    radio_defecto = 'AN'
                    texto_defecto = partes[1] if len(partes) > 1 else ''
                elif valor_str == 'AN':
                    radio_defecto = 'AN'
                elif valor_str in ['Presente', 'Conservada', 'N']:
                    radio_defecto = 'N'
                elif valor_str in ['Ausente', 'No Conservada', 'NE', 'No Registrado']:
                    radio_defecto = 'NE'
                else:
                    # Si tiene un texto libre antiguo, se recupera asumiendo que fue una anomalía
                    radio_defecto = 'AN'
                    texto_defecto = valor_str

            contenedor = ui.column().classes('w-full gap-1 mb-2')
            with contenedor:
                ui.label(label).classes('text-xs font-semibold text-blue-700')
                radio = ui.radio({'N': 'N', 'AN': 'AN', 'NE': 'NE'}, value=radio_defecto).props('inline dense')
                input_texto = ui.input(label='Especifique anomalía...', value=texto_defecto).classes('w-full text-xs').props('dense')
                input_texto.bind_visibility_from(radio, 'value', lambda v: v == 'AN')
            
            return {'radio': radio, 'input': input_texto}

        with ui.dialog().classes('w-full') as dialog, ui.card().classes('w-full max-w-6xl shadow-lg rounded-lg').style("width:100%; max-width:none;"):
            ui.label('Editar Examen de Miembro Inferior').classes(HEADER_TITLE_CLASSES)
            
            # Fecha input
            with ui.input('Fecha').classes('w-full') as fecha_input:
                fecha_input.value = examen.fecha_registro.strftime('%Y-%m-%d')
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

            with ui.element('div').classes('row q-col-gutter-lg w-full'):
                
                # ==================== COLUMNA 1: PIE IZQUIERDO ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Izquierdo').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Enfermedades Podálicas').classes('text-lg font-semibold text-blue-700')
                    opc_enf = ['Pie Plano, cavo , supinado',  'Hallux Valgus', 'Dedos En Garra', 'Pie de Charcot', 'Amp Menores', 'Dedos en martillo', 'Otras']
                    enf_izq_db = [e.padecimiento for e in examen.defromidades_podalicas_izquierdo]
                    enf_izq_select = [val for val in enf_izq_db if val in opc_enf]
                    enf_izq_otras = [val for val in enf_izq_db if val not in opc_enf]
                    if enf_izq_otras: enf_izq_select.append('Otras')

                    defromidades_podalicas_izquierdo = ui.select(opc_enf, value=enf_izq_select, multiple=True).classes(INPUT_CLASSES+ ' w-64').props('use-chips')
                    otra_enf_pod_izq = ui.input('Especifique otra enfermedad', value=enf_izq_otras[0] if enf_izq_otras else '').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(defromidades_podalicas_izquierdo, 'value', lambda v: v and 'Otras' in v)

                    ui.label('Lesiones Dermatológicas').classes('text-lg font-semibold text-blue-700')
                    opc_les = ['Epidermofitosis', 'Piel seca y Callosa' , 'Hiperpigmentación', 'Dermatitis', 'Celulitis', 'Úlceras', 'Palidez', 'Cianosis','Rubicundez', 'Dedos con necrosis', 'Otras']
                    les_izq_db = [l.padecimiento for l in examen.lesiones_dermatologicas_izquierdo]
                    les_izq_select = [val for val in les_izq_db if val in opc_les]
                    les_izq_otras = [val for val in les_izq_db if val not in opc_les]
                    if les_izq_otras: les_izq_select.append('Otras')

                    lesiones_dermatologicas_izquierdo = ui.select(opc_les, value=les_izq_select, multiple=True).classes(INPUT_CLASSES+ ' w-64').props('use-chips')
                    otra_les_derm_izq = ui.input('Especifique otra lesión', value=les_izq_otras[0] if les_izq_otras else '').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(lesiones_dermatologicas_izquierdo, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Uñas').classes('text-lg font-semibold text-blue-700')
                    lesiones_uñas_izquierdo_values = [l.padecimiento for l in examen.lesiones_uñas_izquierdo]
                    lesiones_uñas_izquierdo = ui.select(
                        ['Onimicosis', 'Paroniquia'], value=lesiones_uñas_izquierdo_values, multiple=True
                    ).classes(INPUT_CLASSES+ ' w-64').props('use-chips')
                    
                    # Campos Dinámicos - Pulsos Izquierdos
                    campos_dinamicos['pulso_femoral_izquierdo'] = crear_campo_dinamico('Pulso Femoral', examen.pulso_femoral_izquierdo)
                    campos_dinamicos['pulso_popliteo_izquierdo'] = crear_campo_dinamico('Pulso Popliteo', examen.pulso_popliteo_izquierdo)
                    campos_dinamicos['pulso_tibial_posterior_izquierdo'] = crear_campo_dinamico('Pulso Tibial Posterior', examen.pulso_tibial_posterior_izquierdo)
                    campos_dinamicos['pulso_pedeo_izquierdo'] = crear_campo_dinamico('Pulso Pedeo', examen.pulso_pedeo_izquierdo)
                    
                    ui.label('EAP').classes('text-lg font-semibold text-blue-700')
                    EAP_izquierdo = ui.radio(['Si', 'No'], value=examen.EAP_izquierdo).props('inline').classes('w-full')
                    
                    campos_dinamicos['venoso_periferico_izquierdo'] = crear_campo_dinamico('Veno Periférico', examen.venoso_periferico_izquierdo)
                    campos_dinamicos['linfatico_izquierdo'] = crear_campo_dinamico('Linfático', examen.linfatico_izquierdo)


                # ==================== COLUMNA 2: PIE IZQUIERDO ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Izquierdo...').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Presión Tibial (mmHg)').classes('text-lg font-semibold text-blue-700')
                    tibial_izquierdo = self.input_clinico('Tibial Izquierdo', min_val=50, max_val=250, valor_inicial=examen.tibial_izquierdo).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Pedia (mmHg)').classes('text-lg font-semibold text-blue-700')
                    pedia_izquierdo = self.input_clinico('Pedia Izquierdo', min_val=30, max_val=250, valor_inicial=examen.pedia_izquierdo).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Humeral (mmHg)').classes('text-lg font-semibold text-blue-700')
                    humeral_izquierdo = self.input_clinico('Humeral Izquierdo', min_val=20, max_val=250, valor_inicial=examen.humeral_izquierdo).classes(INPUT_CLASSES)
                    
                    ui.label('LOPS').classes('text-lg font-semibold text-blue-700')
                    LOPS_izquierdo = ui.radio(['Si', 'No'], value=examen.LOPS_izquierdo).props('inline').classes('w-full')

                    # Campos Dinámicos - Sensibilidad Izquierdos
                    campos_dinamicos['patelar_izquierdo'] = crear_campo_dinamico('Patelar', examen.patelar_izquierdo)
                    campos_dinamicos['aquileano_izquierdo'] = crear_campo_dinamico('Aquileano', examen.aquileano_izquierdo)
                    campos_dinamicos['palestesia_izquierdo'] = crear_campo_dinamico('Palestesia (Profunda)', examen.palestesia_izquierdo)
                    
                    ui.label('Sensibilidad Superficial').classes('text-base font-bold text-gray-800 mt-2 mb-1')
                    campos_dinamicos['tactil_izquierdo'] = crear_campo_dinamico('Táctil', examen.tactil_izquierdo)
                    campos_dinamicos['termica_izquierdo'] = crear_campo_dinamico('Térmica', examen.termica_izquierdo)
                    campos_dinamicos['dolorosa_izquierdo'] = crear_campo_dinamico('Dolorosa', examen.dolorosa_izquierdo)


                # ==================== COLUMNA 3: PIE DERECHO ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Derecho').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Enfermedades Podálicas').classes('text-lg font-semibold text-blue-700')
                    enf_der_db = [e.padecimiento for e in examen.defromidades_podalicas_derecho]
                    enf_der_select = [val for val in enf_der_db if val in opc_enf]
                    enf_der_otras = [val for val in enf_der_db if val not in opc_enf]
                    if enf_der_otras: enf_der_select.append('Otras')

                    defromidades_podalicas_derecho = ui.select(opc_enf, value=enf_der_select, multiple=True).classes(INPUT_CLASSES+' w-64').props('use-chips')
                    otra_enf_pod_der = ui.input('Especifique otra enfermedad', value=enf_der_otras[0] if enf_der_otras else '').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(defromidades_podalicas_derecho, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Dermatológicas').classes('text-lg font-semibold text-blue-700')
                    les_der_db = [l.padecimiento for l in examen.lesiones_dermatologicas_derecho]
                    les_der_select = [val for val in les_der_db if val in opc_les]
                    les_der_otras = [val for val in les_der_db if val not in opc_les]
                    if les_der_otras: les_der_select.append('Otras')

                    lesiones_dermatologicas_derecho = ui.select(opc_les, value=les_der_select, multiple=True).classes(INPUT_CLASSES+' w-64').props('use-chips')
                    otra_les_derm_der = ui.input('Especifique otra lesión', value=les_der_otras[0] if les_der_otras else '').classes(INPUT_CLASSES+ ' w-64').bind_visibility_from(lesiones_dermatologicas_derecho, 'value', lambda v: v and 'Otras' in v)
                    
                    ui.label('Lesiones Uñas').classes('text-lg font-semibold text-blue-700')
                    lesiones_uñas_derecho_values = [l.padecimiento for l in examen.lesiones_uñas_derecho]
                    lesiones_uñas_derecho = ui.select(
                        ['Onimicosis', 'Paroniquia'], value=lesiones_uñas_derecho_values, multiple=True
                    ).classes(INPUT_CLASSES).props('use-chips')
                    
                    # Campos Dinámicos - Pulsos Derechos
                    campos_dinamicos['pulso_femoral_derecho'] = crear_campo_dinamico('Pulso Femoral', examen.pulso_femoral_derecho)
                    campos_dinamicos['pulso_popliteo_derecho'] = crear_campo_dinamico('Pulso Popliteo', examen.pulso_popliteo_derecho)
                    campos_dinamicos['pulso_tibial_posterior_derecho'] = crear_campo_dinamico('Pulso Tibial Posterior', examen.pulso_tibial_posterior_derecho)
                    campos_dinamicos['pulso_pedeo_derecho'] = crear_campo_dinamico('Pulso Pedeo', examen.pulso_pedeo_derecho)
                    
                    ui.label('EAP').classes('text-lg font-semibold text-blue-700')
                    EAP_derecho = ui.radio(['Si', 'No'], value=examen.EAP_derecho).props('inline').classes('w-full')
                    
                    campos_dinamicos['venoso_periferico_derecho'] = crear_campo_dinamico('Veno Periférico', examen.venoso_periferico_derecho)
                    campos_dinamicos['linfatico_derecho'] = crear_campo_dinamico('Linfático', examen.linfatico_derecho)


                # ==================== COLUMNA 4: PIE DERECHO ====================
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Pie Derecho...').classes('text-xl font-bold text-green-700 border-b-2 border-green-200 pb-2 mb-3')
                    
                    ui.label('Presión Tibial (mmHg)').classes('text-lg font-semibold text-blue-700')
                    tibial_derecho = self.input_clinico('Tibial Derecho', min_val=50, max_val=250, valor_inicial=examen.tibial_derecho).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Pedia (mmHg)').classes('text-lg font-semibold text-blue-700')
                    pedia_derecho = self.input_clinico('Pedia Derecho', min_val=30, max_val=250, valor_inicial=examen.pedia_derecho).classes(INPUT_CLASSES)
                    
                    ui.label('Presión Humeral (mmHg)').classes('text-lg font-semibold text-blue-700')
                    humeral_derecho = self.input_clinico('Humeral Derecho', min_val=20, max_val=250, valor_inicial=examen.humeral_derecho).classes(INPUT_CLASSES)

                    ui.label('LOPS').classes('text-lg font-semibold text-blue-700')
                    LOPS_derecho = ui.radio(['Si', 'No'], value=examen.LOPS_derecho).props('inline').classes('w-full')
                    
                    # Campos Dinámicos - Sensibilidad Derechos
                    campos_dinamicos['patelar_derecho'] = crear_campo_dinamico('Patelar', examen.patelar_derecho)
                    campos_dinamicos['aquileano_derecho'] = crear_campo_dinamico('Aquileano', examen.aquileano_derecho)
                    campos_dinamicos['palestesia_derecho'] = crear_campo_dinamico('Palestesia (Profunda)', examen.palestesia_derecho)
                    
                    ui.label('Sensibilidad Superficial').classes('text-base font-bold text-gray-800 mt-2 mb-1')
                    campos_dinamicos['tactil_derecho'] = crear_campo_dinamico('Táctil', examen.tactil_derecho)
                    campos_dinamicos['termica_derecho'] = crear_campo_dinamico('Térmica', examen.termica_derecho)
                    campos_dinamicos['dolorosa_derecho'] = crear_campo_dinamico('Dolorosa', examen.dolorosa_derecho)

            
            with ui.column().classes('w-full gap-4 mt-6'):
                ui.label('Impresión Diagnóstica').classes('text-xl font-bold text-blue-700 border-b-2 border-blue-200 pb-2')
                impresion_diagnostica = ui.select(
                    options=['Pie de Riesgo Grado 0', 'Pie de Riesgo Grado 1', 'Pie de Riesgo Grado 2', 
                            'Pie de Riesgo Grado 3', 'Pie de Riesgo Grado 4',"No Registrado" ],
                    label='Seleccione la impresión diagnóstica',value=examen.impresion_diagnostica
                ).classes(INPUT_CLASSES+' w-64')
                
            
            def procesar_y_actualizar():
                def obtener_valor_final(campo_dict):
                    r_val = campo_dict['radio'].value
                    i_val = campo_dict['input'].value
                    if r_val == 'AN':
                        return f"AN:{i_val.strip()}" if i_val and i_val.strip() else "AN"
                    return r_val

                enf_izq = [otra_enf_pod_izq.value if x == 'Otras' and otra_enf_pod_izq.value else x for x in defromidades_podalicas_izquierdo.value]
                enf_izq = [x for x in enf_izq if x != 'Otras']
                
                les_izq = [otra_les_derm_izq.value if x == 'Otras' and otra_les_derm_izq.value else x for x in lesiones_dermatologicas_izquierdo.value]
                les_izq = [x for x in les_izq if x != 'Otras']

                enf_der = [otra_enf_pod_der.value if x == 'Otras' and otra_enf_pod_der.value else x for x in defromidades_podalicas_derecho.value]
                enf_der = [x for x in enf_der if x != 'Otras']
                
                les_der = [otra_les_derm_der.value if x == 'Otras' and otra_les_derm_der.value else x for x in lesiones_dermatologicas_derecho.value]
                les_der = [x for x in les_der if x != 'Otras']

                exito , mesg = self.controlador_podologia.actualizar_examen_miembro_inferior(
                    examen, fecha_input.value,
                    enf_izq, les_izq, lesiones_uñas_izquierdo.value,
                    obtener_valor_final(campos_dinamicos['pulso_femoral_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['pulso_popliteo_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['pulso_tibial_posterior_izquierdo']),
                    obtener_valor_final(campos_dinamicos['pulso_pedeo_izquierdo']), 
                    EAP_izquierdo.value, tibial_izquierdo.value, pedia_izquierdo.value,
                    humeral_izquierdo.value, 
                    obtener_valor_final(campos_dinamicos['patelar_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['aquileano_izquierdo']), 
                    LOPS_izquierdo.value, 
                    obtener_valor_final(campos_dinamicos['palestesia_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['tactil_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['termica_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['dolorosa_izquierdo']),
                    enf_der, les_der, lesiones_uñas_derecho.value,
                    obtener_valor_final(campos_dinamicos['pulso_femoral_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_popliteo_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_tibial_posterior_derecho']), 
                    obtener_valor_final(campos_dinamicos['pulso_pedeo_derecho']), 
                    EAP_derecho.value, tibial_derecho.value, pedia_derecho.value,
                    humeral_derecho.value, 
                    obtener_valor_final(campos_dinamicos['patelar_derecho']), 
                    obtener_valor_final(campos_dinamicos['aquileano_derecho']),
                    LOPS_derecho.value, 
                    obtener_valor_final(campos_dinamicos['palestesia_derecho']), 
                    obtener_valor_final(campos_dinamicos['tactil_derecho']), 
                    obtener_valor_final(campos_dinamicos['termica_derecho']), 
                    obtener_valor_final(campos_dinamicos['dolorosa_derecho']),
                    impresion_diagnostica.value,
                    obtener_valor_final(campos_dinamicos['venoso_periferico_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['venoso_periferico_derecho']),
                    obtener_valor_final(campos_dinamicos['linfatico_izquierdo']), 
                    obtener_valor_final(campos_dinamicos['linfatico_derecho']), 
                    dialog
                )
                if exito:
                    self.mostrar_examenes_podologicos.refresh()
                    ui.notify(mesg, color='green')
                else:
                    ui.notify(f"Error: {mesg}", color='red')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=procesar_y_actualizar).props('flat').classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()
 
                
                
    def eliminar_examen_miembro_inferior(self, examen):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este examen?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_miembros_inferior(examen, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()

    

    def confirmar_eliminacion_miembros_inferior(self, examen, dialog):
        try:
            self.controlador_podologia.eliminar_examen(examen)
            ui.notify('Examen de Miembros inferiores  eliminado correctamente', type='positive')
            dialog.close()
            self.mostrar_examenes_podologicos.refresh()  # Actualizar la vista
        except Exception as e:
            log_error_and_notify(e, f'Error eliminando Miembros inferiores  {self.paciente.no_hc}')
            self.session.rollback()
            ui.notify(f'Error al eliminar el Examen de Miembros inferiores: {str(e)}', type='negative')      
    