# views/historia_clinica_mensuraciones_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES, HC_CARD_PROFESSIONAL
)
from controllers.historia_clinica_mensuraciones_controller import MensuracionesController

class HistoriaClinicaMensuracionesMixin:

    @property
    def controlador_mensuraciones(self):
        """Garantiza la instancia perezosa del controlador MVC de mensuraciones."""
        if not hasattr(self, '_controlador_mensuraciones'):
            self._controlador_mensuraciones = MensuracionesController(self.session)
        return self._controlador_mensuraciones

    @ui.refreshable
    def mostrar_mensuraciones(self):
        # Solicitamos los datos limpios y procesados al controlador
        mensuraciones_historial, u = self.controlador_mensuraciones.obtener_mensuraciones_procesadas(self.paciente)

        with ui.column().classes('w-full p-6 gap-6'):
            # Layout principal de dos columnas
            with ui.row().classes('full-width q-col-gutter-md'):
                
                # --- COLUMNA IZQUIERDA: RESUMEN INTEGRAL ---
                with ui.column().classes('col-12 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        # Cabecera original
                        with ui.row().classes('justify-between items-center mb-6'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('analytics', color='primary', size='md')
                                ui.label('Evaluación Nutricional y Mensuraciones').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso("mensuraciones_manage"):
                                ui.button('Nuevo Registro', icon='add', on_click=self.agregar_mensuracion).classes(PRIMARY_BUTTON_CLASSES)
                        
                        if u:
                            imc_color, imc_estado = u.clasificar_imc
                            g_color, g_estado = u.clasificar_composicion_corporal
                            
                            # 1. Bloque de Composición Corporal (Talla y Peso)
                            with ui.grid(columns=2).classes('w-full gap-4 mb-4'):
                                with ui.column().classes('p-4 rounded-xl bg-slate-50 border border-slate-100 items-center'):
                                    ui.label('Talla (Altura)').classes('text-[10px] font-bold text-slate-400 uppercase')
                                    with ui.row().classes('items-baseline gap-1'):
                                        ui.label(f'{u.talla}').classes('text-3xl font-black text-slate-800')
                                        ui.label('cm').classes('text-sm text-slate-500 font-bold')
                                
                                with ui.column().classes('p-4 rounded-xl bg-slate-50 border border-slate-100 items-center'):
                                    ui.label('Peso Corporal').classes('text-[10px] font-bold text-slate-400 uppercase')
                                    with ui.row().classes('items-baseline gap-1'):
                                        ui.label(f'{u.peso}').classes('text-3xl font-black text-slate-800')
                                        ui.label('kg').classes('text-sm text-slate-500 font-bold')

                            with ui.row().classes('w-full gap-4 no-wrap'):
                                with ui.column().classes(f'w-full p-4 rounded-xl bg-{imc_color}-50 border-2 border-{imc_color}-100 items-center mb-4'):
                                    ui.label('Índice de Masa Corporal (IMC)').classes(f'text-[10px] font-bold text-{imc_color}-600 uppercase')
                                    
                                    valor_imc = f"{u.IMC:.1f}" if isinstance(u.IMC, (int, float)) else u.IMC
                                    ui.label(valor_imc).classes(f'text-4xl font-black text-{imc_color}-900')
                                    ui.label(imc_estado).classes(f'text-xs font-bold bg-{imc_color}-200 text-{imc_color}-900 px-4 py-1 rounded-full mt-1')
                                
                                with ui.column().classes(f'p-4 rounded-xl bg-{g_color}-50 border border-{g_color}-100 items-center'):
                                    ui.label('U.S. Navy (Perímetros)').classes(f'text-[9px] font-bold text-{g_color}-600 uppercase')
                                    
                                    grasa_v = f"{u.grasa_marina:.1f}%" if isinstance(u.grasa_marina, (int, float)) else u.grasa_marina
                                    ui.label(grasa_v).classes(f'text-2xl font-black text-{g_color}-900')
                                    ui.label(g_estado).classes(f'text-[10px] font-bold text-{g_color}-700')

                                with ui.column().classes('p-4 rounded-xl bg-indigo-50 border border-indigo-100 items-center'):
                                    ui.label('Deurenberg (IMC)').classes('text-[9px] font-bold text-indigo-400 uppercase')
                                    
                                    deuren_v = f"{u.grasa_deurenberg:.1f}%" if isinstance(u.grasa_deurenberg, (int, float)) else u.grasa_deurenberg
                                    ui.label(deuren_v).classes('text-2xl font-black text-indigo-800')
                                    ui.label('Estadístico').classes('text-[10px] font-medium text-indigo-600')

                            # 3. Antropometría Detallada
                            ui.label('Medidas de Circunferencia e Índices').classes('text-[10px] font-bold text-slate-400 uppercase mb-2')
                            with ui.grid(columns=2).classes('w-full gap-3'):
                                for label, valor, extra_class in [
                                    ('Cintura:', f'{u.cintura} cm', ''),
                                    ('Cadera:', f'{u.cadera} cm', ''),
                                    ('Cuello:', f'{u.cuello} cm', ''),
                                    ('Índice C/C:', f'{u.ICC}', 'text-indigo-600'),
                                    ('Índice C/Alt:', f'{u.ICaltura}', 'text-indigo-600')
                                ]:
                                    with ui.row().classes('justify-between p-2 border-b'):
                                        ui.label(label).classes('text-sm text-slate-600')
                                        ui.label(valor).classes(f'font-bold {extra_class}')

                            # 4. Metas y Recomendaciones
                            with ui.row().classes('w-full gap-3 mt-4'):
                                with ui.column().classes('flex-1 p-3 bg-blue-50 rounded-lg border border-blue-100'):
                                    ui.label('Peso Ideal (PI)').classes('text-[9px] font-bold text-blue-400 uppercase')
                                    ui.label(f'{u.PI} kg').classes('text-lg font-bold text-blue-800')
                                with ui.column().classes('flex-1 p-3 bg-green-50 rounded-lg border border-green-100'):
                                    ui.label('Dieta Prescrita').classes('text-[9px] font-bold text-green-400 uppercase')
                                    ui.label(f'{u.dieta}').classes('text-sm font-bold text-green-800')
                        else:
                            with ui.column().classes('items-center justify-center py-20 w-full'):
                                ui.icon('straighten', size='lg', color='slate-200')
                                ui.label('No hay datos registrados').classes('text-slate-400 italic')

                # --- COLUMNA DERECHA: HISTORIAL EXHAUSTIVO ---
                with ui.column().classes('col-12 col-md-5'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        ui.label('Historial de Mediciones').classes(HEADER_TITLE_CLASSES + ' mb-4')
                        with ui.scroll_area().classes('h-[550px] pr-4'):
                            if mensuraciones_historial:
                                for m in mensuraciones_historial:
                                    m_g_color, m_g_estado = m.clasificar_composicion_corporal
                                    with ui.card().classes('w-full p-0 border border-slate-100 shadow-none mb-4 rounded-xl'):
                                        with ui.row().classes('w-full bg-slate-500 p-2 justify-between items-center px-4'):
                                            ui.label(m.fecha_registro.strftime("%d/%m/%Y")).classes('text-sm font-bold text-white')
                                            with ui.row().classes('gap-1'):
                                                if tiene_permiso("mensuraciones_manage"):
                                                    ui.button(icon='edit', on_click=lambda e, m=m: self.editar_mensuracion(m)).props('flat dense size=sm color=white')
                                                    ui.button(icon='delete', on_click=lambda e, m=m: self.eliminar_mensuracion(m)).props('flat dense size=sm color=white')
                                        
                                        with ui.column().classes('w-full p-4 gap-3'):
                                            with ui.row().classes('w-full justify-between border-b pb-2 items-center'):
                                                ui.label(f"Peso: {m.peso}kg").classes('font-bold text-slate-700')
                                                ui.label(f"IMC: {m.IMC:.1f}").classes('font-black text-blue-600')
                                                ui.label(f"Grasa: {m.grasa_marina}%").classes(f'font-bold text-{m_g_color}-600 bg-{m_g_color}-50 px-2 rounded')
                                            
                                            with ui.grid(columns=4).classes('w-full text-[10px] text-slate-500 font-medium'):
                                                for l, v, c in [('CINTURA', f'{m.cintura}cm', 'text-slate-800'), 
                                                            ('CADERA', f'{m.cadera}cm', 'text-slate-800'),
                                                            ('CUELLO', f'{m.cuello}cm', 'text-slate-800'),
                                                            ('ICC', m.ICC, 'text-indigo-600'), 
                                                            ('IC/ALT', m.ICaltura, 'text-indigo-600'),
                                                            ('Talla', f'{m.talla}cm', 'text-slate-800'),
                                                            ('GRASA (D)', f'{m.grasa_deurenberg}%', 'text-orange-600')]:
                                                    with ui.column():
                                                        ui.label(l).classes('font-bold text-[8px]')
                                                        ui.label(str(v)).classes(f'{c} text-sm')
                                            
                                            with ui.row().classes('w-full bg-slate-50 p-2 rounded text-[11px] justify-between'):
                                                ui.label(f"PI: {m.PI} kg").classes('font-bold text-blue-700')
                                                ui.label(f"DIETA: {m.dieta}").classes('font-bold text-green-700')
                            else:
                                ui.label('Sin historial').classes('text-slate-300 text-center w-full py-10')
            
    def agregar_mensuracion(self):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Nueva Mensuracion').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes('w-full') as fecha_input:
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

            with ui.grid(columns=2):
                talla_input = self.input_clinico('Talla (cm)', min_val=50, max_val=250, valor_inicial=None).classes(INPUT_CLASSES)
                peso_input = self.input_clinico('Peso (kg)', min_val=1, max_val=300, valor_inicial=None).classes(INPUT_CLASSES)
                cintura_input = self.input_clinico('Cintura (cm)', min_val=20, max_val=200, valor_inicial=None).classes(INPUT_CLASSES)
                cadera_input = self.input_clinico('Cadera (cm)', min_val=20, max_val=200, valor_inicial=None).classes(INPUT_CLASSES)
                cuello_input = self.input_clinico('Cuello (cm)', min_val=10, max_val=80, valor_inicial=None).classes(INPUT_CLASSES)
                dieta_input = ui.select(label='Dieta', options=["1000", "1200", "1500", "1800", "2000", "2200", "Otras"], value="1000").classes(INPUT_CLASSES)
                otra_dieta_input = ui.input(label='Especifique otra dieta').classes().bind_visibility_from(dieta_input, 'value', backward=lambda v: v == 'Otras')
    
            def guardar_mensuracion():
                campos_requeridos = [
                    (fecha_input, "Fecha"),
                    (peso_input, "Peso"),
                    (talla_input, "Talla"),
                ]
                
                error = False
                for campo, nombre in campos_requeridos:
                    if not campo.value:
                        ui.notify(f'El campo {nombre} es obligatorio', type='negative')
                        campo.classes(add='border-red-500')
                        error = True
                    else:
                        campo.classes(remove='border-red-500')
                
                if error:
                    return

                # Delegación de persistencia al Controlador
                dieta_final = otra_dieta_input.value if dieta_input.value == 'Otras' else dieta_input.value
                exito, msg = self.controlador_mensuraciones.guardar_mensuracion(
                    paciente_id=self.paciente.id,
                    fecha_str=fecha_input.value,
                    peso=peso_input.value,
                    talla=talla_input.value,
                    cintura=cintura_input.value,
                    cadera=cadera_input.value,
                    cuello=cuello_input.value,
                    dieta=dieta_final
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_mensuraciones.refresh()
                else:
                    ui.notify(msg, type='negative')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar_mensuracion).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def editar_mensuracion(self, mensuracion):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('Editar Mensuracion').classes(HEADER_TITLE_CLASSES)
            opciones_dieta = ["1000", "1200", "1500", "1800", "2000", "2200", "Otras"]
            
            fecha_value = mensuracion.fecha_registro.strftime('%Y-%m-%d') if mensuracion.fecha_registro else ''
            with ui.input('Fecha', value=fecha_value).classes('w-full') as fecha_input:
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

            with ui.grid(columns=2):
                talla_input = self.input_clinico('Talla (cm)', min_val=50, max_val=250, valor_inicial=mensuracion.talla).classes(INPUT_CLASSES)
                peso_input = self.input_clinico('Peso (kg)', min_val=1, max_val=300, valor_inicial=mensuracion.peso).classes(INPUT_CLASSES)
                cintura_input = self.input_clinico('Cintura (cm)', min_val=20, max_val=200, valor_inicial=mensuracion.cintura).classes(INPUT_CLASSES)
                cadera_input = self.input_clinico('Cadera (cm)', min_val=20, max_val=200, valor_inicial=mensuracion.cadera).classes(INPUT_CLASSES)
                cuello_input = self.input_clinico('Cuello (cm)', min_val=10, max_val=80, valor_inicial=mensuracion.cuello).classes(INPUT_CLASSES)

                es_dieta_otra = mensuracion.dieta not in opciones_dieta and mensuracion.dieta is not None
                valor_inicial_select = "Otras" if es_dieta_otra else mensuracion.dieta
                dieta_input = ui.select(label='Dieta', options=opciones_dieta, value=valor_inicial_select).classes(INPUT_CLASSES)
               
                otra_dieta_input = ui.input(label='Especifique otra dieta', value=mensuracion.dieta if es_dieta_otra else "")\
                    .classes('w-full ' + INPUT_CLASSES)\
                    .bind_visibility_from(dieta_input, 'value', backward=lambda v: v == 'Otras')

            def guardar():
                campos_requeridos = [
                    (fecha_input, "Fecha"),
                    (peso_input, "Peso"),
                    (talla_input, "Talla")
                ]
                
                error = False
                for campo, nombre in campos_requeridos:
                    if not campo.value:
                        ui.notify(f'El campo {nombre} es obligatorio', type='negative')
                        campo.classes(add='border-red-500')
                        error = True
                    else:
                        campo.classes(remove='border-red-500')
                
                if error:
                    return

                # Delegación de actualización al Controlador
                dieta_final = otra_dieta_input.value if dieta_input.value == "Otras" else dieta_input.value
                exito, msg = self.controlador_mensuraciones.actualizar_mensuracion(
                    mensuracion=mensuracion,
                    fecha_str=fecha_input.value,
                    peso=peso_input.value,
                    talla=talla_input.value,
                    cintura=cintura_input.value,
                    cadera=cadera_input.value,
                    cuello=cuello_input.value,
                    dieta=dieta_final
                )
                
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_mensuraciones.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def eliminar_mensuracion(self, mensuracion):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Está seguro que desea eliminar esta mensuracion?').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def ejecutar_eliminacion():
                    exito, msg = self.controlador_mensuraciones.eliminar_mensuracion(mensuracion)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_mensuraciones.refresh()
                    else:
                        ui.notify(msg, type='negative')
                        dialog.close()
                
                ui.button('Eliminar', on_click=ejecutar_eliminacion).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            
            dialog.open()