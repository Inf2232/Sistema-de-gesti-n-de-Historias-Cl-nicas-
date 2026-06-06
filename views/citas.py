from datetime import datetime, timedelta, date
from nicegui import ui
import locale
from sidebar import SidebarReutilizable
from controllers.cita_controller import CitaController
from authenticar import devolver_usuario_actual, cerrar_sesion


# DESIGN TOKENS
# ---------------------------------------------------------------------------
PAGE_PADDING = 'q-pa-md'
GAP_SM       = 'q-gutter-sm'
GAP_MD       = 'q-gutter-md'
CARD_BASE    = 'rounded-xl shadow-2 bg-white'
INPUT_PROPS  = 'outlined dense rounded'
INPUT_COLOR  = 'color=primary'
BTN_PRIMARY  = 'color=primary unelevated rounded'
BTN_SUCCESS  = 'color=positive unelevated rounded'
BTN_DANGER   = 'color=negative flat round dense'
TEXT_H5      = 'text-h5 text-weight-bold text-primary'
TEXT_SUBTITLE= 'text-subtitle2 text-grey-7'
TEXT_CAPTION = 'text-caption text-grey-6'
CHIP_TIME    = 'bg-blue-1 text-blue-8 text-weight-bold rounded-lg'
CHIP_DATE    = 'bg-teal-1 text-teal-8 text-weight-bold rounded-lg'

try:
    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
except Exception:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except Exception:
        pass



