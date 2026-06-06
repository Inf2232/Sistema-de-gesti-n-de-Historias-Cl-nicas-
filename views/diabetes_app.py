from nicegui import ui, events
from datetime import date, datetime
import os

from controllers.diabetes_app_controller import DiabetesAppController
from sidebar import SidebarReutilizable
from authenticar import devolver_usuario_actual, cerrar_sesion
from seguridad_roles import requiere_permiso, tiene_permiso
from Errores import log_error_and_notify

THEME = {
    'primary': 'blue-600',
    'primary_dark': 'blue-800',
    'secondary': 'slate-500',
    'accent': 'indigo-600',
    'success': 'green-800',
    'error': 'red-500',
    'warning': 'deep-orange',
    'bg_light': 'bg-slate-50',
    'surface': 'bg-white'
}

CARD_CLASSES = 'w-full shadow-xl rounded-2xl border border-blue-100 bg-white'
INPUT_CLASSES = ' text-xs rounded-lg focus:border-blue-500 '
HEADER_TITLE_CLASSES = 'text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800'
NOTIFICATION_CONTAINER_CLASSES = 'items-center justify-center text-center py-10 gap-2'
NOTIFICATION_ICON_CLASSES = 'text-blue-200 text-6xl'
NOTIFICATION_LABEL_CLASSES = 'text-gray-500 text-lg'
BASE_BUTTON_CLASSES = 'font-medium rounded-lg py-2 transition-all shadow-md hover:shadow-lg'
PRIMARY_BUTTON_CLASSES = f'bg-blue-600 hover:bg-blue-700 text-white {BASE_BUTTON_CLASSES}'
SUCCESS_BUTTON_CLASSES = f'bg-green-500 hover:bg-green-600 text-white {BASE_BUTTON_CLASSES}'
DANGER_BUTTON_CLASSES = 'bg-red-600 hover:bg-red-700 text-white font-semibold rounded-full p-2 shadow transition-all'

