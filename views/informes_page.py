from nicegui import ui
from sidebar import SidebarReutilizable
from authenticar import devolver_usuario_actual, cerrar_sesion
from models import Session, Institucion
from .ventana_informe import mostrar_pagina_informes
from .citas import GAP_SM

class InformesApp:
    def __init__(self):
        usuario = devolver_usuario_actual()
        if not usuario:
            ui.navigate.to('/')
            return

        self.usuario_actual = usuario
        db = Session()
        inst = db.query(Institucion).filter_by(
            id=usuario.get('institucion_id')
        ).first()
        db.close()

        self.sidebar = SidebarReutilizable(self)
        self.setup_sidebar()
        self.setup_layout()

        # Inyectar provincia antes de mostrar la ventana
        from .ventana_informe import VentanaInformeAdmin
        provincia = inst.provincia_default if inst else None

        with ui.column().classes('w-full p-4'):
            mostrar_pagina_informes(provincia=provincia)

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
                    ui.label('Informes').classes('text-white text-h6 text-weight-bold gt-xs')

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