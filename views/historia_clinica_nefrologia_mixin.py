

"""
Vista del módulo de Nefrología.
Toda la UI de NiceGUI: resumen, historial, diálogos de agregar/editar/eliminar.

Clasificación KDIGO 2012:
  A1 — Normal / Levemente aumentada   (< 30 mg/g)
  A2 — Moderadamente aumentada        (30–300 mg/g)   ← antes «microalbuminuria»
  A3 — Severamente aumentada          (> 300 mg/g)    ← antes «macroalbuminuria»
"""

from nicegui import ui

from .historia_clinica_constants import (
    HEADER_TITLE_CLASSES,
    PRIMARY_BUTTON_CLASSES,
    DANGER_BUTTON_CLASSES,
    SUCCESS_BUTTON_CLASSES,
    INPUT_CLASSES,
    HC_CARD_PROFESSIONAL,
    HC_SECTION_CARD,
)
from seguridad_roles import tiene_permiso
from controllers.historia_clinica_nefrologia_controller import (
    HistoriaClinicaNefrologiaControllerMixin,
    clasificar_albuminuria,
    derivar_categoria_global,
)

# ──────────────────────────────────────────────────────────────────────────────
#  CONSTANTES DE PRESENTACIÓN
# ──────────────────────────────────────────────────────────────────────────────

_CAT_COLOR: dict[str | None, str] = {
    'A1': 'green',
    'A2': 'orange',
    'A3': 'red',
    None: 'grey',
}

_CAT_DESCRIPCION: dict[str, str] = {
    'A1': 'Normal / Leve',
    'A2': 'Moderada',
    'A3': 'Severa',
}

_UNIDADES_ALBUMINURIA = ['mg/g', 'mg/24h', 'mg/mmol']

_OPCIONES_UTS = [
    "Normal", "Nefromegalia", "Disminución del tamaño Renal",
    "Aumento Ecogenicidad Cortical", "Atrofia Cortical",
    "Mala Delimitación Cortico-Medular", "Quistes Renales Simples",
    "Calcificaciones del Parenquíma Renal", "Litiasis Renal",
    "Malformaciones Renales", "Monorreno", "Doppler", "Otros",
]


# ──────────────────────────────────────────────────────────────────────────────
#  HELPERS DE PRESENTACIÓN  (privados al módulo)
# ──────────────────────────────────────────────────────────────────────────────

def _badge_categoria(categoria: str | None) -> None:
    """Renderiza un badge coloreado con la categoría A1/A2/A3."""
    color = _CAT_COLOR.get(categoria, 'grey')
    texto = categoria if categoria else '—'
    descripcion = _CAT_DESCRIPCION.get(categoria, 'Sin datos')
    with ui.row().classes('items-center gap-2'):
        ui.badge(texto, color=color).classes('text-white font-bold px-3 py-1 text-sm rounded-full')
        ui.label(descripcion).classes('text-xs text-gray-500')


def _parsear_uts_renal(valor_guardado: str, opciones: list[str]) -> tuple[list[str], str]:
    """
    Convierte el string guardado de UTS en (lista_seleccionada, detalle_otros).
    """
    seleccionados: list[str] = []
    detalle = ""

    if not valor_guardado:
        return seleccionados, detalle

    partes = valor_guardado.split("; ") if "; " in valor_guardado else [valor_guardado]
    for parte in partes:
        if "Otros: " in parte:
            detalle = parte.replace("Otros: ", "").strip()
            seleccionados.append("Otros")
        elif parte in opciones:
            seleccionados.append(parte)
        else:
            seleccionados.append("Otros")
            detalle = parte

    return seleccionados, detalle


# ──────────────────────────────────────────────────────────────────────────────
#  COMPONENTE INTERNO: lista interactiva de mediciones de albuminuria
# ──────────────────────────────────────────────────────────────────────────────