class DiabetesApp:
    def __init__(self):
        ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        # Inicialización de la capa Controller
        self.ctrl = DiabetesAppController()
        
        usuario = devolver_usuario_actual()
        self.ingresos_temporales = []
        
        if not usuario:
            ui.navigate.to('/')
            return

        self.usuario_actual = usuario
        inst_id = usuario.get('institucion_id')
        rol = usuario.get('rol')

        # Consumo indirecto de datos institucionales a través del Controlador
        info_institucion = self.ctrl.get_institucion_info(rol, inst_id)
        self.institucion_nombre = info_institucion['institucion_nombre']
        self.provincia_default = info_institucion['provincia_default']
        self.has_institucion = info_institucion['has_institucion']

        self.content_container = ui.column().classes('w-full p-4')
        self.sidebar = SidebarReutilizable(self)
        self.selected_year = "Todos"
        self.setup_sidebar()
        self.setup_navigation()

    def setup_navigation(self):
        from .citas import GAP_SM

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
                </style>
            ''')

            with ui.row().classes('items-center no-wrap ' + GAP_SM):
                ui.button(icon='menu', on_click=self.sidebar.toggle) \
                    .props('flat round color=white size=sm')
                ui.button(icon='arrow_back', on_click=ui.navigate.back) \
                    .props('flat round color=white size=sm')
                with ui.row().classes('items-center no-wrap q-gutter-x-xs'):
                    ui.icon('').classes('text-white text-h5')
                    ui.label('Principal').classes('text-white text-h6 text-weight-bold gt-xs')

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
             
    def mostrar_formulario_paciente(self):
        with ui.dialog().props('maximized') as self.dialog, \
        ui.card().classes('w-full h-full overflow-y-auto rounded-none shadow-none'):

            with ui.element('div').classes('row items-center justify-between bg-blue-800 text-white q-px-md q-py-sm sticky top-0 z-10'):
                ui.label('Nuevo Paciente').classes('text-lg text-white font-bold')
                ui.button(icon='close', on_click=self.dialog.close).props('flat round dense').classes('text-white')

            with ui.element('div').classes('q-pa-md'):
                opciones_provincias = self.ctrl.get_provincias()

                today         = datetime.now().strftime('%Y/%m/%d')
                current_month = datetime.now().strftime('%Y/%m')

                self._seccion_titulo('Identificación y Datos Generales')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.no_hc_input = ui.input('Número HC').classes(INPUT_CLASSES)

                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.ci_input = ui.input('Carnet de Identidad').classes(INPUT_CLASSES)

                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.nombres_input = ui.input('Nombres').classes(INPUT_CLASSES)

                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.apellidos_input = ui.input('Apellidos').classes(INPUT_CLASSES)

                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        with ui.input('Fecha de Historia Clínica').classes(INPUT_CLASSES) as self.fecha_hc_input:
                            with ui.menu().props('no-parent-event').classes('shadow-lg rounded-xl') as menu_hc:
                                ui.date().bind_value(self.fecha_hc_input).props(
                                    f'locale="es" default-year-month={current_month} :options="date => date <= \'{today}\'"'
                                ).classes('rounded-xl')
                                with ui.row().classes('justify-end px-4 py-2 rounded-b-xl'):
                                    ui.button('Cerrar', on_click=menu_hc.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                            with self.fecha_hc_input.add_slot('append'):
                                ui.icon('event').on('click', menu_hc.open).classes('cursor-pointer text-gray-500')

                    with ui.element('div').classes('col-12'):
                        with ui.element('div').classes('row items-center q-col-gutter-sm'):
                            with ui.element('div').classes('col-12'):
                                ui.label('Tiempo de Evolución al Ingreso').classes('text-xs text-blue-600 font-bold uppercase')
                                ui.label('Ingrese el tiempo al momento de crear la HC.').classes('text-xs text-blue-400 italic')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_evolucion_anios = ui.number('Años', min=0).classes(INPUT_CLASSES).props('dense')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_evolucion_meses = ui.number('Meses', min=0, max=11).classes(INPUT_CLASSES).props('dense')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_evolucion_dias = ui.number('Días', min=0, max=30).classes(INPUT_CLASSES).props('dense')

                self._seccion_titulo('Dirección')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.calle_input = ui.input('Calle').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-2'):
                        self.numero_input = ui.input('No. / Apto').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-6'):
                        self.entre_calles_input = ui.input('Entre Calles').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.provincia_input = ui.select(
                            options=opciones_provincias,
                            label='Provincia',
                            value=self.provincia_default if self.has_institucion else None,
                            on_change=self.actualizar_municipios
                        ).classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.municipio_input = ui.select(options=[], label='Municipio', on_change=self.actualizar_areas_salud).classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.area_salud_input = ui.select(options=[], label='Área de Salud').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.telefono_input = ui.input('Teléfono').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.nombre_contacto_emergencia = ui.input('Nombre de Contacto de Emergencia').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.tel_emergencia = ui.input('Teléfono de Emergencia').classes(INPUT_CLASSES)

                self._seccion_titulo('Datos Personales')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.sexo_input = ui.select(options=['Masculino', 'Femenino'], label='Sexo').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.color_piel = ui.select(['Negro', 'Blanco', 'Mestizo'], label='Color de Piel').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.escolaridad_input = ui.select(['6to Grado', '9no Grado', '12mo Grado', 'Universitario', 'No especificado'], label='Nivel Educacional').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-3'):
                        self.estado_civil_input = ui.select(['Acompañado', 'No acompañado'], label='Estado Civil').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-6'):
                        self.ocupacion_input = ui.select(['Estudiante', 'Con vínculo laboral: Trabajador Estatal', 'Con vínculo laboral: Trabajador No Estatal', 'Sin vínculo laboral'], label='Ocupación').classes(INPUT_CLASSES)

                self._seccion_titulo('Datos Clínicos del Diagnóstico')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.forma_presentacion_diagnostico = ui.select(
                            ['Sintomas Clinicos', 'Asintomatico', 'Cetoacidosis(Probada)', 'Durante el embarazo', 'Complicaciones asociadas', 'Otros'],
                            label='Forma de Presentación del Diagnóstico',
                            on_change=lambda: self.actualizar_campo_otros()
                        ).classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.mostrar_campo_otros = False
                        self.otros_forma_presentacion_diagnostico = ui.input('Especificar otra forma de presentación').classes(INPUT_CLASSES).bind_visibility_from(self, 'mostrar_campo_otros')
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.glucemia_debut_input = self.input_clinico('Glucemia al Diagnóstico (mmol/L)', min_val=2, max_val=40, valor_inicial=None).classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.exceso_peso_diagnostico = ui.select(['Si', 'No', 'No Precisado'], label='Exceso de Peso al Diagnóstico').classes(INPUT_CLASSES)
                    
                    with ui.element('div').classes('col-12').bind_visibility_from(self.exceso_peso_diagnostico, 'value', backward=lambda v: v == 'Si'):
                        with ui.element('div').classes('row q-col-gutter-sm items-center'):
                            with ui.element('div').classes('col-12'):
                                ui.label('Tiempo de exceso de peso:').classes('text-xs text-blue-600 font-bold uppercase')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_exceso_peso_anios = ui.number('Años', min=0).classes(INPUT_CLASSES).props('dense')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_exceso_peso_meses = ui.number('Meses', min=0, max=11).classes(INPUT_CLASSES).props('dense')
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.remision_input = ui.select(['CMD APS', 'Hospital', 'Espontaneamente'], label='Remisión').classes(INPUT_CLASSES)
                
                self._seccion_titulo('Tratamiento Inicial')
                # Lista temporal para guardar el esquema interactivo antes de consolidar en DB
                # Si estás editando un paciente, debes poblar esta lista con los datos recuperados (ver Paso C)
                self.esquema_inicial_temporal = [] 

                with ui.card().classes('w-full border border-dashed border-blue-200 q-pa-sm'):
                    
                    # Contenedor refrescable para listar fármacos añadidos
                    @ui.refreshable
                    def mostrar_lista_tratamiento_inicial():
                        with ui.column().classes('w-full gap-2 mb-4'):
                            if not self.esquema_inicial_temporal:
                                ui.label('No hay medicamentos registrados en el tratamiento inicial.').classes('text-xs italic text-slate-400')
                            else:
                                for index, item in enumerate(self.esquema_inicial_temporal):
                                    with ui.row().classes('w-full items-center justify-between p-2 bg-green-50 rounded-lg border border-green-100'):
                                        with ui.column().classes('gap-0'):
                                            ui.label(f"Fármaco: {item['tratamiento']}").classes('text-sm font-bold text-green-800')
                                            ui.label(f"Dosis: {item['dosis']} | Año de Inicio: {item['anio_inicio']}").classes('text-[11px] text-slate-600')
                                        ui.button(icon='delete', on_click=lambda i=index: eliminar_farmaco_inicial(i)).props('flat round dense color="red"').classes('hover:bg-red-100')

                    def eliminar_farmaco_inicial(index):
                        self.esquema_inicial_temporal.pop(index)
                        mostrar_lista_tratamiento_inicial.refresh()

                    # Render inicial de la lista
                    mostrar_lista_tratamiento_inicial()

                    # Formulario de entrada para un nuevo medicamento de la lista inicial
                    with ui.element('div').classes('row q-col-gutter-sm items-end q-mt-sm'):
                        with ui.element('div').classes('col-12 col-sm-4 col-md-4'):
                            farmaco_sel = ui.select(
                                ['Tratamiento No Farmacologico', 'SUR', 'Metformina', 'Insulina', 'Otros'], 
                                label='Medicamento / Terapia'
                            ).classes(INPUT_CLASSES)
                        
                        with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                            dosis_sel_input = ui.input('Dosis').classes(INPUT_CLASSES).props('dense')
                        
                        with ui.element('div').classes('col-12 col-sm-4 col-md-2'):
                            anio_sel_input = ui.number('Año de inicio', min=1950, max=datetime.now().year).classes(INPUT_CLASSES).props('dense')
                        
                        with ui.element('div').classes('col-12').bind_visibility_from(farmaco_sel, 'value', backward=lambda v: v == 'Otros'):
                            otro_farmaco_input = ui.input('Especificar otro medicamento...').classes('w-full ' + INPUT_CLASSES)

                        def añadir_farmaco_a_inicial():
                            nombre_farmaco = farmaco_sel.value
                            if nombre_farmaco == 'Otros':
                                nombre_farmaco = otro_farmaco_input.value

                            if nombre_farmaco:
                                self.esquema_inicial_temporal.append({
                                    'tratamiento': nombre_farmaco,
                                    'dosis': dosis_sel_input.value or "No especificada",
                                    'anio_inicio': int(anio_sel_input.value) if anio_sel_input.value else "No especificado"
                                })
                                # Limpiar inputs
                                farmaco_sel.set_value(None)
                                dosis_sel_input.set_value(None)
                                anio_sel_input.set_value(None)
                                if 'otro_farmaco_input' in locals() or 'otro_farmaco_input' in globals():
                                    otro_farmaco_input.set_value(None)
                                
                                mostrar_lista_tratamiento_inicial.refresh()
                            else:
                                ui.notify('Seleccione o especifique un medicamento', type='warning')

                        with ui.element('div').classes('col-12 col-sm-auto'):
                            ui.button('Añadir Fármaco', icon='add', on_click=añadir_farmaco_a_inicial).classes(SUCCESS_BUTTON_CLASSES)
                self._seccion_titulo('Tratamiento Inicial')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                        self.tratamiento_inicial_input = ui.select(
                            ['Tratamiento No Farmacologico', 'SUR', 'Metformina', 'Insulina', 'Insulina + SUR', 'Insulina + Metformina', 'SUR + Metformina', 'Otros'],
                            label='Tratamiento Inicial'
                        ).classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12').bind_visibility_from(self.tratamiento_inicial_input, 'value', backward=lambda v: v and v != 'Tratamiento No Farmacologico'):
                        with ui.element('div').classes('row q-col-gutter-sm'):
                            with ui.element('div').classes('col-12 col-sm-6 col-md-4').bind_visibility_from(self.tratamiento_inicial_input, 'value', backward=lambda v: v == 'Otros'):
                                self.otros_tratamiento_input = ui.input('Especificar otro tratamiento').classes(INPUT_CLASSES)
                            with ui.element('div').classes('col-12 col-sm-6 col-md-4'):
                                self.dosis_tratamiento_input = ui.input('Especificar dosis').classes(INPUT_CLASSES).props('dense')
                            with ui.element('div').classes('col-12 col-sm-4 col-md-2'):
                                self.ano_inicio_tratamiento_input = ui.number('Año de inicio').classes(INPUT_CLASSES).props('dense')

                self._seccion_titulo('Prediabetes')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                        self.prediabetes_input = ui.select(['Si', 'No', 'No Precisado'], label='¿Prediabetes?').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12').bind_visibility_from(self.prediabetes_input, 'value', backward=lambda v: v == 'Si'):
                        with ui.element('div').classes('row q-col-gutter-sm items-center'):
                            with ui.element('div').classes('col-12'):
                                ui.label('Tiempo de Prediabetes').classes('text-xs text-blue-600 font-bold uppercase')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_prediabetes_anios = ui.number('Años', min=0).classes(INPUT_CLASSES).props('dense')
                            with ui.element('div').classes('col-4 col-sm-2 col-md-1'):
                                self.tiempo_prediabetes_meses = ui.number('Meses', min=0, max=11).classes(INPUT_CLASSES).props('dense')

                self._seccion_titulo('Estado del Paciente')
                with ui.element('div').classes('row q-col-gutter-md'):
                    with ui.element('div').classes('col-12'):
                        self.estado_actual_input = ui.checkbox('Defunción').classes(INPUT_CLASSES)
                    with ui.element('div').classes('col-12').bind_visibility_from(self.estado_actual_input, 'value'):
                        with ui.element('div').classes('row q-col-gutter-sm'):
                            with ui.element('div').classes('col-12'):
                                ui.label('Detalles del Fallecimiento:').classes('text-xs text-red-700 font-bold uppercase')
                            with ui.element('div').classes('col-12 col-md-8'):
                                self.causa_fallecimiento_input = ui.textarea('Causa de la defunción').classes(INPUT_CLASSES + ' bg-red-50').props('outlined clearable placeholder="Escriba la causa clínica..."')

                self._seccion_titulo('Ingresos por Diabetes')
                with ui.card().classes('w-full border border-dashed border-blue-200 q-pa-sm'):
                    self.mostrar_lista_ingresos()
                    with ui.element('div').classes('row q-col-gutter-sm items-end q-mt-sm'):
                        with ui.element('div').classes('col-12 col-sm-6 col-md-5'):
                            motivo_sel = ui.select(['Cetoacidosis diabética', 'Estado Hiperosmolar no cetosico', 'Descontrol Metabolicó', 'Infecciones', 'Otros'], label='Motivo de Ingreso').classes(INPUT_CLASSES)
                        with ui.element('div').classes('col-12 col-sm-4 col-md-3'):
                            fecha_ing = ui.input('Fecha').classes(INPUT_CLASSES)
                            with fecha_ing.add_slot('append'):
                                ui.icon('calendar_month').on('click', lambda: menu_f.open()).classes('cursor-pointer')
                                with ui.menu() as menu_f:
                                    ui.date().bind_value(fecha_ing)
                        with ui.element('div').classes('col-12').bind_visibility_from(motivo_sel, 'value', backward=lambda v: v == 'Otros'):
                            otros_det = ui.input('Especificar motivo...').classes('w-full ' + INPUT_CLASSES)

                        def añadir_a_lista():
                            if motivo_sel.value and fecha_ing.value:
                                self.ingresos_temporales.append({
                                    'motivo': motivo_sel.value,
                                    'fecha':  fecha_ing.value,
                                    'especificacion': otros_det.value if motivo_sel.value == 'Otros' else ''
                                })
                                motivo_sel.set_value(None)
                                fecha_ing.set_value(None)
                                otros_det.set_value(None)
                                self.mostrar_lista_ingresos.refresh()
                            else:
                                ui.notify('Complete motivo y fecha', type='warning')

                        with ui.element('div').classes('col-12 col-sm-auto'):
                            ui.button('Añadir Ingreso', icon='add', on_click=añadir_a_lista).classes(PRIMARY_BUTTON_CLASSES)

            with ui.element('div').classes('row items-center justify-end q-px-md q-py-sm q-gutter-sm bg-white border-t border-gray-200 sticky bottom-0 z-10'):
                ui.button('Cancelar', on_click=self.dialog.close).classes(DANGER_BUTTON_CLASSES)
                ui.button('Guardar', on_click=lambda: self.guardar_paciente()).classes(SUCCESS_BUTTON_CLASSES)
                ui.keyboard(lambda e: self.guardar_paciente() if e.action.keydown and e.key == 'Enter' else None)

        self.dialog.open()
        if self.provincia_input.value:
            self.actualizar_municipios()

    def _seccion_titulo(self, texto: str):
        with ui.element('div').classes('col-12 q-mt-md q-mb-xs'):
            ui.label(texto).classes('text-xs font-black text-blue-700 uppercase tracking-widest border-b border-blue-100 pb-1 w-full block')
        
    def actualizar_municipios(self, value=None):
        nombre_provincia = self.provincia_input.value
        if not nombre_provincia:
            self.municipio_input.options = []
            self.municipio_input.value = None
            self.municipio_input.update()
            return

        self.municipio_input.options = self.ctrl.get_municipios(nombre_provincia)
        self.municipio_input.value = None
        self.area_salud_input.options = []
        self.area_salud_input.value = None
        self.municipio_input.update()
        self.area_salud_input.update()

    def actualizar_areas_salud(self, value=None):
        nombre_municipio = self.municipio_input.value
        nombre_provincia = self.provincia_input.value

        if not nombre_municipio or not nombre_provincia:
            self.area_salud_input.options = []
            self.area_salud_input.update()
            return

        self.area_salud_input.options = self.ctrl.get_areas_salud(nombre_provincia, nombre_municipio)
        self.area_salud_input.value = None
        self.area_salud_input.update()

    def actualizar_campo_otros(self):
        self.mostrar_campo_otros = (self.forma_presentacion_diagnostico.value == 'Otros')
        self.otros_forma_presentacion_diagnostico.update()
    
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
                        ui.button(icon='delete', on_click=lambda i=index: self.eliminar_ingreso(i)).props('flat round dense color="red"').classes('hover:bg-red-100')

    def eliminar_ingreso(self, index):
        self.ingresos_temporales.pop(index)
        self.mostrar_lista_ingresos.refresh()

    def guardar_paciente(self):
        if not tiene_permiso('pacientes_add'):
            ui.notify('No tienes permiso para agregar pacientes', type='negative')
            return
        try:
            usuario_actual = devolver_usuario_actual()
            institucion_actual_id = usuario_actual.get('institucion_id')
            
            if institucion_actual_id is None:
                ui.notify('Error: El usuario no tiene una institución asignada.', type='negative')
                return
            
            campos_requeridos = {
                "Número HC": self.no_hc_input.value,
                "Carnet de Identidad": self.ci_input.value,
                "Nombres": self.nombres_input.value,
                "Apellidos": self.apellidos_input.value,
                "Fecha de Historia Clínica": self.fecha_hc_input.value,
                "Sexo": self.sexo_input.value,
                "Color de Piel": self.color_piel.value,
                "Provincia": self.provincia_input.value,
                "Municipio": self.municipio_input.value
            }
            
            campos_faltantes = [nombre for nombre, valor in campos_requeridos.items() if not valor]
            if campos_faltantes:
                ui.notify(f'Campos requeridos faltantes: {", ".join(campos_faltantes)}', type='negative')
                return

            try:
                fecha_hc = datetime.strptime(self.fecha_hc_input.value, '%Y-%m-%d').date()
            except ValueError:
                log_error_and_notify("Formato de fecha inválido", "Error al validar fecha de historia clínica")
                ui.notify('Formato de fecha incorrecto. Use YYYY-MM-DD', type='negative')
                return

            if self.glucemia_debut_input.value:
                try:
                    glucemia = float(self.glucemia_debut_input.value)
                    if glucemia <= 0: raise ValueError
                except ValueError:
                    log_error_and_notify("Glucemia inválida", "Error al validar glucemia al Diagnóstico")
                    ui.notify('La glucemia debe ser un número entero positivo', type='negative')
                    return

            forma_presentacion = self.forma_presentacion_diagnostico.value
            if forma_presentacion == 'Otros':
                forma_presentacion = self.otros_forma_presentacion_diagnostico.value

            tratamiento_inicial = self.tratamiento_inicial_input.value
            if tratamiento_inicial == 'Otros':
                tratamiento_inicial = self.otros_tratamiento_input.value

            if not (self.ci_input.value.isdigit() and len(self.ci_input.value) == 11):
                ui.notify('El carnet debe contener exactamente 11 dígitos numéricos.', color='red')
                return
            
            # Verificación asíncrona de existencia delegada al Controlador
            existencia = self.ctrl.validar_existencia(self.no_hc_input.value, self.ci_input.value)
            if existencia['existe_hc']:
                ui.notify('El número de Historia Clínica ya está registrado.', type='negative', color='red', icon='error')
                return 
            if existencia['existe_ci']:
                ui.notify('El número de Carnet de Identidad ya está registrado.', type='negative', color='red', icon='error')
                return

            paciente_payload = {
                'no_hc': self.no_hc_input.value,
                'ci': self.ci_input.value,
                'nombres': self.nombres_input.value,
                'apellidos': self.apellidos_input.value,
                'telefono': self.telefono_input.value or "",
                'nombre_contacto_emergencia': self.nombre_contacto_emergencia.value or "",
                'tel_emergencia': self.tel_emergencia.value or "",
                'nombre_provincia': self.provincia_input.value or "",
                'nombre_municipio': self.municipio_input.value or "",
                'nombre_area': self.area_salud_input.value or "",
                'fecha_hc': fecha_hc,
                'estado_actual': "Defunción" if self.estado_actual_input.value else "",
                'calle': self.calle_input.value or "",
                'numero': self.numero_input.value or "",
                'entre_calles': self.entre_calles_input.value or "",
                'sexo': self.sexo_input.value or "",
                'color_piel': self.color_piel.value or "",
                'escolaridad': self.escolaridad_input.value or "",
                'ocupacion': self.ocupacion_input.value or "",
                'estado_civil': self.estado_civil_input.value or "",
                'tiempo_evolucion_anios': self.tiempo_evolucion_anios.value or 0,
                'tiempo_evolucion_meses': self.tiempo_evolucion_meses.value or 0,
                'forma_presentacion_diagnostico': forma_presentacion or "",
                'glucemia_debut': float(self.glucemia_debut_input.value) if self.glucemia_debut_input.value else 0,
                'exceso_peso_diagnostico': self.exceso_peso_diagnostico.value or "",
                'tiempo_exceso_peso_anios': self.tiempo_exceso_peso_anios.value or 0,
                'tiempo_exceso_peso_meses': self.tiempo_exceso_peso_meses.value or 0,
                'remision': self.remision_input.value or "",
                'tratamiento_inicial_json': self.esquema_inicial_temporal,
                'prediabetes': self.prediabetes_input.value or "No",
                'tiempo_prediabetes_anios': self.tiempo_prediabetes_anios.value or 0,
                'tiempo_prediabetes_meses': self.tiempo_prediabetes_meses.value or 0,
                'causa_fallecimiento': self.causa_fallecimiento_input.value or ""
            }

            exito, resultado = self.ctrl.guardar_paciente(paciente_payload, self.ingresos_temporales, institucion_actual_id)
            if exito:
                ui.notify('Paciente guardado correctamente', type='positive', color='green', icon='check_circle')
                self.dialog.close()
                ui.navigate.to(f'/historia_clinica/{resultado}')
                self.mostrar_lista_pacientes()
            else:
                ui.notify(f'Error: {resultado}', type='negative', color='red', icon='error')

        except Exception as e:
            log_error_and_notify(e, "Error al guardar el paciente")
            ui.notify(f'Error al guardar el paciente: {str(e)}', type='negative', color='red', icon='error')

    def actualizar_filtro_ano(self):
        self.selected_year = self.year_select.value
        self.mostrar_lista_pacientes()

   
    @requiere_permiso('pacientes_view')
    @ui.refreshable
    def mostrar_lista_pacientes(self):
        self.content_container.clear()
        try:
            usuario_actual = self.usuario_actual
            inst_id = usuario_actual.get('institucion_id')
            rol = usuario_actual.get('rol')

            with self.content_container:
                with ui.row().classes('full-width'):
                    self._seccion_titulo('Filtros')

                    with ui.row().classes('items-center q-mb-md'):
                        ui.label('Año:').classes('text-sm font-medium text-gray-600')
                        ui.icon('event').classes('text-gray-500')
                        self.year_select = ui.select(
                            options=[str(year) for year in range(2007, date.today().year + 1)] + ['Todos'],
                            value=str(self.selected_year) if self.selected_year else 'Todos',
                            on_change=self.actualizar_filtro_ano
                        ).classes(INPUT_CLASSES)

                        ui.label(f'Pacientes con Diabetes del año {self.selected_year}').classes(HEADER_TITLE_CLASSES)
                        if tiene_permiso('pacientes_add'):
                            ui.button(icon='person_add', on_click=self.mostrar_formulario_paciente) \
                                .classes(f'{PRIMARY_BUTTON_CLASSES} w=1/3').tooltip('Agregar Paciente')
                        ui.add_head_html('<style>#c1{padding-top: 0 !important;}</style>')

                # ── UNA SOLA LLAMADA para todos los tabs + estadísticas ──
                datos = self.ctrl.get_todos_los_pacientes(rol, inst_id, self.year_select.value)
                stats = datos['stats']

                with ui.row().classes('full-width q-col-gutter-md'):
                    with ui.column().classes('col-12 col-md-7'):
                        with ui.tabs().classes('bg-white rounded-xl shadow-sm border border-gray-200 mb-4') \
                                .props('shrink stretch inline-label outside-arrows mobile-arrows') as tabs:
                            todos        = ui.tab('Todos los Pacientes').classes('q-px-md q-py-sm font-medium hover:text-blue-600')
                            Ingresados   = ui.tab('Ingresados').classes('q-px-md q-py-sm font-medium transition-all hover:text-blue-600')
                            Seguimiento  = ui.tab('Seguimiento').classes('q-px-md q-py-sm font-medium transition-all hover:text-blue-600')
                            No_ingresados= ui.tab('No Ingresados').classes('q-px-md q-py-sm font-medium transition-all hover:text-blue-600')
                            Defunciones  = ui.tab('Defunciones').classes('q-px-md q-py-sm font-medium transition-all hover:text-blue-600')
                            Inactivos    = ui.tab('Inactivos').classes('q-px-md q-py-sm font-medium transition-all hover:text-red-600')

                        # Mapa tab → clave del dict que ya trajo el controlador
                        tab_a_datos = [
                            (todos,         datos['todos']),
                            (Ingresados,    datos['Ingresado']),
                            (Seguimiento,   datos['Seguimiento']),
                            (No_ingresados, datos['No Ingresado']),
                            (Defunciones,   datos['Defunción']),
                            (Inactivos,     datos['inactivos']),
                        ]

                        with ui.tab_panels(tabs, value=todos).classes('full-width'):
                            for panel, pacientes_data in tab_a_datos:
                                with ui.tab_panel(panel).classes('q-pa-none'):
                                    self._crear_tabla(pacientes_data)

                    with ui.column().classes('col-12 col-md-4'):
                        with ui.card().classes(CARD_CLASSES):
                            with ui.column().classes('full-height full-width'):
                                ui.label('Estadísticas Generales').classes(
                                    HEADER_TITLE_CLASSES + ' mb-4 pb-2 border-b border-gray-200'
                                )
                                ui.label(f'Total de pacientes registrados: {stats["total"]}').classes(
                                    NOTIFICATION_LABEL_CLASSES + ' mb-4'
                                )

                                ui.highchart({
                                    'title': False,
                                    'chart': {'type': 'pie', 'height': '300px', 'style': {'fontFamily': 'inherit'}},
                                    'plotOptions': {
                                        'pie': {
                                            'allowPointSelect': True,
                                            'cursor': 'pointer',
                                            'dataLabels': {'enabled': True, 'format': '<b>{point.name}</b>: {point.percentage:.1f} %'},
                                            'showInLegend': True
                                        }
                                    },
                                    'series': [{
                                        'name': 'Pacientes',
                                        'colorByPoint': True,
                                        'data': [
                                            {'name': 'Ingresados',     'y': stats['ingresados'],   'color': '#073cf1'},
                                            {'name': 'En seguimiento', 'y': stats['seguimiento'],  'color': '#37e109'},
                                            {'name': 'No ingresado',   'y': stats['no_ingresado'], 'color': '#f1c40f'},
                                            {'name': 'Defunciones',    'y': stats['defunciones'],  'color': '#e42d08'},
                                        ]
                                    }],
                                    'credits': {'enabled': False}
                                }).classes('w-full')

        except Exception as e:
            log_error_and_notify(e, "Carga de Pacientes para la Tabla")
        
    def _crear_tabla(self, dataset_pacientes):
        if not dataset_pacientes:
            with ui.card().classes(CARD_CLASSES + ' text-center'):
                ui.icon('search_off', size='xl').classes(NOTIFICATION_ICON_CLASSES)
                ui.label('No se encontraron pacientes').classes(NOTIFICATION_LABEL_CLASSES)
            return

        columns = [
            {'name': 'no_hc', 'label': 'No. HC', 'field': 'no_hc', 'sortable': True, 'align': 'left'},
            {'name': 'ci', 'label': 'CI', 'field': 'ci', 'sortable': True, 'align': 'left'},
            {'name': 'nombres', 'label': 'Nombres', 'field': 'nombres', 'sortable': True, 'align': 'left'},
            {'name': 'apellidos', 'label': 'Apellidos', 'field': 'apellidos', 'sortable': True, 'align': 'left'},
            {'name': 'edad', 'label': 'Edad', 'field': 'edad', 'sortable': True, 'align': 'left'},
            {'name': 'area_salud', 'label': 'Área de Salud', 'field': 'area_salud', 'sortable': True, 'align': 'left'},
            {'name': 'telefono', 'label': 'Teléfono', 'field': 'telefono', 'sortable': True, 'align': 'left'}
        ]
        
        def on_row_click(e):
            row_data = e.args[1]
            ui.navigate.to(f'/historia_clinica/{row_data["no_hc"]}')
       
        table = ui.table(columns=columns, rows=dataset_pacientes, row_key='no_hc', pagination=15).classes('full-width rounded-xl overflow-hidden shadow-sm border border-grey-3').props('''
            dense bordered flat
            header-class="bg-gray-100 text-gray-700 font-semibold"
            row-class="hover:bg-blue-50 transition-colors cursor-pointer"
            no-data-label="No hay pacientes para mostrar"
            grid-header
            card-container-class="grid-cols-1 sm:grid-cols-2"                                                                                                                                             
            ''')
        
        with table.add_slot('top-left'):
            def toggle() -> None:
                table.toggle_fullscreen()
                button.props('icon=fullscreen_exit' if table.is_fullscreen else 'icon=fullscreen')
            button = ui.button('Toggle fullscreen', icon='fullscreen', on_click=toggle).props('flat')

        table.on('rowClick', on_row_click)
        ui.input('Buscar').bind_value(table, 'filter').classes(f'{INPUT_CLASSES} !w-1/3 ')

    def input_clinico(self, label, min_val, max_val, valor_inicial):
        return ui.number(
            label=label, 
            value=valor_inicial, 
            min=min_val, 
            max=max_val,
            validation={
                f'Rango: {min_val}-{max_val}': lambda v: min_val <= v <= max_val if v else True
            }
        ).classes(INPUT_CLASSES).props('stack-label outlined')