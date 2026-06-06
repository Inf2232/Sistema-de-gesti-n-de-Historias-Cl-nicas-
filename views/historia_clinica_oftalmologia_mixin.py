# historia_clinica_oftalmologia_mixin.py
from datetime import datetime
from nicegui import ui
from models import Oftalmologia
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
from controllers.historia_clinica_oftalmologia_controller import HistoriaClinicaOftalmologiaController

class HistoriaClinicaOftalmologiaMixin:

    @property
    def controlador_oftalmologia(self):
        """Inicializa de forma segura el controlador bajo demanda."""
        if not hasattr(self, '_controlador_oftalmologia'):
            self._controlador_oftalmologia = HistoriaClinicaOftalmologiaController(self.session)
        return self._controlador_oftalmologia

    @ui.refreshable
    def mostrar_oftalmologia(self):
        with ui.column().classes('w-full p-6 gap-6 bg-gray-50'):
            # Resumen de Exámenes Oftalmológicos
            with ui.card().classes(HC_CARD_PROFESSIONAL):
                with ui.row().classes('justify-between items-center mb-4'):
                    ui.label('Exámenes Oftalmológicos').classes(HEADER_TITLE_CLASSES)
                    if tiene_permiso('oftalmologia_manage'):
                        ui.button('Agregar Nuevo', icon='add', on_click=self.agregar_examen_oftalmologico
                                ).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                    
                examenes = self.paciente.oftalmologia
                if examenes:
                    # Obtener el último examen
                    ultimo_examen = max(examenes, key=lambda x: x.fecha_registro)
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.column().classes('gap-4'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                ui.icon('calendar_today').classes('text-blue-600')
                                ui.label(f'Último examen: {ultimo_examen.fecha_registro.strftime("%d/%m/%Y")}'
                                        ).classes('text-lg font-semibold text-gray-700')
                            
                            with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):

                                with ui.element('div').classes(
                                    'col-12 col-md-6'):
                                    # Ojo Izquierdo (OI)
                                    with ui.card().classes(HC_SECTION_CARD):    
                                        ui.label("Ojo Izquierdo (OI)").classes('font-bold text-lg text-blue-700 mb-3 border-b border-gray-300 pb-2')
                                        with ui.grid(columns=2).classes('gap-4'):
                                            with ui.column().classes('gap-3'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Visión Borrosa").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.vision_borrosa_oi or "No registrado"}').classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Agudeza Visual").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.av_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Refracción Dinámica").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.rd_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Acomodación").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.a_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Sensibilidad al Contraste").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.sa_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                            with ui.column().classes('gap-3'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Motilidad Ocular").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.m_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Fondo de Ojo").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.fo_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Hemorragia Vítrea").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.hemorragia_vitrea_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Maculopatía").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.maculopatia_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Catarata").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.catarata_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Glaucoma").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.glaucoma_oi}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):
                                    # Ojo Derecho (OD)
                                    with ui.card().classes(HC_SECTION_CARD):
                                        ui.label("Ojo Derecho (OD)").classes('font-bold text-lg text-blue-700 mb-3 border-b border-gray-300 pb-2')
                                        with ui.grid(columns=2).classes('gap-4'):
                                            with ui.column().classes('gap-3'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Visión Borrosa").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.vision_borrosa_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Agudeza Visual").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.av_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Refracción Dinámica").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.rd_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Acomodación").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.a_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Sensibilidad al Contraste").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.sa_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                            with ui.column().classes('gap-3'):
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Motilidad Ocular").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.m_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Fondo de Ojo").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.fo_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Hemorragia Vítrea").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.hemorragia_vitrea_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Maculopatía").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.maculopatia_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Catarata").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.catarata_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.label("Glaucoma").classes('text-sm font-medium text-gray-600')
                                                    ui.label(f'{ultimo_examen.glaucoma_od}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                
                            with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):

                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label("Retinopatía Diabética").classes('text-sm font-medium text-gray-600')
                                            ui.label(f'{ultimo_examen.retinopatia_diabetica}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label("Retinopatía Hipertensiva").classes('text-sm font-medium text-gray-600')
                                            ui.label(f'{ultimo_examen.retinopatia_hipertensiva}' or "No registrado").classes('text-base font-semibold text-gray-800')
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label("Retinopatía Arterioesclerótica").classes('text-sm font-medium text-gray-600')
                                            ui.label(f'{ultimo_examen.retinopatia_artereo_esclerosis}' or "No registrado").classes('text-base font-semibold text-gray-800')
                else:
                    with ui.card().classes(HC_SECTION_CARD):
                        ui.icon('info').classes('text-gray-400 text-4xl mb-2')
                        ui.label('No hay exámenes oftalmológicos registrados').classes('text-gray-500 italic text-center py-4')

            # Historial completo
            with ui.expansion('Ver historial completo', icon='history').classes('w-full mt-4 bg-white rounded-lg'):
                with ui.card().classes(HC_CARD_PROFESSIONAL):
                    if examenes:
                        examenes_ordenados = sorted(examenes, key=lambda x: x.fecha_registro, reverse=True)
                        with ui.column().classes('w-full gap-4'):
                            for examen in examenes_ordenados:
                                with ui.card().classes(HC_SECTION_CARD):
                                    with ui.row().classes('justify-between items-center mb-3 border-b border-gray-200 pb-2'):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.icon('event').classes('text-blue-600')
                                            ui.label(f'Fecha: {examen.fecha_registro.strftime("%d/%m/%Y")}').classes('font-semibold text-gray-700')
                                        
                                        with ui.row().classes('gap-1'):
                                            if tiene_permiso('oftalmologia_manage'):
                                                ui.button(icon='edit', on_click=lambda e, ex=examen: self.editar_examen_oftalmologico(ex)
                                                        ).props('flat round dense color="primary"').classes(PRIMARY_BUTTON_CLASSES)
                                                ui.button(icon='delete', on_click=lambda e, ex=examen: self.eliminar_examen_oftalmologico(ex)
                                                        ).props('flat round dense color="error"').classes(DANGER_BUTTON_CLASSES)
                                                
                                    
                                    with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                                # Ojo Izquierdo
                                            with ui.card().classes(HC_SECTION_CARD):
                                                ui.label('Ojo Izquierdo (OI)').classes('font-bold text-blue-700 mb-2')
                                                with ui.grid(columns=2).classes('gap-2'):
                                                    with ui.column().classes('gap-2'):
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Visión Borrosa").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.vision_borrosa_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Agudeza Visual").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.av_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Refracción").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.rd_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Acomodación").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.a_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Sens. Contraste").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.sa_oi}').classes('text-sm font-semibold text-gray-800')
                                                    with ui.column().classes('gap-2'):
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Motilidad").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.m_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Fondo Ojo").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.fo_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("H. Vítrea").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.hemorragia_vitrea_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Maculopatía").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.maculopatia_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Catarata").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.catarata_oi}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Glaucoma").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.glaucoma_oi}').classes('text-sm font-semibold text-gray-800')
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            # Ojo Derecho
                                            with ui.card().classes(HC_SECTION_CARD):
                                                ui.label('Ojo Derecho (OD)').classes('font-bold text-blue-700 mb-2')
                                                with ui.grid(columns=2).classes('gap-2'):
                                                    with ui.column().classes('gap-2'):
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Visión Borrosa").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.vision_borrosa_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Agudeza Visual").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.av_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Refracción").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.rd_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Acomodación").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.a_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Sens. Contraste").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.sa_od}').classes('text-sm font-semibold text-gray-800')
                                                    with ui.column().classes('gap-2'):
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Motilidad").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.m_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Fondo Ojo").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.fo_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("H. Vítrea").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.hemorragia_vitrea_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Maculopatía").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.maculopatia_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Catarata").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.catarata_od}').classes('text-sm font-semibold text-gray-800')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label("Glaucoma").classes('text-xs font-medium text-gray-600')
                                                            ui.label(f'{examen.glaucoma_od}').classes('text-sm font-semibold text-gray-800')
                                        
                                    with ui.row().classes('gap-4 mt-3'):
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.row().classes('items-center gap-2'):
                                                ui.label("Ret. Diabética").classes('text-xs font-medium text-gray-600')
                                                ui.label(f'{examen.retinopatia_diabetica}').classes('text-sm font-semibold text-gray-800')
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.row().classes('items-center gap-2'):
                                                ui.label("Ret. Hipertensiva").classes('text-xs font-medium text-gray-600')
                                                ui.label(f'{examen.retinopatia_hipertensiva}').classes('text-sm font-semibold text-gray-800')
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.row().classes('items-center gap-2'):
                                                ui.label("Ret. Arterio.").classes('text-xs font-medium text-gray-600')
                                                ui.label(f'{examen.retinopatia_artereo_esclerosis}').classes('text-sm font-semibold text-gray-800')
                    else:
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('No hay registros de exámenes oftalmológicos').classes('text-gray-500 italic text-center py-4')


    def agregar_examen_oftalmologico(self):
        with ui.dialog().classes('w-full') as dialog, ui.card().style("width:80%; max-width:none;") :
            ui.label('Agregar Examen Oftalmológico').classes(HEADER_TITLE_CLASSES   )
            
            # Fecha del examen
            with ui.input('Fecha').classes('w-full') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(
                            f'locale="es" '
                            f'default-year-month={self.current_month} '
                            f':options="date => date <= \'{self.today}\'"'
                        ):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            # Campos comunes para ambos ojos
            with ui.column().classes('gap-4 w-full'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('Retinopatía Diabética').classes('text-lg font-bold text-blue-800')
                    retinopatia_diabetica = ui.select(
                        ['No', 'No Proliferativa', 'Proliferativa', 'No Precisada'], 
                        value='No'
                    ).classes(INPUT_CLASSES+ ' w-64')
                with ui.row().classes('items-center gap-2'):
                
                    ui.label('Retinopatía Hipertensiva').classes('text-lg font-bold text-blue-800')
                    retinopatia_hipertensiva = ui.select(
                        ['No', 'Grado 1', 'Grado 2', 'Grado 3', 'Grado 4', 'No Precisada'], 
                        value='No'
                    ).classes(INPUT_CLASSES+ ' w-64')
                with ui.row().classes('items-center gap-2'):
                
                    ui.label('Retinopatía Arterioesclerótica').classes('text-lg font-bold text-blue-800')
                    retinopatia_artereo_esclerosis = ui.select(
                        ['No', 'Grado 1', 'Grado 2', 'Grado 3', 'Grado 4', 'No Precisada'], 
                        value='No'
                    ).classes(INPUT_CLASSES+ ' w-64')

            # Contenedor principal para las dos columnas (Ojo Izquierdo y Ojo Derecho)
            with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):
                # Columna 1 - Ojo Izquierdo (OI)
                with ui.element('div').classes(
                                            'col-12 col-md-3'
                                        ):
                    ui.label('Ojo Izquierdo (OI)').classes('text-lg font-bold text-green-800')
                    
                    # Campos específicos para el Ojo Izquierdo
                    ui.label('Visión Borrosa').classes('text-lg font-bold text-blue-800')
                    vision_borrosa_oi = ui.select(
                    ['Si', 'No',], 
                    value=None
                ).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Agudeza Visual').classes('text-lg font-bold text-blue-800')
                    av_oi = self.input_clinico('Agudeza Visual', min_val=0, max_val=2, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Refracción Dinámica').classes('text-lg font-bold text-blue-800')
                    rd_oi = self.input_clinico('Refracción Dinámica', min_val=-30, max_val=30, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Acomodación').classes('text-lg font-bold text-blue-800')
                    a_oi = self.input_clinico('Acomodación', min_val=0, max_val=20, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Sensibilidad al Contraste').classes('text-lg font-bold text-blue-800')
                    sa_oi = self.input_clinico('Sensibilidad al Contraste', min_val=0, max_val=2, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')


                with ui.element('div').classes(
                                            'col-12 col-md-3'
                                        ):
                    ui.label('Ojo Izquierdo (OI)').classes('text-lg font-bold text-green-800')

                    ui.label('Motilidad Ocular').classes('text-lg font-bold text-blue-800')
                    m_oi = self.input_clinico('Motilidad Ocular', min_val=-4, max_val=4, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Fondo de Ojo').classes('text-lg font-bold text-blue-800')
                    fo_oi = self.input_clinico('Fondo de Ojo', min_val=0, max_val=10, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Hemorragia Vítrea').classes('text-lg font-bold text-blue-800')
                    hemorragia_vitrea_oi = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Maculopatía').classes('text-lg font-bold text-blue-800')
                    maculopatia_oi = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Catarata').classes('text-lg font-bold text-blue-800')
                    catarata_oi = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Glaucoma').classes('text-lg font-bold text-blue-800')
                    glaucoma_oi = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    

                # Columna 2 - Ojo Derecho (OD)
                with ui.element('div').classes(
                                            'col-12 col-md-3'
                                        ):
                    ui.label('Ojo Derecho (OD)').classes('text-lg font-bold text-green-800')
                    
                    # Campos específicos para el Ojo Derecho
                    ui.label('Visión Borrosa').classes('text-lg font-bold text-blue-800')
                    vision_borrosa_od = ui.select(
                    ['Si', 'No',], 
                    value=None
                ).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Agudeza Visual').classes('text-lg font-bold text-blue-800')
                    av_od = self.input_clinico('Agudeza Visual', min_val=0, max_val=2, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Refracción Dinámica').classes('text-lg font-bold text-blue-800')
                    rd_od = self.input_clinico('Refracción Dinámica', min_val=-30, max_val=30, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Acomodación').classes('text-lg font-bold text-blue-800')
                    a_od = self.input_clinico('Acomodación', min_val=0, max_val=20, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Sensibilidad al Contraste').classes('text-lg font-bold text-blue-800')
                    sa_od = self.input_clinico('Sensibilidad al Contraste', min_val=0, max_val=2, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')


                with ui.element('div').classes(
                                            'col-12 col-md-3'
                                        ):
                    ui.label('Ojo Derecho (OD)').classes('text-lg font-bold text-green-800')

                    ui.label('Motilidad Ocular').classes('text-lg font-bold text-blue-800')
                    m_od = self.input_clinico('Motilidad Ocular', min_val=-4, max_val=4, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Fondo de Ojo').classes('text-lg font-bold text-blue-800')
                    fo_od = self.input_clinico('Fondo de Ojo', min_val=0, max_val=10, valor_inicial=None).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Hemorragia Vítrea').classes('text-lg font-bold text-blue-800')
                    hemorragia_vitrea_od = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Maculopatía').classes('text-lg font-bold text-blue-800')
                    maculopatia_od = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Catarata').classes('text-lg font-bold text-blue-800')
                    catarata_od = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Glaucoma').classes('text-lg font-bold text-blue-800')
                    glaucoma_od = ui.select(
                    ['Si', 'No',], 
                    value='No'
                ).classes(INPUT_CLASSES+ ' w-38')

            def procesar_y_guardar():
                datos_oftalmologia = {
                    'retinopatia_diabetica': retinopatia_diabetica.value,
                    'retinopatia_hipertensiva': retinopatia_hipertensiva.value,
                    'retinopatia_artereo_esclerosis': retinopatia_artereo_esclerosis.value,
                    'vision_borrosa_oi': vision_borrosa_oi.value,
                    'av_oi': av_oi.value,
                    'rd_oi': rd_oi.value,
                    'a_oi': a_oi.value,
                    'sa_oi': sa_oi.value,
                    'm_oi': m_oi.value,
                    'fo_oi': fo_oi.value,
                    'hemorragia_vitrea_oi': hemorragia_vitrea_oi.value,
                    'maculopatia_oi': maculopatia_oi.value,
                    'catarata_oi': catarata_oi.value,
                    'glaucoma_oi': glaucoma_oi.value,
                    'vision_borrosa_od': vision_borrosa_od.value,
                    'av_od': av_od.value,
                    'rd_od': rd_od.value,
                    'a_od': a_od.value,
                    'sa_od': sa_od.value,
                    'm_od': m_od.value,
                    'fo_od': fo_od.value,
                    'hemorragia_vitrea_od': hemorragia_vitrea_od.value,
                    'maculopatia_od': maculopatia_od.value,
                    'catarata_od': catarata_od.value,
                    'glaucoma_od': glaucoma_od.value,
                }

                # CORRECCIÓN: Se envía self.paciente.id y no un objeto examen
                exito, msg = self.controlador_oftalmologia.guardar_examen(
                    self.paciente.id, 
                    fecha_input.value, 
                    **datos_oftalmologia
                )

                if exito:
                    ui.notify(msg, color='green')
                    dialog.close()
                    self.mostrar_oftalmologia.refresh()
                else:
                    ui.notify(f"Error: {msg}", color='red')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=procesar_y_guardar).props('flat').classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()


    def editar_examen_oftalmologico(self, examen):
        with ui.dialog().classes('w-full') as dialog, ui.card().style("width:80%; max-width:none;"):
            ui.label('Editar Examen Oftalmológico').classes(HEADER_TITLE_CLASSES)
            
            # Fecha input con valor inicial del examen
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

            # Campos comunes para ambos ojos con valores iniciales
            with ui.column().classes('gap-4 w-full'):
                with ui.row().classes('items-center gap-2'):
                    ui.label('Retinopatía Diabética').classes('text-lg font-bold text-blue-800')
                    retinopatia_diabetica = ui.select(
                        ['No', 'No Proliferativa', 'Proliferativa', 'No Precisada'], 
                        value=examen.retinopatia_diabetica
                    ).classes(INPUT_CLASSES+ ' w-64')
                with ui.row().classes('items-center gap-2'):
                    ui.label('Retinopatía Hipertensiva').classes('text-lg font-bold text-blue-800')
                    retinopatia_hipertensiva = ui.select(
                        ['No', 'Grado 1', 'Grado 2', 'Grado 3', 'Grado 4', 'No Precisada'], 
                        value=examen.retinopatia_hipertensiva
                    ).classes(INPUT_CLASSES+ ' w-64')
                with ui.row().classes('items-center gap-2'):
                    ui.label('Retinopatía Arterioesclerótica').classes('text-lg font-bold text-blue-800')
                    retinopatia_artereo_esclerosis = ui.select(
                        ['No', 'Grado 1', 'Grado 2', 'Grado 3', 'Grado 4', 'No Precisada'], 
                        value=examen.retinopatia_artereo_esclerosis
                    ).classes(INPUT_CLASSES+ ' w-64')

            # Contenedor principal
            with ui.element('div').classes('row q-col-gutter-lg w-full'):
                # Columna 1 - Ojo Izquierdo (OI)
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Ojo Izquierdo (OI)').classes('text-lg font-bold text-green-800')
                    
                    ui.label('Visión Borrosa').classes('text-lg font-bold text-blue-800')
                    vision_borrosa_oi = ui.select(['Si', 'No'], value=examen.vision_borrosa_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Agudeza Visual').classes('text-lg font-bold text-blue-800')
                    av_oi = self.input_clinico('Agudeza Visual', min_val=0, max_val=2, valor_inicial=examen.av_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Refracción Dinámica').classes('text-lg font-bold text-blue-800')
                    rd_oi = self.input_clinico('Refracción Dinámica', min_val=-30, max_val=30, valor_inicial=examen.rd_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Acomodación').classes('text-lg font-bold text-blue-800')
                    a_oi = self.input_clinico('Acomodación', min_val=0, max_val=20, valor_inicial=examen.a_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Sensibilidad al Contraste').classes('text-lg font-bold text-blue-800')
                    sa_oi = self.input_clinico('Sensibilidad al Contraste', min_val=0, max_val=2, valor_inicial=examen.sa_oi).classes(INPUT_CLASSES+ ' w-38')

                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Ojo Izquierdo (OI)').classes('text-lg font-bold text-green-800')

                    ui.label('Motilidad Ocular').classes('text-lg font-bold text-blue-800')
                    m_oi = self.input_clinico('Motilidad Ocular', min_val=-4, max_val=4, valor_inicial=examen.m_oi).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Fondo de Ojo').classes('text-lg font-bold text-blue-800')
                    fo_oi = self.input_clinico('Fondo de Ojo', min_val=0, max_val=10, valor_inicial=examen.fo_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Hemorragia Vítrea').classes('text-lg font-bold text-blue-800')
                    hemorragia_vitrea_oi = ui.select(['Si', 'No'], value=examen.hemorragia_vitrea_oi).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Maculopatía').classes('text-lg font-bold text-blue-800')
                    maculopatia_oi = ui.select(['Si', 'No'], value=examen.maculopatia_oi).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Catarata').classes('text-lg font-bold text-blue-800')
                    catarata_oi = ui.select(['Si', 'No'], value=examen.catarata_oi).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Glaucoma').classes('text-lg font-bold text-blue-800')
                    glaucoma_oi = ui.select(['Si', 'No'], value=examen.glaucoma_oi).classes(INPUT_CLASSES+ ' w-38')
                    
                # Columna 2 - Ojo Derecho (OD)
                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Ojo Derecho (OD)').classes('text-lg font-bold text-green-800')
                    
                    ui.label('Visión Borrosa').classes('text-lg font-bold text-blue-800')
                    vision_borrosa_od = ui.select(['Si', 'No'], value=examen.vision_borrosa_od).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Agudeza Visual').classes('text-lg font-bold text-blue-800')
                    av_od = self.input_clinico('Agudeza Visual', min_val=0, max_val=2, valor_inicial=examen.av_od).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Refracción Dinámica').classes('text-lg font-bold text-blue-800')
                    rd_od = self.input_clinico('Refracción Dinámica', min_val=-30, max_val=30, valor_inicial=examen.rd_od).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Acomodación').classes('text-lg font-bold text-blue-800')
                    a_od = self.input_clinico('Acomodación', min_val=0, max_val=20, valor_inicial=examen.a_od).classes(INPUT_CLASSES+ ' w-38')
                    
                    ui.label('Sensibilidad al Contraste').classes('text-lg font-bold text-blue-800')
                    sa_od = self.input_clinico('Sensibilidad al Contraste', min_val=0, max_val=2, valor_inicial=examen.sa_od).classes(INPUT_CLASSES+ ' w-38')

                with ui.element('div').classes('col-12 col-md-3'):
                    ui.label('Ojo Derecho (OD)').classes('text-lg font-bold text-green-800')

                    ui.label('Motilidad Ocular').classes('text-lg font-bold text-blue-800')
                    m_od = self.input_clinico('Motilidad Ocular', min_val=-4, max_val=4, valor_inicial=examen.m_od).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Fondo de Ojo').classes('text-lg font-bold text-blue-800')
                    fo_od = self.input_clinico('Fondo de Ojo', min_val=0, max_val=10, valor_inicial=examen.fo_od).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Hemorragia Vítrea').classes('text-lg font-bold text-blue-800')
                    hemorragia_vitrea_od = ui.select(['Si', 'No'], value=examen.hemorragia_vitrea_od).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Maculopatía').classes('text-lg font-bold text-blue-800')
                    maculopatia_od = ui.select(['Si', 'No'], value=examen.maculopatia_od).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Catarata').classes('text-lg font-bold text-blue-800')
                    catarata_od = ui.select(['Si', 'No'], value=examen.catarata_od).classes(INPUT_CLASSES+ ' w-38')
                    ui.label('Glaucoma').classes('text-lg font-bold text-blue-800')
                    glaucoma_od = ui.select(['Si', 'No'], value=examen.glaucoma_od).classes(INPUT_CLASSES+ ' w-38')

            def procesar_y_actualizar():
                datos_oftalmologia = {
                    'retinopatia_diabetica': retinopatia_diabetica.value,
                    'retinopatia_hipertensiva': retinopatia_hipertensiva.value,
                    'retinopatia_artereo_esclerosis': retinopatia_artereo_esclerosis.value,
                    'vision_borrosa_oi': vision_borrosa_oi.value,
                    'av_oi': av_oi.value,
                    'rd_oi': rd_oi.value,
                    'a_oi': a_oi.value,
                    'sa_oi': sa_oi.value,
                    'm_oi': m_oi.value,
                    'fo_oi': fo_oi.value,
                    'hemorragia_vitrea_oi': hemorragia_vitrea_oi.value,
                    'maculopatia_oi': maculopatia_oi.value,
                    'catarata_oi': catarata_oi.value,
                    'glaucoma_oi': glaucoma_oi.value,
                    'vision_borrosa_od': vision_borrosa_od.value,
                    'av_od': av_od.value,
                    'rd_od': rd_od.value,
                    'a_od': a_od.value,
                    'sa_od': sa_od.value,
                    'm_od': m_od.value,
                    'fo_od': fo_od.value,
                    'hemorragia_vitrea_od': hemorragia_vitrea_od.value,
                    'maculopatia_od': maculopatia_od.value,
                    'catarata_od': catarata_od.value,
                    'glaucoma_od': glaucoma_od.value,
                }

                # Envía el objeto a actualizar
                exito, msg = self.controlador_oftalmologia.actualizar_examen(
                    examen, 
                    fecha_input.value, 
                    **datos_oftalmologia
                )

                if exito:
                    ui.notify(msg, color='green')
                    dialog.close()
                    self.mostrar_oftalmologia.refresh()
                else:
                    ui.notify(f"Error: {msg}", color='red')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=procesar_y_actualizar).props('flat').classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

            dialog.open()


    def eliminar_examen_oftalmologico(self, examen):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar este examen?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self._confirmar_eliminacion_oftalmologia(examen, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()

    def _confirmar_eliminacion_oftalmologia(self, examen, dialog):
        exito, msg = self.controlador_oftalmologia.eliminar_examen(examen)
        if exito:
            ui.notify(msg, color='green')
            dialog.close()
            self.mostrar_oftalmologia.refresh()
        else:
            ui.notify(f"Error: {msg}", color='red')