def _seccion_albuminuria(mediciones_data: list[dict], input_classes: str, primary_btn: str):
    """
    Construye la sección de entrada de mediciones de albuminuria para los diálogos.

    Retorna la función refreshable `mostrar_lista` para que el diálogo pueda
    llamarla al inicio y el botón Agregar la refresque.
    """

    def borrar_item(index: int) -> None:
        mediciones_data.pop(index)
        mostrar_lista.refresh()

    @ui.refreshable
    def mostrar_lista() -> None:
        # ── Categoría global derivada (read-only, reactiva) ──────────────────
        cat_global = derivar_categoria_global(mediciones_data)
        with ui.row().classes('w-full items-center gap-2 mb-3 p-2 bg-emerald-50 rounded-lg border border-emerald-200'):
            ui.icon('analytics', color='green', size='xs')
            ui.label('Categoría Global:').classes('text-xs font-semibold text-emerald-700')
            _badge_categoria(cat_global)
            ui.label('(calculada automáticamente — KDIGO 2012)').classes('text-xs text-gray-400 ml-1')

        # ── Lista de mediciones ───────────────────────────────────────────────
        if not mediciones_data:
            ui.label('No hay mediciones agregadas.').classes('text-xs italic text-slate-400 my-2 self-center')
            return

        with ui.column().classes('w-full gap-1 p-2 rounded-lg bg-slate-50 border border-slate-200 shadow-inner'):
            for i, item in enumerate(mediciones_data):
                cat = item.get('categoria')
                color = _CAT_COLOR.get(cat, 'grey')
                with ui.row().classes(
                    'w-full items-center justify-between p-2 bg-white rounded '
                    'border border-blue-100 hover:bg-blue-50 transition-colors'
                ):
                    # Valor y unidad
                    ui.label(f"{item['valor']:.2f} {item['unidad']}") \
                        .classes('text-sm font-bold text-blue-700 flex-grow')
                    # Badge de categoría derivada
                    if cat:
                        ui.badge(cat, color=color).classes('text-white font-bold px-2 py-1 text-xs rounded-full')
                    else:
                        ui.badge('Sin unidad KDIGO', color='grey').classes('text-xs opacity-70') \
                            .tooltip('Unidad mg/dL no permite clasificación directa. Usar mg/g o mg/24h.')
                    # Botón eliminar
                    ui.button(icon='delete', on_click=lambda idx=i: borrar_item(idx)) \
                        .props('flat round dense color="negative"') \
                        .classes('hover:bg-red-100 ml-2').tooltip('Eliminar medición')

    # ── Fila de entrada: valor + unidad + botón agregar ───────────────────────
    with ui.row().classes('w-full items-end gap-2 mb-2'):
        ma_valor = ui.number(
            label='Valor', min=0, max=10000,
        ).classes('flex-grow ' + input_classes).props('stack-label outlined')

        ma_unidad = ui.select(
            options=_UNIDADES_ALBUMINURIA,
            value='mg/g',
            label='Unidad',
        ).classes(input_classes + ' w-32').props('stack-label outlined') \
         .tooltip('mg/g (ACR) es la unidad preferida según KDIGO/ADA')

        def anadir() -> None:
            val = ma_valor.value
            uni = ma_unidad.value
            if not val or val <= 0:
                ui.notify('Ingrese un valor mayor a 0', type='warning')
                return
            cat = clasificar_albuminuria(val, uni)
            mediciones_data.append({'valor': val, 'unidad': uni, 'categoria': cat})
            ma_valor.set_value(None)
            mostrar_lista.refresh()

        ui.button(icon='add', on_click=anadir) \
            .props('round').classes(primary_btn).tooltip('Agregar medición')

    mostrar_lista()
    return mostrar_lista


# ──────────────────────────────────────────────────────────────────────────────
#  MIXIN VISTA
# ──────────────────────────────────────────────────────────────────────────────

