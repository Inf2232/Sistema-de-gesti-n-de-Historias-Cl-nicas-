# En: D:\trabajos\diabetes\DiabApp\app\nicegui\functions\historia_clinica_obstetrica_mixin.py
from nicegui import ui
from Errores import log_error_and_notify
from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES, PRIMARY_BUTTON_CLASSES, DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES, INPUT_CLASSES, HC_CARD_PROFESSIONAL, HC_SECTION_CARD
)
from seguridad_roles import tiene_permiso
from controllers.historia_clinica_obstetrica_controller import HistoriaClinicaObstetricaController

class HistoriaClinicaObstetricaMixin:

    @property
    def controlador_obstetrico(self):
        """Inicializa de forma segura el controlador bajo demanda."""
        if not hasattr(self, '_controlador_obstetrico'):
            self._controlador_obstetrico = HistoriaClinicaObstetricaController(self.session)
        return self._controlador_obstetrico

    @ui.refreshable
    def mostrar_historia_obstetrica(self):
        # Verificar si el paciente es mujer
        if self.paciente.sexo.lower() != 'femenino':
            with ui.element('div').classes('column full-width q-pa-lg q-gutter-y-lg'):
                with ui.card().classes(f'{HC_CARD_PROFESSIONAL} full-width'):
                    with ui.element('div').classes('column items-center q-pa-xl text-center q-gutter-y-lg full-width'):
                        ui.icon('info', size='xl', color='blue')
                        ui.label('Historia Obstétrica').classes(HEADER_TITLE_CLASSES)
                        with ui.element('div').classes('column q-gutter-y-md text-center'):
                            ui.label('Esta sección solo está disponible para pacientes femeninas').classes('text-h6 text-weight-medium text-grey-8')
                            ui.label('La historia obstétrica incluye información sobre gestaciones, partos, abortos y otros datos reproductivos específicos de la mujer.').classes('text-body1 text-grey-7')
                        with ui.card().classes(f'{HC_SECTION_CARD} q-mt-lg q-pa-md'):
                            with ui.element('div').classes('column items-center q-gutter-y-xs'):
                                ui.icon('person', size='md', color='grey-5')
                                ui.label(f'Paciente: {self.paciente.nombres} {self.paciente.apellidos}').classes('text-subtitle1 text-weight-medium text-grey-8')
                                ui.label(f'Sexo: {self.paciente.sexo}').classes('text-body2 text-grey-6')
                        with ui.element('div').classes('row items-center q-gutter-x-sm bg-blue-1 q-px-md q-py-sm q-mt-md rounded-borders'):
                            ui.icon('navigate_next', color='blue-8')
                            ui.label('Puede navegar a otras secciones usando las pestañas superiores').classes('text-body2 text-blue-9')
            return
        
        # --- CONSULTA DE DATOS PROCESADA POR EL CONTROLADOR ---
        historias_ordenadas, ultima = self.controlador_obstetrico.obtener_historias_procesadas(self.paciente)

        with ui.element('div').classes('column full-width q-pa-md'):
            with ui.element('div').classes('row full-width q-col-gutter-md'):
                
                # --- COLUMNA IZQUIERDA: RESUMEN ---
                with ui.element('div').classes('col-12 col-md-6'):
                    with ui.card().classes(f'{HC_CARD_PROFESSIONAL} full-width q-pa-md'):
                        with ui.element('div').classes('row justify-between items-center full-width'):
                            ui.label('Resumen del Último Registro').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso("hist_obstetrica_manage"):
                                ui.button('Nuevo', icon='add', on_click=self.agregar_historia_obstetrica).classes(PRIMARY_BUTTON_CLASSES)

                        if ultima:
                            ui.label(f'Registrado el {ultima.fecha_registro.strftime("%d/%m/%Y")}').classes('text-caption text-weight-bold text-blue-8 q-mt-sm')
                            with ui.element('div').classes('row full-width q-col-gutter-sm q-mt-sm'):
                                with ui.element('div').classes('col column q-gutter-y-xs'):
                                    ui.label('Ginecología').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                    ui.label(f"G:{ultima.gestaciones} P:{ultima.partos} A:{ultima.abortos}").classes('text-body2 text-weight-bold')
                                    ui.label(f'Ab. Esp: {ultima.abortos_espontaneos}').classes('text-caption')
                                    ui.label(f'Ab. Prov: {ultima.abortos_provocados}').classes('text-caption')
                                    ui.label(f"Menarca: {ultima.edad_menarca or '-'}a").classes('text-caption')
                                    ui.label(f"Edad Inicio: {ultima.edad_primera_relacion_sexual or '-'}a").classes('text-caption')
                                
                                with ui.element('div').classes('col column q-gutter-y-xs'):
                                    ui.label('Riesgos').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                    ui.label(f"Antecedentes EHE: {ultima.ehe}").classes('text-caption')
                                    for ehe in ultima.ehe_historial or []:
                                        ui.label(f" - Emb {ehe.get('no_emb', '?')}: EG {ehe.get('eg', '?')} sem").classes('text-caption text-grey-6')
                            
                                    diab_txt = f"Diab Gest: {ultima.diabetes_gestacional}"
                                    if ultima.diabetes_insulina == "Si": diab_txt += " (Insul)"
                                    ui.label(diab_txt).classes('text-caption text-red-9')
                                    if ultima.fecha_diabetes_gestacionaria:
                                        ui.label(f"Dx: {ultima.fecha_diabetes_gestacionaria.strftime('%m/%Y')}").classes('text-caption text-grey-6')
                                    if ultima.edad_materna_al_diagnostico is not None:
                                        ui.label(f"Edad al Dx: {ultima.edad_materna_al_diagnostico} años").classes('text-caption text-grey-6')
                                    for diab in ultima.diabetes_gestacional_historial or []:
                                        ui.label(f" - Emb {diab.get('no_emb', '?')}: EG {diab.get('eg', '?')} sem").classes('text-caption text-grey-6')
                                        
                                with ui.element('div').classes('col column q-gutter-y-xs'):
                                    ui.label('Fetal/Otros').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                    ui.label(f"Macrofetos: {ultima.macrofetos}").classes('text-caption')
                                    for macro in ultima.macrofetos_historial or []:
                                        ui.label(f" - Emb {macro.get('no_emb', '?')}").classes('text-caption text-grey-6')
                                    ui.label(f"Muertes Peri: {ultima.muertes_perinatales}").classes('text-caption')
                                    malf = f"Malf: {ultima.malformaciones}"
                                    if ultima.malformaciones == "Si" and ultima.malformaciones_cuales:
                                        malf += f" ({ultima.malformaciones_cuales})"
                                    ui.label(malf).classes('text-caption')

                            with ui.element('div').classes('row full-width q-col-gutter-sm q-mt-md'):
                                with ui.element('div').classes('col-6'):
                                    with ui.element('div').classes('column q-pa-sm q-card--bordered rounded-borders'):
                                        ui.label('Anticoncepción').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                        t_act = f"{ultima.tiempo_anticoncepcion_actual_anos}a {ultima.tiempo_anticoncepcion_actual_meses}m"
                                        ui.label(f"Act: {ultima.anticoncepcion_actual} ({t_act})").classes('text-caption text-deep-purple-9')
                                        t_prev = f"{ultima.tiempo_anticoncepcion_prev_anos}a {ultima.tiempo_anticoncepcion_prev_meses}m"
                                        ui.label(f"Prev: {ultima.anticoncepcion_previa} ({t_prev})").classes('text-caption text-grey-6')
                                
                                if ultima.edad_menopausia:
                                    with ui.element('div').classes('col-6 column justify-center'):
                                        ui.label(f"Menopausia: {ultima.edad_menopausia} años").classes('text-caption text-weight-bold')
                                        ui.label(f"Tipo: {ultima.tipo_menopausia}").classes('text-caption')
                        else:
                            ui.label('Sin registros previos').classes('text-italic text-grey-5 text-body2 q-pa-md')

                # --- COLUMNA DERECHA: GRÁFICO ---
                with ui.element('div').classes('col-12 col-md-6 gt-sm'):
                    ui.highchart({
                        'title': False,
                        'chart': {'type': 'column', 'height': 250},
                        'xAxis': {'categories': ['Gestaciones', 'Partos', 'Abortos']},
                        'series': [{'name': 'Cantidad', 'data': [ultima.gestaciones if ultima else 0, ultima.partos if ultima else 0, ultima.abortos if ultima else 0]}]
                    }).classes('full-width q-card--bordered rounded-borders')

            # --- HISTORIAL COMPLETO ---
            with ui.expansion('Ver Historial de Registros', icon='history').classes('full-width q-mt-md bg-white rounded-borders q-card--bordered'):
                if historias_ordenadas:
                    with ui.element('div').classes('column full-width q-pa-md q-gutter-y-md'):
                        for h in historias_ordenadas:
                            with ui.card().classes(f'{HC_CARD_PROFESSIONAL} full-width'):
                                with ui.element('div').classes('row justify-between items-center full-width'):
                                    ui.label('Registro Histórico').classes(HEADER_TITLE_CLASSES)
                                    with ui.element('div').classes('row q-gutter-x-sm'):
                                        if tiene_permiso("hist_obstetrica_manage"):
                                            ui.button(icon='edit', on_click=lambda e, h=h: self.editar_historia_obstetrica(h)).props('flat color="primary"').classes(PRIMARY_BUTTON_CLASSES)
                                            ui.button(icon='delete', on_click=lambda e, h=h: self.eliminar_historia_obstetrica(h)).props('flat dense size=sm color="negative"').classes(DANGER_BUTTON_CLASSES)

                                ui.label(f'Registrado el {h.fecha_registro.strftime("%d/%m/%Y")}').classes('text-caption text-weight-bold text-blue-8 q-mt-sm')
                                with ui.element('div').classes('row full-width q-col-gutter-sm q-mt-sm'):
                                    with ui.element('div').classes('col column q-gutter-y-xs'):
                                        ui.label('Ginecología').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                        ui.label(f"G:{h.gestaciones} P:{h.partos} A:{h.abortos}").classes('text-body2 text-weight-bold')
                                        ui.label(f'Ab. Esp: {h.abortos_espontaneos}').classes('text-caption')
                                        ui.label(f'Ab. Prov: {h.abortos_provocados}').classes('text-caption')
                                        ui.label(f"Menarca: {h.edad_menarca or '-'}a").classes('text-caption')
                                        ui.label(f"Edad inicio: {h.edad_primera_relacion_sexual or '-'}a").classes('text-caption')
                                        
                                    with ui.element('div').classes('col column q-gutter-y-xs'):
                                        ui.label('Riesgos').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                        ui.label(f"Antecedentes EHE: {h.ehe}").classes('text-caption')
                                        for ehe in h.ehe_historial or []:
                                            ui.label(f" - Emb {ehe.get('no_emb', '?')}: EG {ehe.get('eg', '?')} sem").classes('text-caption text-grey-6')
                                
                                        diab_txt = f"Diab Gest: {h.diabetes_gestacional}"
                                        if h.diabetes_insulina == "Si": diab_txt += " (Insul)"
                                        ui.label(diab_txt).classes('text-caption text-red-9')
                                        if h.fecha_diabetes_gestacionaria:
                                            ui.label(f"Dx: {h.fecha_diabetes_gestacionaria.strftime('%m/%Y')}").classes('text-caption text-grey-6')
                                        if h.edad_materna_al_diagnostico is not None:
                                            ui.label(f"Edad al Dx: {h.edad_materna_al_diagnostico} años").classes('text-caption text-grey-6')
                                        for diab in h.diabetes_gestacional_historial or []:
                                            ui.label(f" - Emb {diab.get('no_emb', '?')}: EG {diab.get('eg', '?')} sem").classes('text-caption text-grey-6')
                                            
                                    with ui.element('div').classes('col column q-gutter-y-xs'):
                                        ui.label('Fetal/Otros').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                        ui.label(f"Macrofetos: {h.macrofetos}").classes('text-caption')
                                        for macro in h.macrofetos_historial or []:
                                            ui.label(f" - Emb {macro.get('no_emb', '?')}").classes('text-caption text-grey-6')
                                        ui.label(f"Muertes Peri: {h.muertes_perinatales}").classes('text-caption')
                                        malf = f"Malf: {h.malformaciones}"
                                        if h.malformaciones == "Si" and h.malformaciones_cuales:
                                            malf += f" ({h.malformaciones_cuales})"
                                        ui.label(malf).classes('text-caption')

                                with ui.element('div').classes('row full-width q-col-gutter-sm q-mt-md'):
                                    with ui.element('div').classes('col-6'):
                                        with ui.element('div').classes('column q-pa-sm q-card--bordered rounded-borders'):
                                            ui.label('Anticoncepción').classes('text-caption text-weight-bold text-uppercase text-grey-5')
                                            t_act = f"{h.tiempo_anticoncepcion_actual_anos}a {h.tiempo_anticoncepcion_actual_meses}m"
                                            ui.label(f"Act: {h.anticoncepcion_actual} ({t_act})").classes('text-caption text-deep-purple-9')
                                            t_prev = f"{h.tiempo_anticoncepcion_prev_anos}a {h.tiempo_anticoncepcion_prev_meses}m"
                                            ui.label(f"Prev: {h.anticoncepcion_previa} ({t_prev})").classes('text-caption text-grey-6')
                                    if h.edad_menopausia:
                                        with ui.element('div').classes('col-6 column justify-center'):
                                            ui.label(f"Menopausia: {h.edad_menopausia} años").classes('text-caption text-weight-bold')
                                            ui.label(f"Tipo: {h.tipo_menopausia}").classes('text-caption')

    def agregar_historia_obstetrica(self):
        historial_diabetes, historial_ehe, historial_macrofetos = [], [], []

        with ui.dialog() as dialog, ui.card().classes('p-4').style("width:950px; max-width:none;"):
            ui.label('Nueva Historia Obstétrica').classes(HEADER_TITLE_CLASSES)
            
            with ui.row().classes('w-full items-center gap-4'):
                with ui.input('Fecha').classes('w-full') as fecha_input:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                            with ui.row().classes('justify-end'):
                                ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                        with fecha_input.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')   

            with ui.grid(columns=4).classes('w-full gap-4 mt-4'):
                edad_menarca = ui.number('Edad Menarca', min=5, max=25).classes(INPUT_CLASSES)
                edad_sexo = ui.number('Edad Inicio de las relaciones sexuales', min=8).classes(INPUT_CLASSES)
                gest_in = ui.number('Gestaciones', value=0, min=0).classes(INPUT_CLASSES)
                part_in = ui.number('Partos', value=0, min=0).classes(INPUT_CLASSES)
                ab_esp_in = ui.number('Ab. Espontáneos', value=0, min=0).classes(INPUT_CLASSES)
                ab_prov_in = ui.number('Ab. Provocados', value=0, min=0).classes(INPUT_CLASSES)
                muertes_per = ui.select(["No","Si"], value="No", label="Muertes Perinatales").classes(INPUT_CLASSES)
                edad_meno = ui.number('Edad Menopausia', value=None ,min=0).classes(INPUT_CLASSES)
                tipo_meno = ui.select(['Natural', 'Quirurgica', 'No Registrado'], label='Tipo Menopausia', value='No Registrado').classes(INPUT_CLASSES)
                malf_sel = ui.select(["No","Si"], value="No", label="Malformaciones").classes('w-full')
                malf_det = ui.input('¿Cuáles?').classes('w-full').bind_visibility_from(malf_sel, 'value', value='Si')

            ui.separator().classes('my-4')
            ui.label('Anticoncepción').classes('text-subtitle1 font-bold mb-2')
            with ui.grid(columns=2).classes('w-full gap-8 border'):
                with ui.column().classes('w-full p-2 rounded bg-blue-50/10'):
                    ant_act_sel = ui.select(['Ninguna', 'Hormonal', 'No Hormonal'], label='Método Actual', value='Ninguna').classes('w-full')
                    with ui.row().classes('items-center gap-2 mt-2').bind_visibility_from(ant_act_sel, 'value', backward=lambda v: v == 'Hormonal'):
                        ui.label('Tiempo empleo:').classes('text-grey-7 text-xs')
                        t_act_anos = ui.number('Años', value=0, min=0).classes('w-16')
                        t_act_meses = ui.number('Meses', value=0, min=0, max=11).classes('w-16')

                with ui.column().classes('w-full p-2 rounded bg-grey-50/10'):
                    ant_prev_sel = ui.select(['Ninguna', 'Hormonal', 'No Hormonal'], label='Método Previo', value='Ninguna').classes('w-full')
                    with ui.row().classes('items-center gap-2 mt-2').bind_visibility_from(ant_prev_sel, 'value', backward=lambda v: v == 'Hormonal'):
                        ui.label('Tiempo empleo:').classes('text-grey-7 text-xs')
                        t_prev_anos = ui.number('Años', value=0, min=0).classes('w-16')
                        t_prev_meses = ui.number('Meses', value=0, min=0, max=11).classes('w-16')

            ui.separator().classes('my-4')
            with ui.grid(columns=3).classes('w-full gap-4'):
                with ui.column().classes('border p-2 rounded shadow-sm'):
                    db_sel = ui.select(["No","Si"], value="No", label="Diabetes Gestacional").classes('w-full')
                    with ui.column().bind_visibility_from(db_sel, 'value', value='Si'):
                        with ui.input('Fecha Diagnóstico').classes('w-full') as fecha_db_input:
                            with ui.menu().props('no-parent-event') as menu_db:
                                with ui.date().bind_value(fecha_db_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"').classes('shadow-lg'):
                                    with ui.row().classes('justify-end p-2'):
                                        ui.button('Cerrar', on_click=menu_db.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                            with fecha_db_input.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu_db.open).classes('cursor-pointer text-primary')
                        db_insu = ui.select(["No","Si"], value="No", label="¿Usa Insulina?").classes('w-full')
                        edad_diag = ui.number('Edad al Diagnóstico', min=10, max=100).classes('w-full')
                        cont_db = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir al Historial', icon='add', on_click=lambda: modal_historial("Diabetes", historial_diabetes, cont_db, db_insu)).props('flat dense color="primary"')

                with ui.column().classes('border p-3 rounded shadow-sm'):
                    ehe_sel = ui.select(["No","Si"], value="No", label="Antecedentes EHE (Hipertensión)").classes('w-full')
                    with ui.column().bind_visibility_from(ehe_sel, 'value', value='Si'):
                        cont_ehe = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir al Historial', icon='add', on_click=lambda: modal_historial("EHE", historial_ehe, cont_ehe)).props('flat dense color="primary"')

                with ui.column().classes('border p-3 rounded shadow-sm'):
                    macro_sel = ui.select(["No","Si"], value="No", label="Macrofetos").classes('w-full')
                    with ui.column().bind_visibility_from(macro_sel, 'value', value='Si'):
                        cont_macro = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir Embarazo', icon='add', on_click=lambda: modal_historial("Macrofetos", historial_macrofetos, cont_macro)).props('flat dense color="primary"')

            def modal_historial(tipo, lista_obj, contenedor, ref_insu=None):
                with ui.dialog() as d, ui.card().classes('p-4 w-64'):
                    ui.label(f'Registro de {tipo}').classes('font-bold mb-2')
                    n_emb = ui.number('No. Embarazo', value=1, min=1, precision=0)
                    eg_sem = ui.number('Edad Gestacional', value=20, min=1) if tipo != "Macrofetos" else None

                    def confirmar():
                        reg = {"no_emb": int(n_emb.value)}
                        if eg_sem: reg["eg"] = int(eg_sem.value)
                        if tipo == "Diabetes": reg["insulina"] = ref_insu.value
                        lista_obj.append(reg)
                        with contenedor:
                            lbl = f"E{reg['no_emb']}" + (f" ({reg['eg']}s)" if eg_sem else "")
                            c = ui.chip(lbl, color='blue-1', icon='check').props('removable')
                            c.on('remove', lambda: lista_obj.remove(reg))
                        d.close()
                    ui.button('Confirmar', on_click=confirmar).classes('w-full mt-4')
                d.open()

            def guardar():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='negative')
                    return

                # EMPAQUETADO DE DATOS CAPTURADOS DE LA INTERFAZ
                datos = {
                    'fecha_registro': fecha_input.value,
                    'edad_menarca': edad_menarca.value,
                    'edad_primera_relacion_sexual': edad_sexo.value,
                    'gestaciones': gest_in.value,
                    'partos': part_in.value,
                    'abortos_espontaneos': ab_esp_in.value,
                    'abortos_provocados': ab_prov_in.value,
                    'anticoncepcion_actual': ant_act_sel.value,
                    'tiempo_act_anos': t_act_anos.value,
                    'tiempo_act_meses': t_act_meses.value,
                    'anticoncepcion_previa': ant_prev_sel.value,
                    'tiempo_prev_anos': t_prev_anos.value,
                    'tiempo_prev_meses': t_prev_meses.value,
                    'diabetes_gestacional': db_sel.value,
                    'diabetes_insulina': db_insu.value if db_sel.value == "Si" else "No",
                    'historial_diabetes': historial_diabetes,
                    'edad_materna_al_diagnostico': edad_diag.value if db_sel.value == "Si" else None,
                    'fecha_db_input': fecha_db_input.value if db_sel.value == "Si" else None,
                    'ehe': ehe_sel.value,
                    'historial_ehe': historial_ehe,
                    'macrofetos': macro_sel.value,
                    'historial_macrofetos': historial_macrofetos,
                    'malformaciones': malf_sel.value,
                    'malformaciones_cuales': malf_det.value if malf_sel.value == "Si" else None,
                    'muertes_perinatales': muertes_per.value,
                    'edad_menopausia': edad_meno.value,
                    'tipo_menopausia': tipo_meno.value
                }

                # DELEGACIÓN AL CONTROLADOR
                exito, msg = self.controlador_obstetrico.guardar_registro(self.paciente.id, datos)
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_historia_obstetrica.refresh()
                else:
                    ui.notify(f'Error al guardar: {msg}', type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar Todo', on_click=guardar).classes(SUCCESS_BUTTON_CLASSES).props('color="success"')

        dialog.open()

    def editar_historia_obstetrica(self, historia):
        historial_diabetes = list(historia.diabetes_gestacional_historial or [])
        historial_ehe = list(historia.ehe_historial or [])
        historial_macrofetos = list(historia.macrofetos_historial or [])

        with ui.dialog() as dialog, ui.card().classes('p-4').style("width:950px; max-width:none;"):
            ui.label('Editar Historia Obstétrica').classes(HEADER_TITLE_CLASSES)
            
            with ui.row().classes('w-full items-center gap-4'):
                with ui.input('Fecha', value=historia.fecha_registro.strftime('%Y-%m-%d') if historia.fecha_registro else '').classes('w-full') as fecha_input:
                    with ui.menu().props('no-parent-event') as menu:
                        with ui.date().bind_value(fecha_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"'):
                            with ui.row().classes('justify-end'):
                                ui.button('Cerrar', on_click=menu.close).props('flat color="error"').classes(DANGER_BUTTON_CLASSES)
                    with fecha_input.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

            with ui.grid(columns=4).classes('w-full gap-4 mt-4'):
                edad_menarca = ui.number('Edad Menarca', value=historia.edad_menarca, min=5, max=25).classes(INPUT_CLASSES)
                edad_sexo = ui.number('Edad Inicio de las relaciones sexuales', value=historia.edad_primera_relacion_sexual, min=8).classes(INPUT_CLASSES)
                gest_in = ui.number('Gestaciones', value=historia.gestaciones, min=0).classes(INPUT_CLASSES)
                part_in = ui.number('Partos', value=historia.partos, min=0).classes(INPUT_CLASSES)
                ab_esp_in = ui.number('Ab. Espontáneos', value=historia.abortos_espontaneos, min=0).classes(INPUT_CLASSES)
                ab_prov_in = ui.number('Ab. Provocados', value=historia.abortos_provocados, min=0).classes(INPUT_CLASSES)
                muertes_per = ui.select(["No","Si"], value=historia.muertes_perinatales, label="Muertes Perinatales").classes(INPUT_CLASSES)
                edad_meno = ui.number('Edad Menopausia', value=historia.edad_menopausia, min=0).classes(INPUT_CLASSES)
                tipo_meno = ui.select(['Natural', 'Quirurgica', 'No Registrado'], label='Tipo Menopausia', value=historia.tipo_menopausia or 'No Registrado').classes(INPUT_CLASSES)
                malf_sel = ui.select(["No","Si"], value=historia.malformaciones, label="Malformaciones").classes('w-full')
                malf_det = ui.input('¿Cuáles?', value=historia.malformaciones_cuales).classes('w-full').bind_visibility_from(malf_sel, 'value', value='Si')
            
            ui.separator().classes('my-4')
            ui.label('Anticoncepción').classes('text-subtitle1 font-bold mb-2')
            with ui.grid(columns=2).classes('w-full gap-8 border'):
                with ui.column().classes('w-full p-2 rounded bg-blue-50/10'):
                    ant_act_sel = ui.select(['Ninguna', 'Hormonal', 'No Hormonal'], label='Método Actual', value=historia.anticoncepcion_actual).classes('w-full')
                    with ui.row().classes('items-center gap-2 mt-2').bind_visibility_from(ant_act_sel, 'value', backward=lambda v: v == 'Hormonal'):
                        ui.label('Tiempo empleo:').classes('text-grey-7 text-xs')
                        t_act_anos = ui.number('Años', value=historia.tiempo_anticoncepcion_actual_anos, min=0).classes('w-16')
                        t_act_meses = ui.number('Meses', value=historia.tiempo_anticoncepcion_actual_meses, min=0, max=11).classes('w-16')

                with ui.column().classes('w-full p-2 rounded bg-grey-50/10'):
                    ant_prev_sel = ui.select(['Ninguna', 'Hormonal', 'No Hormonal'], label='Método Previo', value=historia.anticoncepcion_previa).classes('w-full')
                    with ui.row().classes('items-center gap-2 mt-2').bind_visibility_from(ant_prev_sel, 'value', backward=lambda v: v == 'Hormonal'):
                        ui.label('Tiempo empleo:').classes('text-grey-7 text-xs')
                        t_prev_anos = ui.number('Años', value=historia.tiempo_anticoncepcion_prev_anos, min=0).classes('w-16')
                        t_prev_meses = ui.number('Meses', value=historia.tiempo_anticoncepcion_prev_meses, min=0, max=11).classes('w-16')

            ui.separator().classes('my-4')
            with ui.grid(columns=3).classes('w-full gap-4'):
                with ui.column().classes('border p-2 rounded shadow-sm'):
                    db_sel = ui.select(["No","Si"], value=historia.diabetes_gestacional, label="Diabetes Gestacional").classes('w-full')
                    with ui.column().bind_visibility_from(db_sel, 'value', value='Si'):
                        with ui.input('Fecha Diagnóstico', value=historia.fecha_diabetes_gestacionaria.strftime('%Y-%m-%d') if historia.fecha_diabetes_gestacionaria else '').classes('w-full') as fecha_db_input:
                            with ui.menu().props('no-parent-event') as menu_db:
                                with ui.date().bind_value(fecha_db_input).props(f'locale="es" default-year-month={self.current_month} :options="date => date <= \'{self.today}\'"').classes('shadow-lg'):
                                    with ui.row().classes('justify-end p-2'):
                                        ui.button('Cerrar', on_click=menu_db.close).props('flat').classes(DANGER_BUTTON_CLASSES).props('color="error"')
                            with fecha_db_input.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu_db.open).classes('cursor-pointer text-primary')
                        edad_diag = ui.number('Edad al Diagnóstico', min=10, max=100, value=historia.edad_materna_al_diagnostico).classes('w-full')
                        db_insu = ui.select(["No","Si"], value=historia.diabetes_insulina, label="¿Usa Insulina?").classes('w-full')
                        cont_db = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir al Historial', icon='add', on_click=lambda: modal_historial("Diabetes", historial_diabetes, cont_db, db_insu)).props('flat dense color="primary"')

                with ui.column().classes('border p-3 rounded shadow-sm'):
                    ehe_sel = ui.select(["No","Si"], value=historia.ehe, label=" Antecedentes EHE (Hipertensión)").classes('w-full')
                    with ui.column().bind_visibility_from(ehe_sel, 'value', value='Si'):
                        cont_ehe = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir al Historial', icon='add', on_click=lambda: modal_historial("EHE", historial_ehe, cont_ehe)).props('flat dense color="primary"')

                with ui.column().classes('border p-3 rounded shadow-sm'):
                    macro_sel = ui.select(["No","Si"], value=historia.macrofetos, label="Macrofetos").classes('w-full')
                    with ui.column().bind_visibility_from(macro_sel, 'value', value='Si'):
                        cont_macro = ui.row().classes('gap-1 mb-2')
                        ui.button('Añadir Embarazo', icon='add', on_click=lambda: modal_historial("Macrofetos", historial_macrofetos, cont_macro)).props('flat dense color="primary"')

            def crear_chip(reg, contenedor, lista_ref):
                with contenedor:
                    eg_val = reg.get('eg')
                    lbl = f"E{reg['no_emb']}" + (f" ({eg_val}s)" if eg_val else "")
                    c = ui.chip(lbl, color='blue-1', icon='edit').props('removable')
                    c.on('remove', lambda: lista_ref.remove(reg))

            for r in historial_diabetes: crear_chip(r, cont_db, historial_diabetes)
            for r in historial_ehe: crear_chip(r, cont_ehe, historial_ehe)
            for r in historial_macrofetos: crear_chip(r, cont_macro, historial_macrofetos)

            def modal_historial(tipo, lista_obj, contenedor, ref_insu=None):
                with ui.dialog() as d, ui.card().classes('p-4 w-64'):
                    ui.label(f'Registro de {tipo}').classes('font-bold mb-2')
                    n_emb = ui.number('No. Embarazo', value=1, min=1, precision=0)
                    eg_sem = ui.number('Edad Gestacional', value=20, min=1) if tipo != "Macrofetos" else None

                    def confirmar():
                        reg = {"no_emb": int(n_emb.value)}
                        if eg_sem: reg["eg"] = int(eg_sem.value)
                        if tipo == "Diabetes": reg["insulina"] = ref_insu.value
                        lista_obj.append(reg)
                        crear_chip(reg, contenedor, lista_obj)
                        d.close()
                    ui.button('Confirmar', on_click=confirmar).classes('w-full mt-4')
                d.open()

            def actualizar():
                if not fecha_input.value:
                    ui.notify('Debe seleccionar una fecha', type='negative')
                    return

                datos = {
                    'fecha_registro': fecha_input.value,
                    'edad_menarca': edad_menarca.value,
                    'edad_primera_relacion_sexual': edad_sexo.value,
                    'gestaciones': gest_in.value,
                    'partos': part_in.value,
                    'abortos_espontaneos': ab_esp_in.value,
                    'abortos_provocados': ab_prov_in.value,
                    'anticoncepcion_actual': ant_act_sel.value,
                    'tiempo_act_anos': t_act_anos.value,
                    'tiempo_act_meses': t_act_meses.value,
                    'anticoncepcion_previa': ant_prev_sel.value,
                    'tiempo_prev_anos': t_prev_anos.value,
                    'tiempo_prev_meses': t_prev_meses.value,
                    'diabetes_gestacional': db_sel.value,
                    'diabetes_insulina': db_insu.value if db_sel.value == "Si" else "No",
                    'historial_diabetes': historial_diabetes,
                    'edad_materna_al_diagnostico': edad_diag.value if db_sel.value == "Si" else None,
                    'fecha_db_input': fecha_db_input.value if db_sel.value == "Si" else None,
                    'ehe': ehe_sel.value,
                    'historial_ehe': historial_ehe,
                    'macrofetos': macro_sel.value,
                    'historial_macrofetos': historial_macrofetos,
                    'malformaciones': malf_sel.value,
                    'malformaciones_cuales': malf_det.value if malf_sel.value == "Si" else None,
                    'muertes_perinatales': muertes_per.value,
                    'edad_menopausia': edad_meno.value,
                    'tipo_menopausia': tipo_meno.value
                }

                # DELEGACIÓN DE LA EDICIÓN AL CONTROLADOR
                exito, msg = self.controlador_obstetrico.actualizar_registro(historia, datos)
                if exito:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    self.mostrar_historia_obstetrica.refresh()
                else:
                    ui.notify(f'Error al actualizar: {msg}', type='negative')

            with ui.row().classes('w-full justify-end gap-4 mt-6'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Actualizar Datos', on_click=actualizar).classes(SUCCESS_BUTTON_CLASSES).props('color="primary"')

        dialog.open()
                
    def eliminar_historia_obstetrica(self, historia):
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label('¿Estás seguro de que deseas eliminar esta historia obstétrica?').classes('text-xl font-bold mb-4 text-red-600')
            with ui.row().classes('w-full justify-end gap-4 mt-4'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Eliminar', on_click=lambda: self.confirmar_eliminacion_historia_obstetrica(historia, dialog)).classes(DANGER_BUTTON_CLASSES).props('color="error"')
            dialog.open()

    def confirmar_eliminacion_historia_obstetrica(self, historia, dialog):
        # DELEGACIÓN DE LA ELIMINACIÓN AL CONTROLADOR
        exito, msg = self.controlador_obstetrico.eliminar_registro(historia)
        if exito:
            ui.notify(msg, type='positive')
            dialog.close()
            self.mostrar_historia_obstetrica.refresh()
        else:
            log_error_and_notify(Exception(msg), 'Error al eliminar historia obstétrica')    
            ui.notify(f'Error al eliminar: {msg}', type='negative')