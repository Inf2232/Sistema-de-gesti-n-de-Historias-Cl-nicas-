from nicegui import ui 
from models import Session, Usuario ,Institucion,Permiso,Rol
from authenticar import *
import os
import shutil
from datetime import datetime
import sqlite3
from sidebar import SidebarReutilizable

import json
from Errores import log_error_and_notify
import asyncio
from .citas import GAP_SM
from controllers.geografia_controller import GeografiaController
from controllers.institucion_controller import InstitucionController
from controllers.usuario_controller import UsuarioController
from controllers.rol_controller import RolController
from controllers.database_controller import DatabaseController
from controllers.audit_controller import AuditController
# Estilos Base para Componentes Visuales
CARD_CLASSES = 'w-full p-4 shadow-xl rounded-2xl border border-blue-100 bg-white'
INPUT_CLASSES = ' rounded-lg border-2 border-blue-200 focus:border-blue-500 focus:ring focus:ring-blue-200/50'
HEADER_TITLE_CLASSES = 'text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800'
NOTIFICATION_CONTAINER_CLASSES = 'items-center justify-center text-center py-10 gap-2'
NOTIFICATION_ICON_CLASSES = 'text-blue-200 text-6xl'
NOTIFICATION_LABEL_CLASSES = 'text-gray-500 text-lg'

# Estilos Base para Botones
BASE_BUTTON_CLASSES = ' font-medium rounded-lg py-2 transition-all shadow-md hover:shadow-lg'

# Estilos Específicos para Botones
PRIMARY_BUTTON_CLASSES = f'bg-blue-600 hover:bg-blue-700 text-white {BASE_BUTTON_CLASSES}'
SUCCESS_BUTTON_CLASSES = f'bg-green-500 hover:bg-green-600 text-white {BASE_BUTTON_CLASSES}'
DANGER_BUTTON_CLASSES = 'bg-red-600 hover:bg-red-700 text-white font-semibold rounded-full p-2 shadow transition-all'
HEADER_NAV_BUTTON_CLASSES = 'text-white hover:bg-blue-700/50 transition-all rounded-full p-2'