class HistoriaClinicaNefrologiaMixin(HistoriaClinicaNefrologiaControllerMixin):
    """
    Mixin con toda la UI NiceGUI del módulo de Nefrología.
    Hereda HistoriaClinicaNefrologiaControllerMixin para acceder a los métodos
    de guardado/actualización.
    """

    # ── VISTA PRINCIPAL ───────────────────────────────────────────────────────

    @ui.refreshable
    def mostrar_nefrologia(self):
        with ui.column().classes('w-full p-0'):
            with ui.element('div').classes('row q-col-gutter-lg w-full'):

                # ── Panel izquierdo: último examen ────────────────────────────
                with ui.element('div').classes('col-12 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        with ui.row().classes('justify-between items-center'):
                            ui.label('Exámenes Nefrológicos').classes(HEADER_TITLE_CLASSES)
                            if tiene_permiso("nefrologia_manage"):
                                ui.button(
                                    'Agregar Nuevo', icon='add',
                                    on_click=self.agregar_examen_nefrologico,
                                ).classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')

                        examenes = self.paciente.nefrologia
                        if examenes:
                            ultimo = max(examenes, key=lambda x: x.fecha_registro)

                            with ui.card().classes(
                                'w-full bg-white p-6 mt-4 shadow-xl rounded-lg border border-blue-200'
                            ):
                                with ui.column().classes('gap-4'):
                                    ui.label(
                                        f'Último examen: {ultimo.fecha_registro.strftime("%d/%m/%Y")}'
                                    ).classes('text-gray-800 font-bold text-lg border-b pb-3')

                                    with ui.grid(columns=2).classes('gap-x-8 gap-y-4'):

                                        # Columna 1: valores bioquímicos
                                        with ui.column().classes('gap-3'):
                                            ui.label('Valores Principales') \
                                                .classes('text-sm font-semibold text-blue-700 mb-1')
                                            self._create_value_row("F. Glomerular", f"{ultimo.filtrado_glomerular_teorico:.2f} mL/min", "blue-600")
                                            self._create_value_row("Creatinina",    f"{ultimo.creatinina} µmol/L",  "blue-600")
                                            self._create_value_row("Urea",          f"{ultimo.urea} mmol/L",        "blue-600")
                                            self._create_value_row("Ácido Úrico",   f"{ultimo.ac_urico} mmol/L",    "green-600")

                                        # Columna 2: marcadores de daño
                                        with ui.column().classes('gap-3'):
                                            ui.label('Marcadores de Daño') \
                                                .classes('text-sm font-semibold text-green-700 mb-1')

                                            if hasattr(ultimo, 'proteinuria_valor') and ultimo.proteinuria_valor:
                                                self._create_value_row("Proteinuria 24h", f"{ultimo.proteinuria_valor:.2f} mg/24h", "blue-600")
                                            prot_color = "red-600" if ultimo.proteinuria == "Patologica" else "green-600"
                                            self._create_value_row("Clasif. Proteinuria", ultimo.proteinuria, color=prot_color)

                                            # ── Albuminuria: categoría global ──────────────────
                                            ui.label('Albuminuria').classes('text-sm font-semibold text-emerald-700 mb-1 mt-2')
                                            cat_global = getattr(ultimo, 'albuminuria_categoria', None)
                                            with ui.row().classes('items-center gap-2 ml-1'):
                                                _badge_categoria(cat_global)

                                            # ── Mediciones individuales ────────────────────────
                                            if ultimo.mediciones_albuminuria:
                                                ui.label('Mediciones').classes('text-xs font-semibold text-gray-500 mt-2')
                                                with ui.column().classes('gap-1 ml-2'):
                                                    for ma in ultimo.mediciones_albuminuria:
                                                        cat = ma.categoria
                                                        color = _CAT_COLOR.get(cat, 'grey')
                                                        with ui.row().classes('items-center gap-2'):
                                                            ui.label(f"• {ma.valor:.2f} {ma.unidad}") \
                                                                .classes('text-green-700 font-mono text-sm')
                                                            if cat:
                                                                ui.badge(cat, color=color) \
                                                                    .classes('text-white font-bold px-2 text-xs rounded-full')
                                            else:
                                                self._create_value_row("Mediciones", "No registradas", "gray-500")

                                    ui.separator().classes('my-2')

                                    # Clasificación y diagnóstico
                                    with ui.row().classes('w-full justify-between items-start gap-4'):

                                        with ui.card().classes(HC_CARD_PROFESSIONAL):
                                            with ui.column().classes('gap-2'):
                                                ui.label("Clasificación de Función Renal") \
                                                    .classes('font-bold text-gray-900 text-base')
                                                classification = ultimo.clasificacion
                                                color_map = {
                                                    "G1": "green", "G2": "blue", "G3A": "yellow",
                                                    "G3B": "orange", "G4": "red", "G5": "purple",
                                                }
                                                color = next(
                                                    (v for k, v in color_map.items() if k in classification), "gray"
                                                )
                                                with ui.row().classes('items-center gap-4'):
                                                    ui.badge(classification.split(" - ")[0], color=color) \
                                                        .classes('text-white font-bold px-4 py-2 text-sm rounded-full')
                                                    ui.label(classification.split(" - ")[1]) \
                                                        .classes('text-gray-700 font-medium text-sm')
                                                self._create_value_row("UTS-Renal", ultimo.uts_renal, "green-500")

                                        with ui.card().classes(HC_SECTION_CARD):
                                            with ui.column().classes('gap-2'):
                                                ui.label("Impresión Diagnóstica") \
                                                    .classes('font-bold text-gray-900 text-base')
                                                nef_color = "red-600" if ultimo.diagnostico_renal == "Si" else "green-600"
                                                self._create_value_row("Diagnóstico Renal", ultimo.diagnostico_renal, color=nef_color)
                                                cit_color = "red-600" if ultimo.cituria == "Patologica" else "green-600"
                                                self._create_value_row("Cituria", ultimo.cituria, color=cit_color)
                        else:
                            with ui.card().classes(HC_SECTION_CARD):
                                ui.icon('info').classes('text-gray-400 text-6xl mb-4')
                                ui.label('No hay exámenes nefrológicos registrados') \
                                    .classes('text-gray-500 italic text-lg')

                # ── Panel derecho: historial completo ─────────────────────────
                with ui.element('div').classes('col-12 col-md-6'):
                    with ui.card().classes(HC_CARD_PROFESSIONAL):
                        ui.label('Historial Completo').classes(HEADER_TITLE_CLASSES)

                        with ui.scroll_area().classes('h-[500px] pr-4'):
                            with ui.column().classes('w-full p-4 gap-4'):
                                if examenes:
                                    for examen in sorted(examenes, key=lambda x: x.fecha_registro, reverse=True):
                                        self._render_examen_historial(examen)
                                else:
                                    with ui.card().classes(HC_SECTION_CARD):
                                        ui.icon('info').classes('text-gray-400 text-6xl mb-4')
                                        ui.label('No hay registros de exámenes nefrológicos') \
                                            .classes('text-gray-500 italic text-lg')

    # ── CARD DE HISTORIAL (privado) ───────────────────────────────────────────

    def _render_examen_historial(self, examen) -> None:
        """Renderiza la card de un examen en el panel de historial."""
        with ui.card().classes(HC_SECTION_CARD):

            # Fila de fecha + acciones
            with ui.row().classes('justify-between items-center border-b pb-3 mb-3'):
                ui.label(f'Fecha: {examen.fecha_registro.strftime("%d/%m/%Y")}') \
                    .classes('text-lg font-bold text-gray-800')
                with ui.row().classes('gap-2'):
                    if tiene_permiso("nefrologia_manage"):
                        ui.button(
                            icon='edit',
                            on_click=lambda e, ex=examen: self.editar_examen_nefrologico(ex),
                        ).props('flat round dense').tooltip('Editar') \
                         .classes(PRIMARY_BUTTON_CLASSES).props('color="primary"')
                        ui.button(
                            icon='delete',
                            on_click=lambda e, ex=examen: self.eliminar_examen_nefrologico(ex),
                        ).props('flat round dense').tooltip('Eliminar') \
                         .classes(DANGER_BUTTON_CLASSES).props('color="error"')

            # Métricas clave (3 columnas)
            with ui.grid(columns=3).classes('w-full gap-4'):

                with ui.column().classes('gap-0 items-center'):
                    ui.label('F. Glomerular').classes('text-xs font-semibold text-gray-500 uppercase')
                    ui.label(f"{examen.filtrado_glomerular_teorico:.2f}") \
                        .classes('text-xl font-extrabold text-blue-600')
                    ui.label('mL/min').classes('text-xs text-gray-400')

                classification = examen.clasificacion
                class_tag = classification.split(" - ")[0]
                color_map = {
                    "G1": "green", "G2": "blue", "G3A": "yellow",
                    "G3B": "orange", "G4": "red", "G5": "purple",
                }
                color = next((v for k, v in color_map.items() if k in classification), "gray")
                with ui.column().classes('gap-0 items-center text-center'):
                    ui.label('Clasif. Renal').classes('text-xs font-semibold text-gray-500 uppercase')
                    ui.badge(class_tag, color=color) \
                        .classes('text-white font-bold px-3 py-1 text-sm w-fit rounded-full mt-1')
                    ui.label(classification.split(" - ")[1]) \
                        .classes('text-xs text-gray-600 truncate max-w-[100px]')

                # Albuminuria global en las métricas
                cat_global = getattr(examen, 'albuminuria_categoria', None)
                alb_color = _CAT_COLOR.get(cat_global, 'grey')
                with ui.column().classes('gap-0 items-center'):
                    ui.label('Albuminuria').classes('text-xs font-semibold text-gray-500 uppercase')
                    txt = cat_global if cat_global else '—'
                    ui.badge(txt, color=alb_color) \
                        .classes('text-white font-bold px-3 py-1 text-sm w-fit rounded-full mt-1')
                    ui.label(_CAT_DESCRIPCION.get(cat_global, 'Sin datos')) \
                        .classes('text-xs text-gray-600')

            ui.separator().classes('my-2')

            # Indicadores detallados
            with ui.column().classes('w-full'):
                self._create_info_row("Creatinina",  f"{examen.creatinina} µmol/L")
                self._create_info_row("Urea",        f"{examen.urea} mmol/L")
                self._create_info_row("Ácido Úrico", f"{examen.ac_urico} mmol/L")

                # Mediciones de albuminuria individuales
                if examen.mediciones_albuminuria:
                    for i, ma in enumerate(examen.mediciones_albuminuria):
                        cat = ma.categoria
                        color = _CAT_COLOR.get(cat, 'grey')
                        label = f"Albuminuria {i + 1} ({ma.unidad})"
                        with ui.row().classes('items-center gap-2'):
                            self._create_info_row(label, f"{ma.valor:.2f} {ma.unidad}", color="green-700")
                            if cat:
                                ui.badge(cat, color=color) \
                                    .classes('text-white font-bold px-2 text-xs rounded-full')
                else:
                    self._create_info_row("Albuminuria", "No registrada", color="gray-500")

                prot_color = "red-600" if examen.proteinuria == "Patologica" else "green-600"
                self._create_info_row("Proteinuria", examen.proteinuria, color=prot_color)
                if hasattr(examen, 'proteinuria_valor') and examen.proteinuria_valor:
                    self._create_info_row("Proteinuria 24h", f"{examen.proteinuria_valor:.2f} mg/24h")

                cit_color = "red-600" if examen.cituria == "Patologica" else "green-600"
                self._create_info_row("Cituria", examen.cituria, color=cit_color)
                nef_color = "red-600" if examen.diagnostico_renal == "Si" else "green-600"
                self._create_info_row("Diagnóstico Renal", examen.diagnostico_renal, color=nef_color)
                self._create_info_row("UTS-Renal", examen.uts_renal)

    # ── DIÁLOGO: AGREGAR ──────────────────────────────────────────────────────

    def agregar_examen_nefrologico(self):
        mediciones_data: list[dict] = []

        with ui.dialog().classes('w-full') as dialog, \
             ui.card().classes('w-[850px] max-w-none p-0'):

            # Header
            with ui.row().classes('w-full bg-slate-50 p-4 items-center justify-between border-b'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('science', color='primary', size='md')
                    ui.label('Nuevo Examen Nefrológico').classes(HEADER_TITLE_CLASSES)
                ui.button(icon='close', on_click=dialog.close).props('flat round dense').classes('text-slate-400')

            with ui.column().classes('w-full p-6 gap-4'):

                # Fecha
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


                with ui.grid(columns=2).classes('w-full gap-6'):

                    # Columna izquierda: función renal + proteinuria
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('FUNCIÓN RENAL') \
                                .classes('text-xs font-black text-blue-600 tracking-widest mb-2')
                            filtrado_glomerular_teorico = self.input_clinico(
                                'Filtrado Glomerular (mL/min)', min_val=0, max_val=200, valor_inicial=None,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label')
                            creatinina = self.input_clinico(
                                'Creatinina (µmol/L)', min_val=20, max_val=2000, valor_inicial=None,
                            ).classes(INPUT_CLASSES + ' w-50')
                            urea = self.input_clinico(
                                'Urea (mmol/L)', min_val=1, max_val=50, valor_inicial=None,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label')
                            ac_urico = self.input_clinico(
                                'Ácido Úrico (mmol/L)', min_val=50, max_val=1500, valor_inicial=None,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label')

                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('PROTEINURIA') \
                                .classes('text-xs font-black text-purple-600 tracking-widest mb-2')
                            proteinuria_valor = self.input_clinico(
                                'Proteinuria 24h (mg/24h)', min_val=0, max_val=20000, valor_inicial=None,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label')
                            proteinuria_clasificacion = ui.select(
                                options=['Normal', 'Patologica'],
                                label='Clasificación de la Proteinuria',
                                value=None,
                            ).classes(INPUT_CLASSES + ' w-full mt-2').props('stack-label outlined dense')

                    # Columna derecha: albuminuria + imagen/diagnóstico
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('ALBUMINURIA (KDIGO 2012)') \
                                .classes('text-xs font-black text-emerald-600 tracking-widest mb-2')
                            ui.label('Ingrese cada medición. La categoría A1/A2/A3 se calcula automáticamente.') \
                                .classes('text-xs text-gray-400 mb-3')

                            # El componente de sección devuelve la función refreshable
                            _seccion_albuminuria(mediciones_data, INPUT_CLASSES, PRIMARY_BUTTON_CLASSES)

                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('IMAGEN Y DIAGNÓSTICO') \
                                .classes('text-xs font-black text-amber-600 tracking-widest mb-2')

                            cituria = ui.select(
                                ['Normal', 'Patologica'], value=None, label='Cituria',
                            ).classes(INPUT_CLASSES + ' w-full').props('stack-label')

                            uts_renal = ui.select(
                                _OPCIONES_UTS,
                                label='Ultrasonido renal', multiple=True, value=[],
                            ).classes(INPUT_CLASSES + ' w-full').props('stack-label')

                            otros_input = ui.input(label='Especificar "Otros"') \
                                .classes(INPUT_CLASSES + ' w-full').props('stack-label') \
                                .bind_visibility_from(
                                    uts_renal, 'value',
                                    backward=lambda v: isinstance(v, list) and "Otros" in v,
                                )

                    diagnostico_renal = ui.select(
                         ['Sano (Sin daño renal)', 'Enfermedad Renal Crónica NO Diabética','Enfermedad Renal Diabética'], value=None, label='Diagnóstico Renal',
                    ).classes(INPUT_CLASSES + ' w-full').props('stack-label')

            # Footer
            with ui.row().classes('w-full p-4 bg-slate-50 border-t justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES)
                ui.button('Guardar', icon='save', on_click=lambda: self.guardar_examen_nefrologico(
                    fecha_input.value,
                    filtrado_glomerular_teorico.value or 0,
                    creatinina.value or 0,
                    urea.value or 0,
                    ac_urico.value or 0,
                    cituria.value,
                    mediciones_data,
                    proteinuria_valor.value or 0,
                    proteinuria_clasificacion.value,
                    diagnostico_renal.value,
                    uts_renal.value or [],
                    otros_input.value or "",
                    dialog,
                )).classes(SUCCESS_BUTTON_CLASSES).props('color=success')

        dialog.open()

    # ── DIÁLOGO: EDITAR ───────────────────────────────────────────────────────

    def editar_examen_nefrologico(self, examen):
        # Inicializar datos temporales desde el examen existente
        mediciones_data: list[dict] = [
            {
                'valor': ma.valor,
                'unidad': ma.unidad,
                'categoria': ma.categoria,   # ya calculada y guardada
                'id': ma.id,
            }
            for ma in examen.mediciones_albuminuria
        ]

        uts_seleccionados, detalle_us = _parsear_uts_renal(examen.uts_renal or "", _OPCIONES_UTS)

        with ui.dialog().classes('w-full') as dialog, \
             ui.card().classes('w-[850px] max-w-none p-0'):

            # Header
            with ui.row().classes('w-full bg-slate-50 p-4 items-center justify-between border-b'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('edit_note', color='primary', size='md')
                    ui.label('Editar Examen Nefrológico').classes(HEADER_TITLE_CLASSES)
                ui.button(icon='close', on_click=dialog.close).props('flat round dense').classes('text-slate-400')

            with ui.column().classes('w-full p-6 gap-4'):

                # Fecha
                with ui.card().classes(HC_SECTION_CARD + ' bg-blue-50/30 border-dashed'):
                    with ui.row().classes('w-full items-center gap-4'):
                        ui.icon('calendar_month', color='primary', size='sm')
                        fecha_input = ui.input('Fecha de Registro') \
                            .classes('flex-grow ' + INPUT_CLASSES).props('stack-label outlined')
                        fecha_input.value = examen.fecha_registro.strftime('%Y-%m-%d')
                        with fecha_input.add_slot('append'):
                            ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                            with ui.menu() as menu:
                                ui.date().bind_value(fecha_input).props(
                                    f'locale="es" default-year-month={self.current_month} '
                                    f':options="date => date <= \'{self.today}\'"'
                                )

                with ui.grid(columns=2).classes('w-full gap-6'):

                    # Columna izquierda: función renal + proteinuria
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('FUNCIÓN RENAL') \
                                .classes('text-xs font-black text-blue-600 tracking-widest mb-2')
                            filtrado_glomerular_teorico = self.input_clinico(
                                'Filtrado Glomerular (mL/min)', min_val=0, max_val=150,
                                valor_inicial=examen.filtrado_glomerular_teorico,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label outlined')
                            creatinina = self.input_clinico(
                                'Creatinina (µmol/L)', min_val=20, max_val=2000,
                                valor_inicial=examen.creatinina,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label outlined')
                            urea = self.input_clinico(
                                'Urea (mmol/L)', min_val=1, max_val=50,
                                valor_inicial=examen.urea,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label outlined')
                            ac_urico = self.input_clinico(
                                'Ácido Úrico (mmol/L)', min_val=50, max_val=1500,
                                valor_inicial=examen.ac_urico,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label outlined')

                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('PROTEINURIA') \
                                .classes('text-xs font-black text-purple-600 tracking-widest mb-2')
                            proteinuria_valor = self.input_clinico(
                                'Proteinuria 24h (mg/24h)', min_val=0, max_val=20000,
                                valor_inicial=getattr(examen, 'proteinuria_valor', 0) or 0,
                            ).classes(INPUT_CLASSES + ' w-50').props('stack-label outlined')
                            opciones_proteinuria = ['Normal', 'Patologica']

                            valor_proteinuria = (
                                examen.proteinuria
                                if examen.proteinuria in opciones_proteinuria
                                else None
                            )

                            proteinuria_clasificacion = ui.select(
                                opciones_proteinuria,
                                value=valor_proteinuria,
                                label='Clasificación de Proteinuria',
                            ).classes(INPUT_CLASSES + ' w-full mt-2').props('stack-label outlined')

                    # Columna derecha: albuminuria + imagen/diagnóstico
                    with ui.column().classes('gap-4'):
                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('ALBUMINURIA (KDIGO 2012)') \
                                .classes('text-xs font-black text-emerald-600 tracking-widest mb-2')
                            ui.label('Ingrese cada medición. La categoría A1/A2/A3 se calcula automáticamente.') \
                                .classes('text-xs text-gray-400 mb-3')

                            _seccion_albuminuria(mediciones_data, INPUT_CLASSES, PRIMARY_BUTTON_CLASSES)

                        with ui.card().classes(HC_SECTION_CARD):
                            ui.label('IMAGEN Y DIAGNÓSTICO') \
                                .classes('text-xs font-black text-amber-600 tracking-widest mb-2')

                            cituria = ui.select(
                                ['Normal', 'Patologica'],
                                value=examen.cituria,
                                label='Cituria',
                            ).classes(INPUT_CLASSES + ' w-full').props('stack-label outlined')

                            uts_renal = ui.select(
                                _OPCIONES_UTS,
                                value=uts_seleccionados or ["Normal"],
                                label='Ultrasonido renal',
                                multiple=True,
                            ).classes(INPUT_CLASSES + ' w-full').props('stack-label outlined')

                            otros_input = ui.input(
                                label='Especificar "Otros"', value=detalle_us,
                            ).classes(INPUT_CLASSES + ' w-full').props('stack-label outlined') \
                             .bind_visibility_from(
                                 uts_renal, 'value',
                                 backward=lambda v: isinstance(v, list) and "Otros" in v,
                             )

                    diagnostico_renal = ui.select(
                        ['Sano (Sin daño renal)', 'Enfermedad Renal Crónica NO Diabética','Enfermedad Renal Diabética'],
                        value=examen.diagnostico_renal or 'Sano (Sin daño renal)',
                        label='Diagnóstico Renal',
                    ).classes(INPUT_CLASSES + ' w-full mt-2').props('stack-label outlined')

            # Footer
            with ui.row().classes('w-full p-4 bg-slate-50 border-t justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close).classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button('Guardar', icon='refresh', on_click=lambda: self.actualizar_examen_nefrologico(
                    examen,
                    fecha_input.value,
                    filtrado_glomerular_teorico.value or 0,
                    creatinina.value or 0,
                    urea.value or 0,
                    ac_urico.value or 0,
                    cituria.value,
                    mediciones_data,
                    proteinuria_valor.value or 0,
                    proteinuria_clasificacion.value,
                    diagnostico_renal.value,
                    uts_renal.value or [],
                    otros_input.value or "",
                    dialog,
                )).classes(SUCCESS_BUTTON_CLASSES).props('color=success')

        dialog.open()

    # ── DIÁLOGO: ELIMINAR ─────────────────────────────────────────────────────

    def eliminar_examen_nefrologico(self, examen):
        with ui.dialog() as dialog, ui.card():
            ui.label('¿Está seguro que desea eliminar este examen nefrológico?')
            with ui.row().classes('w-full justify-end gap-4'):
                ui.button('Cancelar', on_click=dialog.close) \
                    .classes(DANGER_BUTTON_CLASSES).props('color="warning"')
                ui.button(
                    'Eliminar',
                    on_click=lambda: self._confirmar_eliminacion_nefrologico(examen, dialog),
                ).classes(DANGER_BUTTON_CLASSES).props('color="error"')
        dialog.open()


