from nicegui import ui
from datetime import date, datetime
from calendar import monthrange
from models import *
from sqlalchemy import case, func, Integer, extract, and_, distinct
from sidebar import SidebarReutilizable
from authenticar import *
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collections import defaultdict
from .citas import GAP_SM

# ══════════════════════════════════════════════════════════════
#  Variables disponibles en la sección de Tendencias
# ══════════════════════════════════════════════════════════════
VARS_COMPARACION = {
    'nuevos_registros': 'Nuevos registros de pacientes',
    'imc_promedio':     'IMC promedio',
    'glucemia_debut':   'Glucemia al debut (media, mmol/L)',
    'pct_control_ta':   '% TA controlada (≤130/80)',
    'pct_retinopatia':  '% con Retinopatía',
    'pct_neuropatia':   '% con Neuropatía (LOPS)',
    'pct_hta':          '% con Hipertensión Arterial',
}

MESES_ES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

COLOR_SEXO = {'Masculino': '#1E88E5', 'Femenino': '#EC407A'}


def _date_input(label, self_obj, attr):
    """Crea un campo de fecha con picker de calendario."""
    with ui.input(label).bind_value(self_obj, attr).classes('w-40') as inp:
        with inp.add_slot('append'):
            ui.icon('calendar_month').on('click', lambda: menu.open())
        with ui.menu() as menu:
            ui.date().bind_value(inp)
    return inp


def _sin_datos():
    with ui.column().classes('w-full items-center justify-center h-36'):
        ui.icon('bar_chart', size='40px', color='grey-4')
        ui.label('Sin datos en el período seleccionado').classes('text-gray-400 mt-2')


def _card_error(e):
    with ui.card().classes('bg-red-50 border border-red-200 p-3'):
        ui.label(f'Error: {e}').classes('text-red-700 text-xs')


