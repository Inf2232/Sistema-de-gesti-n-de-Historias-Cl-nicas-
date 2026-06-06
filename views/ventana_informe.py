from __future__ import annotations

import asyncio
import base64
import hashlib
import re
import time
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
import tempfile
from seguridad_roles import *
from nicegui import ui

from models import Session as DbSession, Provincia, Municipio, AreaSalud, Indicaciones, Paciente

from controllers.motor_informe import (
    SECCIONES_DISPONIBLES, SECCIONES_DEFAULT,
    generar_informe, buscar_paciente,
)
from controllers.motor_informe_admin import (
    generar_informe_admin, obtener_opciones_filtro,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES COMPARTIDAS
# ═══════════════════════════════════════════════════════════════════════════════

_RE_EMOJI = re.compile(
    '['
    '\U0001F300-\U0001FAFF'
    '\U00002600-\U000027BF'
    '\U0001F000-\U0001F02F'
    '\U0001F0A0-\U0001F0FF'
    '\U0000200D\U0000FE0F'
    ']+',
    flags=re.UNICODE,
)

def _sin_emoji(texto: str) -> str:
    return _RE_EMOJI.sub('', texto).strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  CSS PDF — v3.0 (tablas sin cortes, diseño profesional)
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_PDF = """
/* ── BASE ───────────────────────────────────────────────────────────────── */
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    color: #1a1a2e;
    line-height: 1.5;
    margin: 0;
    padding: 0;
}
.page { width: 100%; }

/* ── TITULOS ─────────────────────────────────────────────────────────────── */
h1 {
    font-size: 13pt;
    color: #ffffff;
    background: #1e3a5f;
    padding: 8px 12px;
    margin: 0 0 8px 0;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    page-break-after: avoid;
}
h2 {
    font-size: 10pt;
    color: #ffffff;
    background: #2e6db4;
    padding: 5px 10px;
    margin-top: 14px;
    margin-bottom: 5px;
    page-break-after: avoid;
}
h3 {
    font-size: 9pt;
    color: #1e3a5f;
    border-bottom: 1.5px solid #c8d8f0;
    padding-bottom: 2px;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
}

/* ── TABLAS ──────────────────────────────────────────────────────────────── */
/* Los anchos se inyectan como atributos HTML width="X%" en cada th/td       */
/* por _postprocesar_tablas(), porque xhtml2pdf ignora CSS para anchos.      */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 10px 0;
    font-size: 8.5pt;
    table-layout: fixed;
}
th {
    background-color: #1e3a5f;
    color: #ffffff;
    padding: 5px 7px;
    text-align: left;
    font-weight: bold;
    word-wrap: break-word;
    white-space: normal;
}
td {
    padding: 4px 7px;
    border-bottom: 1px solid #dde3f0;
    vertical-align: top;
    word-wrap: break-word;
    white-space: normal;
}
tr.even td { background-color: #f4f7fb; }

/* ── BARRAS DE PROGRESO ──────────────────────────────────────────────────── */
.barra-wrap {
    background: #dde3f0;
    border-radius: 3px;
    height: 8px;
    width: 100%;
    display: block;
}
.barra-fill {
    background: #2e6db4;
    border-radius: 3px;
    height: 8px;
    display: block;
}
.barra-ambar { background: #e67e22; }
.barra-rojo  { background: #c0392b; }

/* ── BLOCKQUOTE ──────────────────────────────────────────────────────────── */
blockquote {
    background: #fffbf0;
    border-left: 4px solid #e6a817;
    margin: 5px 0 7px 0;
    padding: 5px 10px;
    font-size: 8.5pt;
    color: #5a4000;
    word-wrap: break-word;
}

/* ── LISTAS ──────────────────────────────────────────────────────────────── */
ul, ol { padding-left: 14px; margin: 3px 0 5px 0; }
li { margin-bottom: 2px; font-size: 9pt; word-wrap: break-word; }

/* ── PARRAFOS Y TEXTO ─────────────────────────────────────────────────────── */
p { margin: 4px 0; font-size: 9pt; word-wrap: break-word; }
strong { font-weight: bold; }
em { font-style: italic; }
code {
    font-family: Courier New, Courier, monospace;
    font-size: 7.5pt;
    background: #f0f2f8;
    padding: 1px 3px;
    word-wrap: break-word;
}
hr { border: none; border-top: 1px solid #d0d5e8; margin: 12px 0; }

/* ── FIRMA ───────────────────────────────────────────────────────────────── */
.firma-block    { margin-top: 28px; page-break-inside: avoid; }
.firma-line     { border-top: 2px solid #1e3a5f; margin-bottom: 10px; }
.firma-table    { width: 100%; border: none; margin: 0; table-layout: fixed; }
.firma-table td {
    border: none;
    vertical-align: top;
    padding: 0 10px 0 0;
    background: none !important;
    border-bottom: none !important;
    word-wrap: break-word;
}
.firma-img     { max-width: 170px; max-height: 60px; margin-bottom: 5px; display: block; }
.firma-nombre  { font-size: 10.5pt; font-weight: bold; color: #1e3a5f; margin-bottom: 2px; }
.firma-esp     { font-size: 9pt;   color: #444; margin-bottom: 1px; }
.firma-reg     { font-size: 8.5pt; color: #666; margin-bottom: 1px; }
.firma-fecha   { font-size: 8pt;   color: #888; margin-top: 3px; }
.firma-hash-box {
    background: #f4f7fb;
    border: 1px solid #b8ccec;
    border-radius: 4px;
    padding: 7px 9px;
}
.firma-hash-titulo { font-weight: bold; color: #1e3a5f; font-size: 8pt; margin-bottom: 4px; }
.firma-hash {
    font-family: Courier New, Courier, monospace;
    font-size: 6.5pt;
    word-wrap: break-word;
    color: #333;
    margin-bottom: 2px;
}
.firma-aviso { font-size: 6.5pt; color: #888; font-style: italic; margin-top: 3px; }

/* ── PAGINACION ──────────────────────────────────────────────────────────── */
@page {
    size: A4;
    margin: 12mm 10mm 12mm 10mm;
}
.page-break { page-break-before: always; }
.no-break   { page-break-inside: avoid; }
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  FIRMA: Markdown (en documento) + HTML (en PDF)
# ═══════════════════════════════════════════════════════════════════════════════

def _bloque_firma_markdown(medico: dict | None, contenido_md: str) -> str:
    if not medico or not medico.get('nombre'):
        return ""
    hash_sha256 = hashlib.sha256(contenido_md.encode('utf-8')).hexdigest()
    fecha_firma = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    lineas = ["\n\n---", "## MEDICO FIRMANTE",
              f"**Nombre:** {medico.get('nombre', '')}"]
    esp = medico.get('especialidad', '').strip()
    reg = medico.get('no_registro', '').strip()
    if esp: lineas.append(f"**Especialidad:** {esp}")
    if reg: lineas.append(f"**No. Registro Medico:** {reg}")
    lineas += [
        f"**Fecha de firma:** {fecha_firma}", "",
        "**Sello de integridad del documento (SHA-256)**",
        f"`{hash_sha256}`", "",
        "*Este codigo verifica que el contenido del informe no ha sido "
        "alterado desde su emision. Conserve este documento junto al sello.*",
    ]
    return "\n\n".join(lineas)


def _bloque_firma_html(medico: dict | None, firma_img_b64: str | None, contenido_md: str) -> str:
    if not medico or not medico.get('nombre'):
        return ""
    hash_sha256 = hashlib.sha256(contenido_md.encode('utf-8')).hexdigest()
    fecha_firma = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    img_html    = (f'<img src="data:image/png;base64,{firma_img_b64}" class="firma-img" />'
                   if firma_img_b64 else "")
    nombre   = medico.get('nombre', '')
    esp_html = f'<div class="firma-esp">{medico.get("especialidad","")}</div>' if medico.get('especialidad') else ''
    reg_html = f'<div class="firma-reg">No. Registro: {medico.get("no_registro","")}</div>' if medico.get('no_registro') else ''
    # Dividir hash en 4 líneas de 16 chars para mejor legibilidad
    h = hash_sha256
    hash_lines = ''.join(
        f'<div class="firma-hash">{h[i:i+32]}</div>' for i in range(0, 64, 32)
    )
    return f"""
<div class="firma-block">
  <div class="firma-line"></div>
  <table class="firma-table"><tr>
    <td class="firma-left">
      {img_html}
      <div class="firma-nombre">{nombre}</div>
      {esp_html}{reg_html}
      <div class="firma-fecha">Firmado: {fecha_firma}</div>
    </td>
    <td class="firma-right">
      <div class="firma-hash-box">
        <div class="firma-hash-titulo">Sello de Integridad (SHA-256)</div>
        {hash_lines}
        <div class="firma-aviso">Este codigo verifica que el contenido del informe
        no ha sido alterado desde su emision. Conservar junto al documento.</div>
      </div>
    </td>
  </tr></table>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF ENGINE — v3.0
# ═══════════════════════════════════════════════════════════════════════════════

def _md_a_html_body(md_text: str) -> str:
    """
    Convierte Markdown a HTML con soporte mejorado de tablas.
    Las tablas generadas llevan clases alternadas para mejorar la legibilidad
    y soportan texto largo sin cortes.
    """
    try:
        import markdown as md_lib
        # md_in_html permite HTML inline dentro de Markdown (barras de progreso, etc.)
        extensiones = ['tables', 'nl2br', 'fenced_code', 'md_in_html']
        try:
            html = md_lib.markdown(md_text, extensions=extensiones)
        except Exception:
            html = md_lib.markdown(md_text, extensions=['tables', 'nl2br', 'fenced_code'])
    except ImportError:
        # Fallback manual si markdown no está instalado
        html = _fallback_md_a_html(md_text)

    # Post-procesar tablas: añadir clases alt a filas pares
    html = _postprocesar_tablas(html)
    return html


def _postprocesar_tablas(html: str) -> str:
    """
    Post-procesa tablas HTML para que xhtml2pdf NO corte el texto:
    1. Detecta el numero de columnas de cada tabla por sus <th>.
    2. Inyecta width="X%" como atributo HTML en cada <th> y <td>.
       (xhtml2pdf ignora CSS para anchos de columna; solo respeta atributos HTML)
    3. Tablas de 2 col (Campo/Valor): 38% / 62%
    4. Tablas de 3 col con barra:     38% / 12% / 50%  (o distribucion uniforme)
    5. Resto: distribucion uniforme.
    6. Añade class="even" a filas pares para striping.
    """
    import re as _re

    def _anchos_para(n_cols: int, encabezados: list) -> list:
        """Devuelve lista de porcentajes que suman 100."""
        enc = [h.lower().strip() for h in encabezados]
        if n_cols == 2:
            # Campo / Valor  o  Variable / Dato
            return [40, 60]
        if n_cols == 3:
            # Categoria / N / %   o similar
            if any(e in ('n', '%') for e in enc[1:]):
                return [56, 12, 32]
            return [40, 30, 30]
        if n_cols == 4:
            # Categoria / N / % / Visual(barra)
            if 'visual' in enc[-1] or 'barra' in enc[-1]:
                return [38, 10, 14, 38]
            return [34, 22, 22, 22]
        if n_cols == 5:
            return [30, 14, 14, 14, 28]
        if n_cols == 6:
            return [26, 12, 12, 12, 12, 26]
        if n_cols == 7:
            return [22, 10, 10, 12, 12, 12, 22]
        # Generica: primera col mas ancha
        primer = 35
        resto  = round((100 - primer) / max(n_cols - 1, 1))
        ajuste = 100 - primer - resto * (n_cols - 1)
        cols   = [primer] + [resto] * (n_cols - 1)
        cols[-1] += ajuste
        return cols

    # Procesar tabla por tabla con regex
    def _procesar_tabla(m):
        tabla_html = m.group(0)

        # Extraer encabezados
        ths_raw = _re.findall(r'<th[^>]*>(.*?)</th>', tabla_html, _re.S | _re.I)
        ths = [_re.sub(r'<[^>]+>', '', t).strip() for t in ths_raw]  # limpiar tags del texto
        n_cols = len(ths) if ths else 0
        if n_cols == 0:
            return tabla_html

        anchos = _anchos_para(n_cols, ths)

        # Inyectar width en <th>
        contador_th = [0]
        def _repl_th(m2):
            idx = contador_th[0] % n_cols
            w   = anchos[idx] if idx < len(anchos) else round(100 / n_cols)
            contador_th[0] += 1
            tag = m2.group(1)  # atributos existentes
            return f'<th {tag} width="{w}%" style="word-wrap:break-word;white-space:normal;">' 
        tabla_html = _re.sub(r'<th([^>]*)>', _repl_th, tabla_html, flags=_re.I)

        # Inyectar width en <td>
        contador_td = [0]
        def _repl_td(m2):
            idx = contador_td[0] % n_cols
            w   = anchos[idx] if idx < len(anchos) else round(100 / n_cols)
            contador_td[0] += 1
            tag = m2.group(1)
            return f'<td {tag} width="{w}%" style="word-wrap:break-word;white-space:normal;">' 
        tabla_html = _re.sub(r'<td([^>]*)>', _repl_td, tabla_html, flags=_re.I)

        # Añadir class="even" a filas pares (excluye thead)
        fila_num = [0]
        en_thead = [False]
        def _repl_tr(m2):
            tag = m2.group(0)
            if '<thead' in tag or en_thead[0]:
                return tag
            fila_num[0] += 1
            if fila_num[0] % 2 == 0:
                return '<tr class="even">'
            return '<tr>'
        # Marcar fin de thead
        tabla_html = tabla_html.replace('</thead>', '</thead><!-- /thead -->')
        def _repl_tr2(m2):
            if '<!-- /thead -->' in tabla_html[:m2.start()]:
                return _repl_tr(m2)
            return m2.group(0)
        tabla_html = _re.sub(r'<tr>', _repl_tr2, tabla_html, flags=_re.I)
        tabla_html = tabla_html.replace('</thead><!-- /thead -->', '</thead>')

        return tabla_html

    return _re.sub(r'<table[^>]*>.*?</table>', _procesar_tabla, html, flags=_re.S | _re.I)


def _fallback_md_a_html(md_text: str) -> str:
    """Conversión Markdown→HTML básica cuando la librería no está disponible."""
    html = md_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for n in range(6, 0, -1):
        html = re.sub(
            r'^#{' + str(n) + r'}\s+(.+)$',
            lambda m, lv=n: f'<h{lv}>{m.group(1)}</h{lv}>',
            html, flags=re.MULTILINE
        )
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    html = re.sub(r'^---+$', '<hr/>', html, flags=re.MULTILINE)
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Tablas Markdown básicas
    def _conv_tabla(bloque: str) -> str:
        lineas = [l.strip() for l in bloque.strip().split('\n')]
        if len(lineas) < 3:
            return bloque
        encabezados = [c.strip() for c in lineas[0].split('|') if c.strip()]
        filas_datos = lineas[2:]
        th_html = ''.join(f'<th>{h}</th>' for h in encabezados)
        rows_html = ''
        for i, fila in enumerate(filas_datos):
            celdas = [c.strip() for c in fila.split('|') if c.strip()]
            cls = ' class="even"' if (i + 1) % 2 == 0 else ''
            td_html = ''.join(f'<td>{c}</td>' for c in celdas)
            rows_html += f'<tr{cls}>{td_html}</tr>'
        return f'<table><thead><tr>{th_html}</tr></thead><tbody>{rows_html}</tbody></table>'

    # Detectar bloques de tabla Markdown
    bloques = re.split(r'\n{2,}', html)
    procesados = []
    for bloque in bloques:
        if '|' in bloque and re.search(r'\|[-: ]+\|', bloque):
            procesados.append(_conv_tabla(bloque))
        elif bloque.strip():
            procesados.append(f'<p>{bloque.replace(chr(10), "<br/>")}</p>')
    return '\n'.join(procesados)


# Marcador que delimita el bloque de firma Markdown
_MARCA_FIRMA_MD = '\n\n---\n\n## MEDICO FIRMANTE'


def _recortar_firma_md(contenido_md: str) -> str:
    """Elimina el bloque de firma Markdown antes de generar el PDF."""
    idx = contenido_md.find(_MARCA_FIRMA_MD)
    return contenido_md[:idx] if idx != -1 else contenido_md


def markdown_a_pdf(
    contenido_md: str,
    ruta_salida: str,
    medico: dict | None = None,
    firma_img_b64: str | None = None,
) -> tuple[bool, str]:
    """
    Convierte Markdown a PDF con xhtml2pdf.
    - Recorta bloque de firma Markdown (evita doble firma).
    - Añade firma HTML estilizada al final.
    - CSS v3.0: tablas sin cortes, word-break en todas las celdas.
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return False, "Instala xhtml2pdf:  pip install xhtml2pdf markdown"

    try:
        md_sin_firma = _recortar_firma_md(contenido_md)
        html_body    = _md_a_html_body(md_sin_firma)
        firma_html   = _bloque_firma_html(medico, firma_img_b64, md_sin_firma)

        html_doc = (
            '<!DOCTYPE html><html>'
            '<head><meta charset="UTF-8"/>'
            f'<style>{_CSS_PDF}</style>'
            '</head>'
            f'<body><div class="page">{html_body}{firma_html}</div></body>'
            '</html>'
        )

        with open(ruta_salida, 'wb') as fout:
            result = pisa.CreatePDF(html_doc, dest=fout, encoding='utf-8')

        if result.err:
            return False, f"xhtml2pdf reportó error(es): {result.err}"
        return True, ""

    except Exception as exc:
        return False, str(exc)


# ═══════════════════════════════════════════════════════════════════════════════
#  MIXIN DE FIRMA (compartido por ambas ventanas)
# ═══════════════════════════════════════════════════════════════════════════════

class _FirmaMixin:
    """
    Provee campos de médico firmante + imagen de firma + exportación PDF.
    Se usa por herencia en VentanaInforme y VentanaInformeAdmin.
    """

    def _init_firma(self):
        self._firma_img_b64:    str | None  = None
        self._input_med_nombre: ui.input | None = None
        self._input_med_esp:    ui.input | None = None
        self._input_med_reg:    ui.input | None = None
        self._preview_firma:    ui.image | None = None
        self._label_sin_firma:  ui.label | None = None

    def _render_datos_medico(self, prefijo: str = ""):
        with ui.expansion(
            'Medico Firmante y Firma Digital', value=False,
        ).classes('w-full bg-white border border-indigo-200 rounded-lg'):
            with ui.column().classes('p-4 gap-3 w-full'):
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    self._input_med_nombre = ui.input(
                        label='Nombre completo del medico',
                        placeholder='Dr. / Dra. ...',
                    ).classes('flex-grow min-w-48')
                    self._input_med_esp = ui.input(
                        label='Especialidad',
                        placeholder='Endocrinologia, Medicina Interna...',
                    ).classes('flex-grow min-w-40')
                    self._input_med_reg = ui.input(
                        label='No. Registro Medico',
                        placeholder='Ej: 12345',
                    ).classes('w-40')
                ui.separator()
                with ui.row().classes('w-full items-start gap-6 flex-wrap'):
                    with ui.column().classes('gap-1'):
                        ui.label('Imagen de firma manuscrita').classes(
                            'text-sm font-semibold text-gray-700')
                        ui.label('Sube una imagen PNG o JPG de tu firma.').classes(
                            'text-xs text-gray-500')
                        ui.upload(
                            label='Seleccionar imagen', auto_upload=True, max_files=1,
                            on_upload=self._on_firma_upload,
                        ).props('accept=".png,.jpg,.jpeg" flat').classes(
                            'mt-1 border border-dashed border-indigo-300 rounded')
                    with ui.column().classes('gap-1'):
                        ui.label('Vista previa').classes('text-xs text-gray-500')
                        with ui.card().classes(
                            'w-52 h-20 flex items-center justify-center '
                            'bg-gray-50 border border-gray-200 rounded'):
                            self._preview_firma = ui.image('').classes(
                                'max-w-full max-h-full object-contain')
                            self._preview_firma.set_visibility(False)
                            self._label_sin_firma = ui.label(
                                'Sin firma cargada').classes('text-xs text-gray-400 italic')
                ui.separator()
                ui.label(
                    'Al generar el informe se añaden los datos del medico y el sello '
                    'SHA-256 al final del documento. El PDF incluye la imagen de firma.'
                ).classes('text-xs text-indigo-700')

    async def _on_firma_upload(self, e):
        try:
            if hasattr(e, 'file') and e.file is not None:
                contenido    = await e.file.read()
                content_type = getattr(e.file, 'content_type', 'image/png')
            elif hasattr(e, 'content') and e.content is not None:
                raw = e.content
                contenido    = raw.read() if hasattr(raw, 'read') else bytes(raw)
                content_type = getattr(e, 'type', 'image/png')
            else:
                raise AttributeError(f"Atributos: {[a for a in dir(e) if not a.startswith('_')]}")
            self._firma_img_b64 = base64.b64encode(contenido).decode('utf-8')
            data_url = f"data:{content_type};base64,{self._firma_img_b64}"
            if self._preview_firma:
                self._preview_firma.set_source(data_url)
                self._preview_firma.set_visibility(True)
            if self._label_sin_firma:
                self._label_sin_firma.set_visibility(False)
            ui.notify('Firma cargada correctamente.', type='positive')
        except Exception as exc:
            ui.notify(f'Error al cargar la firma: {exc}', type='negative')

    def _construir_medico_dict(self) -> dict | None:
        nombre = self._input_med_nombre.value.strip() if self._input_med_nombre else ''
        if not nombre:
            return None
        return {
            'nombre':       nombre,
            'especialidad': self._input_med_esp.value.strip() if self._input_med_esp else '',
            'no_registro':  self._input_med_reg.value.strip() if self._input_med_reg else '',
        }

    def _render_editor_comun(self):
        """Área de edición + barra de herramientas + botón PDF."""
        with ui.card().classes('w-full shadow-lg'):
            with ui.row().classes(
                'w-full p-3 bg-gray-100 border-b items-center gap-2 flex-wrap'
            ):
                ui.label('Informe').classes('font-semibold text-gray-700 flex-grow')
                ui.button('Vista previa', on_click=self._toggle_preview)\
                    .props('flat size=sm color=primary')\
                    .tooltip('Alternar entre editor y vista renderizada')
                ui.button('Copiar', on_click=self._copiar_markdown)\
                    .props('flat size=sm').tooltip('Copiar Markdown al portapapeles')
                ui.button('Limpiar', on_click=self._limpiar_editor)\
                    .props('flat size=sm color=grey').tooltip('Vaciar el editor')
                self._btn_pdf = ui.button('Exportar PDF', on_click=self._exportar_pdf)\
                    .props('elevated color=red-8 size=sm')\
                    .tooltip('Descargar PDF con firma y sello de integridad')
            with ui.column().classes('w-full'):
                self._editor = ui.textarea(
                    placeholder='El informe aparecera aqui. Puedes editarlo antes de exportar a PDF.',
                    on_change=lambda e: setattr(self, '_markdown_actual', e.value),
                ).classes('w-full font-mono text-sm').props('outlined rows=30 autogrow')
                self._preview_container = ui.column().classes('w-full p-4')
                self._preview_container.set_visibility(False)

    def _toggle_preview(self):
        self._modo_preview = not self._modo_preview
        if self._editor:
            self._editor.set_visibility(not self._modo_preview)
        if self._preview_container:
            self._preview_container.set_visibility(self._modo_preview)
            if self._modo_preview:
                self._preview_container.clear()
                with self._preview_container:
                    ui.markdown(self._markdown_actual).classes('w-full leading-relaxed')

    def _copiar_markdown(self):
        if not self._markdown_actual.strip():
            ui.notify('No hay contenido para copiar.', type='warning'); return
        ui.run_javascript(f'navigator.clipboard.writeText({repr(self._markdown_actual)})')
        ui.notify('Markdown copiado al portapapeles', type='positive')

    def _limpiar_editor(self):
        if self._editor: self._editor.set_value('')
        self._markdown_actual = ''
        if self._preview_container:
            self._preview_container.clear()
            self._preview_container.set_visibility(False)
        self._modo_preview = False
        if self._editor: self._editor.set_visibility(True)

    async def _exportar_pdf(self):
        if not self._markdown_actual.strip():
            ui.notify('No hay contenido para exportar.', type='warning'); return
        client    = ui.context.client
        medico    = self._construir_medico_dict()
        firma_b64 = self._firma_img_b64
        contenido = self._markdown_actual
        ui.notify('Generando PDF...', type='info', timeout=3000)
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        cola: Queue = Queue()
        def _worker_pdf():
            try:
                tmp = tempfile.NamedTemporaryFile(
                    suffix='.pdf', prefix='informe_', delete=False, dir=tempfile.gettempdir())
                tmp.close()
                exito, error = markdown_a_pdf(contenido, tmp.name, medico=medico, firma_img_b64=firma_b64)
                loop.call_soon_threadsafe(cola.put_nowait, (exito, tmp.name, error))
            except Exception as exc:
                loop.call_soon_threadsafe(cola.put_nowait, (False, '', str(exc)))
        ThreadPoolExecutor(max_workers=1).submit(_worker_pdf)
        exito, ruta, error = await cola.get()
        with client:
            if exito:
                ui.download(ruta, filename=f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                ui.notify('PDF generado y descargado correctamente.', type='positive')
            else:
                ui.notify(f'No se pudo generar el PDF: {error}  Markdown copiado al portapapeles.',
                          type='warning', timeout=10000)
                ui.run_javascript(f'navigator.clipboard.writeText({repr(contenido)})')

    def _render_panel_espera_base(self) -> tuple:
        with ui.card().classes('w-full bg-blue-900 text-white rounded-lg px-5 py-4') as panel:
            panel.set_visibility(False)
            with ui.row().classes('items-center gap-4 w-full'):
                ui.spinner('dots', size='lg', color='white')
                with ui.column().classes('gap-1 flex-grow'):
                    label_estado = ui.label('').classes('text-sm font-semibold text-white')
                    with ui.row().classes('items-center gap-2 text-blue-300'):
                        ui.label('Tiempo:').classes('text-xs')
                        label_tiempo = ui.label('0s').classes('text-xs font-mono text-blue-200')
                    ui.label('Procesando... el informe aparecera en instantes.').classes(
                        'text-xs text-blue-300 italic')
        return panel, label_estado, label_tiempo


# ═══════════════════════════════════════════════════════════════════════════════
#  VENTANA RESUMEN HC (paciente individual)
# ═══════════════════════════════════════════════════════════════════════════════

class VentanaInforme(_FirmaMixin):
    def __init__(self, no_hc_inicial: str | None = None):
        self._no_hc_inicial     = no_hc_inicial
        self._secciones_sel     : list[str] = [k for k in SECCIONES_DISPONIBLES if k in SECCIONES_DEFAULT]
        self._markdown_actual   : str       = ""
        self._generando         : bool      = False
        self._t_inicio          : float     = 0.0
        self._modo_preview      : bool      = False
        self._fases = [
            "Consultando base de datos...",
            "Analizando tendencias clinicas...",
            "Procesando secciones...",
            "Estructurando el informe...",
        ]
        self._init_firma()
        self._input_busqueda    : ui.input    | None = None
        self._editor            : ui.textarea | None = None
        self._preview_container : ui.column   | None = None
        self._panel_espera      : ui.card     | None = None
        self._label_estado      : ui.label    | None = None
        self._label_tiempo      : ui.label    | None = None
        self._btn_pdf           : ui.button   | None = None

    def mostrar(self):
        with ui.column().classes('w-full max-w-6xl mx-auto p-4 gap-3'):
            self._render_buscador()
            self._render_datos_medico()
            self._render_selector_secciones()
            self._panel_espera, self._label_estado, self._label_tiempo = \
                self._render_panel_espera_base()
            self._render_editor_comun()
        ui.timer(1.0, self._tick_espera)
        if self._no_hc_inicial:
            ui.timer(0.1, lambda: self._disparar_generacion(self._no_hc_inicial), once=True)

    def _render_buscador(self):
        with ui.card().classes('w-full bg-blue-50 border border-blue-200 rounded-lg p-4'):
            with ui.row().classes('w-full items-end gap-4'):
                self._input_busqueda = ui.input(
                    label='No. Historia Clinica o Carnet de Identidad',
                    placeholder='Ej: 880214 o 85051212345',
                    value=self._no_hc_inicial or '',
                ).classes('flex-grow text-base')
                ui.button('Generar Informe',
                          on_click=lambda: self._disparar_generacion(
                              self._input_busqueda.value.strip())
                          ).props('elevated color=primary size=md').classes('h-12')

    def _render_selector_secciones(self):
        with ui.expansion('Secciones a incluir', value=True)\
                .classes('w-full bg-white border border-gray-200 rounded-lg'):
            with ui.column().classes('p-3 gap-1'):
                with ui.element('div').classes('row q-col-gutter-lg w-full'):
                    for clave, etiqueta in SECCIONES_DISPONIBLES.items():
                        checked = clave in self._secciones_sel
                        ui.checkbox(_sin_emoji(etiqueta), value=checked,
                                    on_change=lambda e, k=clave: self._toggle(k, e.value))\
                            .classes('text-sm')

    def _toggle(self, clave: str, valor: bool):
        if valor:
            if clave not in self._secciones_sel:
                self._secciones_sel.append(clave)
        else:
            self._secciones_sel = [k for k in self._secciones_sel if k != clave]

    def _set_secciones(self, todas: bool):
        self._secciones_sel = list(SECCIONES_DISPONIBLES.keys()) if todas else []
        ui.notify('Todas las secciones seleccionadas' if todas else 'Secciones desmarcadas',
                  type='info')

    def _tick_espera(self):
        if not self._generando: return
        elapsed = int(time.monotonic() - self._t_inicio)
        if self._label_tiempo: self._label_tiempo.set_text(f'{elapsed}s')
        idx = (elapsed // 2) % len(self._fases)
        if self._label_estado: self._label_estado.set_text(self._fases[idx])

    def _disparar_generacion(self, termino: str):
        termino = termino.strip()
        if not termino:
            ui.notify('Ingresa el No. de HC o CI.', type='warning'); return
        if not self._secciones_sel:
            ui.notify('Selecciona al menos una seccion.', type='warning'); return
        if self._generando:
            ui.notify('Ya hay un informe generandose.', type='warning'); return
        asyncio.ensure_future(self._generar_async(termino, ui.context.client))

    async def _generar_async(self, termino: str, client):
        self._generando = True
        self._t_inicio  = time.monotonic()
        secciones       = list(self._secciones_sel)
        medico_dict     = self._construir_medico_dict()
        with client:
            self._panel_espera.set_visibility(True)
            self._label_estado.set_text('Consultando base de datos...')
            self._label_tiempo.set_text('0s')
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        cola: Queue = Queue()
        def _worker():
            try:
                resultado = generar_informe(termino, secciones, medico=medico_dict)
                loop.call_soon_threadsafe(cola.put_nowait, resultado)
            except Exception as exc:
                loop.call_soon_threadsafe(cola.put_nowait, (None, str(exc), {}))
        ThreadPoolExecutor(max_workers=1).submit(_worker)
        md, nombre_o_error, alertas = await cola.get()
        with client:
            self._panel_espera.set_visibility(False)
        self._generando = False
        if md is None:
            with client:
                ui.notify(f'Paciente "{termino}" no encontrado.' if not nombre_o_error
                          else f'Error: {nombre_o_error}', type='negative')
            return
        bloque = _bloque_firma_markdown(medico_dict, md)
        if bloque: md = md + bloque
        with client:
            self._markdown_actual = md
            self._editor.set_value(md)
            ui.notify(f'Informe de {nombre_o_error} generado correctamente.',
                      type='positive', timeout=3000)


# ═══════════════════════════════════════════════════════════════════════════════
#  VENTANA INFORME ADMINISTRATIVO INSTITUCIONAL
# ═══════════════════════════════════════════════════════════════════════════════

class VentanaInformeAdmin:

    def __init__(self):
        self._markdown_actual    : str              = ""
        self._generando          : bool             = False
        self._t_inicio           : float            = 0.0
        self._modo_preview       : bool             = False
        self._firma_img_b64      : str | None       = None

        self._fases = [
            "Consultando pacientes...",
            "Extrayendo métricas individuales...",
            "Calculando estadísticas agregadas...",
            "Redactando informe...",
        ]

        # Filtros
        self._fecha_inicio   : date | None = None
        self._fecha_fin      : date | None = None
        self._areas_sel      : list[str]   = []
        self._municipios_sel : list[str]   = []
        self._tipo_dm        : str | None  = None
        self._estado_sel     : str | None  = None

        # Opciones cargadas de BD
        self._opciones: dict | None = None

        # Widgets UI
        self._select_areas      : ui.select   | None = None
        self._select_municipios : ui.select   | None = None
        self._select_dm         : ui.select   | None = None
        self._select_estado     : ui.select   | None = None
        self._input_med_nombre  : ui.input    | None = None
        self._input_med_esp     : ui.input    | None = None
        self._input_med_reg     : ui.input    | None = None
        self._preview_firma     : ui.image    | None = None
        self._label_sin_firma   : ui.label    | None = None
        self._editor            : ui.textarea | None = None
        self._preview_container : ui.column   | None = None
        self._panel_espera      : ui.card     | None = None
        self._label_estado      : ui.label    | None = None
        self._label_tiempo      : ui.label    | None = None
        self._btn_pdf           : ui.button   | None = None

    def mostrar(self):
        with ui.column().classes('w-full max-w-6xl mx-auto p-4 gap-3'):
            self._render_filtros()
            self._render_datos_medico()
            self._render_panel_espera()
            self._render_editor_y_herramientas()
        ui.timer(1.0, self._tick_espera)
        ui.timer(0.3, self._cargar_opciones, once=True)

    @staticmethod
    def _args_a_fecha(args) -> date | None:
        raw = args[0] if isinstance(args, list) else args
        if not raw:
            return None
        try:
            return datetime.strptime(str(raw), '%Y/%m/%d').date()
        except ValueError:
            try:
                return date.fromisoformat(str(raw))
            except ValueError:
                return None

    def _date_input(self, label, attr):
        with ui.input(label).bind_value(self, attr).classes('w-40') as inp:
            with inp.add_slot('append'):
                ui.icon('calendar_month').on('click', lambda: menu.open())
            with ui.menu() as menu:
                ui.date().bind_value(inp)
        return inp

    def _render_filtros(self):
        with ui.row().classes(
            'items-center gap-4 p-4 bg-slate-50 rounded-xl shadow-sm w-full flex-wrap'
        ):
            ui.label('Período del Informe Administrativo:').classes('font-bold text-blue-900')
            self._date_input('Fecha inicio', '_fecha_inicio')
            self._date_input('Fecha fin', '_fecha_fin')

            self._select_municipios = ui.select(
                options=[],
                multiple=True,
                label='Municipio',
                on_change=self._on_municipio_change,
            ).props('outlined dense use-chips').classes('min-w-44')

            self._select_areas = ui.select(
                options=[],
                multiple=True,
                label='Área de salud',
                on_change=lambda e: setattr(self, '_areas_sel', e.value or []),
            ).props('outlined dense use-chips').classes('min-w-44')

            self._select_dm = ui.select(
                options=['Todos'], value='Todos', label='Tipo DM',
                on_change=lambda e: setattr(
                    self, '_tipo_dm', None if e.value == 'Todos' else e.value),
            ).props('outlined dense').classes('w-32')

            self._select_estado = ui.select(
                options=['Todos'], value='Todos', label='Estado',
                on_change=lambda e: setattr(
                    self, '_estado_sel', None if e.value == 'Todos' else e.value),
            ).props('outlined dense').classes('w-36')

            ui.button(
                'Filtrar', on_click=self._disparar_generacion,
            ).classes('bg-blue-600 text-white shadow-md h-10 self-end')

    def _on_municipio_change(self, e):
        self._municipios_sel = e.value or []
        self._recargar_areas_desde_bd()

    def _recargar_areas_desde_bd(self):
        db = DbSession()
        try:
            provincia_nombre = getattr(self, '_provincia', None)
            if self._municipios_sel:
                areas: list[str] = []
                for nombre_mun in self._municipios_sel:
                    q = db.query(Municipio)
                    if provincia_nombre:
                        q = q.join(Provincia).filter(
                            Municipio.nombre == nombre_mun,
                            Provincia.nombre == provincia_nombre,
                        )
                    else:
                        q = q.filter(Municipio.nombre == nombre_mun)
                    mun_obj = q.first()
                    if mun_obj:
                        areas.extend(a.nombre for a in mun_obj.areas_salud if a.nombre)
                opciones = sorted(set(areas))
            else:
                q_area = db.query(AreaSalud).order_by(AreaSalud.nombre)
                if provincia_nombre:
                    q_area = (
                        q_area
                        .join(Municipio, AreaSalud.municipio_id == Municipio.id)
                        .join(Provincia, Municipio.provincia_id == Provincia.id)
                        .filter(Provincia.nombre == provincia_nombre)
                    )
                opciones = [a.nombre for a in q_area.all() if a.nombre]

            self._areas_sel = [a for a in self._areas_sel if a in opciones]
            if self._select_areas:
                self._select_areas.options = opciones
                self._select_areas.value   = self._areas_sel or None
                self._select_areas.update()
        except Exception as exc:
            print(f"[_recargar_areas_desde_bd] {exc}")
        finally:
            db.close()

    def _cargar_opciones(self):
        provincia_nombre = getattr(self, '_provincia', None)
        db = DbSession()
        try:
            if provincia_nombre:
                prov_obj   = db.query(Provincia).filter_by(nombre=provincia_nombre).first()
                municipios = sorted(m.nombre for m in prov_obj.municipios if m.nombre) \
                    if prov_obj else []
            else:
                municipios = sorted(
                    r.nombre for r in db.query(Municipio).order_by(Municipio.nombre).all()
                    if r.nombre
                )

            q_area = db.query(AreaSalud).order_by(AreaSalud.nombre)
            if provincia_nombre:
                q_area = (
                    q_area
                    .join(Municipio, AreaSalud.municipio_id == Municipio.id)
                    .join(Provincia, Municipio.provincia_id == Provincia.id)
                    .filter(Provincia.nombre == provincia_nombre)
                )
            areas = [a.nombre for a in q_area.all() if a.nombre]

            tipos_dm = sorted(set(
                r[0] for r in db.query(Indicaciones.tipo_diabetes).distinct().all() if r[0]
            ))
            estados = sorted(set(
                r[0] for r in db.query(Paciente.estado_actual).distinct().all() if r[0]
            ))

            self._opciones = {
                'municipios': municipios,
                'areas':      areas,
                'tipos_dm':   tipos_dm,
                'estados':    estados,
            }
        except Exception as exc:
            print(f"[VentanaInformeAdmin._cargar_opciones] {exc}")
            self._opciones = {'municipios': [], 'areas': [], 'tipos_dm': [], 'estados': []}
        finally:
            db.close()
            self._actualizar_opciones_ui()

    def _actualizar_opciones_ui(self):
        if not self._opciones:
            return
        try:
            self._select_municipios.options = self._opciones.get('municipios', [])
            self._select_municipios.update()
            self._select_areas.options = self._opciones.get('areas', [])
            self._select_areas.update()
            self._select_dm.options     = ['Todos'] + self._opciones.get('tipos_dm', [])
            self._select_estado.options = ['Todos'] + self._opciones.get('estados', [])
            self._select_dm.update()
            self._select_estado.update()
        except Exception as exc:
            print(f"[_actualizar_opciones_ui] {exc}")

    def _render_datos_medico(self):
        with ui.expansion(
            'Médico Firmante y Firma Digital', value=False,
        ).classes('w-full bg-white border border-indigo-200 rounded-lg'):
            with ui.column().classes('p-4 gap-3 w-full'):
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    self._input_med_nombre = ui.input(
                        label='Nombre completo del médico',
                        placeholder='Dr. / Dra. ...',
                    ).classes('flex-grow min-w-48')
                    self._input_med_esp = ui.input(
                        label='Especialidad',
                        placeholder='Endocrinología, Medicina Interna...',
                    ).classes('flex-grow min-w-40')
                    self._input_med_reg = ui.input(
                        label='No. Registro Médico',
                        placeholder='Ej: 12345',
                    ).classes('w-40')
                ui.separator()
                with ui.row().classes('w-full items-start gap-6 flex-wrap'):
                    with ui.column().classes('gap-1'):
                        ui.label('Imagen de firma manuscrita').classes(
                            'text-sm font-semibold text-gray-700')
                        ui.label('Sube una imagen PNG o JPG de tu firma.').classes(
                            'text-xs text-gray-500')
                        ui.upload(
                            label='Seleccionar imagen', auto_upload=True, max_files=1,
                            on_upload=self._on_firma_upload,
                        ).props('accept=".png,.jpg,.jpeg" flat').classes(
                            'mt-1 border border-dashed border-indigo-300 rounded')
                    with ui.column().classes('gap-1'):
                        ui.label('Vista previa').classes('text-xs text-gray-500')
                        with ui.card().classes(
                            'w-52 h-20 flex items-center justify-center '
                            'bg-gray-50 border border-gray-200 rounded'):
                            self._preview_firma = ui.image('').classes(
                                'max-w-full max-h-full object-contain')
                            self._preview_firma.set_visibility(False)
                            self._label_sin_firma = ui.label(
                                'Sin firma cargada').classes('text-xs text-gray-400 italic')
                ui.separator()
                ui.label(
                    'El sello SHA-256 se calcula sobre el contenido completo del informe '
                    'y se incrusta en el PDF.'
                ).classes('text-xs text-indigo-700')

    async def _on_firma_upload(self, e):
        try:
            if hasattr(e, 'file') and e.file is not None:
                contenido    = await e.file.read()
                content_type = getattr(e.file, 'content_type', 'image/png')
            elif hasattr(e, 'content') and e.content is not None:
                raw          = e.content
                contenido    = raw.read() if hasattr(raw, 'read') else bytes(raw)
                content_type = getattr(e, 'type', 'image/png')
            else:
                raise AttributeError("Formato de evento no reconocido")
            self._firma_img_b64 = base64.b64encode(contenido).decode('utf-8')
            data_url = f"data:{content_type};base64,{self._firma_img_b64}"
            if self._preview_firma:
                self._preview_firma.set_source(data_url)
                self._preview_firma.set_visibility(True)
            if self._label_sin_firma:
                self._label_sin_firma.set_visibility(False)
            ui.notify('Firma cargada correctamente.', type='positive')
        except Exception as exc:
            ui.notify(f'Error al cargar la firma: {exc}', type='negative')

    def _construir_medico_dict(self) -> dict | None:
        nombre = self._input_med_nombre.value.strip() if self._input_med_nombre else ''
        if not nombre:
            return None
        return {
            'nombre':       nombre,
            'especialidad': self._input_med_esp.value.strip() if self._input_med_esp else '',
            'no_registro':  self._input_med_reg.value.strip() if self._input_med_reg else '',
        }

    def _render_panel_espera(self):
        with ui.card().classes(
            'w-full bg-indigo-900 text-white rounded-lg px-5 py-4'
        ) as panel:
            self._panel_espera = panel
            panel.set_visibility(False)
            with ui.row().classes('items-center gap-4 w-full'):
                ui.spinner('dots', size='lg', color='white')
                with ui.column().classes('gap-1 flex-grow'):
                    self._label_estado = ui.label('').classes('text-sm font-semibold text-white')
                    with ui.row().classes('items-center gap-2'):
                        ui.label('Tiempo transcurrido:').classes('text-xs text-indigo-300')
                        self._label_tiempo = ui.label('0s').classes('text-xs font-mono text-indigo-200')
                    ui.label('Procesando registros de todos los pacientes...').classes(
                        'text-xs text-indigo-300 italic')

    def _tick_espera(self):
        if not self._generando:
            return
        elapsed = int(time.monotonic() - self._t_inicio)
        if self._label_tiempo:
            self._label_tiempo.set_text(f'{elapsed}s')
        idx = (elapsed // 2) % len(self._fases)
        if self._label_estado:
            self._label_estado.set_text(self._fases[idx])

    def _render_editor_y_herramientas(self):
        with ui.card().classes('w-full shadow-lg'):
            with ui.row().classes(
                'w-full p-3 bg-gray-100 border-b items-center gap-2 flex-wrap'
            ):
                ui.label('Informe Administrativo').classes('font-semibold text-gray-700 flex-grow')
                ui.button('Vista previa', on_click=self._toggle_preview)\
                    .props('flat size=sm color=primary')\
                    .tooltip('Alternar entre editor y vista renderizada')
                ui.button('Copiar', on_click=self._copiar_markdown)\
                    .props('flat size=sm').tooltip('Copiar Markdown al portapapeles')
                ui.button('Limpiar', on_click=self._limpiar_editor)\
                    .props('flat size=sm color=grey').tooltip('Vaciar el editor')
                self._btn_pdf = ui.button(
                    'Exportar PDF', on_click=self._exportar_pdf
                ).props('elevated color=red-8 size=sm')\
                 .tooltip('Descargar PDF con firma y sello SHA-256')
            with ui.column().classes('w-full'):
                self._editor = ui.textarea(
                    placeholder='El informe administrativo aparecerá aquí una vez generado.',
                    on_change=lambda e: setattr(self, '_markdown_actual', e.value),
                ).classes('w-full font-mono text-sm').props('outlined rows=30 autogrow')
                self._preview_container = ui.column().classes('w-full p-4')
                self._preview_container.set_visibility(False)

    def _toggle_preview(self):
        self._modo_preview = not self._modo_preview
        if self._editor:
            self._editor.set_visibility(not self._modo_preview)
        if self._preview_container:
            self._preview_container.set_visibility(self._modo_preview)
            if self._modo_preview:
                self._preview_container.clear()
                with self._preview_container:
                    ui.markdown(self._markdown_actual).classes('w-full leading-relaxed')

    def _copiar_markdown(self):
        if not self._markdown_actual.strip():
            ui.notify('No hay contenido para copiar.', type='warning')
            return
        ui.run_javascript(f'navigator.clipboard.writeText({repr(self._markdown_actual)})')
        ui.notify('Markdown copiado al portapapeles', type='positive')

    def _limpiar_editor(self):
        if self._editor:
            self._editor.set_value('')
        self._markdown_actual = ''
        if self._preview_container:
            self._preview_container.clear()
            self._preview_container.set_visibility(False)
        self._modo_preview = False
        if self._editor:
            self._editor.set_visibility(True)

    def _disparar_generacion(self):
        if self._generando:
            ui.notify('Ya hay un informe generándose.', type='warning')
            return
        asyncio.ensure_future(self._generar_async(ui.context.client))

    async def _generar_async(self, client):
        self._generando = True
        self._t_inicio  = time.monotonic()
        medico_dict     = self._construir_medico_dict()
        fecha_inicio_doc = self._args_a_fecha(self._fecha_inicio)
        fecha_fin_doc    = self._args_a_fecha(self._fecha_fin)
        filtros = {
            'fecha_inicio': fecha_inicio_doc,
            'fecha_fin':    fecha_fin_doc,
            'areas':        list(self._areas_sel),
            'municipios':   list(self._municipios_sel),
            'tipo_dm':      self._tipo_dm,
            'estado':       self._estado_sel,
        }
        with client:
            self._panel_espera.set_visibility(True)
            self._label_estado.set_text('Consultando pacientes...')
            self._label_tiempo.set_text('0s')
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        cola: Queue = Queue()
        def _worker():
            try:
                md, total = generar_informe_admin(filtros, medico=medico_dict)
                loop.call_soon_threadsafe(cola.put_nowait, (md, total, None))
            except Exception as exc:
                import traceback; traceback.print_exc()
                loop.call_soon_threadsafe(cola.put_nowait, ('', 0, str(exc)))
        ThreadPoolExecutor(max_workers=1).submit(_worker)
        md, total, error = await cola.get()
        with client:
            self._panel_espera.set_visibility(False)
        self._generando = False
        if error:
            with client:
                ui.notify(f'Error al generar el informe: {error}', type='negative')
            return
        if total == 0:
            with client:
                ui.notify('No se encontraron pacientes con los filtros indicados.', type='warning')
            return
        with client:
            self._markdown_actual = md
            self._editor.set_value(md)
            ui.notify(f'Informe administrativo generado — {total} pacientes analizados.',
                      type='positive', timeout=4000)

    async def _exportar_pdf(self):
        if not self._markdown_actual.strip():
            ui.notify('No hay contenido para exportar.', type='warning')
            return
        client    = ui.context.client
        medico    = self._construir_medico_dict()
        firma_b64 = self._firma_img_b64
        contenido = self._markdown_actual
        ui.notify('Generando PDF con sello de integridad...', type='info', timeout=3000)
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        cola: Queue = Queue()
        def _worker_pdf():
            try:
                tmp = tempfile.NamedTemporaryFile(
                    suffix='.pdf', prefix='informe_admin_', delete=False, dir=tempfile.gettempdir())
                tmp.close()
                exito, error = markdown_a_pdf(contenido, tmp.name, medico=medico, firma_img_b64=firma_b64)
                loop.call_soon_threadsafe(cola.put_nowait, (exito, tmp.name, error))
            except Exception as exc:
                loop.call_soon_threadsafe(cola.put_nowait, (False, '', str(exc)))
        ThreadPoolExecutor(max_workers=1).submit(_worker_pdf)
        exito, ruta, error = await cola.get()
        with client:
            if exito:
                nombre_archivo = f"informe_admin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                ui.download(ruta, filename=nombre_archivo)
                ui.notify('PDF generado y descargado correctamente.', type='positive')
            else:
                ui.notify(f'No se pudo generar el PDF: {error}  Se copió el Markdown al portapapeles.',
                          type='warning', timeout=10000)
                ui.run_javascript(f'navigator.clipboard.writeText({repr(contenido)})')


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRACIÓN — tabs unificados
# ═══════════════════════════════════════════════════════════════════════════════

def crear_seccion_informes():
    with ui.tabs().classes('w-full') as tabs:
        tab_hc    = ui.tab('Resumen HC',               icon='person')
        tab_admin = ui.tab('Informes Administrativos', icon='bar_chart')
    with ui.tab_panels(tabs, value=tab_hc).classes('w-full'):
        with ui.tab_panel(tab_hc):
            VentanaInforme().mostrar()
        with ui.tab_panel(tab_admin):
            VentanaInformeAdmin().mostrar()


def abrir_dialogo_informe(no_hc: str):
    with ui.dialog().props('maximized') as dialogo:
        with ui.card().classes('w-full h-full overflow-y-auto p-0'):
            with ui.row().classes(
                'w-full justify-between items-center px-5 py-3 '
                'bg-blue-800 text-white sticky top-0 z-10'
            ):
                ui.label('Resumen de Historia Clinica').classes('text-lg font-bold')
                ui.button('Cerrar', on_click=dialogo.close).props('flat color=white')
            VentanaInforme(no_hc_inicial=no_hc).mostrar()
    dialogo.open()


def mostrar_pagina_informes(no_hc: str | None = None, provincia: str | None = None):
    ui.add_head_html('''
        <style>
            #c1 { padding-top: 0 !important; }
            .nicegui-content { overflow-x: hidden; }
        </style>
    ''')
    with ui.tabs().classes('w-full bg-blue-800 text-white px-4') as tabs:
        tab_hc    = ui.tab('Resumen de HC').classes('text-white')
        tab_admin = ui.tab('Informes Administrativos').classes('text-white')
    with ui.tab_panels(tabs, value=tab_hc).classes('w-full'):
        
        with ui.tab_panel(tab_hc):
            if tiene_permiso('hc_resumen'):
                VentanaInforme(no_hc_inicial=no_hc).mostrar()
            else:
                ui.label('No tienes permiso para acceder a esta sección.').classes(
                    'text-red-600 font-semibold p-4'
                )
      
        with ui.tab_panel(tab_admin):
            if tiene_permiso('resumen_admin'):
                ventana_admin = VentanaInformeAdmin()
                ventana_admin._provincia = provincia
                ventana_admin.mostrar()
            else:
                ui.label('No tienes permiso para acceder a esta sección.').classes(
                    'text-red-600 font-semibold p-4'
                )