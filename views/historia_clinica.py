from nicegui import ui,events
from datetime import datetime
from models import *
from sidebar import SidebarReutilizable
import locale
from authenticar import *
from Errores import log_error_and_notify
from exportar_hc import *
from sqlalchemy.exc import IntegrityError 
from seguridad_roles import requiere_permiso, tiene_permiso

from controllers.historia_clinica_controller import HistoriaClinicaController
from .historia_clinica_constants import (
    THEME,
    CARD_CLASSES,
    HC_CARD_PROFESSIONAL,
    HC_SECTION_CARD,
    INPUT_CLASSES,
    HEADER_TITLE_CLASSES,
    BASE_BUTTON_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    HEADER_NAV_BUTTON_CLASSES,
    HC_ICON_ACTION_BUTTON,
)
from .historia_clinica_paciente_mixin import HistoriaClinicaPacienteMixin
from .historia_clinica_indicaciones_mixin import HistoriaClinicaIndicacionesMixin
from .historia_clinica_apf_mixin import HistoriaClinicaApfMixin
from .historia_clinica_apf_diabetes_mixin import HistoriaClinicaApfDiabetesMixin
from .historia_clinica_ingresos_mixin import HistoriaClinicaIngresosMixin
from .historia_clinica_app_mixin import HistoriaClinicaAppMixin
from .historia_clinica_habitos_mixin import HistoriaClinicaHabitosMixin
from .historia_clinica_obstetrica_mixin import HistoriaClinicaObstetricaMixin
from .historia_clinica_tratamientos_mixin import HistoriaClinicaTratamientosMixin
from .historia_clinica_examenes_fisicos_mixin import HistoriaClinicaExamenesFisicosMixin
from .historia_clinica_mensuraciones_mixin import HistoriaClinicaMensuracionesMixin
from .historia_clinica_educacion_mixin import HistoriaClinicaEducacionMixin
from .historia_clinica_complementarios_mixin import HistoriaClinicaComplementariosMixin
from .historia_clinica_podologia_mixin import HistoriaClinicaPodologiaMixin
from .historia_clinica_oftalmologia_mixin import HistoriaClinicaOftalmologiaMixin
from .historia_clinica_nefrologia_mixin import HistoriaClinicaNefrologiaMixin
from .historia_clinica_estomatologia_mixin import HistoriaClinicaEstomatologiaMixin
from .historia_clinica_cardiologia_mixin import HistoriaClinicaCardiologiaMixin
from .citas import GAP_SM
from controllers.historia_clinica_tratamientos_controller import ControladorTratamientos
from controllers.controlador_examenes_fisicos import ControladorExamenesFisicos
# locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252') 