# ══════════════════════════════════════════════════════════════
#  CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════
class Dashboard:
    def __init__(self):
        self.session = Session()
        self.usuario_actual = devolver_usuario_actual() or {}
        rol_actual = str(self.usuario_actual.get('rol', '')).strip().lower()
        self.es_usuario_admin = rol_actual in ['admin', 'superadmin', 'superadministrador']
        self.institucion_id_usuario  = self.usuario_actual.get('institucion_id')
        self.institucion_id_seleccionada = self.institucion_id_usuario
        self.instituciones_disponibles   = {}
        self._render_token = 0
        self._cargar_instituciones()

        # ── Filtros globales (Tabs 1 y 2) ──
        self.desde = date(2005, 1, 1).strftime('%Y-%m-%d')
        self.hasta = date.today().strftime('%Y-%m-%d')

        # ── Estado Tab 3: Tendencias ──
        hoy = date.today()
        self.comp_modo    = 'rangos'
        self.comp_var     = 'nuevos_registros'
        self.comp_a_desde = date(hoy.year - 1, 1,  1).strftime('%Y-%m-%d')
        self.comp_a_hasta = date(hoy.year - 1, 12, 31).strftime('%Y-%m-%d')
        self.comp_b_desde = date(hoy.year,     1,  1).strftime('%Y-%m-%d')
        self.comp_b_hasta = hoy.strftime('%Y-%m-%d')
        self.comp_año     = str(hoy.year)
        self._comp_token  = 0

        self.sidebar = SidebarReutilizable(self)
        self.setup_sidebar()
        self.barra_filtros()
        self.contenedor_cartas = ui.column().classes('w-full gap-4')
        self.setup_layout()

    # ──────────────────────────────────────────────────────────
    #  Instituciones y condiciones
    # ──────────────────────────────────────────────────────────
    def _cargar_instituciones(self):
        try:
            if self.es_usuario_admin:
                instituciones = self.session.query(Institucion).order_by(Institucion.nombre).all()
                self.instituciones_disponibles = {i.id: i.nombre for i in instituciones}
                if not self.institucion_id_seleccionada and instituciones:
                    self.institucion_id_seleccionada = instituciones[0].id
            elif self.institucion_id_usuario:
                inst = self.session.query(Institucion).filter(
                    Institucion.id == self.institucion_id_usuario).first()
                if inst:
                    self.instituciones_disponibles = {inst.id: inst.nombre}
        except Exception as e:
            print(f"Error cargando instituciones: {e}")
            self.instituciones_disponibles = {}

    def _condicion_institucion_paciente(self):
        if self.es_usuario_admin:
            if self.institucion_id_seleccionada is None:
                return True
            return Paciente.institucion_id == self.institucion_id_seleccionada
        if self.institucion_id_usuario is None:
            return False
        return Paciente.institucion_id == self.institucion_id_usuario

    # ──────────────────────────────────────────────────────────
    #  Helpers: Obtener último registro de cada tabla relacionada
    # ──────────────────────────────────────────────────────────

    def _get_latest_examen_fisico(self):
        """Subquery para obtener el último ExamenFisico por paciente (por ID)."""
        latest = self.session.query(
            ExamenFisico.paciente_id,
            func.max(ExamenFisico.id).label('max_id')
        ).group_by(ExamenFisico.paciente_id).subquery()
        
        return self.session.query(ExamenFisico)\
            .join(latest, and_(ExamenFisico.paciente_id == latest.c.paciente_id,
                              ExamenFisico.id == latest.c.max_id)).subquery()

    def _get_latest_nefrologia(self):
        """Subquery para obtener la última Nefrologia por paciente (por ID)."""
        latest = self.session.query(
            Nefrologia.paciente_id,
            func.max(Nefrologia.id).label('max_id')
        ).group_by(Nefrologia.paciente_id).subquery()
        
        return self.session.query(Nefrologia)\
            .join(latest, and_(Nefrologia.paciente_id == latest.c.paciente_id,
                              Nefrologia.id == latest.c.max_id)).subquery()

    def _get_latest_oftalmologia(self):
        """Subquery para obtener la última Oftalmologia por paciente (por ID)."""
        latest = self.session.query(
            Oftalmologia.paciente_id,
            func.max(Oftalmologia.id).label('max_id')
        ).group_by(Oftalmologia.paciente_id).subquery()
        
        return self.session.query(Oftalmologia)\
            .join(latest, and_(Oftalmologia.paciente_id == latest.c.paciente_id,
                              Oftalmologia.id == latest.c.max_id)).subquery()

    def _get_latest_examen_miembros_inferiores(self):
        """Subquery para obtener el último ExamenMiembrosInferiores por paciente (por ID)."""
        latest = self.session.query(
            ExamenMiembrosInferiores.paciente_id,
            func.max(ExamenMiembrosInferiores.id).label('max_id')
        ).group_by(ExamenMiembrosInferiores.paciente_id).subquery()
        
        return self.session.query(ExamenMiembrosInferiores)\
            .join(latest, and_(ExamenMiembrosInferiores.paciente_id == latest.c.paciente_id,
                              ExamenMiembrosInferiores.id == latest.c.max_id)).subquery()

    def _get_latest_complementarios(self):
        """Subquery para obtener el último Complementarios por paciente (por ID)."""
        latest = self.session.query(
            Complementarios.paciente_id,
            func.max(Complementarios.id).label('max_id')
        ).group_by(Complementarios.paciente_id).subquery()
        
        return self.session.query(Complementarios)\
            .join(latest, and_(Complementarios.paciente_id == latest.c.paciente_id,
                              Complementarios.id == latest.c.max_id)).subquery()

    def _get_latest_mensuraciones(self):
        """Subquery para obtener la última Mensuraciones por paciente (por ID)."""
        latest = self.session.query(
            Mensuraciones.paciente_id,
            func.max(Mensuraciones.id).label('max_id')
        ).group_by(Mensuraciones.paciente_id).subquery()
        
        return self.session.query(Mensuraciones)\
            .join(latest, and_(Mensuraciones.paciente_id == latest.c.paciente_id,
                              Mensuraciones.id == latest.c.max_id)).subquery()

    def _get_latest_antecedente_patologico_personal(self):
        """Subquery para obtener el último AntecedentePatologicoPersonal por paciente (por ID)."""
        latest = self.session.query(
            AntecedentePatologicoPersonal.paciente_id,
            func.max(AntecedentePatologicoPersonal.id).label('max_id')
        ).group_by(AntecedentePatologicoPersonal.paciente_id).subquery()
        
        return self.session.query(AntecedentePatologicoPersonal)\
            .join(latest, and_(AntecedentePatologicoPersonal.paciente_id == latest.c.paciente_id,
                              AntecedentePatologicoPersonal.id == latest.c.max_id)).subquery()

    #  Layout y sidebar
    
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
                    ui.label('Dashboard').classes('text-white text-h6 text-weight-bold gt-xs')

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

    def setup_sidebar(self):
        self.sidebar = self.sidebar.crear_sidebar()

    # ──────────────────────────────────────────────────────────
    #  Barra de filtros globales
    # ──────────────────────────────────────────────────────────
    def barra_filtros(self):
        with ui.row().classes('items-center gap-4 p-4 bg-slate-50 rounded-xl shadow-sm'):
            ui.label('Período de Historias Clínicas:').classes('font-bold text-blue-900')
            if self.es_usuario_admin:
                ui.select(
                    options=self.instituciones_disponibles, label='Institución'
                ).bind_value(self, 'institucion_id_seleccionada').on(
                    'update:model-value',
                    lambda _: self._programar_actualizacion_dashboard()
                ).classes('w-64')
            _date_input('Inicio', self, 'desde')
            _date_input('Fin',    self, 'hasta')
            ui.button(
                'Filtrar', icon='filter_alt',
                on_click=self._programar_actualizacion_dashboard
            ).classes('bg-blue-600 text-white shadow-md')

    # ──────────────────────────────────────────────────────────
    #  Ciclo de renderizado
    # ──────────────────────────────────────────────────────────
    def _programar_actualizacion_dashboard(self):
        self._render_token += 1
        token = self._render_token
        self.contenedor_cartas.clear()
        with self.contenedor_cartas:
            with ui.card().classes('w-full p-6 shadow'):
                with ui.row().classes('items-center gap-3'):
                    ui.spinner(size='lg')
                    ui.label('Cargando dashboard...').classes('text-gray-700')
        ui.timer(0.05, lambda: self.actualizar_dashboard(token), once=True)

    def actualizar_dashboard(self, token=None):
        if token is not None and token != self._render_token:
            return
        self.contenedor_cartas.clear()
        try:
            f1 = datetime.strptime(self.desde, '%Y-%m-%d').date()
            f2 = datetime.strptime(self.hasta, '%Y-%m-%d').date()
        except ValueError:
            ui.notify('Formato de fecha inválido. Use YYYY-MM-DD.', type='warning')
            return
        with self.contenedor_cartas:
            self.setup_dashboard_filtrado(f1, f2)
 
    #  SETUP PRINCIPAL — 3 TABS

    def setup_dashboard_filtrado(self, f1, f2):
        self.contenedor_cartas.clear()
        token_actual = self._render_token

        ui.add_head_html('''
            <style>
                #c1 { padding-top: 0 !important; }
                .nicegui-content { overflow-x: hidden; }
            </style>
        ''')

        with self.contenedor_cartas:
            ui.label('Panel de Control').classes(
                'text-4xl font-extrabold text-blue-800 mb-2 tracking-tight '
                'border-b-2 border-blue-200 pb-2')

            with ui.tabs().classes('w-full') as tabs:
                ui.tab('resumen',   label='Resumen General',       icon='dashboard')
                ui.tab('niveles',   label='Análisis por Niveles',   icon='layers')
                ui.tab('tendencias',label='Tendencias',             icon='trending_up')

            with ui.tab_panels(tabs, value='resumen').classes('w-full'):

                # ══════════════════════════════════════════════
                #  TAB 1 — RESUMEN GENERAL
                # ══════════════════════════════════════════════
                with ui.tab_panel('resumen'):
                    with ui.column().classes('w-full gap-4') as blq:
                        with ui.card().classes('w-full p-4') as tarjeta_carga:
                            with ui.row().classes('items-center gap-3'):
                                ui.spinner(size='md')
                                estado = ui.label('Renderizando indicadores...').classes('text-gray-700')

                    def bloque_1():
                        if token_actual != self._render_token: return
                        with blq:
                            ui.label('Indicadores Clave').classes(
                                'text-2xl font-semibold text-gray-700 mt-4 mb-2')
                            with ui.grid().classes('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6'):
                                self.total_pacientes_card(f1, f2)
                                self.antecedentes_familiares_card(f1, f2)
                                self.hipertension_card(f1, f2)
                                self.nefropatia_card(f1, f2)
                                self.card_promedio_edad(f1, f2)
                        estado.set_text('Cargando distribuciones...')
                        ui.timer(0.05, bloque_2, once=True)

                    def bloque_2():
                        if token_actual != self._render_token: return
                        with blq:
                            ui.label('Distribuciones Principales').classes(
                                'text-2xl font-semibold text-gray-700 mt-6 mb-2')
                            with ui.element('div').classes(
                                'row q-col-gutter-lg w-full'
                            ):
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):
                                    self.card_promedio_e_categorias_imc(f1, f2)
                                with ui.element('div').classes(
                                    'col-12 col-md-6'
                                ):
                                    self.card_obesidad_debut(f1, f2)
                                with ui.element('div').classes(            
                                    'col-12 col-md-6'
                                ):
                                   
                                    self.card_comorbilidades(f1, f2)
                        estado.set_text('Cargando análisis avanzados...')
                    

                 
                        tarjeta_carga.delete()

                    ui.timer(0.01, bloque_1, once=True)

                #  TAB 2 — ANÁLISIS POR NIVELES (3 sub-tabs)
              
                with ui.tab_panel('niveles'):
                    with ui.tabs().classes('w-full') as subtabs:
                        ui.tab('pob',  label='Poblacional',   icon='people')
                        ui.tab('clin', label='Clínico',       icon='monitor_heart')
                        ui.tab('diab', label='Diabetes',      icon='vaccines')

                    with ui.tab_panels(subtabs, value='pob').classes('w-full'):

                        # ── Sub-tab: Poblacional ──
                        with ui.tab_panel('pob'):
                            with ui.column().classes('w-full gap-4') as blq_pob:
                                with ui.card().classes('w-full p-4') as ldr_pob:
                                    with ui.row().classes('items-center gap-3'):
                                        ui.spinner(size='md')
                                        ui.label('Cargando nivel poblacional...').classes('text-gray-600')

                            def cargar_pob():
                                if token_actual != self._render_token: return
                                with blq_pob:
                                    ui.label('Distribución Demográfica').classes(
                                        'text-2xl font-semibold text-gray-700 mt-2 mb-2')
                                    with ui.element('div').classes(
                                        'row q-col-gutter-lg w-full'
                                    ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_distribucion_sexo(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_grupos_edad(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_color_piel(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_estado_civil(f1, f2)
                                    with ui.column().classes('w-full gap-4 mb-4'):
                                        self.card_ocupacion_detalle(f1, f2)
                                        self.card_escolaridad_ocupacion(f1, f2)
                                ldr_pob.delete()

                            ui.timer(0.05, cargar_pob, once=True)

                        # ── Sub-tab: Clínico ──
                        with ui.tab_panel('clin'):
                            with ui.column().classes('w-full gap-4') as blq_clin:
                                with ui.card().classes('w-full p-4') as ldr_clin:
                                    with ui.row().classes('items-center gap-3'):
                                        ui.spinner(size='md')
                                        ui.label('Cargando nivel clínico...').classes('text-gray-600')

                            def cargar_clin():
                                if token_actual != self._render_token: return
                                with blq_clin:
                                    ui.label('Estado Nutricional y Tensión Arterial').classes(
                                        'text-2xl font-semibold text-gray-700 mt-2 mb-2')
                                    with ui.element('div').classes(
                                        'row q-col-gutter-lg w-full'
                                    ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_promedio_e_categorias_imc(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_hta_control(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_imc_vs_control_hta(f1, f2)
                                       
                                            
                                        
                                    with ui.element('div').classes(
                                        'row q-col-gutter-lg w-full'
                                    ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_filtrado_glomerular(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_lipidos_y_nefropatia(f1, f2)
                                    ui.label('Comorbilidades').classes(
                                        'text-2xl font-semibold text-gray-700 mt-4 mb-2')
                                    with ui.column().classes('w-full'):
                                        self.card_comorbilidades(f1, f2)
                                ldr_clin.delete()

                            ui.timer(0.05, cargar_clin, once=True)

                        # ── Sub-tab: Diabetes ──
                        with ui.tab_panel('diab'):
                            with ui.column().classes('w-full gap-4') as blq_diab:
                                with ui.card().classes('w-full p-4') as ldr_diab:
                                    with ui.row().classes('items-center gap-3'):
                                        ui.spinner(size='md')
                                        ui.label('Cargando nivel diabetes...').classes('text-gray-600')

                            def cargar_diab():
                                if token_actual != self._render_token: return
                                with blq_diab:
                                    ui.label('Al Diagnóstico').classes(
                                        'text-2xl font-semibold text-gray-700 mt-2 mb-2')
                                    with ui.element('div').classes(
                                        'row q-col-gutter-lg w-full'
                                    ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_modo_debut(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_obesidad_debut(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_glucemia_debut_dist(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_clasificacion_diabetes(f1, f2)
                                    ui.label('Tratamiento y Evolución').classes(
                                        'text-2xl font-semibold text-gray-700 mt-4 mb-2')
                                    with ui.element('div').classes(
                                        'row q-col-gutter-lg w-full'
                                    ):
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_tratamiento_dist(f1, f2)
                                        with ui.element('div').classes(
                                            'col-12 col-md-6'
                                        ):
                                            self.card_glucemia_media_por_grupo_edad(f1, f2)
                                    ui.label('Complicaciones').classes(
                                        'text-2xl font-semibold text-gray-700 mt-4 mb-2')
                                    with ui.column().classes('w-full gap-4'):
                                        self.card_correlacion_tiempo_complicaciones(f1, f2)
                                ldr_diab.delete()

                            ui.timer(0.05, cargar_diab, once=True)

                with ui.tab_panel('tendencias'):
                    self.setup_tab_tendencias()



    #  TAB 3: LÓGICA COMPLETA DE TENDENCIAS
    def setup_tab_tendencias(self):
        """Construye la UI completa de la pestaña de Tendencias - Comparación por Rangos."""

        with ui.column().classes('w-full gap-6 p-2'):
            # ── Encabezado ──
            with ui.row().classes('items-center gap-3'):
                ui.icon('trending_up', size='32px', color='blue-700')
                with ui.column():
                    ui.label('Tendencias y Comparación Temporal').classes(
                        'text-2xl font-bold text-blue-800')
                    ui.label(
                        'Compara variables clínicas y epidemiológicas entre dos períodos. '
                        'Los filtros de esta sección son independientes del filtro global.'
                    ).classes('text-sm text-gray-500')

            # ── Selector de Variable ──
            with ui.card().classes('p-4 border-l-4 border-blue-500'):
                ui.label('Variable a analizar').classes(
                    'text-xs font-bold text-gray-500 uppercase tracking-wider mb-2')
                ui.select(
                    options=VARS_COMPARACION,
                    label='Variable'
                ).bind_value(self, 'comp_var').classes('w-full')

            # ── Controles de fechas ──
            with ui.card().classes('w-full p-4 border-l-4 border-orange-400'):
             self._build_controles_comp()

            # ── Botón ──
            ui.button(
                'Generar gráfico', icon='auto_graph',
                on_click=self._generar_tendencia
            ).classes('bg-blue-700 text-white font-bold shadow-md px-6')

            # ── Área del gráfico ──
            self._comp_chart = ui.column().classes('w-full gap-4')

    def _build_controles_comp(self):
        """Construye controles para comparación por rangos A y B."""
        with ui.row().classes('items-end gap-8 flex-wrap'):
            with ui.column().classes('gap-2'):
                ui.label('Período A').classes(
                    'text-xs font-bold text-blue-600 uppercase tracking-wider')
                with ui.row().classes('gap-3 items-end'):
                    _date_input('Desde', self, 'comp_a_desde')
                    _date_input('Hasta', self, 'comp_a_hasta')
            with ui.column().classes('gap-2'):
                ui.label('Período B').classes(
                    'text-xs font-bold text-orange-600 uppercase tracking-wider')
                with ui.row().classes('gap-3 items-end'):
                    _date_input('Desde', self, 'comp_b_desde')
                    _date_input('Hasta', self, 'comp_b_hasta')

    def _generar_tendencia(self):
        self._comp_token += 1
        token = self._comp_token
        self._comp_chart.clear()
        with self._comp_chart:
            with ui.card().classes('w-full p-4'):
                with ui.row().classes('items-center gap-3'):
                    ui.spinner(size='md')
                    ui.label('Calculando...').classes('text-gray-600')
        ui.timer(0.05, lambda: self._render_tendencia(token), once=True)

    def _render_tendencia(self, token):
        if token != self._comp_token:
            return
        self._comp_chart.clear()
        var  = self.comp_var
        label_var = VARS_COMPARACION.get(var, var)

        with self._comp_chart:
            try:
                self._render_rangos(var, label_var)
            except Exception as e:
                _card_error(e)
                print(f'Error render_tendencia: {e}')

    # ── Renderizadores por modo ──

    def _render_rangos(self, var, label_var):
        """Gráfico de barras agrupadas comparando Período A vs Período B."""
        try:
            fA1 = datetime.strptime(self.comp_a_desde, '%Y-%m-%d').date()
            fA2 = datetime.strptime(self.comp_a_hasta, '%Y-%m-%d').date()
            fB1 = datetime.strptime(self.comp_b_desde, '%Y-%m-%d').date()
            fB2 = datetime.strptime(self.comp_b_hasta, '%Y-%m-%d').date()
        except ValueError:
            ui.notify('Fechas inválidas', type='warning')
            return

        val_a = self._calcular_metrica(var, fA1, fA2)
        val_b = self._calcular_metrica(var, fB1, fB2)
        diff  = round(val_b - val_a, 2)
        pct_diff = round(diff / val_a * 100, 1) if val_a else 0

        label_a = f"Período A\n{fA1.strftime('%d/%m/%y')} – {fA2.strftime('%d/%m/%y')}"
        label_b = f"Período B\n{fB1.strftime('%d/%m/%y')} – {fB2.strftime('%d/%m/%y')}"

        with ui.card().classes('w-full p-4'):
            with ui.row().classes('w-full gap-6 mb-4 items-start flex-wrap'):
                # Indicador A
                with ui.card().classes('p-4 border-l-4 border-blue-500 flex-1 min-w-48'):
                    ui.label('Período A').classes('text-xs text-blue-600 font-bold uppercase')
                    ui.label(f"{fA1.strftime('%d/%m/%Y')} — {fA2.strftime('%d/%m/%Y')}").classes('text-xs text-gray-500')
                    ui.label(str(val_a)).classes('text-3xl font-black text-blue-800')
                # Indicador B
                with ui.card().classes('p-4 border-l-4 border-orange-500 flex-1 min-w-48'):
                    ui.label('Período B').classes('text-xs text-orange-600 font-bold uppercase')
                    ui.label(f"{fB1.strftime('%d/%m/%Y')} — {fB2.strftime('%d/%m/%Y')}").classes('text-xs text-gray-500')
                    ui.label(str(val_b)).classes('text-3xl font-black text-orange-800')
                # Variación
                color_diff = 'green-700' if diff >= 0 else 'red-700'
                icono_diff = 'arrow_upward' if diff >= 0 else 'arrow_downward'
                with ui.card().classes('p-4 border-l-4 border-gray-400 flex-1 min-w-48'):
                    ui.label('Variación').classes('text-xs text-gray-500 font-bold uppercase')
                    with ui.row().classes('items-center gap-1'):
                        ui.icon(icono_diff, color=color_diff)
                        ui.label(f"{'+' if diff>=0 else ''}{diff}  ({'+' if pct_diff>=0 else ''}{pct_diff}%)").classes(
                            f'text-2xl font-black text-{color_diff}')

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[label_var], y=[val_a],
                name='Período A',
                marker_color='#1E88E5',
                text=[val_a], textposition='auto',
            ))
            fig.add_trace(go.Bar(
                x=[label_var], y=[val_b],
                name='Período B',
                marker_color='#FB8C00',
                text=[val_b], textposition='auto',
            ))
            fig.update_layout(
                title=f'Comparación: {label_var}',
                barmode='group',
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_title=label_var,
                margin=dict(t=50, b=40, l=40, r=20),
                legend=dict(orientation='h', y=1.1),
            )
            ui.plotly(fig).classes('w-full')

    def _render_meses(self, var, label_var):
        """Gráfico de línea mensual para el año seleccionado."""
        try:
            año = int(self.comp_año)
        except ValueError:
            ui.notify('Año inválido', type='warning')
            return

        valores = []
        for mes in range(1, 13):
            ultimo_dia = monthrange(año, mes)[1]
            f1 = date(año, mes, 1)
            f2 = date(año, mes, ultimo_dia)
            valores.append(self._calcular_metrica(var, f1, f2))

        with ui.card().classes('w-full p-4'):
            # Miniindicadores: mínimo, máximo, promedio
            v_no_nulos = [v for v in valores if v > 0]
            with ui.row().classes('gap-4 mb-4 flex-wrap'):
                for lbl, val in [
                    ('Máximo', max(valores) if valores else 0),
                    ('Mínimo', min(v_no_nulos) if v_no_nulos else 0),
                    ('Promedio', round(sum(valores)/len(valores), 1) if valores else 0),
                ]:
                    with ui.card().classes('p-3 border-t-4 border-blue-400 min-w-32'):
                        ui.label(lbl).classes('text-xs text-gray-500 font-bold uppercase')
                        ui.label(str(val)).classes('text-2xl font-black text-blue-800')

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=MESES_ES, y=valores,
                mode='lines+markers+text',
                text=[str(v) for v in valores],
                textposition='top center',
                line=dict(color='#1E88E5', width=3),
                marker=dict(size=10, color='#1E88E5'),
                fill='tozeroy',
                fillcolor='rgba(30,136,229,0.08)',
                name=str(año),
            ))
            fig.update_layout(
                title=f'{label_var} — Año {año}',
                height=380,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_title=label_var,
                xaxis_title='Mes',
                margin=dict(t=50, b=40, l=40, r=20),
            )
            ui.plotly(fig).classes('w-full')



    #  CÁLCULO DE MÉTRICAS (helper central para comparación)

    def _calcular_metrica(self, variable, f1, f2):
        """Devuelve un valor numérico para la variable en el rango [f1, f2]."""
        cond = self._condicion_institucion_paciente()
        try:
            if variable == 'nuevos_registros':
                return self.session.query(func.count(distinct(Paciente.id)))\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).scalar() or 0

            elif variable == 'imc_promedio':
                latest_m = self._get_latest_mensuraciones()
                res = self.session.query(latest_m.c.peso, latest_m.c.talla)\
                    .join(Paciente, Paciente.id == latest_m.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).all()
                vals = []
                for peso, talla in res:
                    if peso and talla and talla > 0:
                        tm = talla / 100 if talla > 3 else talla
                        vals.append(peso / (tm ** 2))
                return round(sum(vals) / len(vals), 1) if vals else 0

            elif variable == 'glucemia_debut':
                val = self.session.query(func.avg(distinct(Paciente.glucemia_debut)))\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond,
                            Paciente.glucemia_debut.isnot(None)).scalar()
                return round(val, 2) if val else 0

            elif variable == 'pct_control_ta':
                latest_ef = self._get_latest_examen_fisico()
                total = self.session.query(func.count(distinct(Paciente.id)))\
                    .join(latest_ef, Paciente.id == latest_ef.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).scalar() or 0
                if total == 0: return 0
                ctrl = self.session.query(func.count(distinct(Paciente.id)))\
                    .join(latest_ef, Paciente.id == latest_ef.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond,
                            latest_ef.c.sistolica_sentado <= 130,
                            latest_ef.c.diastolica_sentado <= 80).scalar() or 0
                return round(ctrl / total * 100, 1)

        

            elif variable == 'pct_retinopatia':
                total = self.session.query(func.count(distinct(Paciente.id)))\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).scalar() or 0
                if total == 0: return 0
                latest_oft = self._get_latest_oftalmologia()
                pos = self.session.query(func.count(distinct(Paciente.id)))\
                    .join(latest_oft, Paciente.id == latest_oft.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond,
                            latest_oft.c.retinopatia_diabetica.in_(
                                ['No Proliferativa', 'Proliferativa'])).scalar() or 0
                return round(pos / total * 100, 1)

            elif variable == 'pct_neuropatia':
                total = self.session.query(func.count(distinct(Paciente.id)))\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).scalar() or 0
                if total == 0: return 0
                latest_emi = self._get_latest_examen_miembros_inferiores()
                pos = self.session.query(func.count(distinct(Paciente.id)))\
                    .join(latest_emi, Paciente.id == latest_emi.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond,
                            ((latest_emi.c.LOPS_derecho == 'Si') |
                             (latest_emi.c.LOPS_izquierdo == 'Si'))).scalar() or 0
                return round(pos / total * 100, 1)

            elif variable == 'pct_hta':
                total = self.session.query(func.count(distinct(Paciente.id)))\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond).scalar() or 0
                if total == 0: return 0
                latest_ant = self._get_latest_antecedente_patologico_personal()
                pos = self.session.query(func.count(distinct(Paciente.id)))\
                    .join(latest_ant, Paciente.id == latest_ant.c.paciente_id)\
                    .join(PatologiaPersonal, PatologiaPersonal.antecedente_id == latest_ant.c.id)\
                    .filter(Paciente.fecha_hc.between(f1, f2), cond,
                            PatologiaPersonal.tipo_patologia.ilike(
                                '%Hipertension arterial%')).scalar() or 0
                return round(pos / total * 100, 1)

        except Exception as e:
            print(f'Error _calcular_metrica({variable}): {e}')
        return 0

    #  NIVEL POBLACIONAL — tarjetas nuevas

    def card_distribucion_sexo(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Distribución por Sexo').classes('text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                res = self.session.query(Paciente.sexo, func.count(distinct(Paciente.id)))\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente(),
                            Paciente.sexo.isnot(None))\
                    .group_by(Paciente.sexo).all()
                if not res:
                    _sin_datos(); return

                labels = [r[0] for r in res]
                values = [r[1] for r in res]
                colores = [COLOR_SEXO.get(l, '#90A4AE') for l in labels]

                fig = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.45,
                    marker_colors=colores,
                    textinfo='label+percent+value',
                    hovertemplate='%{label}: %{value} pacientes (%{percent})<extra></extra>'
                ))
                fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10),
                                  showlegend=True)
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_grupos_edad(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Distribución por Grupos de Edad y Sexo').classes(
                'text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                pacientes = self.session.query(Paciente)\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente()).all()

                grupos = ['<30', '30–49', '50–69', '≥70']
                datos  = {g: {'Masculino': 0, 'Femenino': 0, 'Otro': 0} for g in grupos}

                for p in pacientes:
                    edad = self.calcular_edad(p.ci)
                    if not isinstance(edad, int): continue
                    if   edad < 30: g = '<30'
                    elif edad < 50: g = '30–49'
                    elif edad < 70: g = '50–69'
                    else:           g = '≥70'
                    sexo = p.sexo if p.sexo in ('Masculino', 'Femenino') else 'Otro'
                    datos[g][sexo] += 1

                if not any(sum(d.values()) for d in datos.values()):
                    _sin_datos(); return

                fig = go.Figure()
                for sexo, color in [('Masculino', '#1E88E5'), ('Femenino', '#EC407A'), ('Otro', '#90A4AE')]:
                    vals = [datos[g][sexo] for g in grupos]
                    if any(vals):
                        fig.add_trace(go.Bar(
                            x=grupos, y=vals, name=sexo,
                            marker_color=color,
                            text=vals, textposition='auto'
                        ))
                fig.update_layout(
                    barmode='stack', height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation='h', y=1.1),
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_color_piel(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Distribución por Color de Piel').classes(
                'text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                res = self.session.query(Paciente.color_piel, func.count(Paciente.id))\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente(),
                            Paciente.color_piel.isnot(None))\
                    .group_by(Paciente.color_piel)\
                    .order_by(func.count(Paciente.id).desc()).all()
                if not res:
                    _sin_datos(); return

                labels = [r[0] for r in res]
                values = [r[1] for r in res]
                colores = ['#8D6E63', '#FFCC80', '#F48FB1', '#A5D6A7',
                           '#90CAF9', '#CE93D8', '#80DEEA']

                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation='h',
                    marker_color=colores[:len(labels)],
                    text=values, textposition='outside',
                ))
                fig.update_layout(
                    height=max(250, len(labels) * 50),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(autorange='reversed'),
                    margin=dict(t=10, b=10, l=10, r=40),
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_estado_civil(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Estado Civil').classes('text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                res = self.session.query(Paciente.estado_civil, func.count(Paciente.id))\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente(),
                            Paciente.estado_civil.isnot(None))\
                    .group_by(Paciente.estado_civil)\
                    .order_by(func.count(Paciente.id).desc()).all()
                if not res:
                    _sin_datos(); return

                labels = [r[0] for r in res]
                values = [r[1] for r in res]

                fig = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.4,
                    marker_colors=['#42A5F5', '#EF5350', '#66BB6A', '#FFA726', '#AB47BC'],
                    textinfo='label+percent',
                ))
                fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_ocupacion_detalle(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Distribución por Ocupación').classes(
                'text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                res = self.session.query(Paciente.ocupacion, func.count(Paciente.id))\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente(),
                            Paciente.ocupacion.isnot(None))\
                    .group_by(Paciente.ocupacion)\
                    .order_by(func.count(Paciente.id).desc()).all()
                if not res:
                    _sin_datos(); return

                labels = [r[0] for r in res]
                values = [r[1] for r in res]
                total  = sum(values)

                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation='h',
                    marker_color='#26A69A',
                    text=[f'{v} ({v/total*100:.1f}%)' if total else v for v in values],
                    textposition='outside',
                ))
                fig.update_layout(
                    height=max(250, len(labels) * 50),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(autorange='reversed'),
                    margin=dict(t=10, b=10, l=10, r=80),
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_glucemia_debut_dist(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Glucemia al diagnóstico — Distribución por Rangos').classes(
                'text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                res = self.session.query(Paciente.glucemia_debut)\
                    .filter(Paciente.fecha_hc.between(f1, f2),
                            self._condicion_institucion_paciente(),
                            Paciente.glucemia_debut.isnot(None)).all()
                if not res:
                    _sin_datos(); return

                rangos_lbl = ['<7.0', '7.0–10.9', '11.0–16.6', '16.7–22.1', '≥22.2']
                rangos_cnt = [0, 0, 0, 0, 0]
                for (g,) in res:
                    if   g < 7.0:   rangos_cnt[0] += 1
                    elif g < 11.0:  rangos_cnt[1] += 1
                    elif g < 16.7:  rangos_cnt[2] += 1
                    elif g < 22.2:  rangos_cnt[3] += 1
                    else:           rangos_cnt[4] += 1

                colores = ['#4CAF50', '#FFCA28', '#FF7043', '#EF5350', '#B71C1C']
                fig = go.Figure(go.Bar(
                    x=rangos_lbl, y=rangos_cnt,
                    marker_color=colores,
                    text=rangos_cnt, textposition='auto',
                ))
                fig.update_layout(
                    height=300,
                    xaxis_title='Glucemia (mmol/L)',
                    yaxis_title='Pacientes',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=40, l=20, r=20),
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)

    def card_tratamiento_dist(self, f1, f2):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Distribución del Tratamiento Actual').classes(
                'text-lg font-bold text-gray-800 mb-3 border-b pb-2')
            try:
                subq = self.session.query(
                    TratamientoActual.paciente_id,
                    func.max(TratamientoActual.fecha_registro).label('max_f')
                ).group_by(TratamientoActual.paciente_id).subquery()

                res = self.session.query(
                    TratamientoActual.tratamiento,
                    func.count(TratamientoActual.paciente_id)
                ).join(subq, and_(
                    TratamientoActual.paciente_id == subq.c.paciente_id,
                    TratamientoActual.fecha_registro == subq.c.max_f
                )).join(Paciente)\
                .filter(Paciente.fecha_hc.between(f1, f2),
                        self._condicion_institucion_paciente(),
                        TratamientoActual.tratamiento.isnot(None))\
                .group_by(TratamientoActual.tratamiento)\
                .order_by(func.count(TratamientoActual.paciente_id).desc()).all()

                if not res:
                    _sin_datos(); return

                labels = [r[0] for r in res]
                values = [r[1] for r in res]

                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation='h',
                    marker_color='#5C6BC0',
                    text=values, textposition='outside',
                ))
                fig.update_layout(
                    height=max(280, len(labels) * 45),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(autorange='reversed'),
                    margin=dict(t=10, b=10, l=10, r=60),
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                _card_error(e)



    def calcular_edad(self, ci):
        try:
            if not ci or not isinstance(ci, str) or len(ci) < 6:
                return 'No disponible'

            if not ci[:6].isdigit():
                return 'No disponible'

            year_2d = int(ci[0:2])
            month   = int(ci[2:4])
            day     = int(ci[4:6])

            # ✅ Umbral dinámico basado en el año actual
            hoy = datetime.now()
            anio_actual_2d = hoy.year % 100  # ej: 2026 → 26

            if year_2d <= anio_actual_2d:
                year = 2000 + year_2d   # 00–26 → 2000–2026
            else:
                year = 1900 + year_2d   # 27–99 → 1927–1999

            # Validar mes y día antes de construir la fecha
            fecha_nacimiento = datetime(year, month, day)  # lanza ValueError si es inválido

            edad = (
                hoy.year - fecha_nacimiento.year
                - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            )
            return edad

        except (ValueError, TypeError):
            return 'No disponible'


    def card_modo_debut(self, f_inicio, f_fin):
        with ui.card().classes('shadow-lg rounded-xl p-6 mb-6 hover:shadow-xl transition-shadow duration-300'):
            ui.label('Distribución de las Formas de Presentación al Diagnóstico').classes(
                'text-xl font-bold text-gray-800 mb-4 border-b pb-2')
            session = self.session
            try:
                debut_distribution = (
                    session.query(
                        Paciente.forma_presentacion_diagnostico,
                        func.count(Paciente.id).label('count'))
                    .filter(Paciente.forma_presentacion_diagnostico.isnot(None))
                    .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                            self._condicion_institucion_paciente())
                    .group_by(Paciente.forma_presentacion_diagnostico)
                    .order_by(func.count(Paciente.id).desc())
                    .all()
                )
                if not debut_distribution:
                    _sin_datos(); return

                modes      = [item[0] for item in debut_distribution]
                counts     = [item[1] for item in debut_distribution]
                total      = sum(counts)
                if total == 0:
                    _sin_datos(); return
                percentages = [round(c / total * 100, 1) for c in counts]

                fig = go.Figure(data=[go.Pie(
                    labels=modes, values=counts, hole=0.4,
                    marker=dict(colors=['#42A5F5','#FF7043','#66BB6A',
                                        '#FFEE58','#26C6DA','#EC407A']),
                    hovertemplate='**%{label}**: %{value} (%{percent})<extra></extra>',
                    textinfo='percent+label'
                )])
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), height=300,
                    showlegend=True, font=dict(size=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                ui.plotly(fig).classes('w-full h-72')

                with ui.expansion('Ver datos detallados').classes('w-full mt-4'):
                    columns = [
                        {'name': 'modo',       'label': 'Modo de Debut', 'field': 'modo',       'align': 'left'},
                        {'name': 'count',      'label': 'Pacientes',     'field': 'count',      'align': 'center'},
                        {'name': 'percentage', 'label': 'Porcentaje',    'field': 'percentage', 'align': 'center'},
                    ]
                    rows = [{'modo': m, 'count': c, 'percentage': f'{p}%'}
                            for m, c, p in zip(modes, counts, percentages)]
                    ui.table(columns=columns, rows=rows, row_key='modo').classes('w-full')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')
                print(f'Error card_modo_debut: {e}')

    def card_obesidad_debut(self, f_inicio, f_fin):
        with ui.card().classes('shadow-lg rounded-xl p-6 mb-6 hover:shadow-xl transition-shadow duration-300'):
            ui.label('Distribución de Exceso de Peso al Diagnóstico').classes(
                'text-lg font-semibold text-gray-800 mb-4')
            session = self.session
            try:
                obesity_data = session.query(
                    Paciente.exceso_peso_diagnostico,
                    func.count(Paciente.id).label('count')
                ).filter(
                    Paciente.exceso_peso_diagnostico.isnot(None),
                    Paciente.fecha_hc.between(f_inicio, f_fin),
                    self._condicion_institucion_paciente()
                ).group_by(Paciente.exceso_peso_diagnostico).all()
                
                if not obesity_data:
                    _sin_datos(); return

                # 1. Iniciamos el mapa con las categorías que queremos mostrar
                data_map = {'Si': 0, 'No': 0, 'No Precisado': 0}

                for item in obesity_data:
                    # Normalizamos el valor de la base de datos para evitar errores de mayúsculas/espacios
                    valor_db = str(item[0]).strip() if item[0] else "No Precisado"
                    cantidad = item[1]

                    if valor_db == 'Si':
                        data_map['Si'] += cantidad
                    elif valor_db == 'No':
                        data_map['No'] += cantidad
                    else:
                        # Aquí caen 'No Precisado', None, o cualquier otro valor
                        data_map['No Precisado'] += cantidad

                # 2. Preparamos los datos para Plotly filtrando solo los que tienen valores > 0
                labels, values, colors = [], [], []

                # Categoría: Sí
                if data_map['Si'] > 0:
                    labels.append('Con Obesidad')
                    values.append(data_map['Si'])
                    colors.append('#FF6B6B') # Rojo

                # Categoría: No
                if data_map['No'] > 0:
                    labels.append('Sin Obesidad')
                    values.append(data_map['No'])
                    colors.append('#6BCB77') # Verde

                # Categoría: No Precisado (Opcional: puedes comentarlo si no quieres que salga en el gráfico)
                if data_map['No Precisado'] > 0:
                    labels.append('No Precisado')
                    values.append(data_map['No Precisado'])
                    colors.append('#94A3B8') # Gris
                fig = go.Figure(data=[go.Pie(
                    labels=labels, values=values, textinfo='percent+label',
                    hole=0.3, marker=dict(colors=colors),
                    hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
                )])
                fig.update_layout(height=350, margin=dict(t=0, b=40, l=0, r=0))
                ui.plotly(fig).classes('w-full h-72')
            except Exception as e:
                print(e)

    def total_pacientes_card(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 hover:shadow-2xl'):
            with ui.column().classes('items-center gap-2 text-center'):
                ui.icon('people', size='32px', color='blue-600')
                ui.label('Pacientes en Periodo').classes('font-semibold text-lg text-blue-700')
                count = self.session.query(func.count(Paciente.id))\
                    .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                            self._condicion_institucion_paciente())\
                    .scalar() or 0
                ui.label(str(count)).classes('text-3xl font-bold text-gray-900')

    def antecedentes_familiares_card(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 hover:shadow-2xl transition-shadow duration-300 border-t-4 border-purple-500'):
            with ui.column().classes('items-center gap-2 text-center w-full'):
                ui.icon('family_restroom', size='32px', color='purple-600')
                ui.label('Diabetes Familiar').classes('text-lg font-semibold text-gray-700')
                session = self.session
                try:
                    total = session.query(func.count(distinct(Paciente.id)))\
                        .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                                self._condicion_institucion_paciente()).scalar() or 0
                    family = session.query(func.count(distinct(Paciente.id)))\
                        .join(AntecedentePatologicoFamiliarDiabetes)\
                        .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                                self._condicion_institucion_paciente()).scalar() or 0
                    percentage = round((family / total) * 100, 1) if total > 0 else 0
                    ui.label(f'{family} ({percentage}%)').classes('text-3xl font-bold text-purple-700')
                    ui.label('Pacientes con carga genética del periodo').classes(
                        'text-xs text-gray-500 uppercase tracking-wider')
                    ui.button().props('flat icon=info').classes('text-purple-400 hover:text-purple-700')\
                        .tooltip(f'De {total} pacientes, {family} tienen antecedentes familiares')
                except Exception as e:
                    print(f'Error antecedentes_familiares_card: {e}')
                    ui.label('Error de datos').classes('text-red-500')

    def hipertension_card(self, f_inicio, f_fin):
        try:
            latest_ant = self._get_latest_antecedente_patologico_personal()
            total_hta = self.session.query(func.count(distinct(Paciente.id)))\
                .join(latest_ant, Paciente.id == latest_ant.c.paciente_id)\
                .join(PatologiaPersonal, PatologiaPersonal.antecedente_id == latest_ant.c.id)\
                .filter(PatologiaPersonal.tipo_patologia.ilike('%Hipertension arterial%'))\
                .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                        self._condicion_institucion_paciente())\
                .scalar() or 0
            total_periodo = self.session.query(func.count(distinct(Paciente.id)))\
                .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                        self._condicion_institucion_paciente())\
                .scalar() or 0
            porcentaje = (total_hta / total_periodo * 100) if total_periodo > 0 else 0

            with ui.card().classes('w-full shadow-md border-l-8 border-blue-600'):
                with ui.row().classes('items-center no-wrap pb-2'):
                    ui.icon('monitor_heart', color='blue-600').classes('text-4xl')
                    with ui.column().classes('ml-2'):
                        ui.label('Hipertensión').classes('text-xs text-grey-6 font-bold uppercase tracking-wider')
                        ui.label('Incidencia en Periodo').classes('text-caption text-grey-5')
                with ui.row().classes('items-end justify-between w-full'):
                    ui.label(f'{total_hta}').classes('text-4xl font-black text-blue-900')
                    with ui.element('div').classes('text-right'):
                        ui.label(f'{porcentaje:.1f}%').classes('text-lg font-bold text-blue-600')
                        ui.label('de los nuevos').classes('text-micro text-grey-5')
        except Exception as e:
            print(f'Error hipertension_card: {e}')
    def nefropatia_card(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 hover:shadow-2xl transition-shadow duration-300'):
            with ui.column().classes('items-center gap-2 text-center'):
                ui.icon('kidney', size='32px', color='teal-600')
                ui.label('Enfermedad Renal Diabética').classes('text-lg font-semibold text-gray-700')
                session = self.session
                try:
                    total = session.query(func.count(distinct(Paciente.id)))\
                        .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                                self._condicion_institucion_paciente()).scalar() or 0
                    
                    latest_nef = self._get_latest_nefrologia()
                    
                    # 1. Filtramos por el nuevo campo y el valor exacto
                    with_neph = session.query(func.count(distinct(Paciente.id)))\
                        .join(latest_nef, Paciente.id == latest_nef.c.paciente_id)\
                        .filter(latest_nef.c.diagnostico_renal == 'Enfermedad Renal Diabética')\
                        .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                                self._condicion_institucion_paciente()).scalar() or 0
                    
                    percentage = round((with_neph / total) * 100, 1) if total > 0 else 0
                    ui.label(f'{with_neph} ({percentage}%)').classes('text-3xl font-bold text-teal-700')
                    ui.button().props('flat icon=info').classes('text-blue-500 hover:text-blue-700')\
                        .tooltip(f'De {total} pacientes, {with_neph} tienen diagnóstico de Enfermedad Renal Diabética')
                except Exception as e:
                    print(f'Error nefropatia_card: {e}')
                    ui.label('Error').classes('text-red-500')

    def card_promedio_edad(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 border-l-8 border-teal-500'):
            with ui.row().classes('items-center w-full justify-between'):
                ui.icon('cake', size='42px', color='teal-600')
                try:
                    pacientes = self.session.query(Paciente)\
                        .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                                self._condicion_institucion_paciente()).all()
                    edades  = [p.edad_actual for p in pacientes
                               if isinstance(p.edad_actual, int)]
                    promedio = round(sum(edades) / len(edades), 1) if edades else 0
                    with ui.column().classes('items-end'):
                        ui.label('Edad Promedio').classes('text-xs text-gray-500 font-bold uppercase')
                        ui.label(f'{promedio} años').classes('text-3xl font-black text-teal-700')
                        ui.label(f'Basado en {len(edades)} pacientes').classes('text-micro text-gray-400')
                except Exception as e:
                    print(f'Error card_promedio_edad: {e}')
                    ui.label('Error de cálculo').classes('text-red-500 text-xs')

    def card_promedio_e_categorias_imc(self, f_inicio, f_fin):
        try:
            subquery = self.session.query(
                Mensuraciones.paciente_id,
                func.max(Mensuraciones.fecha_registro).label('max_fecha')
            ).group_by(Mensuraciones.paciente_id).subquery()

            res = self.session.query(
                Mensuraciones.peso, Mensuraciones.talla
            ).join(subquery, and_(
                Mensuraciones.paciente_id == subquery.c.paciente_id,
                Mensuraciones.fecha_registro == subquery.c.max_fecha
            )).join(Paciente).filter(
                Paciente.fecha_hc.between(f_inicio, f_fin),
                self._condicion_institucion_paciente()
            ).all()

            imc_values = []
            for peso, talla in res:
                if peso and talla and talla > 0:
                    tm = talla / 100 if talla > 3 else talla
                    imc_values.append(peso / (tm ** 2))

            categorias = {'Bajo peso': 0, 'Normal': 0, 'Sobrepeso': 0,
                          'Obesidad G1': 0, 'Obesidad G2': 0, 'Obesidad G3': 0}
            for imc in imc_values:
                if   imc < 18.5: categorias['Bajo peso'] += 1
                elif imc < 25:   categorias['Normal'] += 1
                elif imc < 30:   categorias['Sobrepeso'] += 1
                elif imc < 35:   categorias['Obesidad G1'] += 1
                elif imc < 40:   categorias['Obesidad G2'] += 1
                else:            categorias['Obesidad G3'] += 1

            promedio_imc = round(sum(imc_values) / len(imc_values), 1) if imc_values else 0

            with ui.card().classes('w-full shadow-xl rounded-xl p-4 mb-4 border-t-8 border-orange-500'):
                with ui.row().classes('justify-between items-center w-full mb-4'):
                    with ui.column():
                        ui.label('Estado Nutricional (IMC)').classes(
                            'text-xs text-gray-500 font-bold uppercase')
                        ui.label(f'Promedio: {promedio_imc}').classes(
                            'text-2xl font-black text-slate-800')
                    ui.icon('scale', size='42px', color='orange-500')

                labels = list(categorias.keys())
                values = list(categorias.values())
                total  = len(imc_values)
                colores = ['#29B6F6','#66BB6A','#FFCA28','#FF7043','#EF5350','#B71C1C']

                fig = go.Figure(go.Bar(
                    x=labels, y=values, marker_color=colores,
                    text=[f'{v}<br>({(v/total*100):.1f}%)' if total else '0' for v in values],
                    textposition='auto',
                ))
                fig.update_layout(
                    height=300, margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(showgrid=True, gridcolor='LightGray', gridwidth=0.5),
                    xaxis=dict(tickfont=dict(size=10))
                )
                ui.plotly(fig).classes('w-full h-64')
        except Exception as e:
            print(f'Error IMC: {e}')
            ui.label('Error al procesar datos nutricionales').classes('text-red')

    def card_imc_vs_control_hta(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 mb-6'):
            ui.label('IMC vs. Presión Arterial').classes('text-lg font-semibold text-gray-800 mb-4')
            try:
                categorias_imc = ['Bajo peso', 'Normal', 'Sobrepeso',
                                  'Obesidad Grado 1', 'Obesidad Grado 2', 'Obesidad Grado 3']
                data = {cat: {'Controlada': 0, 'No Controlada': 0} for cat in categorias_imc}

                pacientes = self.session.query(Paciente).filter(
                    Paciente.fecha_hc.between(f_inicio, f_fin),
                    self._condicion_institucion_paciente()
                ).all()

                for p in pacientes:
                    mensuraciones = p.mensuraciones
                    if not mensuraciones: continue
                    um = max(mensuraciones, key=lambda x: x.fecha_registro)
                    imc = getattr(um, 'IMC', None)
                    if imc is None: continue

                    examenes = p.examen_fisico
                    if not examenes: continue
                    ue = max(examenes, key=lambda x: x.fecha_registro)
                    s, d = ue.sistolica_sentado, ue.diastolica_sentado
                    if s is None or d is None: continue

                    if   imc < 18.5: cat = 'Bajo peso'
                    elif imc < 25:   cat = 'Normal'
                    elif imc < 30:   cat = 'Sobrepeso'
                    elif imc < 35:   cat = 'Obesidad Grado 1'
                    elif imc < 40:   cat = 'Obesidad Grado 2'
                    else:            cat = 'Obesidad Grado 3'

                    estado = 'Controlada' if (s <= 130 and d <= 80) else 'No Controlada'
                    if cat in data:
                        data[cat][estado] += 1

                x          = categorias_imc
                y_control  = [data[cat]['Controlada']   for cat in categorias_imc]
                y_no_ctrl  = [data[cat]['No Controlada'] for cat in categorias_imc]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=x, y=y_control, name='TA Controlada (≤130/80)',
                    marker_color='#4CAF50', text=y_control, textposition='auto'))
                fig.add_trace(go.Bar(
                    x=x, y=y_no_ctrl, name='TA No Controlada (>130/80)',
                    marker_color='#F44336', text=y_no_ctrl, textposition='auto'))
                fig.update_layout(
                    xaxis_title='Categoría IMC', yaxis_title='Pacientes',
                    margin=dict(t=20, b=40, l=40, r=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                ui.plotly(fig).classes('w-full h-72')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')

    def card_hta_control(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 mb-6'):
            ui.label('Control de Presión Arterial por Sexo').classes('text-lg font-semibold text-gray-800 mb-4')
            try:
                subquery = self.session.query(
                    ExamenFisico.paciente_id,
                    func.max(ExamenFisico.fecha_registro).label('max_fecha')
                ).group_by(ExamenFisico.paciente_id).subquery()

                res = self.session.query(
                    Paciente.sexo,
                    ExamenFisico.sistolica_sentado,
                    ExamenFisico.diastolica_sentado
                ).join(subquery, and_(
                    ExamenFisico.paciente_id == subquery.c.paciente_id,
                    ExamenFisico.fecha_registro == subquery.c.max_fecha
                )).join(Paciente).filter(
                    Paciente.fecha_hc.between(f_inicio, f_fin),
                    self._condicion_institucion_paciente(),
                    Paciente.sexo.in_(['Masculino', 'Femenino'])
                ).all()

                datos = {
                    'Controlada (≤130/80)': {'Masculino': 0, 'Femenino': 0},
                    'No Controlada':        {'Masculino': 0, 'Femenino': 0},
                }
                for sexo, sistolica, diastolica in res:
                    if sistolica is None or diastolica is None: continue
                    estado = 'Controlada (≤130/80)' if (sistolica <= 130 and diastolica <= 80) else 'No Controlada'
                    datos[estado][sexo] += 1

                categorias = ['Controlada (≤130/80)', 'No Controlada']
                masculino  = [datos[cat]['Masculino'] for cat in categorias]
                femenino   = [datos[cat]['Femenino']  for cat in categorias]

                fig = go.Figure()
                fig.add_trace(go.Bar(x=categorias, y=masculino, name='Masculino',
                                     marker_color='#1E88E5', text=masculino, textposition='auto'))
                fig.add_trace(go.Bar(x=categorias, y=femenino,  name='Femenino',
                                     marker_color='#EC407A', text=femenino,  textposition='auto'))
                fig.update_layout(
                    barmode='stack',
                    margin=dict(t=20, b=10, l=0, r=0),
                    yaxis_title='Número de pacientes',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(x=0, y=1.1, orientation='h')
                )
                ui.plotly(fig).classes('w-full h-64')
            except Exception as e:
                ui.label(f'Error al cargar control HTA').classes('text-red-500')
                print(f'Error card_hta_control: {e}')

    
    def card_glucemia_media_por_grupo_edad(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 mb-6'):
            ui.label('Glucemia media por grupo de edad').classes('text-h6')
            rows = []
            for p in self.session.query(Paciente).filter(
                Paciente.fecha_hc.between(f_inicio, f_fin),
                self._condicion_institucion_paciente()
            ).all():
                try:
                    edad = self.calcular_edad(p.ci)
                except AttributeError:
                    continue
                if isinstance(edad, str): continue

                if   edad < 30: grupo = '<30'
                elif edad < 50: grupo = '30-49'
                elif edad < 70: grupo = '50-69'
                else:           grupo = '≥70'

                if p.complementarios:
                    c = max(p.complementarios, key=lambda x: x.fecha_registro)
                    if c.glucemia is not None:
                        rows.append({'edad_grp': grupo, 'glucemia': c.glucemia})

            df = pd.DataFrame(rows)
            if df.empty:
                ui.label('No hay datos de glucemia disponibles').classes('text-caption')
                return

            orden = ['<30', '30-49', '50-69', '≥70']
            stats = df.groupby('edad_grp')['glucemia'].mean().reset_index(name='mean')
            stats['edad_grp'] = pd.Categorical(stats['edad_grp'], categories=orden, ordered=True)
            stats = stats.sort_values('edad_grp')

            fig = px.bar(stats, x='edad_grp', y='mean',
                         labels={'edad_grp': 'Grupo de edad', 'mean': 'Glucemia media (mmol/L)'},
                         title='Glucemia por Grupo de Edad', height=400)
            fig.update_traces(marker_color='steelblue', opacity=0.8,
                              texttemplate='%{y:.2f}', textposition='outside')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(t=30, b=10, l=10, r=10),
                              yaxis_title='Glucemia (mmol/L)')
            if not stats.empty:
                fig.update_yaxes(range=[0, stats['mean'].max() * 1.2])
            ui.plotly(fig).classes('w-full')

    def card_clasificacion_diabetes(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6 border-t-8 border-blue-800'):
            ui.label('Distribución Clínica de Diabetes').classes('text-lg font-bold text-slate-800 mb-2')
            ui.label('Basado en la última indicación registrada por paciente').classes(
                'text-xs text-slate-500 mb-4')
            try:
                subquery = self.session.query(
                    Indicaciones.paciente_id,
                    func.max(Indicaciones.fecha_registro).label('max_fecha')
                ).group_by(Indicaciones.paciente_id).subquery()

                results = self.session.query(
                    Indicaciones.tipo_diabetes,
                    func.count(Indicaciones.paciente_id)
                ).join(subquery, and_(
                    Indicaciones.paciente_id == subquery.c.paciente_id,
                    Indicaciones.fecha_registro == subquery.c.max_fecha
                )).join(Paciente).filter(
                    Paciente.fecha_hc.between(f_inicio, f_fin),
                    self._condicion_institucion_paciente()
                ).group_by(Indicaciones.tipo_diabetes).all()

                cats = [
                    'Diabetes Mellitus Tipo 1 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 1 Con Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Sin Evidencias de Complicaciones',
                    'Diabetes Mellitus Tipo 2 Con Evidencias de Complicaciones',
                ]
                counts = {cat: 0 for cat in cats}
                for tipo, cnt in results:
                    if tipo in counts: counts[tipo] = cnt

                y_labels = ['T1 - Sin Comp.', 'T1 - Con Comp.', 'T2 - Sin Comp.', 'T2 - Con Comp.']
                valores  = [counts[cat] for cat in cats]
                colores  = ['#64B5F6', '#EF5350', '#1976D2', '#C62828']

                fig = go.Figure(go.Bar(
                    x=valores, y=y_labels, orientation='h',
                    marker_color=colores,
                    text=[f' {v} pac.' for v in valores],
                    textposition='outside', cliponaxis=False
                ))
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=40), height=300,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(autorange='reversed'),
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                print(f'Error card_clasificacion_diabetes: {e}')

    def card_comorbilidades(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Comorbilidades Más Frecuentes').classes('text-h6 font-semibold mb-2')
            session = self.session
            try:
                latest_ant = self._get_latest_antecedente_patologico_personal()

                patologias = session.query(
                    PatologiaPersonal.tipo_patologia,
                    func.count(distinct(Paciente.id))
                )\
                .join(latest_ant, Paciente.id == latest_ant.c.paciente_id)\
                .join(PatologiaPersonal, PatologiaPersonal.antecedente_id == latest_ant.c.id)\
                .filter(
                    Paciente.fecha_hc.between(f_inicio, f_fin),
                    self._condicion_institucion_paciente()
                )\
                .group_by(PatologiaPersonal.tipo_patologia)\
                .order_by(func.count(distinct(Paciente.id)).desc())\
                .limit(6)\
                .all()

                if not patologias:
                    ui.label('Sin datos').classes('text-gray-500'); return

                labels = [p[0] for p in patologias]
                values = [p[1] for p in patologias]

                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation='h',
                    marker_color='#7E57C2'
                ))
                fig.update_layout(
                    height=350,
                    xaxis_title='Número de pacientes',
                    yaxis=dict(autorange='reversed'),
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')

    def card_escolaridad_ocupacion(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Nivel Educacional y Ocupación').classes('text-h6 font-semibold mb-2')
            session = self.session
            try:
                escolaridad = session.query(Paciente.escolaridad, func.count(Paciente.id))\
                    .filter(Paciente.escolaridad.isnot(None))\
                    .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                            self._condicion_institucion_paciente())\
                    .group_by(Paciente.escolaridad).all()

                ocupacion = session.query(Paciente.ocupacion, func.count(Paciente.id))\
                    .filter(Paciente.ocupacion.isnot(None))\
                    .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                            self._condicion_institucion_paciente())\
                    .group_by(Paciente.ocupacion)\
                    .order_by(func.count(Paciente.id).desc())\
                    .limit(8).all()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[e[0] for e in escolaridad], y=[e[1] for e in escolaridad],
                    name='Nivel Educacional', marker_color='#26A69A'))
                fig.add_trace(go.Bar(
                    x=[o[0] for o in ocupacion], y=[o[1] for o in ocupacion],
                    name='Ocupación (Top 8)', marker_color='#FFA726', visible='legendonly'))
                fig.update_layout(
                    height=350, barmode='group', xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)')
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')

    def card_filtrado_glomerular(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Clasificación del Filtrado Glomerular').classes('text-h6 font-semibold mb-2')
            session = self.session
            try:
                latest_nef = self._get_latest_nefrologia()
                nefros = session.query(latest_nef.c.filtrado_glomerular_teorico)\
                    .join(Paciente, Paciente.id == latest_nef.c.paciente_id)\
                    .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                            self._condicion_institucion_paciente()).all()
                g1 = g2 = g3a = g3b = g4 = g5 = 0
                for (fg,) in nefros:
                    if fg is None: continue
                    if   fg >= 90:       g1  += 1
                    elif 60 <= fg < 90:  g2  += 1
                    elif 45 <= fg < 60:  g3a += 1
                    elif 30 <= fg < 45:  g3b += 1
                    elif 15 <= fg < 30:  g4  += 1
                    elif fg < 15:        g5  += 1

                labels = ['G1 (≥90)','G2 (60-89)','G3A (45-59)',
                          'G3B (30-44)','G4 (15-29)','G5 (<15)']
                values = [g1, g2, g3a, g3b, g4, g5]
                fig = go.Figure(go.Bar(
                    x=labels, y=values,
                    marker_color=['#4CAF50','#81C784','#FFB74D','#FF8A65','#EF5350','#D32F2F']
                ))
                fig.update_layout(
                    height=300, xaxis_title='Estadio de ERC', yaxis_title='Pacientes',
                    plot_bgcolor='rgba(0,0,0,0)')
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')

    def card_lipidos_y_nefropatia(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Perfil Lipídico y Daño Renal Diabético').classes('text-lg font-semibold text-gray-800 mb-4')
            session = self.session
            try:
                latest_comp = self._get_latest_complementarios()
                latest_nef = self._get_latest_nefrologia()
                
                # 1. Cambiamos la columna solicitada a 'diagnostico_renal'
                results = session.query(
                    latest_comp.c.colesterol,
                    latest_comp.c.trigliceridos,
                    latest_nef.c.diagnostico_renal
                ).join(Paciente, Paciente.id == latest_comp.c.paciente_id)\
                 .outerjoin(latest_nef, Paciente.id == latest_nef.c.paciente_id)\
                 .filter(
                     latest_comp.c.colesterol.isnot(None),
                     latest_comp.c.trigliceridos.isnot(None),
                     Paciente.fecha_hc.between(f_inicio, f_fin),
                     self._condicion_institucion_paciente()
                 ).all()

                cats = [
                    'Colesterol Normal + Trig. Normal', 'Colesterol Riesgo + Trig. Normal',
                    'Colesterol Alto + Trig. Normal',   'Colesterol Normal + Trig. Alto',
                    'Colesterol Riesgo + Trig. Alto',   'Colesterol Alto + Trig. Alto'
                ]
                
                # Puedes cambiar estos textos si quieres ser más específico clínicamente
                data = {cat: {'Con nefropatía': 0, 'Sin nefropatía': 0} for cat in cats}

                for col, trig, nefro in results:
                    col_cat  = 'Normal' if col < 5.17 else ('Riesgo' if col <= 6.2 else 'Alto')
                    trig_cat = 'Normal' if trig <= 1.7 else 'Alto'
                    key = f'Colesterol {col_cat} + Trig. {trig_cat}'
                    
                    if key in data:
                        # 2. Validamos contra el nuevo string exacto
                        es_nefropata = (nefro == 'Enfermedad Renal Diabética')
                        data[key]['Con nefropatía' if es_nefropata else 'Sin nefropatía'] += 1

                fig = go.Figure()
                fig.add_trace(go.Bar(x=cats, y=[data[c]['Con nefropatía'] for c in cats],
                                     name='Con Daño Renal Diabético', marker_color='#E53935'))
                fig.add_trace(go.Bar(x=cats, y=[data[c]['Sin nefropatía'] for c in cats],
                                     name='Sin Daño / Otras', marker_color='#4CAF50'))
                fig.update_layout(
                    barmode='stack', height=400,
                    xaxis_title='Perfil lipídico', yaxis_title='Número de pacientes',
                    plot_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45,
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                ui.plotly(fig).classes('w-full h-72')
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500')

    def card_correlacion_tiempo_complicaciones(self, f_inicio, f_fin):
        with ui.card().classes('w-full shadow-xl rounded-xl p-6'):
            ui.label('Correlación: Tiempo de Evolución vs. Complicaciones').classes('text-h6')
            session = self.session
            try:
                latest_nef = self._get_latest_nefrologia()
                latest_oft = self._get_latest_oftalmologia()
                latest_emi = self._get_latest_examen_miembros_inferiores()
                
                # 1. Ajuste: pedimos 'diagnostico_renal' en lugar de 'nefropatia_diabetica'
                results = session.query(
                    Paciente.id,
                    Paciente.tiempo_evolucion_anios,
                    Paciente.tiempo_evolucion_meses,
                    latest_nef.c.diagnostico_renal, 
                    latest_oft.c.retinopatia_diabetica,
                    latest_emi.c.LOPS_derecho,
                    latest_emi.c.LOPS_izquierdo
                ).outerjoin(latest_nef, Paciente.id == latest_nef.c.paciente_id)\
                 .outerjoin(latest_oft, Paciente.id == latest_oft.c.paciente_id)\
                 .outerjoin(latest_emi, Paciente.id == latest_emi.c.paciente_id)\
                 .filter(Paciente.fecha_hc.between(f_inicio, f_fin),
                         self._condicion_institucion_paciente()).all()

                rangos         = ['<1 años', '1-5 años', '6-10 años', '10+ años']
                complicaciones = ['Nefropatía', 'Retinopatía', 'Neuropatía']
                conteo_total    = defaultdict(int)
                conteo_afect    = defaultdict(int)

                for row in results:
                    anios = (row.tiempo_evolucion_anios or 0) + \
                            ((row.tiempo_evolucion_meses or 0) / 12)
                    if   anios < 1:  rango = '<1 años'
                    elif anios < 5:  rango = '1-5 años'
                    elif anios < 10: rango = '6-10 años'
                    else:            rango = '10+ años'

                    # 2. Ajuste: La nefropatía se cuenta si el diagnóstico es específicamente el diabético
                    tiene = [
                        row.diagnostico_renal == 'Enfermedad Renal Diabética',
                        row.retinopatia_diabetica in ['No Proliferativa', 'Proliferativa'],
                        (row.LOPS_derecho == 'Si') or (row.LOPS_izquierdo == 'Si')
                    ]
                    
                    for comp, t in zip(complicaciones, tiene):
                        key = (rango, comp)
                        conteo_total[key] += 1
                        if t: conteo_afect[key] += 1

                z_data = []
                for comp in complicaciones:
                    row_vals = []
                    for rango in rangos:
                        key   = (rango, comp)
                        tot   = conteo_total[key]
                        afect = conteo_afect[key]
                        row_vals.append(round(afect / tot * 100, 1) if tot > 0 else 0)
                    z_data.append(row_vals)

                fig = go.Figure(data=go.Heatmap(
                    z=z_data, x=rangos, y=complicaciones,
                    colorscale='Reds', text=z_data,
                    texttemplate='%{text}%',
                    colorbar=dict(title='Porcentaje')
                ))
                fig.update_layout(
                    height=350, margin=dict(l=20, r=20, t=40, b=60),
                    xaxis_title='Rango de Tiempo', yaxis_title='Complicación'
                )
                ui.plotly(fig).classes('w-full')
            except Exception as e:
                ui.label(f'Error: {str(e)}').classes('text-red-500')