class ConfiguracionApp:
    def __init__(self):
        self.sidebar = SidebarReutilizable(self)
        self.setup_sidebar()
        self.setup_navigation()
        self.session = Session()
        
        self.geo_ctrl = GeografiaController()
        self.inst_ctrl = InstitucionController()
        self.user_ctrl = UsuarioController()
        self.rol_ctrl = RolController()
        self.db_ctrl = DatabaseController()
        self.audit_ctrl = AuditController()
        

    def setup_navigation(self):
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
                    ui.label('Configuracion').classes('text-white text-h6 text-weight-bold gt-xs')

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

    def setup_configuracion_ui(self):
        with ui.column().classes('w-full max-w-5xl mx-auto my-6 p-4'):
            with ui.card().classes('w-full shadow-xl rounded-xl overflow-hidden'):
                with ui.tabs().classes('w-full bg-indigo-50') as tabs:
                    usuarios_tab = ui.tab('Usuarios', icon='people').classes('px-6 py-3 text-indigo-800 font-medium hover:bg-indigo-100 transition-colors')
                    roles_tab = ui.tab('Gestión de Roles', icon='admin_panel_settings').classes('px-6 py-3 text-indigo-800 font-medium hover:bg-indigo-100 transition-colors')
                    database_tab = ui.tab('Base de Datos', icon='storage').classes('px-6 py-3 text-indigo-800 font-medium hover:bg-indigo-100 transition-colors')
                    audit_tab = ui.tab('Auditoría', icon='history').classes('px-6 py-3 text-indigo-800 font-medium hover:bg-indigo-100 transition-colors')
                    institucion_tab = ui.tab('Institución', icon='apartment').classes('px-6 py-3 text-indigo-800')
                ui.add_head_html('''
                                  <style>
                                      #c1{
                                          padding-top: 0 !important;
                                      }
                                  </style>
                              ''')

                with ui.tab_panels(tabs, value=usuarios_tab).classes('w-full bg-white'):
                    with ui.tab_panel(usuarios_tab):
                        self.setup_gestion_usuarios_ui()
                    with ui.tab_panel(roles_tab):
                        self.setup_configuracion_roles_ui()
                    with ui.tab_panel(database_tab):
                        self.setup_database_ui()
                    with ui.tab_panel(audit_tab):
                        self.setup_audit_ui()
                    with ui.tab_panel(institucion_tab):
                        self.setup_institucion_ui()

                                          
    def setup_configuracion_roles_ui(self):
        with ui.card().classes('w-full p-6 shadow-lg'):
            ui.label('🛡️ Gestión de Seguridad y Permisos').classes('text-2xl font-bold text-indigo-900 mb-4')
            
            with ui.row().classes('w-full items-center gap-4 mb-6'):
                # Cargar roles llamando al controlador
                roles = self.rol_ctrl.obtener_roles()
                self.rol_selector = ui.select(
                    {r.id: r.nombre for r in roles}, 
                    label='Seleccione un Rol para editar',
                    on_change=self.cargar_permisos_del_rol
                ).classes('w-64')
                
                ui.button(icon='add', on_click=self.abrir_modal_nuevo_rol).props('round outline color=primary').tooltip('Crear nuevo rol')
                self.btn_eliminar_rol = ui.button(icon='delete', on_click=self.confirmar_eliminacion_rol).props('round outline color=negative').tooltip('Eliminar este rol')
                self.btn_eliminar_rol.set_visibility(False)
                
                ui.button('Guardar Cambios', icon='save', on_click=self.guardar_configuracion_permisos).classes(SUCCESS_BUTTON_CLASSES)

            ui.separator()

            # Contenedor para la matriz de checkboxes
            self.permisos_container = ui.grid(columns=3).classes('w-full gap-4 mt-6')
            self.checkboxes_permisos = {}

    def confirmar_eliminacion_rol(self):
        """Muestra ventana de confirmación delegando las comprobaciones previas al controlador."""
        rol_id = self.rol_selector.value
        if not rol_id: return

        rol = self.rol_ctrl.obtener_rol_por_id(rol_id)
        if not rol: return

        # Trasladamos las reglas de negocio críticas al backend (Controlador) antes de abrir el modal
        if rol.nombre.lower() in ['admin', 'superadministrador', 'médico']:
            ui.notify(f'El rol "{rol.nombre}" es un rol del sistema y no puede eliminarse.', type='warning')
            return

        with ui.dialog() as dialog, ui.card().classes('p-4'):
            ui.label(f'¿Está seguro de eliminar el rol "{rol.nombre}"?').classes('text-lg font-bold')
            ui.label('Esta acción no se puede deshacer y revocará accesos.').classes('text-sm text-gray-500')
            
            with ui.row().classes('justify-end w-full mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Eliminar', on_click=lambda: self.ejecutar_eliminacion_rol(rol_id, dialog), color='negative')
        dialog.open()

    def ejecutar_eliminacion_rol(self, rol_id, dialog):
        """Solicita la remoción al controlador y limpia el estado visual."""
        exito, mensaje = self.rol_ctrl.eliminar_rol(rol_id)
        
        if exito:
            ui.notify(mensaje, type='positive')
            self.rol_selector.value = None
            self.refrescar_selector_roles()
            self.permisos_container.clear()
            self.btn_eliminar_rol.set_visibility(False)
            dialog.close()
        else:
            ui.notify(mensaje, type='negative')

    def cargar_permisos_del_rol(self):
        """Puebla la interfaz gráfica con los checkboxes de permisos correspondientes."""
        if not self.rol_selector.value:
            self.btn_eliminar_rol.set_visibility(False)
            return
        
        self.btn_eliminar_rol.set_visibility(True)
        self.permisos_container.clear()
        self.checkboxes_permisos = {}

        # Consumo de datos mediante el controlador
        todos_los_permisos = self.rol_ctrl.obtener_permisos()
        rol_actual = self.rol_ctrl.obtener_rol_por_id(self.rol_selector.value)
        
        if not rol_actual: return
        ids_permisos_activos = [p.id for p in rol_actual.permisos]

        with self.permisos_container:
            for permiso in todos_los_permisos:
                cb = ui.checkbox(permiso.nombre).classes('text-gray-700 font-medium')
                cb.value = permiso.id in ids_permisos_activos
                
                # Mapeamos el ID del permiso con el componente UI para su posterior lectura
                self.checkboxes_permisos[permiso.id] = cb
                
                with ui.tooltip():
                    ui.label(permiso.descripcion or f"Codename: {permiso.codename}")

    def guardar_configuracion_permisos(self):
        """Recolecta los estados de los componentes gráficos y solicita la sincronización al controlador."""
        if not self.rol_selector.value:
            ui.notify('Seleccione un rol primero', type='warning')
            return

        # Extraer los IDs marcados como True en la interfaz
        ids_seleccionados = [p_id for p_id, cb in self.checkboxes_permisos.items() if cb.value]
        
        # Enviar lote de IDs al controlador para persistencia
        exito, mensaje = self.rol_ctrl.guardar_permisos_rol(self.rol_selector.value, ids_seleccionados)
        
        if exito:
            ui.notify(mensaje, type='positive')
        else:
            ui.notify(mensaje, type='negative')

    def abrir_modal_nuevo_rol(self):
        """Diálogo de inserción de un nuevo rol."""
        with ui.dialog() as dialog, ui.card().classes('p-4 w-80'):
            ui.label('Crear Nuevo Rol').classes('text-lg font-bold')
            nombre_input = ui.input('Nombre del Rol', placeholder='Ej: Auditor').classes('w-full')
            
            def guardar_nuevo_rol():
                nombre = nombre_input.value
                exito, resultado = self.rol_ctrl.crear_rol(nombre)
                
                if exito:
                    ui.notify(f'Rol "{resultado.nombre}" creado con éxito', type='positive')
                    self.refrescar_selector_roles()
                    self.rol_selector.value = resultado.id  # Preselecciona automáticamente el nuevo rol
                    dialog.close()
                else:
                    ui.notify(resultado, type='negative')

            with ui.row().classes('justify-end w-full mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Crear', on_click=guardar_nuevo_rol).classes(PRIMARY_BUTTON_CLASSES)
        dialog.open()   

    def refrescar_selector_roles(self):
        """Sincroniza el listado visual del componente selector con los datos del controlador."""
        roles = self.rol_ctrl.obtener_roles()
        self.rol_selector.options = {r.id: r.nombre for r in roles}
        self.rol_selector.update()

    def setup_gestion_usuarios_ui(self):
        with ui.card().classes('w-full p-6 shadow-lg'):
            with ui.row().classes('w-full justify-between items-center mb-6'):
                ui.label('👥 Gestión de Usuarios del Sistema').classes('text-2xl font-bold text-indigo-900')
                ui.button('Nuevo Usuario', icon='person_add', on_click=self.abrir_modal_usuario).classes(SUCCESS_BUTTON_CLASSES)

            # Columnas exactamente como las tenías estructuradas
            columns = [
                {'name': 'username', 'label': 'Nombre de Usuario', 'field': 'username', 'align': 'left', 'sortable': True},
                {'name': 'rol', 'label': 'Rol Asignado', 'field': 'rol', 'align': 'center', 'sortable': True},
                {'name': 'institucion', 'label': 'Institución', 'field': 'institucion', 'align': 'left'},
                {'name': 'ultimo_acceso', 'label': 'Último Acceso', 'field': 'ultimo_acceso', 'align': 'center'},
                {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'right'}
            ]

            self.usuarios_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full border-none')
            
            # Slot nativo de Quasar para inyectar botones de acción en filas
            self.usuarios_table.add_slot('body-cell-acciones', '''
                <q-td :props="props">
                    <q-btn flat round color="primary" icon="edit" @click="$parent.$emit('edit', props.row)" />
                    <q-btn flat round color="negative" icon="delete" @click="$parent.$emit('delete', props.row)" />
                </q-td>
            ''')
            
            self.usuarios_table.on('edit', lambda msg: self.abrir_modal_usuario(msg.args))
            self.usuarios_table.on('delete', lambda msg: self.eliminar_usuario_confirmacion(msg.args))

            self.actualizar_tabla_usuarios()

    def abrir_modal_usuario(self, datos_usuario=None):
        """Ventana para Crear o Editar usuario delegando lógica al Controlador."""
        is_edit = datos_usuario is not None
        titulo = "Editar Usuario" if is_edit else "Registrar Nuevo Usuario"
        
        with ui.dialog() as dialog, ui.card().classes('p-6 w-96'):
            ui.label(titulo).classes('text-xl font-bold mb-4')
            
            username_input = ui.input('Username', value=datos_usuario['username'] if is_edit else '').classes('w-full mb-2')
            
            pass_label = 'Nueva Contraseña' if is_edit else 'Contraseña'
            password_input = ui.input(pass_label, password=True, password_toggle_button=True).classes('w-full mb-2')
            
            # SELECTORES POBLADOS MEDIANTE CONTROLADOR
            roles_db = self.user_ctrl.obtener_roles()
            rol_select = ui.select(
                {r.id: r.nombre for r in roles_db}, 
                label='Rol del Sistema',
                value=next((r.id for r in roles_db if r.nombre == datos_usuario['rol']), None) if is_edit else None
            ).classes('w-full mb-2')

            inst_db = self.user_ctrl.obtener_instituciones()
            inst_select = ui.select(
                {i.id: i.nombre for i in inst_db}, 
                label='Institución (Opcional)',
                value=datos_usuario.get('institucion_id') if is_edit else None
            ).classes('w-full mb-4')

            def guardar():
                # Obtenemos los valores de los inputs de la interfaz
                username = username_input.value
                password = password_input.value
                rol_id = rol_select.value
                inst_id = inst_select.value
                user_id = datos_usuario['id'] if is_edit else None

                # Delegamos la persistencia y hashing al controlador
                exito, mensaje = self.user_ctrl.guardar_usuario(username, password, rol_id, inst_id, user_id)
                
                if exito:
                    ui.notify(mensaje, type='positive')
                    self.actualizar_tabla_usuarios()
                    dialog.close()
                else:
                    ui.notify(mensaje, type='negative')

            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Guardar', on_click=guardar).classes(PRIMARY_BUTTON_CLASSES)
        
        dialog.open()
    
    def eliminar_usuario_confirmacion(self, user_data):
        """Muestra un diálogo de confirmación validando la sesión actual."""
        from authenticar import devolver_usuario_actual
        usuario_sesion = devolver_usuario_actual()

        # Validación visual inmediata de auto-eliminación
        if usuario_sesion and usuario_sesion['username'] == user_data['username']:
            ui.notify('No puedes eliminar tu propia cuenta mientras estás en sesión.', type='negative')
            return

        with ui.dialog() as dialog, ui.card().classes('p-6'):
            ui.label(f'¿Eliminar al usuario "{user_data["username"]}"?').classes('text-lg font-bold')
            ui.label('Esta acción es permanente y se perderá el rastro de acceso de este usuario.').classes('text-sm text-gray-600')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Cancelar', on_click=dialog.close).props('flat')
                ui.button('Eliminar Permanentemente', 
                          on_click=lambda: self.ejecutar_eliminacion_usuario(user_data['id'], dialog),
                          color='negative').classes('text-white')
        dialog.open()

    def ejecutar_eliminacion_usuario(self, user_id, dialog):
        """Ejecuta la eliminación solicitándola al controlador."""
        exito, mensaje = self.user_ctrl.eliminar_usuario(user_id)
        
        if exito:
            ui.notify(mensaje, type='positive')
            self.actualizar_tabla_usuarios()
            dialog.close()
        else:
            ui.notify(mensaje, type='negative')

    def actualizar_tabla_usuarios(self):
        """Solicita los datos al controlador y actualiza las filas visibles."""
        try:
            usuarios = self.user_ctrl.obtener_todos_los_usuarios()
            rows = []
            for u in usuarios:
                rows.append({
                    'id': u.id,
                    'username': u.username,
                    'rol': u.rol_relacion.nombre if u.rol_relacion else 'Sin Rol',
                    'institucion': u.institucion.nombre if u.institucion else 'Global',
                    'ultimo_acceso': u.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if u.ultimo_acceso else 'Nunca',
                    'institucion_id': u.institucion_id
                })
            self.usuarios_table.rows = rows
            self.usuarios_table.update()
        except Exception as e:
            ui.notify(f'Error al refrescar tabla de usuarios: {e}', type='negative')
    
    def setup_database_ui(self):
        with ui.column().classes('w-full gap-6 p-4'):
            
            # --- Card para Exportar/Descargar Backup ---
            with ui.card().classes(CARD_CLASSES):
                with ui.column().classes('w-full gap-4 p-5'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('download', size='lg', color='primary').classes('text-indigo-600')
                        ui.label('Exportar Base de Datos').classes('text-xl font-semibold text-gray-800')
                    
                    ui.label('Descarga un archivo .db con toda la información actual. Puedes guardarlo en tu PC, memoria USB o disco externo.').classes('text-gray-600')
                    ui.button('Descargar Backup', on_click=self.descargar_backup, icon='save_alt').classes(PRIMARY_BUTTON_CLASSES)

            # --- Card para Importar/Restaurar Backup ---
            with ui.card().classes(CARD_CLASSES):
                with ui.column().classes('w-full gap-4 p-5'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('upload', size='lg', color='primary').classes('text-indigo-600')
                        ui.label('Restaurar Base de Datos').classes('text-xl font-semibold text-gray-800')
                    
                    ui.label('Selecciona un archivo .db desde tu memoria USB o PC para sobreescribir la base de datos actual.').classes('text-gray-600 text-sm')
                    
                    # Componente de carga directa
                    ui.upload(
                        label='Arrastra tu archivo .db aquí o haz clic para buscar', 
                        auto_upload=True, 
                        on_upload=self.restaurar_desde_archivo
                    ).props('accept=.db max-files="1"').classes('max-w-full w-full')

    def descargar_backup(self):
        """Pide la ruta al controlador e instruye al navegador del cliente iniciar la descarga."""
        try:
            # Obtenemos la ruta limpia desde el controlador
            db_path = self.db_ctrl.obtener_ruta_base_datos()
            nombre_archivo = f"backup_sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # Acción puramente visual/de cliente
            ui.download(db_path, filename=nombre_archivo)
            ui.notify('Descarga iniciada. Selecciona dónde guardar el archivo.', type='positive', position='top-right')
        except Exception as e:
            log_error_and_notify(e, "Error al preparar la descarga del backup")
            ui.notify(f'Error al descargar: {str(e)}', type='negative', position='top-right')

    async def restaurar_desde_archivo(self, e):
        """Manejador asíncrono que lee los datos de la UI y los transfiere al controlador."""
        try:
            # 1. Leer los bytes binarios directamente del componente NiceGUI (Responsabilidad de la Vista)
            file_data = await e.file.read()

            # 2. Enviar el lote de bytes al controlador para su procesamiento pesado (Reglas de Negocio)
            exito, mensaje = self.db_ctrl.restaurar_desde_bytes(file_data)

            if exito:
                ui.notify(f'{mensaje} Reiniciando entorno...', type='positive', position='top-right')
                # Espera prudencial para asegurar la lectura visual de la notificación
                await asyncio.sleep(2)
                ui.navigate.reload()
            else:
                ui.notify(mensaje, type='negative', position='top-right')

        except Exception as ex:
            log_error_and_notify(ex, "Error crítico en la interfaz al restaurar la base de datos")
            ui.notify(f'Error en la restauración: {str(ex)}', type='negative', position='top-right')




    def setup_audit_ui(self):
        with ui.column().classes('w-full gap-4 p-4'):
            # Encabezado Seccionado
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('📜 Registro de Auditoría').classes(HEADER_TITLE_CLASSES)

            # --- SECCIÓN DE FILTROS (Tarjeta Independiente) ---
            with ui.card().classes('w-full p-4 shadow-md'):
                with ui.grid(columns=4).classes('w-full items-end gap-4'):
                    self.filtro_usuario = ui.input('Usuario', placeholder='Ej: admin').classes(INPUT_CLASSES)
                    self.filtro_accion = ui.select(
                        ['', 'login', 'ACCESO_LECTURA', 'crear', 'actualizar', 'eliminar', 'archivar', 'desarchivar'], 
                        label='Acción'
                    ).classes(INPUT_CLASSES)
                    
                    self.filtro_fecha = ui.select(
                        options={1: 'Últimas 24h', 7: 'Última semana', 30: 'Último mes', 0: 'Todo el tiempo'},
                        label='Periodo',
                        value=7
                    ).classes(INPUT_CLASSES)
                    
                    with ui.row().classes('gap-2'):
                        ui.button('Limpiar', icon='refresh', on_click=self.limpiar_filtros).props('flat')
                        ui.button('Buscar', icon='search', on_click=lambda: self.actualizar_tabla_auditoria(reset_page=True)).classes(PRIMARY_BUTTON_CLASSES)

            # --- SECCIÓN DE TABLA ---
            columns = [
                {'name': 'fecha', 'label': 'Fecha/Hora', 'field': 'fecha', 'align': 'left', 'sortable': True},
                {'name': 'usuario', 'label': 'Usuario', 'field': 'usuario', 'align': 'left'},
                {'name': 'accion', 'label': 'Acción', 'field': 'accion', 'align': 'center'},
                {'name': 'tabla', 'label': 'Tabla', 'field': 'tabla', 'align': 'left'},
                {'name': 'registro_id', 'label': 'ID Registro', 'field': 'registro_id', 'align': 'center'},
                {'name': 'ver_detalles', 'label': 'Detalles', 'field': 'ver_detalles', 'align': 'center'},
            ]

            self.audit_table = ui.table(
                columns=columns, 
                rows=[], 
                row_key='id_interno' 
            ).classes('w-full bg-white shadow-lg')
            self.audit_table.props('dense separator=horizontal pagination.rowsPerPage=15')

            # Slot para badges de colores estilizados
            self.audit_table.add_slot('body-cell-accion', '''
                <q-td :props="props">
                    <q-badge :color="props.value.includes('crear') || props.value.includes('login') ? 'green' : props.value.includes('eliminar') ? 'red' : 'blue'">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')

            # Slot de botón Seguro: Pasamos el 'id_interno' en lugar de la cadena cruda JSON para evitar fallos de escape de caracteres HTML
            self.audit_table.add_slot('body-cell-ver_detalles', '''
                <q-td :props="props">
                    <q-btn flat round icon="visibility" color="primary" @click="$parent.$emit('solicitar_detalles', props.row.id_interno)" />
                </q-td>
            ''')
            
            # Captura del evento emitido desde el renglón de la tabla
            self.audit_table.on('solicitar_detalles', lambda e: self.procesar_apertura_detalles(e.args))

            ui.label('Mostrando hasta un máximo de 200 registros recientes según los filtros aplicados.').classes('text-xs text-slate-400 mt-2')

            self.actualizar_tabla_auditoria()

    def actualizar_tabla_auditoria(self, reset_page=False):
        """Solicita los datos filtrados al controlador y refresca de forma limpia la interfaz."""
        try:
            # 1. Vaciar la tabla visualmente para dar feedback inmediato al usuario
            self.audit_table.rows = []
            self.audit_table.update()

            # 2. Delegar la búsqueda pesada de datos al controlador de la lógica de negocio
            filas_procesadas = self.audit_ctrl.obtener_logs_filtrados(
                usuario=self.filtro_usuario.value,
                accion=self.filtro_accion.value,
                dias_periodo=self.filtro_fecha.value
            )

            # 3. Asignar los resultados limpios a la UI
            self.audit_table.rows = filas_procesadas
            self.audit_table.update()
            
            # Guardamos temporalmente las filas en la vista para poder recuperar el JSON de detalles localmente sin volver a consultar la DB
            self._cached_rows = filas_procesadas

            ui.notify(f'Filtro aplicado: {len(filas_procesadas)} registros cargados.', type='positive', position='top-right')
        except Exception as e:
            log_error_and_notify(e, "Error al actualizar la tabla de auditoría")
            ui.notify('No se pudieron recuperar los registros de auditoría', type='negative')

    def procesar_apertura_detalles(self, id_interno_arg):
        """Busca el JSON correspondiente dentro de la caché local basándose en el id recibido."""
        try:
            # NiceGUI devuelve los argumentos empaquetados en una lista o diccionario dependiendo del evento
            id_buscado = id_interno_arg[0] if isinstance(id_interno_arg, list) else id_interno_arg
            
            # Buscar el registro en la caché local de filas actuales
            registro = next((r for r in self._cached_rows if r['id_interno'] == id_buscado), None)
            
            if registro and registro.get('raw_detalles'):
                self.mostrar_modal_detalles(registro['raw_detalles'])
            else:
                ui.notify('Este registro no contiene detalles adicionales.', type='info')
        except Exception as e:
            log_error_and_notify(e, "Error al procesar la solicitud de detalles")

    def mostrar_modal_detalles(self, raw_json):
        """Muestra los detalles en un cuadro de diálogo correctamente formateado."""
        with ui.dialog() as dialog, ui.card().classes('w-[550px] max-w-full p-4'):
            ui.label('Detalles de la Operación').classes('text-xl font-bold text-gray-800 mb-2')
            
            try:
                # Comprobación de tipo y deserialización segura
                import json
                data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                ui.json_editor({'content': {'json': data}}).classes('w-full border border-gray-200 rounded-lg')
            except Exception as e:
                # Fallback por si la auditoría contiene texto plano en lugar de un objeto JSON estructurado
                ui.label('Contenido del registro (Texto Plano):').classes('text-xs font-semibold text-gray-500 mt-2')
                ui.label(str(raw_json)).classes('font-mono text-sm bg-gray-100 p-3 rounded w-full overflow-x-auto')
            
            ui.button('Cerrar', on_click=dialog.close).classes('w-full mt-4 bg-slate-700 hover:bg-slate-800 text-white')
        dialog.open()

    def limpiar_filtros(self):
        """Restaura los valores por defecto de la interfaz y actualiza los datos."""
        self.filtro_usuario.value = ''
        self.filtro_accion.value = ''
        self.filtro_fecha.value = 7
        self.actualizar_tabla_auditoria()

    def setup_institucion_ui(self):
        with ui.column().classes('w-full gap-6 p-4'):
            ui.label('Configuración Institucional y Geográfica').classes('text-2xl font-bold text-gray-800')

            # --- SECCIÓN 1: GESTIÓN DE INSTITUCIONES ---
            with ui.card().classes('w-full p-4 shadow-md rounded-lg'):
                with ui.row().classes('items-center gap-2 mb-4'):
                    ui.icon('apartment', size='md').classes('text-indigo-600')
                    ui.label('Directorio de Instituciones').classes('text-lg font-bold')
                
                with ui.row().classes('w-full gap-4 items-end'):
                    self.inst_select = ui.select(options={}, label='Seleccionar Institución', on_change=self.cargar_datos_institucion).classes('w-1/3')
                    ui.button('Limpiar para Nueva Institución', icon='add', on_click=self.nueva_institucion).classes('bg-green-600 text-white')

                with ui.grid(columns=3).classes('w-full gap-4 mt-4'):
                    self.inst_nombre = ui.input('Nombre Oficial').classes('w-full')
                    self.inst_direccion = ui.input('Dirección').classes('w-full')
                    self.inst_provincia = ui.select(options={}, label='Provincia de la Institución').classes('w-full')
                
                ui.button('Guardar / Actualizar Institución', icon='save', on_click=self.guardar_institucion).classes('mt-4 bg-blue-600 text-white')

            # --- SECCIÓN 2: GESTOR GEOGRÁFICO (CRUD COMPLETO) ---
            with ui.card().classes('w-full p-4 shadow-md rounded-lg'):
                with ui.row().classes('items-center gap-2 mb-4'):
                    ui.icon('map', size='md').classes('text-green-600')
                    ui.label('Codificador Geográfico (CoDPA)').classes('text-lg font-bold')

                with ui.grid(columns=3).classes('w-full gap-6'):
                    
                    # COLUMNA 1: PROVINCIAS
                    with ui.column().classes('w-full bg-gray-50 p-4 rounded-lg border'):
                        ui.label('1. Provincias').classes('font-bold text-gray-700')
                        self.lista_provincias = ui.select(options={}, label='Seleccionar para editar', on_change=self.on_prov_select).classes('w-full')
                        
                        self.inp_prov_nom = ui.input('Nombre Provincia').classes('w-full')
                        self.inp_prov_cod = ui.input('Código (Ej: 34)').classes('w-full')
                        
                        with ui.row().classes('w-full justify-between mt-2'):
                            ui.button(icon='add', on_click=self.add_provincia).props('flat color=green').tooltip('Agregar Nueva')
                            ui.button(icon='save', on_click=self.edit_provincia).props('flat color=blue').tooltip('Guardar Cambios')
                            ui.button(icon='delete', on_click=self.del_provincia).props('flat color=red').tooltip('Eliminar')

                    # COLUMNA 2: MUNICIPIOS
                    with ui.column().classes('w-full bg-gray-50 p-4 rounded-lg border'):
                        ui.label('2. Municipios').classes('font-bold text-gray-700')
                        self.lista_municipios = ui.select(options={}, label='Seleccionar para editar', on_change=self.on_mun_select).classes('w-full')
                        
                        self.inp_mun_nom = ui.input('Nombre Municipio').classes('w-full')
                        self.inp_mun_cod = ui.input('Código (Ej: 34.01)').classes('w-full')
                        
                        with ui.row().classes('w-full justify-between mt-2'):
                            ui.button(icon='add', on_click=self.add_municipio).props('flat color=green').tooltip('Agregar Nuevo')
                            ui.button(icon='save', on_click=self.edit_municipio).props('flat color=blue').tooltip('Guardar Cambios')
                            ui.button(icon='delete', on_click=self.del_municipio).props('flat color=red').tooltip('Eliminar')

                    # COLUMNA 3: ÁREAS DE SALUD
                    with ui.column().classes('w-full bg-gray-50 p-4 rounded-lg border'):
                        ui.label('3. Áreas de Salud').classes('font-bold text-gray-700')
                        self.lista_areas = ui.select(options={}, label='Seleccionar para editar').classes('w-full').on_value_change(self.on_area_select)
                        
                        self.inp_area_nom = ui.input('Nombre del Área').classes('w-full')
                        
                        with ui.row().classes('w-full justify-between mt-2'):
                            ui.button(icon='add', on_click=self.add_area).props('flat color=green').tooltip('Agregar Nueva')
                            ui.button(icon='save', on_click=self.edit_area).props('flat color=blue').tooltip('Guardar Cambios')
                            ui.button(icon='delete', on_click=self.del_area).props('flat color=red').tooltip('Eliminar')

            # Cargas iniciales
            self.recargar_instituciones()
            self.recargar_provincias()

    # ==========================================
    # LÓGICA DE INSTITUCIONES
    # ==========================================
    def recargar_instituciones(self):
        try:
            # 1. Cargar las instituciones en el select principal (lo que ya hacías)
            insts = self.inst_ctrl.obtener_instituciones()
            self.inst_select.options = {i.id: i.nombre for i in insts}
            self.inst_select.update()

            # 2. SOLUCIÓN: Cargar las provincias en el select de la institución
            # Usamos el controlador de geografía que ya tienes inicializado
            provincias = self.geo_ctrl.obtener_provincias()
            
            # Guardamos el nombre como CLAVE y VALOR para que coincida con lo que esperan tus informes
            self.inst_provincia.options = {p.nombre: p.nombre for p in provincias}
            self.inst_provincia.update()

        except Exception as e:
            ui.notify(f'Error al cargar componentes de institución: {e}', type='negative')

    def nueva_institucion(self):
        # Esta función de UI queda idéntica, es puramente visual
        self.inst_select.value = None
        self.inst_nombre.value = ""
        self.inst_direccion.value = ""
        self.inst_provincia.value = None

    def cargar_datos_institucion(self, e):
        if not e.value: 
            return
        try:
            # Buscamos la institución a través del controlador
            inst = self.inst_ctrl.obtener_institucion_por_id(e.value)
            if inst:
                self.inst_nombre.value = inst.nombre
                self.inst_direccion.value = inst.direccion if inst.direccion else ""
                self.inst_provincia.value = inst.provincia_default if inst.provincia_default else None
        except Exception as exc:
            ui.notify(f'Error al cargar datos: {exc}', type='negative')

    def guardar_institucion(self):
        # 1. Recolectamos los datos de la UI
        nombre = self.inst_nombre.value
        direccion = self.inst_direccion.value
        provincia = self.inst_provincia.value
        inst_id = self.inst_select.value  # Si hay ID, edita. Si es None, crea.

        # 2. Le pasamos el paquete de datos al controlador
        exito, mensaje = self.inst_ctrl.guardar_institucion(nombre, direccion, provincia, institucion_id=inst_id)
        
        # 3. La UI reacciona según lo que diga el controlador
        if exito:
            ui.notify(mensaje, type='positive')
            self.recargar_instituciones()
            self.nueva_institucion() # Limpia los campos tras guardar
        else:
            ui.notify(mensaje, type='warning')
    
    # ==========================================
    # LÓGICA GEOGRÁFICA (provincias )
    # ==========================================
    def recargar_provincias(self):
        try:
            provincias = self.geo_ctrl.obtener_provincias()
            self.lista_provincias.set_options({p.id: p.nombre for p in provincias})
        except Exception as e:
            ui.notify(f'Error al cargar provincias: {e}', type='negative')

    def on_prov_select(self, e):
        if not e.value: 
            return
        try:
            municipios = self.geo_ctrl.obtener_municipios_por_provincia(e.value)
            self.lista_municipios.set_options({m.id: m.nombre for m in municipios})
            self.lista_areas.set_options({})
            self.inp_area_nom.value = ''
        except Exception as exc:
            ui.notify(f'Error al cargar municipios: {exc}', type='negative')

    def add_provincia(self):
        nombre = self.inp_prov_nom.value
        codigo = self.inp_prov_cod.value
        
        exito, mensaje = self.geo_ctrl.guardar_provincia(nombre, codigo)
        if exito:
            ui.notify(mensaje, type='positive')
            self.recargar_provincias()
            self.inp_prov_nom.value = ''
            self.inp_prov_cod.value = ''
        else:
            ui.notify(mensaje, type='warning')

    def edit_provincia(self):
        prov_id = self.lista_provincias.value
        nombre = self.inp_prov_nom.value
        codigo = self.inp_prov_cod.value
        
        if not prov_id: 
            return ui.notify('Seleccione una provincia para editar', type='warning')
            
        exito, mensaje = self.geo_ctrl.guardar_provincia(nombre, codigo, provincia_id=prov_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.recargar_provincias()
        else:
            ui.notify(mensaje, type='warning')

    def del_provincia(self):
        prov_id = self.lista_provincias.value
        if not prov_id: 
            return ui.notify('Seleccione una provincia para eliminar', type='warning')
            
        exito, mensaje = self.geo_ctrl.eliminar_provincia(prov_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.recargar_provincias()
            self.lista_municipios.set_options({})
        else:
            ui.notify(mensaje, type='negative', position='top-right')

    # ==========================================
    # LÓGICA GEOGRÁFICA (MUNICIPIOS)
    # ==========================================
    def on_mun_select(self, e):
        if not e.value: 
            return
        try:
            areas = self.geo_ctrl.obtener_areas_por_municipio(e.value)
            self.lista_areas.set_options({a.id: a.nombre for a in areas})
            self.inp_area_nom.value = ''
        except Exception as exc:
            ui.notify(f'Error al cargar áreas de salud: {exc}', type='negative')

    def add_municipio(self):
        prov_id = self.lista_provincias.value
        nombre = self.inp_mun_nom.value
        codigo = self.inp_mun_cod.value
        
        exito, mensaje = self.geo_ctrl.guardar_municipio(nombre, codigo, prov_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.on_prov_select(type('obj', (object,), {'value': prov_id}))
            self.inp_mun_nom.value = ''
            self.inp_mun_cod.value = ''
        else:
            ui.notify(mensaje, type='warning')

    def edit_municipio(self):
        mun_id = self.lista_municipios.value
        nombre = self.inp_mun_nom.value
        codigo = self.inp_mun_cod.value
        
        if not mun_id: 
            return ui.notify('Seleccione un municipio para editar', type='warning')
            
        try:
            # Necesitamos saber a qué provincia pertenece para refrescar la UI correctamente
            municipios = self.geo_ctrl.obtener_municipios_por_provincia(self.lista_provincias.value)
            mun_obj = next((m for m in municipios if m.id == mun_id), None)
            prov_id = mun_obj.provincia_id if mun_obj else self.lista_provincias.value
            
            exito, mensaje = self.geo_ctrl.guardar_municipio(nombre, codigo, prov_id, municipio_id=mun_id)
            if exito:
                ui.notify(mensaje, type='positive')
                self.on_prov_select(type('obj', (object,), {'value': prov_id}))
            else:
                ui.notify(mensaje, type='warning')
        except Exception as e:
            ui.notify(f'Error: {e}', type='negative')

    def del_municipio(self):
        mun_id = self.lista_municipios.value
        prov_id = self.lista_provincias.value
        
        if not mun_id: 
            return ui.notify('Seleccione un municipio para eliminar', type='warning')
            
        exito, mensaje = self.geo_ctrl.eliminar_municipio(mun_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.on_prov_select(type('obj', (object,), {'value': prov_id}))
            self.lista_areas.set_options({})
        else:
            ui.notify(mensaje, type='negative', position='top-right')

    # ==========================================
    # LÓGICA GEOGRÁFICA (ÁREAS DE SALUD)
    # ==========================================
    def on_area_select(self, e):
        if not e.value: 
            return
        area = self.geo_ctrl.obtener_area_por_id(e.value)
        if area: 
            self.inp_area_nom.value = area.nombre

    def add_area(self):
        mun_id = self.lista_municipios.value
        nombre = self.inp_area_nom.value
        
        exito, mensaje = self.geo_ctrl.guardar_area_salud(nombre, mun_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.on_mun_select(type('obj', (object,), {'value': mun_id}))
            self.inp_area_nom.value = ''
        else:
            ui.notify(mensaje, type='warning')

    def edit_area(self):
        area_id = self.lista_areas.value
        mun_id = self.lista_municipios.value
        nombre = self.inp_area_nom.value
        
        if not area_id: 
            return ui.notify('Seleccione un área de la lista para editar', type='warning')
            
        exito, mensaje = self.geo_ctrl.guardar_area_salud(nombre, mun_id, area_id=area_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.on_mun_select(type('obj', (object,), {'value': mun_id}))
        else:
            ui.notify(mensaje, type='warning')

    def del_area(self):
        area_id = self.lista_areas.value
        mun_id = self.lista_municipios.value
        
        exito, mensaje = self.geo_ctrl.eliminar_area_salud(area_id)
        if exito:
            ui.notify(mensaje, type='positive')
            self.on_mun_select(type('obj', (object,), {'value': mun_id}))
            self.inp_area_nom.value = ''
        else:
            ui.notify(mensaje, type='negative', position='top-right')