class CitasPage:
    def __init__(self):
        # ── Setup de UI y Controlador ───────────────────────────────────────
        self.ctrl = CitaController() 
        
        self._select_paciente   = None   
        self._pacientes_cache   = {}
        self._dialog            = None
        self.selected_date      = date.today()
        self.citas_del_dia      = []
        self.proximas_citas     = []
        self.search_text        = None

        self.sidebar  = SidebarReutilizable(self)
        self.setup_sidebar()
        self.setup_navigation()


    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------
    def setup_navigation(self):
        with ui.header() \
                .classes('items-center justify-between q-px-md q-py-xs shadow-3') \
                .style('background:linear-gradient(135deg,#1565C0 0%,#0D47A1 100%);'
                       'position:sticky;top:0;z-index:2000;'):

            ui.add_head_html('''
                <style>
                    #c1 { padding-top: 0 !important; }
                    .cita-card-hover { transition: box-shadow .2s, transform .15s; }
                    .cita-card-hover:hover {
                        box-shadow: 0 8px 24px rgba(21,101,192,.18) !important;
                        transform: translateY(-2px);
                    }
                    .stat-number { font-size: 2rem; font-weight: 800; line-height: 1; }
                    .timeline-line {
                        border-left: 2px dashed #BBDEFB;
                        margin-left: 6px;
                    }
                </style>
            ''')

            with ui.row().classes('items-center no-wrap ' + GAP_SM):
                ui.button(icon='menu', on_click=self.sidebar.toggle) \
                    .props('flat round color=white size=sm')
                ui.button(icon='arrow_back', on_click=ui.navigate.back) \
                    .props('flat round color=white size=sm')
                with ui.row().classes('items-center no-wrap q-gutter-x-xs'):
                    ui.icon('calendar_month').classes('text-white text-h5')
                    ui.label('Citas').classes('text-white text-h6 text-weight-bold gt-xs')

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

    # -----------------------------------------------------------------------
    # PÁGINA PRINCIPAL
    # -----------------------------------------------------------------------
    @ui.refreshable
    def mostrar_page(self):
        with ui.column().classes(f'w-full {PAGE_PADDING} ' + GAP_MD):

            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('gap-0'):
                    ui.label('Gestión de Citas Médicas').classes(TEXT_H5)
                    ui.label(
                        f'Hoy: {date.today().strftime("%A %d de %B, %Y").capitalize()}'
                    ).classes(TEXT_SUBTITLE)

            ui.separator().props('color=blue-3')

            self._render_stats()

            # Grid responsivo: 1 col móvil / 3 cols desktop
            with ui.element('div').classes('row q-col-gutter-md w-full'):

                # Columna izquierda — Búsqueda + Nueva cita
                with ui.element('div').classes('col-12 col-md-4'):
                    self._render_panel_busqueda()
                    self._render_panel_agregar_cita()

                # Columna central — Citas del día
                with ui.element('div').classes('col-12 col-md-4'):
                    self._render_citas_dia()

                # Columna derecha — Próximas citas
                with ui.element('div').classes('col-12 col-md-4'):
                    self._render_proximas_citas()

    # -----------------------------------------------------------------------
    # KPI STATS
    # -----------------------------------------------------------------------
    def _render_stats(self):
        total_hoy      = len(self.citas_del_dia)
        total_proximas = len(self.proximas_citas)
        proxima_hora   = '—'
        ahora          = datetime.now().time()
        futuras_hoy    = [c for c in self.citas_del_dia if c.hora >= ahora]
        if futuras_hoy:
            proxima_hora = futuras_hoy[0].hora.strftime('%H:%M')

        stats = [
            ('event_note',  str(total_hoy),      'Citas hoy',       '#1565C0', '#E3F2FD'),
            ('schedule',    proxima_hora,         'Próxima hora',    '#00695C', '#E0F2F1'),
            ('date_range',  str(total_proximas),  'Próximos 7 días', '#6A1B9A', '#F3E5F5'),
        ]

        with ui.row().classes('w-full ' + GAP_SM + ' no-wrap lt-sm:flex-col'):
            for icon, valor, label, color_text, color_bg in stats:
                with ui.card().classes(CARD_BASE + ' q-pa-md flex-1') \
                        .style(f'border-left:4px solid {color_text};'):
                    with ui.row().classes('items-center ' + GAP_SM + ' no-wrap'):
                        with ui.element('div').classes('rounded-lg q-pa-sm') \
                                .style(f'background:{color_bg};'):
                            ui.icon(icon).style(f'color:{color_text};font-size:1.6rem;')
                        with ui.column().classes('gap-0'):
                            ui.label(valor).classes('stat-number').style(f'color:{color_text};')
                            ui.label(label).classes(TEXT_CAPTION)

    # -----------------------------------------------------------------------
    # PANEL BÚSQUEDA
    # -----------------------------------------------------------------------
    def _render_panel_busqueda(self):
        with ui.card().classes(CARD_BASE + ' q-pa-md ' + GAP_SM):
            with ui.row().classes('items-center ' + GAP_SM):
                ui.icon('manage_search').classes('text-primary text-h5')
                ui.label('Buscar Citas').classes('text-subtitle1 text-weight-bold text-primary')

            ui.separator().props('color=blue-2')

            ui.label('Seleccione una fecha').classes(TEXT_CAPTION + ' q-mt-sm')
            self.calendar = ui.date(
                value=self.selected_date,
                on_change=self.actualizar_fecha
            ).props('today-btn color=primary').classes('w-full')

            ui.separator().props('color=blue-2 q-my-sm')

            self.search_text = ui.input(
                label='Buscar por CI o Nombre',
                placeholder='CI, nombre o apellido…'
            ).props(INPUT_PROPS + ' ' + INPUT_COLOR + ' clearable prepend-icon=person_search') \
             .classes('w-full')

            with ui.row().classes('w-full ' + GAP_SM + ' q-mt-sm'):
                ui.button('Buscar', icon='search', on_click=self.buscar_citas) \
                    .props(BTN_PRIMARY).classes('flex-1')
                

            ui.label('💡 Deje vacío el buscador para ver todas las citas.') \
                .classes(TEXT_CAPTION + ' text-italic q-mt-xs')

    # -----------------------------------------------------------------------
    # PANEL AGREGAR CITA
    # -----------------------------------------------------------------------
    def _render_panel_agregar_cita(self):
        with ui.card().classes(CARD_BASE + ' q-pa-md ' + GAP_SM + ' q-mt-md'):
            with ui.expansion('Nueva Cita') \
                    .props('icon=add_circle_outline expand-icon-toggle') \
                    .classes('text-subtitle1 text-weight-bold text-positive w-full'):

                ui.separator().props('color=green-2 q-mb-md')

                ui.label('Paciente').classes(TEXT_CAPTION + ' text-weight-bold q-mb-xs')

                # El select se asigna AQUÍ — el atributo existe desde este momento
                self._select_paciente = (
                        ui.select(
                            options=[],
                            label='Seleccionar paciente',
                            with_input=True,
                            clearable=True,
                        )
                        .props('outlined dense rounded color=positive use-input hide-selected '
                            'fill-input input-debounce=300')
                        .classes('w-full')
                        .on('filter', self._filtrar_pacientes_select)
                    )

                # Carga segura: el select ya está asignado justo arriba
                self._cargar_opciones_pacientes()

                ui.separator().props('color=green-1 q-my-sm')

                with ui.row().classes('w-full ' + GAP_SM + ' lt-sm:flex-col'):
                    with ui.column().classes('flex-1 gap-0'):
                        ui.label('Fecha').classes(TEXT_CAPTION + ' text-weight-bold q-mb-xs')
                        self._input_fecha_nueva = (
                            ui.date(value=str(self.selected_date))
                            .props('outlined dense today-btn color=positive mask=YYYY-MM-DD')
                            .classes('w-full')
                        )
                    with ui.column().classes('flex-1 gap-0'):
                        ui.label('Hora').classes(TEXT_CAPTION + ' text-weight-bold q-mb-xs')
                        self._input_hora_nueva = (
                            ui.time(value='08:00')
                            .props('outlined dense color=positive format24h now-btn')
                            .classes('w-full')
                        )

                ui.separator().props('color=green-1 q-my-sm')

                ui.label('Notas / Motivo').classes(TEXT_CAPTION + ' text-weight-bold q-mb-xs')
                self._input_notas_nueva = (
                    ui.textarea(
                        label='Opcional — máx. 200 caracteres',
                        placeholder='Ej: Control mensual, revisión de resultados…',
                    )
                    .props('outlined dense rounded color=positive rows=2 maxlength=200 counter')
                    .classes('w-full')
                )

                ui.separator().props('color=green-2 q-my-sm')

                ui.button('Guardar Cita', icon='save', on_click=self._guardar_nueva_cita) \
                    .props('unelevated rounded color=positive').classes('w-full')

    # -----------------------------------------------------------------------
    # CITAS DEL DÍA
    # -----------------------------------------------------------------------
    def _render_citas_dia(self):
        fecha_str = self.selected_date.strftime('%A %d/%m/%Y').capitalize()

        with ui.card().classes(CARD_BASE + ' q-pa-md ' + GAP_SM):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center ' + GAP_SM):
                    ui.icon('today').classes('text-primary text-h5')
                    ui.label(f'Citas — {fecha_str}') \
                        .classes('text-subtitle1 text-weight-bold text-primary')
                if self.citas_del_dia:
                    ui.badge(str(len(self.citas_del_dia))).props('color=primary rounded')

            ui.separator().props('color=blue-2')

            if not self.citas_del_dia:
                self._render_empty_state('No hay citas para este día', 'event_busy')
            else:
                with ui.scroll_area().classes('w-full').style('max-height:55vh;'):
                    with ui.column().classes('w-full ' + GAP_SM + ' timeline-line q-pl-md q-py-sm'):
                        ahora = datetime.now().time()
                        for cita in self.citas_del_dia:
                            pasada = (cita.hora < ahora and cita.fecha_consulta == date.today())
                            self._render_cita_card(cita, modo='hora', pasada=pasada)

    # -----------------------------------------------------------------------
    # PRÓXIMAS CITAS
    # -----------------------------------------------------------------------
    def _render_proximas_citas(self):
        with ui.card().classes(CARD_BASE + ' q-pa-md ' + GAP_SM):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center ' + GAP_SM):
                    ui.icon('date_range').classes('text-purple text-h5')
                    ui.label('Próximas Citas (7 días)') \
                        .classes('text-subtitle1 text-weight-bold text-purple')
                if self.proximas_citas:
                    ui.badge(str(len(self.proximas_citas))).props('color=purple rounded')

            ui.separator().props('color=purple-2')

            if not self.proximas_citas:
                self._render_empty_state('No hay citas en los próximos 7 días', 'event_available')
            else:
                with ui.scroll_area().classes('w-full').style('max-height:55vh;'):
                    with ui.column().classes('w-full ' + GAP_SM + ' q-py-sm'):
                        for cita in self.proximas_citas:
                            self._render_cita_card(cita, modo='fecha')

    # -----------------------------------------------------------------------
    # TARJETA DE CITA
    # -----------------------------------------------------------------------
    def _render_cita_card(self, cita, modo: str = 'hora', pasada: bool = False):
        opacity = 'opacity:.5;' if pasada else ''

        with ui.card() \
                .classes('cita-card-hover w-full q-pa-sm rounded-xl') \
                .style(f'border:1px solid #E3F2FD;{opacity}') \
                .on('click', lambda e, c=cita: self._abrir_detalle_cita(c)):

            with ui.row().classes('items-center no-wrap w-full ' + GAP_SM):

                if modo == 'hora':
                    with ui.column().classes(
                        CHIP_TIME + ' items-center justify-center q-pa-sm rounded-lg'
                    ).style('min-width:60px;'):
                        ui.label(cita.hora.strftime('%H:%M')) \
                            .classes('text-h6 text-weight-bold text-blue-8')
                        if pasada:
                            ui.label('pasada').classes('text-caption text-grey-6')
                else:
                    with ui.column().classes(
                        CHIP_DATE + ' items-center justify-center q-pa-sm rounded-lg'
                    ).style('min-width:60px;'):
                        ui.label(cita.fecha_consulta.strftime('%d/%m')) \
                            .classes('text-subtitle2 text-weight-bold text-teal-8')
                        ui.label(cita.hora.strftime('%H:%M')) \
                            .classes('text-caption text-teal-7')

                with ui.column().classes('gap-0 flex-grow ellipsis'):
                    ui.label(f'{cita.paciente.nombres} {cita.paciente.apellidos}') \
                        .classes('text-subtitle2 text-weight-bold text-grey-9 ellipsis')
                    with ui.row().classes('items-center ' + GAP_SM + ' no-wrap'):
                        ui.chip(f'CI: {cita.paciente.ci}') \
                            .props('dense color=blue-1 text-color=blue-8 square')
                        if cita.notas:
                            texto = cita.notas[:28] + '…' if len(cita.notas) > 28 else cita.notas
                            ui.label(texto).classes(TEXT_CAPTION + ' text-italic ellipsis')

                ui.icon('chevron_right').classes('text-grey-4')

    # -----------------------------------------------------------------------
    # ESTADO VACÍO
    # -----------------------------------------------------------------------
    def _render_empty_state(self, mensaje: str, icono: str = 'inbox'):
        with ui.column().classes('items-center justify-center q-py-xl w-full gap-2'):
            ui.icon(icono).props('size=3rem color=blue-2')
            ui.label(mensaje).classes(TEXT_SUBTITLE + ' text-center')
            ui.label('Realice una búsqueda para ver resultados') \
                .classes(TEXT_CAPTION + ' text-center')

    # -----------------------------------------------------------------------
    # DIÁLOGO DE DETALLE
    # -----------------------------------------------------------------------
    def _abrir_detalle_cita(self, cita):
        paciente = cita.paciente
        nombre   = f'{paciente.nombres} {paciente.apellidos}'
        fecha    = cita.fecha_consulta.strftime('%A %d/%m/%Y').capitalize()
        hora     = cita.hora.strftime('%H:%M')
        inst     = paciente.institucion.nombre if paciente.institucion else '—'
        notas    = cita.notas or 'Sin notas registradas.'

        with ui.dialog().props('persistent') as dlg, \
             ui.card().classes('rounded-xl q-pa-lg shadow-5') \
                      .style('min-width:320px;max-width:480px;'):

            with ui.row().classes('items-center justify-between w-full q-mb-sm'):
                with ui.row().classes('items-center ' + GAP_SM):
                    ui.icon('person').props('color=primary size=md')
                    ui.label('Detalle de Cita') \
                        .classes('text-h6 text-weight-bold text-primary')
                ui.button(icon='close', on_click=dlg.close) \
                    .props('flat round dense color=grey')

            ui.separator().props('color=blue-2 q-mb-sm')

            with ui.row().classes('items-center ' + GAP_SM + ' q-mb-sm'):
                with ui.element('div') \
                        .classes('rounded-full bg-blue-1 flex items-center justify-center') \
                        .style('width:52px;height:52px;'):
                    ui.label(nombre[0].upper()) \
                        .classes('text-h5 text-weight-bold text-blue-8')
                with ui.column().classes('gap-0'):
                    ui.label(nombre).classes('text-subtitle1 text-weight-bold text-grey-9')
                    ui.chip(f'CI: {paciente.ci}') \
                        .props('dense color=blue-1 text-color=blue-8 square')

            ui.separator().props('color=blue-1 q-my-sm')

            for icono_c, label_c, valor_c in [
                ('calendar_today', 'Fecha',      fecha),
                ('schedule',       'Hora',        hora),
                ('business',       'Institución', inst),
                ('sticky_note_2',  'Notas',       notas),
            ]:
                with ui.row().classes('items-start ' + GAP_SM + ' q-mb-xs'):
                    ui.icon(icono_c).props('color=primary size=xs').classes('q-mt-xs')
                    with ui.column().classes('gap-0'):
                        ui.label(label_c).classes(TEXT_CAPTION + ' text-weight-bold')
                        ui.label(valor_c).classes('text-body2 text-grey-9')

            ui.separator().props('color=blue-2 q-my-sm')

            with ui.row().classes('justify-end ' + GAP_SM):
                ui.button('Cancelar', on_click=dlg.close).props('flat rounded color=grey')
                ui.button(
                    'Ver Historia Clínica',
                    icon='folder_open',
                    on_click=lambda: [dlg.close(), self.abrir_historia_clinica(paciente)]
                ).props(BTN_PRIMARY)

        dlg.open()

    # -----------------------------------------------------------------------
    # LÓGICA — BÚSQUEDA
    # -----------------------------------------------------------------------
    def actualizar_fecha(self, e):
        if isinstance(e.value, str):
            self.selected_date = datetime.strptime(e.value, '%Y-%m-%d').date()
        else:
            self.selected_date = e.value

    def buscar_citas(self):
        try:
            if not getattr(self, 'selected_date', None):
                ui.notify('Seleccione una fecha primero', type='warning', position='top')
                return

            if isinstance(self.selected_date, str):
                self.selected_date = datetime.strptime(self.selected_date, '%Y-%m-%d').date()

            usuario = devolver_usuario_actual()
            inst_id = usuario.get('institucion_id')
            search_query = self.search_text.value.strip() if self.search_text and self.search_text.value else ''

            # --- AQUÍ OCURRE LA MAGIA DEL MVC ---
            # Le pedimos al controlador los datos, la vista no sabe NADA de SQL.
            self.citas_del_dia, self.proximas_citas = self.ctrl.buscar_citas(
                fecha_seleccionada=self.selected_date,
                institucion_id=inst_id,
                search_text=search_query
            )

            self.mostrar_page.refresh()

            total = len(self.citas_del_dia) + len(self.proximas_citas)
            if total == 0:
                ui.notify('No se encontraron citas', type='info', position='top-right', timeout=3000)
            else:
                ui.notify(f'✅ {total} cita(s) cargadas', type='positive', position='top-right', timeout=2500)

        except Exception as exc:
            print(f'Error en controlador: {exc}')
            ui.notify('Error al buscar citas en el servidor', type='negative', position='top-right')

    def abrir_historia_clinica(self, paciente):
        ui.navigate.to(f'/historia_clinica/{paciente.no_hc}')

    # -----------------------------------------------------------------------
    # LÓGICA — PACIENTES EN SELECT
    # -----------------------------------------------------------------------
    def _cargar_opciones_pacientes(self):
        if not hasattr(self, '_select_paciente') or self._select_paciente is None:
            return
        try:
            usuario = devolver_usuario_actual()
            inst_id = usuario.get('institucion_id')
           
            # --- DELEGADO AL CONTROLADOR ---
            pacientes = self.ctrl.obtener_pacientes_activos(inst_id)
            
            self._pacientes_cache = {p.id: p for p in pacientes}
            self._select_paciente.set_options([
                (p.id, f'{p.apellidos}, {p.nombres}  —  CI: {p.ci}')
                for p in pacientes
            ])
        except Exception as exc:
            ui.notify('Error al cargar la lista de pacientes.', type='negative', position='top-right')

    def _filtrar_pacientes_select(self, e):
        texto = (e.args[0] if e.args else '').lower().strip()
        cache = getattr(self, '_pacientes_cache', {})

        if not texto:
            opciones = [
                (p.id, f'{p.apellidos}, {p.nombres}  —  CI: {p.ci}')
                for p in cache.values()
            ]
        else:
            opciones = [
                (p.id, f'{p.apellidos}, {p.nombres}  —  CI: {p.ci}')
                for p in cache.values()
                if texto in p.apellidos.lower()
                or texto in p.nombres.lower()
                or texto in str(p.ci).lower()
            ]

        self._select_paciente.set_options(opciones)
        if len(e.args) > 1 and callable(e.args[1]):
            e.args[1](opciones)

    # -----------------------------------------------------------------------
    # LÓGICA — GUARDAR CITA
    # -----------------------------------------------------------------------
    def _guardar_nueva_cita(self):
        errores = []
        valor = self._select_paciente.value
        paciente_id = valor[0] if isinstance(valor, tuple) else valor
        fecha_raw   = self._input_fecha_nueva.value if hasattr(self, '_input_fecha_nueva') else None
        hora_raw    = self._input_hora_nueva.value  if hasattr(self, '_input_hora_nueva')  else None

        if not paciente_id: errores.append('Seleccione un paciente.')
        if not fecha_raw: errores.append('Seleccione una fecha.')
        if not hora_raw: errores.append('Seleccione una hora.')

        if errores:
            ui.notify(' · '.join(errores), type='warning', position='top-right', timeout=4000)
            return

        try:
            fecha_cita = datetime.strptime(fecha_raw, '%Y-%m-%d').date() if isinstance(fecha_raw, str) else fecha_raw
            hora_cita = datetime.strptime(hora_raw, '%H:%M').time() if isinstance(hora_raw, str) else hora_raw
            notas = self._input_notas_nueva.value

            # --- DELEGADO AL CONTROLADOR ---
            exito, mensaje = self.ctrl.crear_cita(paciente_id, fecha_cita, hora_cita, notas)

            if not exito:
                ui.notify(f'⚠️ {mensaje}', type='warning', position='top-right', timeout=5000)
                return

            paciente = self._pacientes_cache.get(paciente_id)
            nombre   = f'{paciente.nombres} {paciente.apellidos}' if paciente else '—'
            ui.notify(
                f'✅ Cita guardada — {nombre} · {fecha_cita.strftime("%d/%m/%Y")} {hora_cita.strftime("%H:%M")}',
                type='positive', position='top-right', timeout=4000
            )

            self._select_paciente.set_value(None)
            self._input_notas_nueva.set_value('')

            if fecha_cita == self.selected_date:
                self.buscar_citas()
            else:
                self.mostrar_page.refresh()

        except Exception as exc:
            ui.notify('Error crítico al intentar guardar la cita.', type='negative', position='top-right')

    