# views/historia_clinica_complementarios_mixin.py
from datetime import datetime
from nicegui import ui
from seguridad_roles import tiene_permiso
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES, PRIMARY_BUTTON_CLASSES, DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES, INPUT_CLASSES, HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)
from controllers.historia_clinica_complementarios_controller import ComplementariosController

class HistoriaClinicaComplementariosMixin:

    @property
    def controlador_complementarios(self):
        if not hasattr(self, '_controlador_complementarios'):
            self._controlador_complementarios = ComplementariosController(self.session)
        return self._controlador_complementarios

    @ui.refreshable
    def mostrar_complementarios(self):
        examenes_historial, ultimo_examen = self.controlador_complementarios.obtener_complementarios_procesados(self.paciente)

        with ui.column().classes('w-full p-4'):
            with ui.row().classes('full-width q-col-gutter-md'):
                    
                # --- COLUMNA IZQUIERDA: RESUMEN ÚLTIMO EXAMEN ---
                with ui.column().classes('col-12 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('justify-between items-center'):
                            ui.label('Exámenes Complementarios').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso("complementarios_manage"):
                                ui.button('Agregar Nuevo', icon='add', on_click=self.agregar_examen_complementario)\
                                    .classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                            
                        if ultimo_examen:
                            with ui.card().classes(HC_SECTION_CARD):
                                with ui.column().classes('gap-4'):
                                    with ui.row().classes('justify-between items-center border-b pb-2'):
                                        ui.label(f'Último examen: {ultimo_examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-700 font-medium')
                                    
                                    with ui.grid(columns=2).classes('gap-4'):
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.column().classes('gap-3'):
                                                self._create_value_row("Hemoglobina", f"{ultimo_examen.hb} g/dL")
                                                self._create_value_row("HbA1c", f"{ultimo_examen.HbA1c} %")
                                                self._create_value_row("Hematocrito", f"{ultimo_examen.hto} %")
                                                self._create_value_row("Eritrosedimentación", f"{ultimo_examen.eritro} mill/mm³")
                                        
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.column().classes('gap-3'):
                                                self._create_value_row("Glucemia", f"{ultimo_examen.glucemia} mmol/L")
                                                self._create_value_row("Colesterol", f"{ultimo_examen.colesterol} mmol/L")
                                                self._create_value_row("Triglicéridos", f"{ultimo_examen.trigliceridos} mmol/L")
                                                self._create_value_row("TGP", f"{ultimo_examen.tgp} U/L")
                                                self._create_value_row("GGT", f"{ultimo_examen.ggt} U/L")
                                                self._create_value_row("HDL-C", ultimo_examen.HDLC)
                                                self._create_value_row("TGO", ultimo_examen.TGO)
                                    
                                    with ui.grid(columns=2).classes('gap-4'):
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.column().classes('gap-3'):
                                                ui.label('Proteínas').classes('font-bold text-gray-800')
                                                self._create_value_row("Proteínas Totales", f"{ultimo_examen.proteinas_totales} g/dL")
                                                self._create_value_row("Albuminuria", f"{ultimo_examen.albuminuria} mmol/L")
                                                self._create_value_row("Globulina", f"{ultimo_examen.globulina} g/dL")
                                        
                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.column().classes('gap-3'):
                                                self._create_value_row("Calcio",ultimo_examen.calcio)
                                                self._create_value_row("Fosforo",ultimo_examen.fosforo)
                                                self._create_value_row("Conteo de Plaquetas",ultimo_examen.conteo_plaquetas)
                                                self._create_value_row("Coagulación",ultimo_examen.coagulacion)
                                                self._create_value_row("Sangramiento",ultimo_examen.sangramiento)
                                    
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.column().classes('gap-2'):
                                            self._create_value_row("Ultrasonido Abdominal", ultimo_examen.ultrasonido_abdominal)
                                            self._create_value_row("Prueba Conducción Nerviosa (Superior)", ultimo_examen.prueba_conduccion_nerviosa_miembro_superior)
                                            self._create_value_row("Prueba Conducción Nerviosa (Inferior)", ultimo_examen.prueba_conduccion_nerviosa_miembro_inferior)
                                    
                                    if ultimo_examen.campos_personalizados:
                                        with ui.card().classes(HC_SECTION_CARD):
                                            ui.label(' Otros Resultados').classes('font-bold text-indigo-800 mb-2')
                                            for campo in ultimo_examen.campos_personalizados:
                                                display_valor = f"{campo.valor} {campo.unidad}" if campo.unidad else campo.valor
                                                with ui.row().classes('justify-between py-1'):
                                                    ui.label(campo.nombre).classes('font-medium text-gray-700')
                                                    ui.label(display_valor).classes('text-gray-900 font-medium')
                        else:
                            ui.icon('info').classes('text-gray-400 text-4xl mb-2')
                            ui.label('No hay exámenes complementarios registrados').classes('text-gray-500 italic')
                
                # --- COLUMNA DERECHA: HISTORIAL COMPLETO ---
                with ui.column().classes('col-12 col-md-5'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        ui.label('Historial Completo').classes(HEADER_TITLE_CLASSES)
                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            if examenes_historial:
                                for examen in examenes_historial:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        with ui.column().classes('gap-4'):
                                            with ui.row().classes('gap-2'):
                                                if tiene_permiso("complementarios_manage"):
                                                    ui.button(icon='edit', on_click=lambda e, ex=examen: self.editar_examen_complementario(ex)).props('flat round dense').classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                                                    ui.button(icon='delete', on_click=lambda e, ex=examen: self.eliminar_examen_complementario(ex)).props('flat round dense').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                                            
                                            with ui.row().classes('justify-between items-center border-b pb-2'):
                                                ui.label(f'Evaluado: {examen.fecha_registro.strftime("%d/%m/%Y")}').classes('text-gray-700 font-medium')
                                            
                                            with ui.grid(columns=2).classes('gap-4'):
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.column().classes('gap-3'):
                                                        self._create_value_row("Hemoglobina", f"{examen.hb} g/dL")
                                                        self._create_value_row("HbA1c", f"{examen.HbA1c} %")
                                                        self._create_value_row("Hematocrito", f"{examen.hto} %")
                                                        self._create_value_row("Eritrosedimentación", f"{examen.eritro} mill/mm³")
                                                
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.column().classes('gap-3'):
                                                        self._create_value_row("Glucemia", f"{examen.glucemia} mmol/L")
                                                        self._create_value_row("Colesterol", f"{examen.colesterol} mmol/L")
                                                        self._create_value_row("Triglicéridos", f"{examen.trigliceridos} mmol/L")
                                                        self._create_value_row("TGP", f"{examen.tgp} U/L")
                                                        self._create_value_row("GGT", f"{examen.ggt} U/L")
                                                        self._create_value_row("HDL-C", examen.HDLC)
                                                        self._create_value_row("TGO", examen.TGO)
                                            
                                            with ui.grid(columns=2).classes('gap-4'):
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.column().classes('gap-3'):
                                                        ui.label('Proteínas').classes('font-bold text-gray-800')
                                                        self._create_value_row("Proteínas Totales", f"{examen.proteinas_totales} g/dL")
                                                        self._create_value_row("Albuminuria", f"{examen.albuminuria} mmol/L")
                                                        self._create_value_row("Globulina", f"{examen.globulina} g/dL")
                                                
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    with ui.column().classes('gap-3'):
                                                        self._create_value_row("Calcio",examen.calcio)
                                                        self._create_value_row("Fosforo",examen.fosforo)
                                                        self._create_value_row("Conteo de Plaquetas",examen.conteo_plaquetas)
                                                        self._create_value_row("Coagulación",examen.coagulacion)
                                                        self._create_value_row("Sangramiento",examen.sangramiento)

                                            with ui.card().classes(HC_SECTION_CARD):
                                                with ui.column().classes('gap-2'):
                                                    self._create_value_row("Ultrasonido Abdominal", examen.ultrasonido_abdominal)
                                                    self._create_value_row("Prueba Conducción Nerviosa (Superior)", examen.prueba_conduccion_nerviosa_miembro_superior)
                                                    self._create_value_row("Prueba Conducción Nerviosa (Inferior)", examen.prueba_conduccion_nerviosa_miembro_inferior)
                                            
                                            if examen.campos_personalizados:
                                                with ui.card().classes(HC_SECTION_CARD):
                                                    ui.label(' Otros Resultados').classes('font-bold text-indigo-800 mb-2')
                                                    for campo in examen.campos_personalizados:
                                                        display_valor = f"{campo.valor} {campo.unidad}" if campo.unidad else campo.valor
                                                        with ui.row().classes('justify-between py-1'):
                                                            ui.label(campo.nombre).classes('font-medium text-gray-700')
                                                            ui.label(display_valor).classes('text-gray-900 font-medium')
                            else:
                                ui.label('No hay registros de exámenes complementarios').classes('text-gray-500 italic')

    def agregar_examen_complementario(self):
        campos_personalizados = [] 

        with ui.dialog().props('maximized') as dialog, ui.card().classes('w-full h-full overflow-y-auto rounded-none shadow-none'):
            ui.label('Agregar Examen Complementario').classes(HEADER_TITLE_CLASSES)
            
            with ui.input('Fecha').classes('w-full mb-6') as fecha_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            with ui.grid(columns=2).classes('w-full max-h-[70vh] pr-4 overflow-y-auto'):
                    
                    # HEMATOLÓGICOS
                    with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                hb = self.input_clinico("Hemoglobina (g/L)", min_val=0, max_val=230, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                HbA1c = self.input_clinico("HbA1c (%)", min_val=0, max_val=20, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                hto = self.input_clinico("Hematocrito (%)", min_val=0, max_val=70, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                conteo_plaquetas = self.input_clinico("Conteo de Plaquetas", min_val=0, max_val=1500, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                eritro = self.input_clinico("Eritrosedimentación mm/h", min_val=0, max_val=150, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                coagulacion = self.input_clinico("Coagulación", min_val=0, max_val=20, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                sangramiento = self.input_clinico("Sangramiento", min_val=0, max_val=20, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')

                    # BIOQUÍMICOS
                    with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                glucemia = self.input_clinico("Glucemia (mmol/L)", min_val=1, max_val=35, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                colesterol = self.input_clinico("Colesterol (mmol/L)", min_val=1, max_val=20, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                trigliceridos = self.input_clinico("Triglicéridos (mmol/L)", min_val=0.2, max_val=20, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                tgp = self.input_clinico("TGP (U/L)", min_val=1, max_val=2000, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                TGO = self.input_clinico("TGO (U/L)", min_val=1, max_val=2000, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                ggt = self.input_clinico("GGT (U/L)", min_val=1, max_val=2000, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                HDLC = self.input_clinico("HDL-C (mmol/L)", min_val=0, max_val=10, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')

                    # PROTEÍNAS
                    with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                proteinas_totales = self.input_clinico("Proteínas Totales (g/dL)", min_val=2, max_val=100, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                albuminuria = self.input_clinico("Albuminuria (mmol/L)", min_val=0, max_val=300, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                globulina = self.input_clinico("Globulina (g/dL)", min_val=1, max_val=60, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')

                    # OTROS
                    with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                calcio = self.input_clinico("Calcio", min_val=0.5, max_val=10, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                                fosforo = self.input_clinico("Fósforo", min_val=0.2, max_val=5, valor_inicial=None).classes(INPUT_CLASSES + ' w-full')
                        with ui.element('div').classes('col-12 col-sm-6'):
                            with ui.column().classes('gap-4 w-full'):
                                prueba_conduccion_nerviosa_miembro_superior = ui.select(options=["Normal", "Patologica", ""], label='Prueba C.N. Superior', value=None).classes(INPUT_CLASSES + ' w-full')
                                prueba_conduccion_nerviosa_miembro_inferior = ui.select(options=["Normal", "Patologica", ""], label='Prueba C.N. Inferior', value=None).classes(INPUT_CLASSES + ' w-full')

                    # ULTRASONIDO
                    with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                        with ui.element('div').classes('col-12'):
                            ultrasonido_abdominal = ui.select(
                                options=[
                                    "Normal", "Aumento Difuso ecogenicidad Leve I", "Aumento Difuso ecogenicidad Moderada II",
                                    "Aumento Difuso ecogenicidad Severo III", "Hepatomegalia", "Ecoestructura heterogénea o Irregular",
                                    "Bordes Hepáticos Lobulador", "Esplenomegalia", "Otros", ""
                                ],
                                label='Ultrasonido Abdominal',
                                multiple=True,
                                value=""
                            ).classes(INPUT_CLASSES + ' w-full')
                        with ui.element('div').classes('col-12'):
                            otros_input = ui.input(label='Especificar "Otros"').classes(INPUT_CLASSES + ' w-full').bind_visibility_from(
                                ultrasonido_abdominal, 'value', backward=lambda v: isinstance(v, list) and "Otros" in v
                            )

            with ui.column().classes('w-full gap-4 p-4 border-t mt-4') as container_personalizados:
                ui.label(' Otros Campos (Personalizados)').classes('font-bold text-lg text-indigo-700')
                
                def agregar_campo_personalizado():
                    with ui.row().classes('w-full gap-2 items-center') as row:
                        ui.input(label='Nombre del campo').classes('flex-1')
                        ui.input(label='Valor').classes('flex-1')
                        ui.input(label='Unidad (opcional)').classes('flex-1')
                        ui.button(icon='delete', on_click=lambda: container_personalizados.remove(row)).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    campos_personalizados.append(row)
                
                ui.button(' Agregar Campo Personalizado', on_click=agregar_campo_personalizado).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

            def ejecutar_guardado():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='warning')
                    return
                
                # Empaquetamos los datos en un diccionario para mantener el método limpio
                datos_examen = {
                    'hb': hb.value or 0, 'hto': hto.value or 0, 'eritro': eritro.value or 0,
                    'glucemia': glucemia.value or 0, 'colesterol': colesterol.value or 0, 'trigliceridos': trigliceridos.value or 0,
                    'HDLC': HDLC.value or None, 'tgp': tgp.value or 0, 'TGO': TGO.value or None,
                    'proteinas_totales': proteinas_totales.value or 0, 'albuminuria': albuminuria.value or 0, 'globulina': globulina.value or 0,
                    'calcio': calcio.value or 0, 'fosforo': fosforo.value or 0, 'conteo_plaquetas': conteo_plaquetas.value or 0,
                    'coagulacion': coagulacion.value or None, 'sangramiento': sangramiento.value or None,
                    'ultrasonido_abdominal': ultrasonido_abdominal.value or [], 'otros_input': otros_input.value or "",
                    'prueba_cn_superior': prueba_conduccion_nerviosa_miembro_superior.value or "",
                    'prueba_cn_inferior': prueba_conduccion_nerviosa_miembro_inferior.value or "",
                    'HbA1c': HbA1c.value or None, 'ggt': ggt.value or None
                }

                exito, msg = self.controlador_complementarios.guardar_examen(
                    self.paciente.id, fecha_input.value, datos_examen, campos_personalizados
                )

                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_complementarios.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', on_click=ejecutar_guardado).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def editar_examen_complementario(self, examen):
        campos_personalizados = []

        with ui.dialog().props('maximized') as dialog, ui.card().classes('w-full h-full overflow-y-auto rounded-none shadow-none'):
            ui.label('Editar Examen Complementario').classes(HEADER_TITLE_CLASSES)

            with ui.input('Fecha').classes('w-full mb-6') as fecha_input:
                fecha_input.value = examen.fecha_registro.strftime('%Y-%m-%d')
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                        with ui.row().classes('justify-end'):
                            ui.button('Cerrar', on_click=menu.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            with ui.grid(columns=2).classes('w-full max-h-[70vh] pr-4 overflow-y-auto'):
                # HEMATOLÓGICOS
                with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            hb = self.input_clinico("Hemoglobina (g/L)", min_val=0, max_val=230, valor_inicial=examen.hb).classes(INPUT_CLASSES + ' w-full')
                            HbA1c = self.input_clinico("HbA1c (%)", min_val=0, max_val=20, valor_inicial=examen.HbA1c).classes(INPUT_CLASSES + ' w-full')
                            hto = self.input_clinico("Hematocrito (%)", min_val=0, max_val=70, valor_inicial=examen.hto).classes(INPUT_CLASSES + ' w-full')
                            conteo_plaquetas = self.input_clinico("Conteo de Plaquetas", min_val=0, max_val=1500, valor_inicial=examen.conteo_plaquetas).classes(INPUT_CLASSES + ' w-full')
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            eritro = self.input_clinico("Eritrosedimentación mm/h", min_val=0, max_val=100, valor_inicial=examen.eritro).classes(INPUT_CLASSES + ' w-full')
                            coagulacion = self.input_clinico("Coagulación", min_val=0, max_val=20, valor_inicial=examen.coagulacion).classes(INPUT_CLASSES + ' w-full')
                            sangramiento = self.input_clinico("Sangramiento", min_val=0, max_val=20, valor_inicial=examen.sangramiento).classes(INPUT_CLASSES + ' w-full')

                # BIOQUÍMICOS
                with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            glucemia = self.input_clinico("Glucemia (mmol/L)", min_val=1, max_val=35, valor_inicial=examen.glucemia).classes(INPUT_CLASSES + ' w-full')
                            colesterol = self.input_clinico("Colesterol (mmol/L)", min_val=0, max_val=20, valor_inicial=examen.colesterol).classes(INPUT_CLASSES + ' w-full')
                            trigliceridos = self.input_clinico("Triglicéridos (mmol/L)", min_val=0.2, max_val=20, valor_inicial=examen.trigliceridos).classes(INPUT_CLASSES + ' w-full')
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            tgp = self.input_clinico("TGP (U/L)", min_val=0, max_val=2000, valor_inicial=examen.tgp).classes(INPUT_CLASSES + ' w-full')
                            TGO = self.input_clinico("TGO (U/L)", min_val=0, max_val=2000, valor_inicial=examen.TGO).classes(INPUT_CLASSES + ' w-full')
                            ggt = self.input_clinico("GGT (U/L)", min_val=0, max_val=2000, valor_inicial=examen.ggt).classes(INPUT_CLASSES + ' w-full')
                            HDLC = self.input_clinico("HDL-C (mmol/L)", min_val=0, max_val=10, valor_inicial=examen.HDLC).classes(INPUT_CLASSES + ' w-full')

                # PROTEÍNAS
                with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            proteinas_totales = self.input_clinico("Proteínas Totales (g/dL)", min_val=0, max_val=100, valor_inicial=examen.proteinas_totales).classes(INPUT_CLASSES + ' w-full')
                            albuminuria = self.input_clinico("Albuminuria (mmol/L)", min_val=0, max_val=300, valor_inicial=examen.albuminuria).classes(INPUT_CLASSES + ' w-full')
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            globulina = self.input_clinico("Globulina (g/dL)", min_val=0, max_val=60, valor_inicial=examen.globulina).classes(INPUT_CLASSES + ' w-full')

                # OTROS FIJOS
                with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            calcio = self.input_clinico("Calcio", min_val=0, max_val=10, valor_inicial=examen.calcio).classes(INPUT_CLASSES + ' w-full')
                            fosforo = self.input_clinico("Fósforo", min_val=0, max_val=5, valor_inicial=examen.fosforo).classes(INPUT_CLASSES + ' w-full')
                    with ui.element('div').classes('col-12 col-sm-6'):
                        with ui.column().classes('gap-4 w-full'):
                            prueba_conduccion_nerviosa_miembro_superior = ui.select(options=["Normal", "Patologica", ""], label='Prueba C.N. Superior', value=examen.prueba_conduccion_nerviosa_miembro_superior).classes(INPUT_CLASSES + ' w-full')
                            prueba_conduccion_nerviosa_miembro_inferior = ui.select(options=["Normal", "Patologica", ""], label='Prueba C.N. Inferior', value=examen.prueba_conduccion_nerviosa_miembro_inferior).classes(INPUT_CLASSES + ' w-full')

                # ULTRASONIDO (Lógica de pre-carga)
                with ui.element('div').classes('row q-col-gutter-md w-full p-4'):
                    opciones_us = ["Normal", "Aumento Difuso ecogenicidad Leve I", "Aumento Difuso ecogenicidad Moderada II", "Aumento Difuso ecogenicidad Severo III", "Hepatomegalia", "Ecoestructura heterogénea o Irregular", "Bordes Hepáticos Lobulador", "Esplenomegalia", "Otros", ""]
                    valor_actual_us = []
                    detalle_us = ""

                    if examen.ultrasonido_abdominal:
                        partes = examen.ultrasonido_abdominal.split("; ")
                        for parte in partes:
                            if "Otros: " in parte:
                                detalle_us = parte.replace("Otros: ", "").strip()
                                valor_actual_us.append("Otros")
                            elif parte in opciones_us:
                                valor_actual_us.append(parte)
                            else:
                                valor_actual_us.append("Otros")
                                detalle_us = parte

                    with ui.element('div').classes('col-12'):
                        ultrasonido_abdominal = ui.select(options=opciones_us, label='Ultrasonido Abdominal', multiple=True, value=valor_actual_us or ["Normal"]).classes(INPUT_CLASSES + ' w-full')
                    with ui.element('div').classes('col-12'):
                        otros_input = ui.input(label='Especificar "Otros"', value=detalle_us).classes(INPUT_CLASSES + ' w-full').bind_visibility_from(ultrasonido_abdominal, 'value', backward=lambda v: isinstance(v, list) and "Otros" in v)

            # CAMPOS PERSONALIZADOS
            with ui.column().classes('w-full gap-4 p-4 border-t mt-4') as container_personalizados:
                ui.label('Otros Campos (Personalizados)').classes('font-bold text-lg text-indigo-700')

                def agregar_campo_personalizado(nombre_v='', valor_v='', unidad_v=''):
                    with ui.element('div').classes('row q-col-gutter-md w-full items-center') as row:
                        with ui.element('div').classes('col-12 col-md-4'):
                            ui.input(label='Nombre del campo', value=nombre_v).classes('w-full')
                        with ui.element('div').classes('col-12 col-md-4'):
                            ui.input(label='Valor', value=valor_v).classes('w-full')
                        with ui.element('div').classes('col-12 col-md-3'):
                            ui.input(label='Unidad (opcional)', value=unidad_v).classes('w-full')
                        with ui.element('div').classes('col-12 col-md-1 flex justify-center'):
                            ui.button(icon='delete', on_click=lambda: (container_personalizados.remove(row), campos_personalizados.remove(row))).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    campos_personalizados.append(row)

                ui.button('Agregar Campo Personalizado', on_click=lambda: agregar_campo_personalizado()).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

                for campo in examen.campos_personalizados:
                    agregar_campo_personalizado(campo.nombre, campo.valor, campo.unidad or "")

            def ejecutar_actualizacion():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='warning')
                    return

                datos_examen = {
                    'hb': hb.value or 0, 'hto': hto.value or 0, 'eritro': eritro.value or 0,
                    'glucemia': glucemia.value or 0, 'colesterol': colesterol.value or 0, 'trigliceridos': trigliceridos.value or 0,
                    'HDLC': HDLC.value or None, 'tgp': tgp.value or 0, 'TGO': TGO.value or None,
                    'proteinas_totales': proteinas_totales.value or 0, 'albuminuria': albuminuria.value or 0, 'globulina': globulina.value or 0,
                    'calcio': calcio.value or 0, 'fosforo': fosforo.value or 0, 'conteo_plaquetas': conteo_plaquetas.value or 0,
                    'coagulacion': coagulacion.value or None, 'sangramiento': sangramiento.value or None,
                    'ultrasonido_abdominal': ultrasonido_abdominal.value or [], 'otros_input': otros_input.value or "",
                    'prueba_cn_superior': prueba_conduccion_nerviosa_miembro_superior.value or "",
                    'prueba_cn_inferior': prueba_conduccion_nerviosa_miembro_inferior.value or "",
                    'HbA1c': HbA1c.value or None, 'ggt': ggt.value or None
                }

                exito, msg = self.controlador_complementarios.actualizar_examen(
                    examen, fecha_input.value, datos_examen, campos_personalizados
                )

                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_complementarios.refresh()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar Cambios', on_click=ejecutar_actualizacion).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')
            
            dialog.open()

    def eliminar_examen_complementario(self, examen):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar este examen complementario?')
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                
                def confirmar():
                    exito, msg = self.controlador_complementarios.eliminar_examen(examen)
                    if exito:
                        ui.notify(msg, type='positive')
                        dialog.close()
                        self.mostrar_complementarios.refresh()
                    else:
                        ui.notify(msg, type='negative')
                        
                ui.button('Eliminar', on_click=confirmar).classes(DANGER_BUTTON_CLASSES).props('color="error"')
        dialog.open()