class HistoriaClinicaApp(
    HistoriaClinicaPacienteMixin,
    HistoriaClinicaIndicacionesMixin,
    HistoriaClinicaAppMixin,
    HistoriaClinicaApfMixin,
    HistoriaClinicaApfDiabetesMixin,
    HistoriaClinicaIngresosMixin,
    HistoriaClinicaHabitosMixin,
    HistoriaClinicaObstetricaMixin,
    HistoriaClinicaTratamientosMixin,
    HistoriaClinicaExamenesFisicosMixin,
    HistoriaClinicaMensuracionesMixin,
    HistoriaClinicaEducacionMixin,
    HistoriaClinicaComplementariosMixin,
    HistoriaClinicaPodologiaMixin,
    HistoriaClinicaOftalmologiaMixin,
    HistoriaClinicaNefrologiaMixin,
    HistoriaClinicaEstomatologiaMixin,
    HistoriaClinicaCardiologiaMixin,
):
    def __init__(self, no_hc):
        self.content_container = ui.column().classes('w-full ')
        self.ingresos_temporales = []
        self.edit_index = None
        self.tabs_cargadas = set()
        self.dict_paneles = {}
        
    

        try:
            
            self.no_hc = no_hc
            self.session = Session()
            
            self.controller = HistoriaClinicaController(self.session)
            self.controlador_tratamientos = ControladorTratamientos(self.session)
            self.controlador_examenes_fisicos = ControladorExamenesFisicos(self.session)
            usuario_actual = devolver_usuario_actual()
            inst_id = usuario_actual.get('institucion_id')
            self.paciente = self.controller.cargar_paciente_con_acceso(
                no_hc=no_hc,
                institucion_id_usuario=inst_id,
                es_superadmin=es_superadmin(),
            )
            
            if not self.paciente:
                # Si el paciente no se encuentra 
                ui.notify(f'Paciente {no_hc} no encontrado o acceso no autorizado.', type='negative')
                # Redirigir al listado para evitar que vean una página en blanco o error.
                ui.navigate.to('/principal')
                # No ejecutar el resto del init
                return

            # Mostrar nombre de institución del paciente ---
            self.institucion_nombre = ""
            try:
                inst_id_paciente = getattr(self.paciente, 'institucion_id', None)
                self.institucion_nombre = self.controller.obtener_nombre_institucion(inst_id_paciente)
            except Exception as e:
                log_error_and_notify(e, f'Error al obtener la institución del paciente {no_hc}')
                self.institucion_nombre = ""
            
        except Exception as e:
            # Capturar cualquier error de BD o lógica y l3oggearlo
            log_error_and_notify(e, f'Carga inicial HC {no_hc}')
            # Asegurar que la UI no se cargue con datos rotos
            ui.navigate.to('/principal') 
            return # Detener la ejecución del __init__
        
        self.sidebar = SidebarReutilizable(self)
        self.setup_sidebar()
        self.setup_layout()
        self.today = datetime.now().strftime('%Y/%m/%d')
        self.current_month = datetime.now().strftime('%Y/%m')
        # Lista de patologías
        self.patologias = [
                "Dislipoproteinemia",
                "Hipertension arterial",
                "Cardiopatía isquemica",
                "Enfermedad Arterial Periferica",
                "AVE",
                "No tiene",
                "Otros"
            ]

    def setup_sidebar(self):
        self.sidebar = self.sidebar.crear_sidebar()

    def setup_layout(self):
        with ui.header() \
                .classes('items-center justify-between q-px-md q-py-xs shadow-3') \
                .style('background: linear-gradient(135deg,#1565C0 0%,#0D47A1 100%);'
                       'position:sticky;top:0;z-index:2000;'):

            ui.add_head_html('''
                <style>
                    #c1 { padding-top: 0 !important; }
                    .cita-card-hover { transition: box-shadow .2s, transform .15s; }
                    .cita-card-hover:hover { box-shadow: 0 8px 24px rgba(21,101,192,.18) !important;
                                             transform: translateY(-2px); }
                    .stat-number { font-size: 2rem; font-weight: 800; line-height: 1; }
                    .timeline-dot::before {
                        content: '';
                        position: absolute; left: -7px; top: 50%;
                        transform: translateY(-50%);
                        width: 14px; height: 14px;
                        border-radius: 50%;
                        background: #1565C0;
                        border: 3px solid #fff;
                        box-shadow: 0 0 0 2px #1565C0;
                    }
                    .timeline-line {
                        border-left: 2px dashed #BBDEFB;
                        margin-left: 6px;
                    }
                </style>
            ''')

            # Izquierda
            with ui.row().classes('items-center no-wrap ' + GAP_SM):
                ui.button(icon='menu', on_click=self.sidebar.toggle) \
                    .props('flat round color=white size=sm')
                ui.button(icon='arrow_back', on_click=ui.navigate.back) \
                    .props('flat round color=white size=sm')
                with ui.row().classes('items-center no-wrap q-gutter-x-xs'):
                    ui.icon('').classes('text-white text-h5')
                    ui.label('Historia clìnica').classes('text-white text-h6 text-weight-bold gt-xs')

            # Derecha
            with ui.row().classes('items-center no-wrap ' + GAP_SM):
                with ui.column().classes('items-end q-mr-xs gt-xs'):
                    usuario = devolver_usuario_actual()
                    ui.label(usuario.get('username', '')).classes('text-white text-caption text-weight-bold')
                    ui.label(usuario.get('rol', '')).classes('text-blue-2 text-caption')
                ui.image('IMG/images.jpg') \
                    .classes('w-9 h-9 rounded-full border-2 border-white shadow-2')
                ui.button(icon='logout', on_click=cerrar_sesion) \
                    .props('round dense color=negative size=sm') \
                    .tooltip('Cerrar sesión')

    @ui.refreshable
    def mostrar_datos_generales(self):
        if not hasattr(self, 'paciente') or not self.paciente:
            return

        with self.content_container:

            from .ventana_informe import abrir_dialogo_informe

            ui.button(
                'Resumen HC',
                icon='summarize',
                on_click=lambda: abrir_dialogo_informe(self.no_hc),
            ).classes(
                'fixed right-3 sm:right-5 bottom-3 sm:bottom-6 z-50 '
                'bg-green-600 hover:bg-green-700 text-white '
                'font-semibold rounded-full shadow-2xl px-4 sm:px-5 py-2 sm:py-3'
            ).props('elevated')

            total_ingresos_diab = len(self.paciente.ingresos_diab) if self.paciente.ingresos_diab else 0

            with ui.card().classes(HC_CARD_PROFESSIONAL):
                with ui.row().classes('w-full justify-between items-start wrap q-col-gutter-md'):

                    # Información principal del paciente
                    with ui.row().classes('items-start gap-3 sm:gap-4 w-full md:w-auto min-w-0 flex-wrap md:flex-nowrap'):
                        # Avatar con estado
                        with ui.column().classes('items-center shrink-0'):
                            with ui.card().classes(HC_SECTION_CARD):
                                ui.icon("person", size='xl').classes(HC_ICON_ACTION_BUTTON)

                            estado_color = (
                                'green' if self.paciente.estado_actual_automatico == 'Ingresado'
                                else 'yellow' if self.paciente.estado_actual_automatico == 'No Ingresado'
                                else 'red'
                            )
                            ui.badge(
                                self.paciente.estado_actual_automatico,
                                color=estado_color
                            ).classes('mt-1 text-xs')

                        # Datos principales
                        with ui.column().classes('gap-1 min-w-0'):
                            ui.label(
                                f'{self.paciente.nombres} {self.paciente.apellidos}'
                            ).classes('text-lg sm:text-xl font-semibold text-gray-800 truncate')

                            if getattr(self, 'institucion_nombre', None):
                                with ui.row().classes('items-center gap-2 mt-1 hidden sm:flex min-w-0'):
                                    ui.icon('business').classes(HC_ICON_ACTION_BUTTON + ' text-sm')
                                    ui.label(self.institucion_nombre).classes(
                                        'text-sm text-indigo-600 font-medium truncate'
                                    )

                            with ui.row().classes('items-center gap-3 sm:gap-4 text-xs sm:text-sm text-gray-600 flex-wrap'):
                                ui.label(f'HC: {self.paciente.no_hc}').classes('font-medium')
                                ui.label(f'CI: {self.paciente.ci}').classes('font-medium')
                                ui.label(f'{self.paciente.edad_actual} años').classes('font-medium')

                    # Botones de acción
                    with ui.row().classes('items-center gap-2 justify-start md:justify-end w-full md:w-auto flex-wrap'):
                        if tiene_permiso('export_data'):
                            ui.button(
                                "",
                                icon='print',
                                on_click=lambda: mostrar_interfaz_exportacion(self.no_hc)
                            ).classes(
                                HC_ICON_ACTION_BUTTON + ' px-3 py-2 rounded-lg'
                            ).tooltip('Imprimir Historia Clínica')

                        if tiene_permiso('pacientes_edit'):
                            ui.button(
                                '',
                                icon='edit',
                                on_click=lambda: self.editar_datos_paciente()
                            ).classes(
                                HC_ICON_ACTION_BUTTON + ' text-blue-700 px-3 py-2 rounded-lg'
                            ).tooltip('Editar Datos del Paciente')

                        if not self.paciente.activo:
                            ui.button(
                                icon='unarchive',
                                on_click=lambda: self.toggle_estado_paciente(self.paciente)
                            ).props('color=green').tooltip('Reactivar Paciente')
                        else:
                            ui.button(
                                icon='archive',
                                on_click=lambda: self.confirmar_desactivacion(self.paciente)
                            ).props('flat color=grey').tooltip('Archivar Paciente (Soft Delete)')

                        if tiene_permiso('pacientes_delete'):
                            ui.button(
                                icon='delete',
                                on_click=lambda: self.confirmar_eliminacion()
                            ).props('flat color=red').tooltip('Eliminar Paciente (Borrado Permanente)')

                # Información rápida
                with ui.row().classes('w-full mt-4 pt-4 border-t border-gray-100'):
                    with ui.grid(columns=6).classes('w-full gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6'):
                        self._create_simple_info_item('wc', 'Sexo', self.paciente.sexo)
                        self._create_simple_info_item('location_on', 'Área', self.paciente.area_salud)
                        self._create_simple_info_item('bloodtype', 'Diabetes', f'{self.paciente.tiempo_evolucion}')
                        self._create_simple_info_item('event', 'Fecha HC', self.paciente.fecha_hc.strftime("%d/%m/%Y"))
                        self._create_simple_info_item('work', 'Ocupación', self.paciente.ocupacion)
                        self._create_simple_info_item('contacts', "Nombre de Contacto de Emergencia", self.paciente.nombre_contacto_emergencia)
                        self._create_simple_info_item('phone', "Teléfono de Emergencia", self.paciente.tel_emergencia)
                        

            # Grid principal con 2 columnas
            with ui.grid(columns=2).classes('gap-6 w-full grid-cols-1 lg:grid-cols-2'):
                # Columna 1: Datos Personales y Demográficos
                with ui.column().classes('space-y-4 w-full min-w-0'):
                    # Datos Personales
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.icon('person', size='md').classes(HC_ICON_ACTION_BUTTON)
                            ui.label('Datos Personales').classes(HEADER_TITLE_CLASSES)

                        with ui.grid(columns=2).classes('gap-4 grid-cols-1 sm:grid-cols-2'):
                            self._create_clean_info_item('Edad', f'{self.paciente.edad_actual} años', 'elderly')
                            self._create_clean_info_item('Sexo', self.paciente.sexo, 'wc')
                            self._create_clean_info_item('Color de Piel', self.paciente.color_piel, 'diversity_3')
                            self._create_clean_info_item('Estado Civil', self.paciente.estado_civil, 'favorite')
                            self._create_clean_info_item('Nivel Educacional', self.paciente.escolaridad, 'school')
                            self._create_clean_info_item('Ocupación', self.paciente.ocupacion, 'work')

                    # Contacto y Ubicación
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.icon('location_on', size='md').classes(HC_ICON_ACTION_BUTTON)
                            ui.label('Contacto y Ubicación').classes(HEADER_TITLE_CLASSES)

                        with ui.grid(columns=2).classes('gap-4 grid-cols-1 sm:grid-cols-2'):
                            self._create_clean_info_item('Teléfono', self.paciente.telefono, 'phone')
                            self._create_clean_info_item('Nombre Contacto Emergencia', self.paciente.nombre_contacto_emergencia, 'contacts')
                            self._create_clean_info_item("Teléfono de Emergencia", self.paciente.tel_emergencia, 'phone')
                            self._create_clean_info_item('Dirección', f'{self.paciente.calle} No. {self.paciente.numero}', 'home')
                            self._create_clean_info_item('Entre calles', self.paciente.entre_calles, 'map')
                            self._create_clean_info_item('Municipio', self.paciente.municipio, 'location_city')
                            self._create_clean_info_item('Provincia', self.paciente.provincia, 'public')
                            self._create_clean_info_item('Área de Salud', self.paciente.area_salud, 'medical_services')

                # Columna 2: Datos Médicos
                with ui.column().classes('space-y-4 w-full min-w-0'):
                    # Datos de la Diabetes
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.icon('bloodtype', size='md').classes(HC_ICON_ACTION_BUTTON)
                            ui.label('Datos de la Diabetes').classes(HEADER_TITLE_CLASSES)

                        with ui.grid(columns=2).classes('gap-4 grid-cols-1 sm:grid-cols-2'):
                            self._create_clean_info_item('Tiempo Evolución', f'{self.paciente.tiempo_evolucion}', 'schedule')
                            self._create_clean_info_item('Forma de Presentación del Diagnóstico', self.paciente.forma_presentacion_diagnostico, 'emergency')
                            self._create_clean_info_item('Glucemia al Diagnóstico', f'{self.paciente.glucemia_debut} mmol/L', 'monitor_heart')
                            self._create_clean_info_item('Exceso de Peso al Diagnóstico', self.paciente.exceso_peso_diagnostico, 'fitness_center')
                            self._create_clean_info_item('Remisión', self.paciente.remision, 'healing')

                            if self.paciente.exceso_peso_diagnostico == 'Si':
                                self._create_clean_info_item(
                                    'Tiempo de Exceso de Peso',
                                    f'{self.paciente.tiempo_exceso_peso_anios} años , {self.paciente.tiempo_exceso_peso_meses} meses',
                                    'schedule'
                                )

                           
                            # 1. Extraer el esquema de medicamentos de forma retrocompatible (Solo si existen datos)
                            medicamentos_iniciales = []

                            if self.paciente.tratamiento_inicial_json and len(self.paciente.tratamiento_inicial_json) > 0:
                                # Formato nuevo (JSON)
                                medicamentos_iniciales = self.paciente.tratamiento_inicial_json
                            elif self.paciente.tratamiento_inicial and self.paciente.tratamiento_inicial.strip() and self.paciente.tratamiento_inicial != 'Ver esquema dinámico':
                                # Formato antiguo (Se procesa SOLO si contiene un texto real y válido)
                                texto_antiguo = self.paciente.tratamiento_inicial.strip()
                                dosis_antigua = self.paciente.dosis_tratamiento or "No especificada"
                                anio_antiguo = self.paciente.ano_inicio_tratamiento or "No especificado"
                                
                                if '+' in texto_antiguo:
                                    partes = [p.strip() for p in texto_antiguo.split('+')]
                                    for p in partes:
                                        if p: 
                                            medicamentos_iniciales.append({
                                                'tratamiento': p,
                                                'dosis': dosis_antigua,
                                                'anio_inicio': anio_antiguo
                                            })
                                else:
                                    medicamentos_iniciales.append({
                                        'tratamiento': texto_antiguo,
                                        'dosis': dosis_antigua,
                                        'anio_inicio': anio_antiguo
                                    })

                            # 2. Renderizar la visualización de forma compacta (Una sola línea por fármaco)
                            if not medicamentos_iniciales:
                                self._create_clean_info_item('Tratamiento Inicial', 'No registrado', 'medication')
                            else:
                                for idx, med in enumerate(medicamentos_iniciales):
                                    nombre_med = med.get('tratamiento', 'No registrado')
                                    
                                    # Si el fármaco requiere detalles, lo unificamos horizontalmente de forma elegante
                                    if nombre_med != 'Tratamiento No Farmacologico':
                                        dosis_val = med.get('dosis', 'No especificada')
                                        anio_val = med.get('anio_inicio', 'No especificado')
                                        # Formato compacto: "Metformina (Dosis: 500mg | Año: 2021)"
                                        valor_compacto = f"{nombre_med} (Dosis: {dosis_val} | Año: {anio_val})"
                                    else:
                                        valor_compacto = nombre_med

                                    # Título dinámico si hay más de uno
                                    label_tratamiento = f"Fármaco Inicial #{idx + 1}" if len(medicamentos_iniciales) > 1 else "Tratamiento Inicial"
                                    
                                    # Renderiza todo en una única fila limpia
                                    self._create_clean_info_item(label_tratamiento, valor_compacto, 'medication')

                            self._create_clean_info_item('¿Prediabetes?', self.paciente.prediabetes, 'help_outline')

                            if self.paciente.prediabetes == 'Si':
                                self._create_clean_info_item(
                                    'Tiempo de Prediabetes',
                                    f'{self.paciente.tiempo_prediabetes_anios} años , {self.paciente.tiempo_prediabetes_meses} meses',
                                    'schedule'
                                )

                    # Estado Actual
                    with ui.card().classes(HC_SECTION_CARD):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.icon('monitor_heart', size='md').classes(HC_ICON_ACTION_BUTTON)
                            ui.label('Estado Actual').classes(HEADER_TITLE_CLASSES)

                        with ui.grid(columns=2).classes('gap-4 grid-cols-1 sm:grid-cols-2'):
                            with ui.row().classes('items-center gap-2 flex-wrap'):
                                ui.icon('favorite').classes('text-red-500')
                                ui.label('Estado').classes('text-gray-700 font-medium')
                                ui.badge(
                                    self.paciente.estado_actual_automatico,
                                    color='green' if self.paciente.estado_actual_automatico == 'Activo' else 'yellow'
                                ).classes('text-xs')

                            if self.paciente.estado_actual_automatico == 'Defunción':
                                self._create_clean_info_item('Causa de Defunción', self.paciente.causa_fallecimiento, 'help_outline')

                            self._create_clean_info_item('Fecha HC', self.paciente.fecha_hc.strftime("%d/%m/%Y"), 'event')

                if self.paciente.ingresos_diab:
                    with ui.column().classes('w-full mt-3'):
                        with ui.card().classes(HC_SECTION_CARD + ' w-full'):
                            with ui.row().classes('items-center justify-between w-full mb-4 flex-wrap gap-2'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('assignment_ind', size='md').classes(HC_ICON_ACTION_BUTTON)
                                    ui.label('Historial de Ingresos Diabetológicos').classes(HEADER_TITLE_CLASSES)

                                with ui.row().classes('items-center gap-2 bg-indigo-50 px-3 py-1 rounded-full'):
                                    ui.label('Total de Ingresos:').classes('text-sm text-indigo-700 font-medium')
                                    ui.badge(str(total_ingresos_diab), color='indigo').classes('text-sm px-2')

                            if total_ingresos_diab == 0:
                                with ui.row().classes('w-full justify-center p-8 border-2 border-dashed border-gray-200 rounded-xl'):
                                    ui.label('No se registran ingresos diabetológicos previos').classes('text-gray-400 italic')
                            else:
                                columnas = [
                                    {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'sortable': True, 'align': 'left'},
                                    {'name': 'motivo', 'label': 'Motivo', 'field': 'motivo', 'align': 'left'},
                                ]

                                filas = []
                                ingresos_ordenados = sorted(
                                    self.paciente.ingresos_diab,
                                    key=lambda x: x.fecha_ingreso or x.id,
                                    reverse=True
                                )

                                for ing in ingresos_ordenados:
                                    filas.append({
                                        'fecha': ing.fecha_ingreso.strftime('%d/%m/%Y') if ing.fecha_ingreso else 'S/F',
                                        'motivo': ing.motivo,
                                    })

                                ui.table(columns=columnas, rows=filas, row_key='fecha').classes('w-full shadow-none border-none')

            # Tabs
            with ui.card().classes(HC_CARD_PROFESSIONAL):
                # Añadimos el evento on_change a los tabs
                with ui.tabs(on_change=lambda e: self.manejar_cambio_tab(e.value)).classes('w-full overflow-x-auto p-2 flex-nowrap') as tabs:
                    tabs_list = [
                        ('Panel Clínico', 'assignment', self.mostrar_panel_paciente),
                        ('Ingresos', 'medication', self.mostrar_ingresos),
                        ('Indicaciones', 'summarize', self.indicaciones),
                        ('APP', 'medical_services', self.mostrar_antecedentes_personales),
                        ('APF', 'family_restroom', self.mostrar_antecedentes_familiares),
                        ('APF Diabetes', 'bloodtype', self.mostrar_apf_diabetes),
                        ('Hábitos Tóxicos', 'smoking_rooms', self.mostrar_habitos_toxicos),
                        ('Historia Obstétrica', 'pregnant_woman', self.mostrar_historia_obstetrica),
                        ('Tratamientos', 'medication', self.mostrar_tratamientos),
                        ('Exámenes Físicos', 'assignment', self.mostrar_examenes_fisicos),
                        ('Evaluación Nutricional y Mensuraciones', 'straighten', self.mostrar_mensuraciones),
                        ('Educación Diabética', 'school', self.mostrar_educacion_diabetica),
                        ('Complementarios', 'science', self.mostrar_complementarios),
                        ('Exámenes Miembros Inferiores', 'podiatry', self.mostrar_examenes_podologicos),
                        ('Oftalmología', 'remove_red_eye', self.mostrar_oftalmologia),
                        ('Nefrología', 'urology', self.mostrar_nefrologia),
                        ('Estomatologia', 'dentistry', self.mostrar_estomatologia),
                        ('Cardiología', 'monitor_heart', self.mostrar_cardiologia),
                    ]

                    for tab_name, icon_name, _ in tabs_list:
                        with ui.tab(tab_name).classes('flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors hover:bg-gray-50 hover:text-blue-600'):
                            ui.icon(icon_name, size='sm')

                # Aquí está el cambio clave:
                with ui.tab_panels(tabs, value=tabs.value).classes('w-full') as self.contenedor_principal:
                    for tab_name, _, tab_function in tabs_list:
                        # Creamos el panel vacío y lo guardamos en un diccionario con su función
                        self.dict_paneles[tab_name] = {
                            'panel': ui.tab_panel(tab_name),
                            'funcion': tab_function
                        }

                # Cargamos la primera pestaña manualmente al inicio (ej. Panel Clínico)
                self.manejar_cambio_tab(tabs.value)
    def manejar_cambio_tab(self, nombre_tab):
        # Si la pestaña no se ha cargado antes
        if nombre_tab not in self.tabs_cargadas:
            info = self.dict_paneles.get(nombre_tab)
            if info:
                # Usamos el panel correspondiente como contexto para renderizar la UI
                with info['panel']:
                    info['funcion']()
                
                # Marcamos como cargada para no repetir la consulta/renderizado
                self.tabs_cargadas.add(nombre_tab)

    def _create_simple_info_item(self, icon_name, label, value):
        with ui.column().classes('items-center text-center gap-1'):
            ui.icon(icon_name, size='sm').classes('text-gray-500')
            ui.label(label).classes('text-xs font-medium text-gray-600')
            ui.label(value).classes('text-sm font-semibold text-gray-800')

    def _create_clean_info_item(self, label, value, icon_name):
        with ui.row().classes('items-center justify-between p-3 bg-gray-50 rounded-lg'):
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon_name, size='sm').classes('text-gray-500')
                ui.label(label).classes('text-sm font-medium text-gray-700')
            ui.label(value).classes('text-sm font-semibold text-gray-800')

    def editar_datos_paciente(self):
            today         = datetime.now().strftime('%Y/%m/%d')
            current_month = datetime.now().strftime('%Y/%m')

            paciente = self.paciente
            if not paciente:
                ui.notify('No se encontró el paciente', type='negative')
                return

            self.original_hc = paciente.no_hc

            # Variables condicionales
            self.mostrar_campo_otros = paciente.forma_presentacion_diagnostico not in [
                'Sintomas Clinicos', 'Asintomatico', 'Cetoacidosis(Probada)',
                'Durante el embarazo', 'Complicaciones asociadas'
            ]
            self.mostrar_campo_otros_tratamiento = paciente.tratamiento_inicial not in [
                'Tratamiento No Farmacologico', 'SUR', 'Metformina', 'Insulina',
                'Insulina + SUR', 'Insulina + Metformina', 'SUR + Metformina'
            ]

            # Cargar instituciones
            instituciones_db        = self.session.query(Institucion).all()
            self.mapa_instituciones = {inst.nombre: inst.id for inst in instituciones_db}
            opciones_instituciones  = list(self.mapa_instituciones.keys())
            nombre_institucion_actual = self.session.query(Institucion.nombre).filter(
                Institucion.id == paciente.institucion_id
            ).scalar()

            # Cargar provincias
            provincias_db      = self.session.query(Provincia).all()
            opciones_provincias = [p.nombre for p in provincias_db]

            # Pre-cargar municipios
            opciones_municipios = []
            if paciente.provincia:
                prov = self.session.query(Provincia).filter_by(nombre=paciente.provincia).first()
                if prov:
                    opciones_municipios = [m.nombre for m in prov.municipios]

            # Pre-cargar áreas
            opciones_areas = []
            if paciente.municipio and paciente.provincia:
                muni = self.session.query(Municipio).join(Provincia).filter(
                    Municipio.nombre == paciente.municipio,
                    Provincia.nombre == paciente.provincia
                ).first()
                if muni:
                    opciones_areas = [a.nombre for a in muni.areas_salud]

            # ── Valores condicionales ─────────────────────────────────────────────
            forma_valor     = ('Otros' if self.mostrar_campo_otros
                            else paciente.forma_presentacion_diagnostico)
            tratam_valor    = ('Otros' if self.mostrar_campo_otros_tratamiento
                            else paciente.tratamiento_inicial)

            # ── Diálogo ───────────────────────────────────────────────────────────
            with ui.dialog().props('maximized') as self.dialog_editar, \
                ui.card().classes('w-full h-full overflow-y-auto rounded-none shadow-none'):

                # Encabezado sticky
                with ui.element('div').classes(
                    'row items-center justify-between '
                    'bg-blue-800 text-white q-px-md q-py-sm '
                    'sticky top-0 z-10'
                ):
                    ui.label(
                        f'Editar: {paciente.nombres} {paciente.apellidos}'
                    ).classes('text-lg text-white font-bold')
                    ui.button(icon='close', on_click=self.dialog_editar.close)\
                        .props('flat round dense').classes('text-white')

                # ── Cuerpo ────────────────────────────────────────────────────────
                with ui.element('div').classes('q-pa-md'):

                    # ══ Identificación ════════════════════════════════════════════
                    self._seccion_titulo('Identificación y Datos Generales')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.no_hc_input = ui.input(
                                'Número HC', value=paciente.no_hc
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.ci_input = ui.input(
                                'Carnet de Identidad', value=paciente.ci
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.nombres_input = ui.input(
                                'Nombres', value=paciente.nombres
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.apellidos_input = ui.input(
                                'Apellidos', value=paciente.apellidos
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.institucion_input = ui.select(
                                options=opciones_instituciones,
                                label='Institución del Paciente',
                                value=nombre_institucion_actual,
                                with_input=True,
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            fecha_val = (paciente.fecha_hc.strftime('%Y-%m-%d')
                                        if paciente.fecha_hc else '')
                            with ui.input(
                                'Fecha de Historia Clínica', value=fecha_val
                            ).classes(INPUT_CLASSES) as self.fecha_hc_input:
                                with ui.menu().props('no-parent-event') as menu_hc:
                                    ui.date().bind_value(self.fecha_hc_input).props(
                                        f'locale="es" '
                                        f'default-year-month={current_month} '
                                        f':options="date => date <= \'{today}\'"'
                                    )
                                    with ui.row().classes('justify-end px-4 py-2'):
                                        ui.button('Cerrar', on_click=menu_hc.close)\
                                            .props('flat color="error"')
                                with self.fecha_hc_input.add_slot('append'):
                                    ui.icon('edit_calendar')\
                                        .on('click', menu_hc.open)\
                                        .classes('cursor-pointer text-gray-500')

                        # Tiempo de evolución
                        with ui.element('div').classes('col-12'):
                            with ui.element('div').classes('row q-col-gutter-sm items-center'):
                                with ui.element('div').classes('col-12'):
                                    ui.label('Tiempo de Evolución al Ingreso')\
                                        .classes('text-xs text-blue-600 font-bold uppercase')
                                    ui.label(
                                        'Ingrese el tiempo al momento de crear la HC. '
                                        'El sistema suma el tiempo transcurrido automáticamente.'
                                    ).classes('text-xs text-blue-400 italic')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_evolucion_anios = self.input_clinico(
                                        'Años', min_val=0, max_val=100,
                                        valor_inicial=paciente.tiempo_evolucion_anios
                                    ).classes(INPUT_CLASSES).props('dense')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_evolucion_meses = self.input_clinico(
                                        'Meses', min_val=0, max_val=11,
                                        valor_inicial=paciente.tiempo_evolucion_meses
                                    ).classes(INPUT_CLASSES).props('dense')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_evolucion_dias = self.input_clinico(
                                        'Días', min_val=0, max_val=30,
                                        valor_inicial=paciente.tiempo_evolucion_dias
                                    ).classes(INPUT_CLASSES).props('dense')

                    # ══ Dirección ═════════════════════════════════════════════════
                    self._seccion_titulo('Dirección')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.calle_input = ui.input(
                                'Calle', value=paciente.calle
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-2'):
                            self.numero_input = ui.input(
                                'No. / Apto', value=paciente.numero
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-6'):
                            self.entre_calles_input = ui.input(
                                'Entre Calles', value=paciente.entre_calles
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.provincia_input = ui.select(
                                options=opciones_provincias,
                                label='Provincia',
                                value=paciente.provincia,
                                on_change=lambda e: self.actualizar_municipios_edicion()
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.municipio_input = ui.select(
                                options=opciones_municipios,
                                label='Municipio',
                                value=paciente.municipio,
                                on_change=lambda e: self.actualizar_areas_edicion()
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.area_salud_input = ui.select(
                                options=opciones_areas,
                                label='Área de Salud',
                                value=paciente.area_salud
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.telefono_input = ui.input(
                                'Teléfono', value=paciente.telefono
                            ).classes(INPUT_CLASSES)
                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.nombre_contacto_emergencia = ui.input('Nombre de Contacto de Emergencia', value=paciente.nombre_contacto_emergencia).classes(INPUT_CLASSES)
                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.tel_emergencia = ui.input(
                                'Teléfono de Emergencia', value=paciente.tel_emergencia
                            ).classes(INPUT_CLASSES)

                    # ══ Datos Personales ══════════════════════════════════════════
                    self._seccion_titulo('Datos Personales')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.sexo_input = ui.select(
                                options=['Masculino', 'Femenino', ''],
                                label='Sexo', value=paciente.sexo
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.color_piel = ui.select(
                                ['Negro', 'Blanco', 'Mestizo'],
                                label='Color de Piel', value=paciente.color_piel
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.escolaridad_input = ui.select(
                                ['6to Grado', '9no Grado', '12mo Grado',
                                'Universitario', 'No especificado', ''],
                                label='Nivel Educacional', with_input=True,
                                value=paciente.escolaridad
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.estado_civil_input = ui.select(
                                ['Acompañado', 'No acompañado', ''],
                                label='Estado Civil', value=paciente.estado_civil
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-6'):
                            self.ocupacion_input = ui.select(
                                ['Estudiante',
                                'Con vínculo laboral: Trabajador Estatal',
                                'Con vínculo laboral: Trabajador No Estatal',
                                'Sin vínculo laboral', ''],
                                label='Ocupación', value=paciente.ocupacion
                            ).classes(INPUT_CLASSES)

                    # ══ Datos Clínicos ════════════════════════════════════════════
                    self._seccion_titulo('Datos Clínicos del Diagnóstico')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.forma_presentacion_diagnostico_input = ui.select(
                                ['Sintomas Clinicos', 'Asintomatico',
                                'Cetoacidosis(Probada)', 'Durante el embarazo',
                                'Complicaciones asociadas', 'Otros', ''],
                                label='Forma de Presentación al Diagnóstico',
                                value=forma_valor,
                                on_change=lambda e: self.actualizar_campo_otros()
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4')\
                                .bind_visibility_from(self, 'mostrar_campo_otros'):
                            self.otros_forma_presentacion_diagnostico_input = ui.input(
                                'Especificar otra forma de presentación',
                                value=(paciente.forma_presentacion_diagnostico
                                    if self.mostrar_campo_otros else '')
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                            self.glucemia_debut_input = self.input_clinico(
                                'Glucemia al Diagnóstico (mmol/L)', min_val=2, max_val=40,
                                valor_inicial=(float(paciente.glucemia_debut)
                                            if paciente.glucemia_debut else None)
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.exceso_peso_diagnostico = ui.select(
                                ['Si', 'No', 'No Precisado', ''],
                                label='Exceso de Peso al Diagnóstico',
                                value=paciente.exceso_peso_diagnostico
                            ).classes(INPUT_CLASSES)

                        # Tiempo exceso de peso — visible si "Si"
                        with ui.element('div').classes('col-12')\
                                .bind_visibility_from(
                                    self.exceso_peso_diagnostico, 'value',
                                    backward=lambda v: v == 'Si'
                                ):
                            with ui.element('div').classes('row q-col-gutter-sm items-center'):
                                with ui.element('div').classes('col-12'):
                                    ui.label('Tiempo de exceso de peso:')\
                                        .classes('text-xs text-blue-600 font-bold uppercase')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_exceso_peso_anios = ui.number(
                                        'Años', min=0,
                                        value=paciente.tiempo_exceso_peso_anios
                                    ).classes(INPUT_CLASSES).props('dense')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_exceso_peso_meses = ui.number(
                                        'Meses', min=0, max=11,
                                        value=paciente.tiempo_exceso_peso_meses
                                    ).classes(INPUT_CLASSES).props('dense')

                        with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                            self.remision_input = ui.select(
                                ['CMD APS', 'Hospital', 'Espontaneamente', ''],
                                label='Remisión', value=paciente.remision
                            ).classes(INPUT_CLASSES)

                   # ══ Tratamiento Inicial ═══════════════════════════════════════
                    self._seccion_titulo('Tratamiento Inicial')

                    # --- BLOQUE DE RETROCOMPATIBILIDAD ---
                    # Inicializamos la lista en memoria con los datos existentes del paciente
                    self.esquema_inicial_temporal = []
                    
                    if paciente.tratamiento_inicial_json and len(paciente.tratamiento_inicial_json) > 0:
                        # Si ya tiene el nuevo formato JSON guardado
                        self.esquema_inicial_temporal = list(paciente.tratamiento_inicial_json)
                    elif paciente.tratamiento_inicial and paciente.tratamiento_inicial != 'Ver esquema dinámico':
                        # Si es un registro viejo plano o compuesto (ej: 'SUR + Metformina')
                        texto_antiguo = paciente.tratamiento_inicial
                        dosis_antigua = paciente.dosis_tratamiento or "No especificada"
                        anio_antiguo = paciente.ano_inicio_tratamiento or "No especificado"

                        if '+' in texto_antiguo:
                            partes = [p.strip() for p in texto_antiguo.split('+')]
                            for p in partes:
                                if p:
                                    self.esquema_inicial_temporal.append({
                                        'tratamiento': p,
                                        'dosis': f"{dosis_antigua} (Migrado)",
                                        'anio_inicio': anio_antiguo
                                    })
                        else:
                            self.esquema_inicial_temporal.append({
                                'tratamiento': texto_antiguo,
                                'dosis': dosis_antigua,
                                'anio_inicio': anio_antiguo
                            })

                    # --- INTERFAZ VISUAL DINÁMICA ---
                    with ui.card().classes('w-full border border-dashed border-blue-200 q-pa-sm'):
                        
                        # Contenedor reactivo que dibuja los fármacos que están en la lista actual
                        @ui.refreshable
                        def mostrar_lista_tratamiento_inicial_edicion():
                            with ui.column().classes('w-full gap-2 mb-4'):
                                if not self.esquema_inicial_temporal:
                                    ui.label('No hay medicamentos registrados en el tratamiento inicial.').classes('text-xs italic text-slate-400')
                                else:
                                    for index, item in enumerate(self.esquema_inicial_temporal):
                                        with ui.row().classes('w-full items-center justify-between p-2 bg-green-50 rounded-lg border border-green-100'):
                                            with ui.column().classes('gap-0'):
                                                ui.label(f"Fármaco: {item['tratamiento']}").classes('text-sm font-bold text-green-800')
                                                ui.label(f"Dosis: {item['dosis']} | Año de Inicio: {item['anio_inicio']}").classes('text-[11px] text-slate-600')
                                            ui.button(icon='delete', on_click=lambda i=index: eliminar_farmaco_inicial_edicion(i)).props('flat round dense color="red"').classes('hover:bg-red-100')

                        def eliminar_farmaco_inicial_edicion(index):
                            self.esquema_inicial_temporal.pop(index)
                            mostrar_lista_tratamiento_inicial_edicion.refresh()

                        # Primer render de la lista precargada
                        mostrar_lista_tratamiento_inicial_edicion()

                        # Inputs para agregar nuevos fármacos al esquema durante la edición
                        with ui.element('div').classes('row q-col-gutter-sm items-end q-mt-sm'):
                            with ui.element('div').classes('col-12 col-sm-4 col-md-4'):
                                farmaco_sel = ui.select(
                                    ['Tratamiento No Farmacologico', 'SUR', 'Metformina', 'Insulina', 'Otros'], 
                                    label='Añadir Medicamento / Terapia'
                                ).classes(INPUT_CLASSES)
                            
                            with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                                dosis_sel_input = ui.input('Dosis').classes(INPUT_CLASSES).props('dense')
                            
                            with ui.element('div').classes('col-12 col-sm-4 col-md-2'):
                                anio_sel_input = ui.number('Año de inicio', min=1950, max=datetime.now().year).classes(INPUT_CLASSES).props('dense')
                            
                            with ui.element('div').classes('col-12').bind_visibility_from(farmaco_sel, 'value', backward=lambda v: v == 'Otros'):
                                otro_farmaco_input = ui.input('Especificar otro medicamento...').classes('w-full ' + INPUT_CLASSES)

                            def añadir_farmaco_a_inicial_edicion():
                                nombre_farmaco = farmaco_sel.value
                                if nombre_farmaco == 'Otros':
                                    nombre_farmaco = otro_farmaco_input.value

                                if nombre_farmaco:
                                    self.esquema_inicial_temporal.append({
                                        'tratamiento': nombre_farmaco,
                                        'dosis': dosis_sel_input.value or "No especificada",
                                        'anio_inicio': int(anio_sel_input.value) if anio_sel_input.value else "No especificado"
                                    })
                                    # Resetear inputs auxiliares
                                    farmaco_sel.set_value(None)
                                    dosis_sel_input.set_value(None)
                                    anio_sel_input.set_value(None)
                                    if 'otro_farmaco_input' in locals() or 'otro_farmaco_input' in globals():
                                        otro_farmaco_input.set_value(None)
                                    
                                    mostrar_lista_tratamiento_inicial_edicion.refresh()
                                else:
                                    ui.notify('Seleccione o especifique un medicamento', type='warning')

                            with ui.element('divs').classes('col-12 col-sm-auto'):
                                ui.button('Añadir al esquema', icon='add', on_click=añadir_farmaco_a_inicial_edicion).classes(SUCCESS_BUTTON_CLASSES)

                    # ══ Prediabetes ═══════════════════════════════════════════════
                    self._seccion_titulo('Prediabetes')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                            self.prediabetes_input = ui.select(
                                ['Si', 'No', 'No Precisado', ''],
                                label='¿Prediabetes?', value=paciente.prediabetes
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12')\
                                .bind_visibility_from(
                                    self.prediabetes_input, 'value',
                                    backward=lambda v: v == 'Si'
                                ):
                            with ui.element('div').classes('row q-col-gutter-sm items-center'):
                                with ui.element('div').classes('col-12'):
                                    ui.label('Tiempo de Prediabetes')\
                                        .classes('text-xs text-blue-600 font-bold uppercase')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_prediabetes_anios = ui.number(
                                        'Años', min=0,
                                        value=paciente.tiempo_prediabetes_anios
                                    ).classes(INPUT_CLASSES).props('dense')
                                with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                    self.tiempo_prediabetes_meses = ui.number(
                                        'Meses', min=0, max=11,
                                        value=paciente.tiempo_prediabetes_meses
                                    ).classes(INPUT_CLASSES).props('dense')

                    # ══ Estado del Paciente ═══════════════════════════════════════
                    self._seccion_titulo('Estado del Paciente')

                    with ui.element('div').classes('row q-col-gutter-md'):

                        with ui.element('div').classes('col-12'):
                            self.estado_actual_input = ui.checkbox(
                                'Defunción',
                                value=(paciente.estado_actual == 'Defunción')
                            ).classes(INPUT_CLASSES)

                        with ui.element('div').classes('col-12 col-md-8')\
                                .bind_visibility_from(self.estado_actual_input, 'value'):
                            ui.label('Detalles del Fallecimiento:')\
                                .classes('text-xs text-red-700 font-bold uppercase q-mb-xs')
                            self.causa_fallecimiento_input = ui.textarea(
                                'Causa de la defunción',
                                value=paciente.causa_fallecimiento
                            ).classes(INPUT_CLASSES + ' bg-red-50')\
                            .props('outlined clearable placeholder="Escriba la causa clínica..."')

                    # ══ Ingresos por Diabetes ═════════════════════════════════════
                    self._seccion_titulo('Ingresos por Diabetes')

                    with ui.card().classes(
                        'w-full border border-dashed border-blue-200 q-pa-sm'
                    ):
                        ui.label('INGRESOS POR DIABETES')\
                            .classes('text-xs font-black text-blue-600 q-mb-sm')

                        # Cargar ingresos existentes
                        self.ingresos_temporales = []
                        if self.paciente.ingresos_diab:
                            for ing in self.paciente.ingresos_diab:
                                self.ingresos_temporales.append({
                                    'motivo': ing.motivo,
                                    'fecha': (ing.fecha_ingreso.strftime('%Y-%m-%d')
                                            if ing.fecha_ingreso else ''),
                                    'especificacion': ing.especificacion_otro or ''
                                })

                        self.mostrar_lista_ingresos()

                        with ui.element('div').classes('row q-col-gutter-sm items-end q-mt-sm'):

                            with ui.element('div').classes('col-12 col-sm-6 col-md-5'):
                                self.motivo_sel = ui.select(
                                    ['Cetoacidosis diabética',
                                    'Estado Hiperosmolar no cetosico',
                                    'Descontrol Metabólico',
                                    'Infecciones', 'Otros'],
                                    label='Motivo de Ingreso'
                                ).classes(INPUT_CLASSES)

                            with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                                self.fecha_ing = ui.input('Fecha').classes(INPUT_CLASSES)
                                with self.fecha_ing.add_slot('append'):
                                    ui.icon('calendar_month')\
                                        .on('click', lambda: menu_f.open())\
                                        .classes('cursor-pointer')
                                    with ui.menu() as menu_f:
                                        ui.date().bind_value(self.fecha_ing)

                            with ui.element('div').classes('col-12')\
                                    .bind_visibility_from(
                                        self.motivo_sel, 'value',
                                        backward=lambda v: v == 'Otros'
                                    ):
                                self.otros_det = ui.input('Especificar motivo...')\
                                    .classes('w-full ' + INPUT_CLASSES)

                            with ui.element('div').classes('col-12 col-sm-auto'):
                                with ui.row().classes('gap-2'):
                                    self.btn_accion = ui.button(
                                        'Añadir Ingreso', icon='add',
                                        on_click=self.procesar_ingreso
                                    ).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

                                    self.btn_cancelar_edit = ui.button(
                                        icon='close',
                                        on_click=self.limpiar_formulario_ingreso
                                    ).props('outline color="red"')\
                                    .tooltip('Cancelar edición')
                                    self.btn_cancelar_edit.set_visibility(False)

                # ── Barra de acciones sticky ──────────────────────────────────────
                with ui.element('div').classes(
                    'row items-center justify-end q-px-md q-py-sm q-gutter-sm '
                    'bg-white border-t border-gray-200 sticky bottom-0 z-10'
                ):
                    ui.button('Cancelar', on_click=self.dialog_editar.close)\
                        .classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                    ui.button('Guardar', on_click=self.guardar_cambios_paciente)\
                        .classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
                    ui.keyboard(
                        lambda e: self.guardar_cambios_paciente()
                        if e.action.keydown and e.key == 'Enter' else None
                    )

            self.dialog_editar.open()
            # ── Helper: título de sección ────────────────────────────────────────────
    def _seccion_titulo(self, texto: str):
        """Separador visual con título de sección."""
        with ui.element('div').classes('col-12 q-mt-md q-mb-xs'):
            ui.label(texto).classes(
                'text-xs font-black text-blue-700 uppercase '
                'tracking-widest border-b border-blue-100 pb-1 w-full block'
            )
        
        
    @ui.refreshable
    def mostrar_panel_paciente(self):
      
        try:
            paciente = self.paciente
            
            with ui.column().classes('w-full p-42 space-y-2'):
                
                with ui.card().classes(HC_CARD_PROFESSIONAL):
                    with ui.column().classes('w-full'):
                        # Encabezado
                        with ui.row().classes('items-center justify-between wrap q-col-gutter-sm mb-2'):
                            ui.label('Gestión de Citas').classes(HEADER_TITLE_CLASSES)
                        
                        # Separar y ordenar citas
                        hoy = datetime.now().date()
                        citas_pasadas = [r for r in paciente.registros if r.fecha_consulta <= hoy]
                        citas_futuras = [r for r in paciente.registros if r.fecha_consulta > hoy]
                        
                        citas_pasadas_ordenadas = sorted(citas_pasadas, key=lambda x: x.fecha_consulta, reverse=True)
                        citas_futuras_ordenadas = sorted(citas_futuras, key=lambda x: x.fecha_consulta)
                        
                        with ui.row().classes('w-full q-col-gutter-lg wrap'):
                            # Columna de próximas citas
                            with ui.column().classes('col-12 col-lg-5 q-gutter-y-md'):
                                # Encabezado con botón
                                with ui.row().classes('items-center justify-between wrap q-col-gutter-sm'):
                                    ui.label('Próximas Citas').classes('text-xl font-semibold text-purple-700')
                                    if tiene_permiso("agenda_add"):
                                    
                                        ui.button('Agendar Nueva', icon='add_circle', 
                                                on_click=lambda: self.mostrar_dialogo_citas(paciente)) \
                                            .classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                                
                                # Tarjeta de próxima cita
                                if citas_futuras_ordenadas:
                                    proxima_cita = citas_futuras_ordenadas[0]
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.row().classes('w-full justify-between items-start wrap q-col-gutter-md'):
                                            with ui.column().classes('space-y-2'):
                                                ui.label('PRÓXIMA CITA').classes('text-xs font-bold text-purple-400 tracking-wide')
                                                ui.label(proxima_cita.fecha_consulta.strftime('%A,%d/%m/%Y')) \
                                                    .classes('text-xl font-bold text-purple-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.icon('schedule', size='sm').classes('text-blue-400')
                                                    ui.label(proxima_cita.hora).classes('text-md font-medium text-blue-600')
                                                if proxima_cita.notas:
                                                    ui.markdown(f"**Notas:** {proxima_cita.notas}").classes('text-sm text-gray-600 mt-2')
                                            with ui.column().classes('items-end'):
                                                if tiene_permiso("agenda_cancel"):
                                                    ui.button(icon='delete',
                                                            on_click=lambda: self.eliminar_cita(proxima_cita)) \
                                                        .props('flat round dense').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                                else:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        ui.icon('event_available', size='xl').classes('text-purple-300 mx-auto')
                                        ui.label('No hay citas programadas').classes('text-lg font-medium text-gray-400 mt-2')
                                        if tiene_permiso("agenda_add"):
                                            ui.button('Agendar ahora', icon='add', 
                                                    on_click=lambda: self.mostrar_dialogo_citas(paciente)) \
                                                .classes(PRIMARY_BUTTON_CLASSES + ' mt-4 mx-auto').props('color="primary"')
                                
                                # Historial de próximas citas
                                if citas_futuras_ordenadas[1:]:
                                    with ui.expansion('Más citas programadas', icon='expand_more').classes('w-full mt-4 bg-white rounded-lg'):
                                        with ui.column().classes('space-y-4 p-4'):
                                            ui.label('Otras citas futuras').classes('text-md font-semibold text-purple-600 mb-2')
                                            for registro in citas_futuras_ordenadas[1:]:
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.row().classes('w-full justify-between items-start wrap q-col-gutter-md'):
                                                        with ui.column().classes('space-y-1'):
                                                            ui.label(registro.fecha_consulta.strftime('%d/%m/%Y')) \
                                                                .classes('font-medium text-purple-800')
                                                            if registro.notas:
                                                                ui.label(registro.notas[:50] + '...' if len(registro.notas) > 50 else registro.notas) \
                                                                    .classes('text-sm text-gray-600')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label(registro.hora).classes('text-sm font-medium text-blue-500')
                                                            if tiene_permiso("agenda_cancel"):
                                                            
                                                                ui.button(icon='delete' ,
                                                                        on_click=lambda r=registro: self.eliminar_cita(r )) \
                                                                    .props('flat round dense color="error"').classes(DANGER_BUTTON_CLASSES)
                            
                            # Columna de historial de consultas
                            with ui.column().classes('col-12 col-lg-5 q-gutter-y-md'):
                                ui.label('Historial de Consultas').classes(HEADER_TITLE_CLASSES)
                                
                                # Tarjeta de última consulta
                                if citas_pasadas_ordenadas:
                                    ultima_cita = citas_pasadas_ordenadas[0]
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.row().classes('w-full justify-between items-start wrap q-col-gutter-md'):
                                            with ui.column().classes('space-y-2'):
                                                ui.label('ÚLTIMA CONSULTA').classes('text-xs font-bold text-blue-400 tracking-wide')
                                                ui.label(ultima_cita.fecha_consulta.strftime('%A, %d/%m/%Y')) \
                                                    .classes('text-xl font-bold text-blue-800')
                                                with ui.row().classes('items-center gap-2'):
                                                    ui.icon('schedule', size='sm').classes('text-blue-400')
                                                    ui.label(ultima_cita.hora).classes('text-md font-medium text-blue-600')
                                                if ultima_cita.notas:
                                                    ui.markdown(f"**Notas:** {ultima_cita.notas}").classes('text-sm text-gray-600 mt-2')
                                            with ui.column().classes('items-end'):
                                                if tiene_permiso("agenda_cancel"):
                                                    ui.button(icon='delete',
                                                            on_click=lambda: self.eliminar_cita(ultima_cita)) \
                                                        .props('flat round dense color="error"').classes(DANGER_BUTTON_CLASSES)
                                else:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        ui.icon('history', size='xl').classes('text-blue-300 mx-auto')
                                        ui.label('No hay consultas anteriores').classes('text-lg font-medium text-gray-400 mt-2')
                                
                                # Historial completo
                                if citas_pasadas_ordenadas[1:]:
                                    with ui.expansion('Ver historial completo', icon='expand_more').classes('w-full mt-4 bg-white rounded-lg'):
                                        with ui.column().classes('space-y-4 p-4'):
                                            ui.label('Consultas anteriores').classes('text-md font-semibold text-blue-600 mb-2')
                                            for registro in citas_pasadas_ordenadas[1:]:
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.row().classes('items-centerjustify-between wrap q-col-gutter-sm'):
                                                        with ui.column().classes('space-y-1'):
                                                            ui.label(registro.fecha_consulta.strftime('%d/%m/%Y')) \
                                                                .classes('font-medium text-blue-800')
                                                            with ui.row().classes('items-center gap-2'):
                                                                ui.icon('schedule', size='xs').classes('text-blue-400')
                                                                ui.label(registro.hora).classes('text-sm font-medium text-blue-500')
                                                            if registro.notas:
                                                                ui.label(registro.notas[:50] + '...' if len(registro.notas) > 50 else registro.notas) \
                                                                    .classes('text-sm text-gray-600')
                                                        ui.button(icon='delete', 
                                                                on_click=lambda r=registro: self.eliminar_cita(r)) \
                                                            .props('flat round dense').classes(DANGER_BUTTON_CLASSES)
                
                ui.label(f'Panel Clínico ').classes(HEADER_TITLE_CLASSES)
                if tiene_permiso("panel_clinico_view"):
                    # Sección de Gráficos con datos reales
                    with ui.row().classes('w-full q-col-gutter-md wrap'):
                        # Gráfico IMC desde Mensuraciones
                        mensuraciones = sorted(paciente.mensuraciones, key=lambda x: x.fecha_registro)
                        with ui.column().classes('col-12 col-xl-5'):
                            self._crear_tarjeta_grafico(
                                título='Evolución del IMC',
                                series=[{
                                    'name': 'IMC',
                                    'type': 'line',
                                    'data': [m.IMC for m in mensuraciones],
                                    'smooth': True,
                                    'lineStyle': {'color': '#3b82f6'},
                                    'areaStyle': {'color': '#bfdbfe'}
                                }],
                                ejes_x=[m.fecha_registro.strftime('%Y-%m-%d') for m in mensuraciones],
                                lineas_referencia=[
                                    (18.5, 'Bajo peso', '#f59e0b'),
                                    (24.9, 'Normal', '#10b981'),
                                    (29.9, 'Sobrepeso', '#f59e0b'),
                                    (34.9, 'Obesidad', '#ef4444'),
                                    (39.9, 'Obesidad Grado 1', '#ef4444'),
                                    (44.9, 'Obesidad Grado 2', '#ef4444'),
                                    (50, 'Obesidad Grado 3', '#ef4444')
                                ]
                            )
                            
                        # Gráfico Glucemia desde Complementarios
                        with ui.column().classes('col-12 col-xl-5'):
                            complementarios = sorted(paciente.complementarios, key=lambda x: x.fecha_registro)
                            self._crear_tarjeta_grafico(
                                título='Control Glucémico',
                                series=[{
                                    'name': 'Glucemia',
                                    'type': 'line',
                                    'data': [c.glucemia for c in complementarios],
                                    'smooth': True,
                                    'lineStyle': {'color': '#ef4444'},
                                    'areaStyle': {'color': '#fecaca'}
                                }],
                                ejes_x=[c.fecha_registro.strftime('%Y-%m-%d') for c in complementarios],
                                lineas_referencia=[
                                    (3.9, 'Normal en ayunas', '#10b981'),
                                    (5.5, 'Normal en ayunas', '#10b981'),
                                    (5.6, 'Prediabetes', '#10b981'),
                                    (6.9, 'Prediabetes', '#10b981'),
                                    (7.0, 'Diabetes', '#10b981'),
                                    (7.8, 'Postprandial (después de comer) normal', '#10b981'),
                                    (10, 'Postprandial en diabetes', '#10b981')
                                ],
                                y_min=1,
                                y_max=30
                            )
                            
                            # Gráfico Función Renal desde Nefrologia
                            nefrologias = sorted(paciente.nefrologia, key=lambda x: x.fecha_registro)
                        with ui.column().classes('col-12 col-xl-5'):
                            
                            self._crear_tarjeta_grafico(
                                título='Filtrado Glomerular Teorico',
                                series=[{
                                    'name': 'GFR',
                                    'type': 'line',
                                    'data': [n.filtrado_glomerular_teorico for n in nefrologias],
                                    'smooth': True,
                                    'lineStyle': {'color': '#10b981'},
                                    'areaStyle': {'color': '#a7f3d0'}
                                }],
                                ejes_x=[n.fecha_registro.strftime('%Y-%m-%d') for n in nefrologias],
                                lineas_referencia=[
                                    (90, 'G1', '#10b981'),
                                    (60, 'G2', '#f59e0b'),
                                    (45, 'G3A', '#f59e0b'),
                                    (30, 'G3B', '#ef4444'),
                                    (15, 'G4', '#dc2626'),
                                    (10, 'G5', '#7f1d1d')
                                        
                                ]
                            )

                        with ui.column().classes('col-12 col-xl-5'):
                            complementarios = sorted(paciente.complementarios, key=lambda x: x.fecha_registro)
                            self._crear_tarjeta_grafico(
                                título='Perfil Lipídico',
                                series=[
                                    {
                                        'name': 'Colesterol',
                                        'type': 'line',
                                        'data': [c.colesterol for c in complementarios],
                                        'smooth': True,
                                        'lineStyle': {'color': '#10b981'},
                                        'areaStyle': {'color': '#a7f3d0'}
                                    },
                                    {
                                        'name': 'HDL',
                                        'type': 'line',
                                        'data': [c.HDLC for c in complementarios],
                                        'smooth': True,
                                        'lineStyle': {'color': '#3b82f6'},
                                        'areaStyle': {'color': '#bfdbfe'}
                                    },
                                    {
                                        'name': 'Triglicéridos',
                                        'type': 'line',
                                        'data': [c.trigliceridos for c in complementarios],
                                        'smooth': True,
                                        'lineStyle': {'color': '#ef4444'},
                                        'areaStyle': {'color': '#fecaca'}
                                    }
                                ],
                                ejes_x=[c.fecha_registro.strftime('%Y-%m-%d') for c in complementarios],
                                lineas_referencia=[
                                    (200, 'Colesterol Normal', '#10b981'),
                                    (40, 'HDL Normal', '#10b981'),
                                    (150, 'Triglicéridos Normal', '#10b981')
                                ],
                                y_min=0,
                                y_max=300
                            )

                        
                    # Sección de Datos Clave
                    with ui.row().classes('w-full q-col-gutter-md wrap'):
                        # Tratamiento Actual
                        with ui.column().classes('col-12 col-md-5 col-xl-3'):
                            tratamientos = [t.tratamiento for t in paciente.tratamiento_actual]
                            self._crear_tarjeta_datos(
                                título='Tratamiento Actual',
                                contenido=[
                                    ('Medicación', '\n'.join(tratamientos)),
                                    ('Último ajuste', max(t.fecha_registro for t in paciente.tratamiento_actual).strftime('%d/%m/%Y') if tratamientos else 'N/A')
                                ],
                                color='bg-blue-50'
                            )
                            
                            # Datos Biométricos
                            ultimo_complementario = complementarios[-1] if complementarios else None
                        with ui.column().classes('col-12 col-md-5 col-xl-3'):
                            self._crear_tarjeta_datos(
                                título='Biometría',
                                contenido=[
                                    ('Trigliceridos', f"{ultimo_complementario.trigliceridos if ultimo_complementario else 'N/A'} mmol/L"),
                                    ('TGO', f"{ultimo_complementario.TGO if ultimo_complementario else 'N/A'} mmol/L")
                                ] if ultimo_complementario else [('Datos', 'No disponibles')],
                                color='bg-red-50'
                            )
                            
                            # Hábitos Tóxicos
                            ultimos_habitos = paciente.habitos_toxicos[-1] if paciente.habitos_toxicos else None
                        with ui.column().classes('col-12 col-md-5 col-xl-3'):
                            self._crear_tarjeta_datos(
                                título='Hábitos Tóxicos',
                                contenido=[
                                    ('Tabaco', ultimos_habitos.fuma if ultimos_habitos else 'N/A'),
                                    ('Alcohol', ultimos_habitos.consumo_excesivo_alcohol if ultimos_habitos else 'N/A')
                                ],
                                color='bg-green-50'
                            )
                else:
                    ui.label('No tienes permiso para ver el panel clínico').classes('text-red-600 font-semibold')

    

                        
        except Exception as e:
            log_error_and_notify(e, f'Error al mostrar el panel del paciente HC {self.paciente.no_hc if self.paciente else "N/A"}')
            ui.notify(f'Error al mostrar el resumen: {str(e)}', type='negative')
    def eliminar_cita(self, registro):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar esta Cita?')
            
            with ui.row().classes('w-full justify-end gap-4'):
                ui.button('Cancelar', on_click=dialog.close).props('color="warning"').classes(DANGER_BUTTON_CLASSES)
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_cita(registro, dialog))\
                    .classes(DANGER_BUTTON_CLASSES).props('color="error"')

        dialog.open()
        

    def confirmar_eliminacion_cita(self, cita, dialog):
        try:
            self.session.delete(cita)
            self.session.commit()
            ui.notify('Cita eliminada correctamente', type='positive')
            self.mostrar_panel_paciente.refresh()
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al eliminar la cita ID {cita.id}')
            ui.notify(f'Error al eliminar la Cita: {str(e)}', type='negative')
        finally:
            dialog.close()   
    def mostrar_dialogo_citas(self, paciente):
        with ui.dialog() as dialog, ui.card().classes('full-width').style('max-width: 760px'):
            ui.label('Agendar Nueva Cita').classes(HEADER_TITLE_CLASSES)
            
            with ui.row().classes('w-full q-col-gutter-md wrap'):
                # Columna izquierda - Fecha y Notas
                with ui.column().classes('col-12 col-md-6 q-gutter-y-md'):
                    # Fecha
                    with ui.row().classes('items-center w-full'):
                        ui.label('Fecha:').classes('text-sm font-medium text-gray-700')
                        fecha_input = ui.date(
                            value=datetime.now().strftime('%Y-%m-%d'),).props(
                            f'locale="es" '
                            f'default-year-month={self.current_month} '
                            f':options="date => date >= \'{self.today}\'"'
                        ).classes('w-full rounded-xl')
                    
                    # Notas 
                    with ui.row().classes('items-start w-full'):
                        ui.label('Notas:').classes('text-sm font-medium text-gray-700')
                        notas_input = ui.textarea().props(
                            'color="purple" outlined autogrow'
                        ).classes('w-full')

    

                # Columna derecha - Hora
                with ui.column().classes('col-12 col-md-6 q-gutter-y-md'):
                    # Hora
                    with ui.row().classes('items-center w-full'):
                        ui.label('Hora:').classes('text-sm font-medium text-gray-700')
                        hora_input = ui.time(value='09:00').classes('w-full')
                    
                    # Espacio vacío para alinear botones
                    ui.space()

            # Botones en la parte inferior
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Agendar', 
                        on_click=lambda: self.agendar_cita(
                            paciente, 
                            fecha_input.value, 
                            notas_input.value,
                            hora_input.value, 
                            dialog
                        )).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
        
        dialog.open()
    def on_page_exit(self):
        """Cierra la sesión de la base de datos cuando el usuario abandona la página"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except Exception as e:
            log_error_and_notify(e, 'Error al cerrar sesión de BD')
    def agendar_cita(self, paciente, fecha, notas, hora_str, dialog):
        try:
            # Convertir la hora de string a objeto time
            hora_obj = datetime.strptime(hora_str, '%H:%M').time()
            
            # Convertir la fecha de string a objeto date
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            
            nuevo_registro = Registro_consulta(
                paciente_id=paciente.id  ,
                fecha_consulta=fecha_obj ,
                hora=hora_obj,  
                notas=notas if notas is not None else "No Registrado",
            )
            
            paciente.registros.append(nuevo_registro)
            self.session.commit()
            
            ui.notify('Cita agendada correctamente', type='positive')
            dialog.close()
            self.mostrar_panel_paciente.refresh()
        except IntegrityError:
            self.session.rollback()
            ui.notify('Error: Ya existe una consulta programada para ese día y hora', type='negative')
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, f'Error al agendar cita para paciente HC {paciente.no_hc}')
            ui.notify(f'Error al agendar cita: {str(e)}', type='negative')
 
    


    

        


    def _crear_tarjeta_grafico(self, título, series, ejes_x, lineas_referencia, y_min=None, y_max=None):
        with ui.card().classes(HC_SECTION_CARD):
            ui.label(título).classes('text-lg font-medium text-gray-700 mb-2')
            config = {
                'tooltip': {'trigger': 'axis'},
                'xAxis': {'type': 'category', 'data': ejes_x},
                'yAxis': {'type': 'value', 'min': y_min, 'max': y_max},
                'series': series,
                'markLine': {
                    'data': [{'yAxis': y, 'label': {'formatter': label}, 'lineStyle': {'color': color}} 
                            for y, label, color in lineas_referencia]
                }
            }
            ui.echart(config).classes('w-full h-64')

    def _crear_tarjeta_datos(self, título, contenido, color):
        with ui.card().classes(f'w-full p-4 {color}'):
            ui.label(título).classes('text-lg font-medium text-gray-700 mb-3')
            for etiqueta, valor in contenido:
                with ui.row().classes('w-full justify-between wrap q-col-gutter-sm py-1'):
                    ui.label(etiqueta).classes('text-gray-600')
                    ui.label(valor).classes('font-medium text-gray-800')
        
   


    
    

    def _create_value_row(self, label, value, color=None):
        with ui.row().classes('items-center gap-3'):
            ui.label(label).classes('font-medium text-gray-700 w-40')
            if color:
                ui.label(value).classes(f'font-mono text-{color} font-semibold')
            else:
                ui.label(value).classes('font-mono text-gray-800')

    def _create_info_row(self, label, value, color=None):
        with ui.row().classes('items-center justify-between py-1 border-b border-gray-100 last:border-0'):
            ui.label(label).classes('text-sm font-medium text-gray-500')
            if color:
                ui.label(value).classes(f'text-sm font-semibold text-{color}')
            else:
                ui.label(value).classes('text-sm font-semibold text-gray-700')

    def _create_medical_info_row(self, label, value, icon_name, color='blue'):
        """Crea una fila de información médica con icono y color específico"""
        with ui.row().classes('items-center justify-between p-2 rounded-lg'):
            with ui.row().classes('items-center gap-2'):
                ui.icon(icon_name, size='sm').classes(f'text-{color}-500')
                ui.label(label).classes('text-xs font-medium text-gray-700')
            ui.label(value).classes('text-xs font-semibold text-gray-800')

    def toggle_estado_paciente(self, paciente):
        try:
            # Cambiamos el estado booleano
            nuevo_estado = not paciente.activo
            paciente.activo = nuevo_estado
            # 1. Guardar en Base de Datos
            self.session.commit()

            ui.navigate.reload() # Refrescamos para ver los cambios
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, "Error al cambiar estado del paciente")
   
    def input_clinico(self, label, min_val=None, max_val=None, valor_inicial=None):

  
        if valor_inicial in ("", None):
            valor_inicial = None
        else:
            try:
                valor_inicial = float(valor_inicial)
            except:
                valor_inicial = None

        return ui.number(
            label=label,
            value=valor_inicial,
            min=min_val,
            max=max_val,
            validation={
                f'Rango: {min_val}-{max_val}':
                lambda v: (min_val <= v <= max_val) if v is not None else True
            }
        )