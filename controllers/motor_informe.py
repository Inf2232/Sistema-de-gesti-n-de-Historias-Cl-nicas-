from __future__ import annotations
from datetime import datetime, date
from typing import Any
import math
from models import (
    Session, Paciente,
    AntecedentePatologicoPersonal, AntecedentePatologicoFamiliarNoDiabetesMellitus,
    AntecedentePatologicoFamiliarDiabetes,
    HabitosToxicos, HistoriaObstetrica,
    TratamientoActual, OtrosTratamientos,
    ExamenFisico, Mensuraciones,
    ResultadoEducacionDiabetologica,
    Complementarios, ExamenMiembrosInferiores,
    Oftalmologia, Nefrologia, Estomatologia,
    Cardiologia, Indicaciones,
)

SECCIONES_DISPONIBLES: dict[str, str] = {
    'datos_basicos':       'Datos Básicos del Paciente',
    'indicaciones':        'Indicaciones / Diagnóstico DM',
    'app':                 'Antecedentes Patológicos Personales',
    'apf':                 'Antecedentes Familiares (No DM)',
    'apf_diabetes':        'Antecedentes Familiares (Diabetes)',
    'habitos_toxicos':     'Hábitos Tóxicos',
    'historia_obstetrica': 'Historia Obstétrica',
    'tratamiento_actual':  'Tratamiento Actual',
    'otros_tratamientos':  'Otros Tratamientos',
    'examen_fisico':       'Examen Físico',
    'mensuraciones':       'Mensuraciones y Composición Corporal',
    'educacion':           'Educación Diabetológica',
    'complementarios':     'Complementarios (Laboratorio)',
    'podologia':           'Podología / Miembros Inferiores',
    'oftalmologia':        'Oftalmología',
    'nefrologia':          'Nefrología',
    'estomatologia':       'Estomatología',
    'cardiologia':         'Cardiología / Riesgo CV',
}

SECCIONES_DEFAULT = {
    'datos_basicos'
}

# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES DE FORMATO
# ═══════════════════════════════════════════════════════════════════════════════

def _f(valor: Any, defecto: str = "—") -> str:
    """Formatea cualquier valor para Markdown."""
    if valor is None:
        return defecto
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, (datetime, date)):
        return valor.strftime('%d/%m/%Y')
    if isinstance(valor, float):
        return str(round(valor, 2))
    return str(valor)


def _nd(texto: str = "Sin registros disponibles") -> str:
    return f"\n> {texto}\n"


def _badge_numerico(valor: float | None, normal: tuple, limite: tuple | None = None) -> str:
    if valor is None or not isinstance(valor, (int, float)):
        return "(desconocido)"
    lo_n, hi_n = normal
    if lo_n <= valor <= hi_n:
        return "(normal)"
    if limite:
        lo_l, hi_l = limite
        if lo_l <= valor <= hi_l:
            return "(límite)"
    return ""


def _badge_texto(valor: str | None, valores_normal: list, valores_limite: list | None = None) -> str:
    if not valor:
        return "(desconocido)"
    v = valor.lower().strip()
    if any(n.lower() in v for n in valores_normal):
        return "(normal)"
    if valores_limite and any(l.lower() in v for l in valores_limite):
        return "(límite)"
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES DE ANÁLISIS ESTADÍSTICO
# ═══════════════════════════════════════════════════════════════════════════════

def _todos(lista: list, campo: str = 'fecha_registro') -> list:
    """
    Retorna TODOS los registros ordenados por fecha (ascendente).
    """
    if not lista:
        return []
    con_fecha = sorted(
        [r for r in lista if getattr(r, campo, None)],
        key=lambda x: getattr(x, campo)
    )
    sin_fecha = [r for r in lista if not getattr(r, campo, None)]
    return con_fecha + sin_fecha


def _ultimo(lista: list, campo: str = 'fecha_registro') -> list:
    """Retorna solo el último registro (para datos de estado actual como hábitos)."""
    regs = _todos(lista, campo)
    return [regs[-1]] if regs else []


def _tendencia(valores: list[Any]) -> str:
    """
    Calcula tendencia usando regresión lineal (más preciso que primer vs último).
    Retorna texto descriptivo.
    """
    nums = [v for v in valores if isinstance(v, (int, float)) and v is not None]
    if len(nums) < 2:
        return "Sin comparativa"
    if len(nums) == 2:
        diff = nums[-1] - nums[0]
        pct = abs(diff) / (abs(nums[0]) + 1e-9) * 100
        if pct < 5:
            return "Estable"
        return (f"Alza (+{round(diff,2)})" if diff > 0 else f"Baja ({round(diff,2)})")

    # Regresión lineal simple
    n = len(nums)
    x_mean = (n - 1) / 2
    y_mean = sum(nums) / n
    num_reg = sum((i - x_mean) * (nums[i] - y_mean) for i in range(n))
    den_reg = sum((i - x_mean) ** 2 for i in range(n))

    if den_reg < 1e-10:
        return "Estable"

    slope = num_reg / den_reg
    rel_slope = abs(slope) / (abs(y_mean) + 1e-9) * 100
    diff = nums[-1] - nums[0]

    if rel_slope < 3:
        return "Estable"
    return (f"Alza (+{round(diff,2)})" if diff > 0 else f"Baja ({round(diff,2)})")


def _estadisticas(
    valores: list[Any],
    normal: tuple | None = None,
    limite: tuple | None = None
) -> dict:
    """
    Calcula estadísticas numéricas completas de una lista de valores.
    normal/limite: rangos para badging de mín, máx, promedio y último.
    """
    nums = [v for v in valores if isinstance(v, (int, float)) and v is not None]
    if not nums:
        return {'n': 0}

    avg = round(sum(nums) / len(nums), 2)
    resultado = {
        'n':       len(nums),
        'min':     round(min(nums), 2),
        'max':     round(max(nums), 2),
        'avg':     avg,
        'primero': round(nums[0], 2),
        'ultimo':  round(nums[-1], 2),
        'tendencia': _tendencia(nums),
    }

    if normal:
        resultado['badge_min'] = _badge_numerico(resultado['min'], normal, limite)
        resultado['badge_max'] = _badge_numerico(resultado['max'], normal, limite)
        resultado['badge_avg'] = _badge_numerico(avg, normal, limite)
        resultado['badge_ult'] = _badge_numerico(resultado['ultimo'], normal, limite)

    return resultado


def _bloque_estadisticas(titulo: str, variables: list[dict]) -> str:
    """
    Genera tabla Markdown con análisis estadístico completo de un conjunto de variables.

    Cada dict en `variables`:
        nombre  : str    — etiqueta de la variable
        valores : list   — lista de valores numéricos
        normal  : tuple  — rango (min, max) normal (opcional)
        limite  : tuple  — rango (min, max) límite (opcional)
    """
    filas = []
    for v in variables:
        est = _estadisticas(v['valores'], v.get('normal'), v.get('limite'))
        if est['n'] == 0:
            continue
        b_min = est.get('badge_min', '')
        b_max = est.get('badge_max', '')
        b_avg = est.get('badge_avg', '')
        b_ult = est.get('badge_ult', '')
        filas.append(
            f"| {v['nombre']} | {est['n']} | "
            f"{est['min']} {b_min} | {est['max']} {b_max} | "
            f"{est['avg']} {b_avg} | {est['ultimo']} {b_ult} | {est['tendencia']} |"
        )

    if not filas:
        return ""

    md  = f"\n### {titulo}\n\n"
    md += "| Variable | N | Mínimo | Máximo | Promedio | Último | Tendencia |\n"
    md += "|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas)
    md += "\n"
    return md


# ═══════════════════════════════════════════════════════════════════════════════
#  BÚSQUEDA DE PACIENTE
# ═══════════════════════════════════════════════════════════════════════════════

def buscar_paciente(termino: str) -> tuple[Paciente | None, Any]:
    """
    Busca paciente por no_hc o ci.
    El llamador es responsable de cerrar la sesión (db).
    """
    db = Session()
    termino = termino.strip()
    p = (
        db.query(Paciente)
        .filter((Paciente.no_hc == termino) | (Paciente.ci == termino))
        .first()
    )
    if not p:
        db.close()
        return None, None
    return p, db


# ═══════════════════════════════════════════════════════════════════════════════
#  EXTRACTORES DE SECCIONES
# ═══════════════════════════════════════════════════════════════════════════════

def _sec_datos_basicos(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    nombre = f"{p.nombres or ''} {p.apellidos or ''}".strip()

    md = f"""## Datos Básicos del Paciente

| Campo | Valor |
|---|---|
| **Nombre completo** | {nombre} |
| **Carnet de Identidad** | {_f(p.ci)} |
| **No. Historia Clínica** | {_f(p.no_hc)} |
| **Edad** | {_f(p.edad_actual)} años |
| **Sexo** | {_f(p.sexo)} |
| **Color de piel** | {_f(p.color_piel)} |
| **Nivel Educacional** | {_f(p.escolaridad)} |
| **Ocupación** | {_f(p.ocupacion)} |
| **Estado civil** | {_f(p.estado_civil)} |
| **Municipio** | {_f(p.municipio)} |
| **Área de Salud** | {_f(p.area_salud)} |
| **Fecha apertura HC** | {_f(p.fecha_hc)} |
| **Tiempo evolución DM** | {p.tiempo_evolucion} |
| **Forma de Presentación del Diagnóstico** | {_f(p.forma_presentacion_diagnostico)} |
| **Glucemia al Diagnóstico** | {_f(p.glucemia_debut)} mmol/L |
| **Exceso peso al diagnóstico** | {_f(p.exceso_peso_diagnostico)} |
| **Tratamiento inicial** | {_f(p.tratamiento_inicial)} |
| **Año inicio tratamiento** | {_f(p.ano_inicio_tratamiento)} |
| **Dosis tratamiento inicial** | {_f(p.dosis_tratamiento)} |
| **Prediabetes** | {_f(p.prediabetes)} |
| **Remisión** | {_f(p.remision)} |
| **Estado actual** | {_f(p.estado_actual)} |
"""
    if p.causa_fallecimiento:
        md += f"| **Causa fallecimiento** | {p.causa_fallecimiento} |\n"

    # Esquema inicial detallado (nuevo formato JSON) ─────────────────────────
    if p.tratamiento_inicial_json and len(p.tratamiento_inicial_json) > 0:
        md += "\n### Esquema de Tratamiento Inicial (Detallado)\n\n"
        md += "| Fármaco / Terapia | Dosis | Año de inicio |\n|---|---|---|\n"
        for item in p.tratamiento_inicial_json:
            md += (
                f"| {item.get('tratamiento', '—')} "
                f"| {item.get('dosis', '—')} "
                f"| {item.get('anio_inicio', '—')} |\n"
            )

    alertas.update({
        'nombre':    nombre,
        'edad':      p.edad_actual,
        'sexo':      p.sexo,
        'evolucion': p.tiempo_evolucion,
    })
    return md, alertas


def _sec_indicaciones(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.indicaciones)
    if not regs:
        return f"## 🩺 Indicaciones / Diagnóstico DM\n{_nd()}", alertas

    tipos, trats = [], []
    filas = []
    for r in regs:
        filas.append(f"| {_f(r.fecha_registro)} | {_f(r.tipo_diabetes)} | {_f(r.tratamiento)} |")
        if r.tipo_diabetes:
            tipos.append(r.tipo_diabetes)
        if r.tratamiento:
            trats.append(r.tratamiento)

    alertas['tipo_dm']       = tipos[-1] if tipos else "No especificado"
    alertas['tratamiento_dm'] = trats[-1] if trats else "No especificado"

    md  = "## 🩺 Indicaciones / Diagnóstico DM\n\n"
    md += f"> 📊 {len(regs)} registros en la historia clínica\n\n"
    md += "| Fecha | Tipo DM | Indicaciones |\n|---|---|---|\n"
    md += "\n".join(filas)
    return md, alertas


def _sec_app(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    items = []
    for ant in p.antecedentes_personales:
        for pat in ant.patologias:
            t_a = pat.tiempo_anios or "?"
            t_m = pat.tiempo_meses or 0
            tiempo_str = f"{t_a}a" + (f" {t_m}m" if t_m else "")
            items.append(f"- {_f(pat.tipo_patologia)} — {tiempo_str} de evolución")

    alertas['app'] = [i.strip('- ').split(' —')[0] for i in items]

    if not items:
        return f"## Antecedentes Patológicos Personales\n{_nd('No se registran antecedentes personales.')}", alertas

    md  = "## Antecedentes Patológicos Personales\n\n"
    md += f"> Total: {len(items)} patología(s) registrada(s)\n\n"
    md += "\n".join(items)
    return md, alertas


def _sec_apf(p: Paciente) -> tuple[str, dict]:
    items = []
    for ant in p.antecedentes_familiares:
        for pat in ant.patologias:
            items.append(f"- {_f(pat.tipo_patologia)}")
    if not items:
        return f"## Antecedentes Familiares (No DM)\n{_nd()}", {}
    md  = "## Antecedentes Familiares (No DM)\n\n"
    md += "\n".join(items)
    return md, {}


def _sec_apf_diabetes(p: Paciente) -> tuple[str, dict]:
    items = []
    for ant in p.antecedentes_familiares_diabetes:
        for grado in ant.grados_parentezco:
            items.append(f"- Familiar con DM — Grado de parentesco: {_f(grado.grado)}")
    if not items:
        return f"## Antecedentes Familiares (Diabetes)\n{_nd('Sin antecedentes familiares de diabetes.')}", {}
    md  = "## Antecedentes Familiares (Diabetes)\n\n"
    md += "\n".join(items)
    return md, {}


def _sec_habitos(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    # Hábitos: mostramos todos los registros históricos, pero alertas del último
    regs = _todos(p.habitos_toxicos)
    if not regs:
        return f"## Hábitos Tóxicos\n{_nd()}", alertas

    filas = []
    for r in regs:
        f_badge = _badge_texto(r.fuma, ['no'], ['ex'])
        a_badge = _badge_texto(r.consumo_excesivo_alcohol, ['no'])
        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.fuma)} {f_badge} | "
            f"{_f(r.cant_cigarros)} | {_f(r.cant_tabacos)} | "
            f"{_f(r.tiempo_sin_fumar)} | {_f(r.consumo_excesivo_alcohol)} {a_badge} |"
        )

    ult = regs[-1]
    alertas['fuma']    = ult.fuma
    alertas['alcohol'] = ult.consumo_excesivo_alcohol

    md  = "## Hábitos Tóxicos\n\n"
    md += f"> {len(regs)} registro(s) en la historia\n\n"
    md += "| Fecha | Fuma | Cigarros/día | Tabacos/día | Tiempo sin fumar | Alcohol excesivo |\n"
    md += "|---|---|---|---|---|---|\n"
    md += "\n".join(filas)
    return md, alertas


def _sec_obstetrica(p: Paciente) -> tuple[str, dict]:
    if p.sexo and 'masculino' in str(p.sexo).lower():
        return "", {}
    regs = _todos(p.historia_obstetrica)
    if not regs:
        return f"## Historia Obstétrica\n{_nd()}", {}

    filas = []
    for r in regs:
        abortos = (r.abortos_espontaneos or 0) + (r.abortos_provocados or 0)
        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.gestaciones)}/{_f(r.partos)} | {abortos} | "
            f"{_f(r.macrofetos)} | {_f(r.diabetes_gestacional)} {_badge_texto(r.diabetes_gestacional,['no'])} | "
            
        )

    r = regs[-1]  # Detalle del último
    md = f"""## Historia Obstétrica

| Campo | Valor |
|---|---|
| **Edad menarca** | {_f(r.edad_menarca)} años |
| **Edad 1ª relación sexual** | {_f(r.edad_primera_relacion_sexual)} años |
| **Edad menopausia** | {_f(r.edad_menopausia)} años ({_f(r.tipo_menopausia)}) |
| **Anticoncepción actual** | {_f(r.anticoncepcion_actual)} |
| **Anticoncepción previa** | {_f(r.anticoncepcion_previa)} |

### Resumen Obstétrico ({len(regs)} consulta(s))

| Fecha | Gestas/Partos | Abortos | Macrofetos | DM Gestacional |
|---|---|---|---|---|
"""
    md += "\n".join(filas)
    return md, {}


def _sec_tratamiento_actual(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.tratamiento_actual)
    if not regs:
        return f"## Tratamiento Actual\n{_nd()}", alertas

    filas, trats = [], []
    for r in regs:
        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.tratamiento)} | {_f(r.sigue_via_clinica)} |"
        )
        if r.tratamiento:
            trats.append(r.tratamiento)

    alertas['tratamiento_actual'] = trats[-1] if trats else "No registrado"

    md  = "## Tratamiento Actual\n\n"
    md += f"> {len(regs)} registro(s) — Último tratamiento: **{alertas['tratamiento_actual']}**\n\n"
    md += "| Fecha | Esquema | Sigue vía clínica |\n|---|---|---|\n"
    md += "\n".join(filas)

    # ── Detalle del esquema farmacológico por registro (nuevo formato JSON) ──
    registros_con_esquema = [r for r in regs if r.esquema_json and len(r.esquema_json) > 0]
    if registros_con_esquema:
        md += "\n\n### Detalle del Esquema Farmacológico\n\n"
        for r in registros_con_esquema:
            md += f"**{_f(r.fecha_registro)}** — {_f(r.tratamiento)}  \n"
            md += "| Fármaco / Terapia | Dosis | Año de inicio |\n|---|---|---|\n"
            for item in r.esquema_json:
                md += (
                    f"| {item.get('tratamiento', '—')} "
                    f"| {item.get('dosis', '—')} "
                    f"| {item.get('anio_inicio', '—')} |\n"
                )
            md += "\n"

    return md, alertas


def _sec_otros_tratamientos(p: Paciente) -> tuple[str, dict]:
    regs = _todos(p.otros_tratamientos)
    if not regs:
        return f"## Otros Tratamientos\n{_nd()}", {}
    filas = [
        f"| {_f(r.fecha_registro)} | {_f(r.tratamiento)} | {_f(r.dosis)} |"
        for r in regs
    ]
    md  = "## Otros Tratamientos\n\n"
    md += f"> {len(regs)} registro(s)\n\n"
    md += "| Fecha | Tratamiento | Dosis |\n|---|---|---|\n"
    md += "\n".join(filas)
    return md, {}


def _sec_examen_fisico(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.examen_fisico)
    if not regs:
        return f"## Examen Físico\n{_nd()}", alertas

    sistolicas  = [r.sistolica_sentado for r in regs]
    diastolicas = [r.diastolica_sentado for r in regs]

    filas_ta = []
    for r in regs:
        ta_s = f"{_f(r.sistolica_sentado)}/{_f(r.diastolica_sentado)}"
        ta_p = f"{_f(r.sistolica_de_pie)}/{_f(r.diastolica_de_pie)}"
        ta_a = f"{_f(r.sistolica_acostado)}/{_f(r.diastolica_acostado)}"
        b_s  = _badge_numerico(r.sistolica_sentado, (0, 129), (0, 139))
        b_d  = _badge_numerico(r.diastolica_sentado, (0, 79), (0, 89))
        filas_ta.append(
            f"| {_f(r.fecha_registro)} | {ta_s} {b_s}{b_d} | {ta_p} | {ta_a} | "
            f"{_f(r.bocio)} | {_f(r.acantosis_nigricans)} |"
        )

    ult = regs[-1]
    alertas.update({
        'ta_sist':  ult.sistolica_sentado,
        'ta_diast': ult.diastolica_sentado,
        'bocio':    ult.bocio,
    })

    md  = "## Examen Físico\n\n"
    md += f"> {len(regs)} examen(es) registrado(s)\n\n"
    md += "### Presión Arterial y Examen General\n\n"
    md += "| Fecha | TA Sentado | TA De pie | TA Acostado | Bocio | Acantosis |\n|---|---|---|---|---|---|\n"
    md += "\n".join(filas_ta)

    # Bloque estadístico TA
    md += _bloque_estadisticas("Análisis Estadístico — Tensión Arterial", [
        {'nombre': 'TA Sistólica (mmHg)',  'valores': sistolicas,  'normal': (0, 129), 'limite': (0, 139)},
        {'nombre': 'TA Diastólica (mmHg)', 'valores': diastolicas, 'normal': (0, 79),  'limite': (0, 89)},
    ])
    md += "\n> 🎯 Normal: <130/80 mmHg | Grado 1: 130-139/80-89 | Grado 2: ≥140/90 mmHg\n"
    return md, alertas


def _sec_mensuraciones(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.mensuraciones)
    if not regs:
        return f"## Mensuraciones y Composición Corporal\n{_nd()}", alertas

    pesos, imcs, cinturas = [], [], []
    filas = []

    for r in regs:
        imc_v    = r.IMC
        imc_num  = isinstance(imc_v, (int, float))
        cls      = r.clasificar_imc[1] if imc_num else "—"
        b_imc    = _badge_numerico(imc_v if imc_num else None, (18.5, 24.9), (17.0, 29.9))
        icc      = r.ICC if not isinstance(r.ICC, str) else None
        b_icc    = "(desconocido)" if icc is None else (
            _badge_numerico(icc, (0, 0.85), (0, 0.95)) if p.sexo and 'femenino' in str(p.sexo).lower()
            else _badge_numerico(icc, (0, 0.90), (0, 1.0))
        )
        pi       = _f(r.PI) if not isinstance(r.PI, str) else "—"
        grasa    = r.grasa_marina
        g_str    = f"{_f(grasa)}%" if isinstance(grasa, (int, float)) else "—"
        g_cls    = r.clasificar_composicion_corporal[1] if not isinstance(grasa, str) else "—"

        pesos.append(r.peso)
        imcs.append(imc_v if imc_num else None)
        cinturas.append(r.cintura)

        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.talla)} | {_f(r.peso)} | "
            f"{_f(imc_v) if imc_num else '—'} {b_imc} ({cls}) | {pi} | "
            f"{_f(r.cintura)} | {_f(r.cadera)} | {_f(r.cuello)} | "
            f"{_f(icc)} {b_icc} | {g_str} ({g_cls}) | {_f(r.dieta)} |"
        )

    ult      = regs[-1]
    imc_ult  = ult.IMC if isinstance(ult.IMC, (int, float)) else None
    alertas.update({
        'peso':      ult.peso,
        'imc':       imc_ult,
        'imc_cls':   ult.clasificar_imc[1] if imc_ult else "No calculable",
        'cintura':   ult.cintura,
        'tend_imc':  _tendencia([v for v in imcs if v is not None]),
        'tend_peso': _tendencia([v for v in pesos if v is not None]),
    })

    md  = "## Mensuraciones y Composición Corporal\n\n"
    md += f"> {len(regs)} medición(es) registrada(s)\n\n"
    md += "| Fecha | Talla (cm) | Peso (kg) | IMC (Clasif.) | PI Ajust. | Cintura | Cadera | Cuello | ICC | Grasa Marina | Dieta |\n"
    md += "|---|---|---|---|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas)

    md += _bloque_estadisticas("Análisis Estadístico — Composición Corporal", [
        {'nombre': 'Peso (kg)',      'valores': [v for v in pesos if v],    'normal': (0, 999)},
        {'nombre': 'IMC',           'valores': [v for v in imcs if v],     'normal': (18.5, 24.9), 'limite': (17.0, 29.9)},
        {'nombre': 'Cintura (cm)',  'valores': [v for v in cinturas if v], 'normal': (0, 79) if p.sexo and 'femenin' in str(p.sexo).lower() else (0, 93)},
    ])
    md += "\n> IMC normal 18.5–24.9 | ICC ♂<0.90 ♀<0.85 | Cintura ♂<94 cm ♀<80 cm\n"
    return md, alertas


def _sec_educacion(p: Paciente) -> tuple[str, dict]:
    regs = _todos(p.resultado_educacion_diabetologica)
    if not regs:
        return f"## Educación Diabetológica\n{_nd()}", {}

    filas = []
    for r in regs:
        mantiene = "—"
        if r.estado:
            estados = sorted(r.estado, key=lambda x: x.fecha_registro or date.min)
            if estados:
                ue = estados[-1]
                mantiene = "Sí" if ue.mantiene_educacion else "No"
        filas.append(f"| {_f(r.fecha_registro)} | {_f(r.inicio)} | {_f(r.final)} | {mantiene} |")

    md  = "## Educación Diabetológica\n\n"
    md += f"> {len(regs)} ciclo(s) de educación registrado(s)\n\n"
    md += "| Fecha | Nivel Inicial | Nivel Final | Mantiene educación |\n|---|---|---|---|\n"
    md += "\n".join(filas)
    return md, {}


def _sec_complementarios(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.complementarios)
    if not regs:
        return f"## Complementarios (Laboratorio)\n{_nd()}", alertas

    glucemias, colesteroles, hb_vals = [], [], []
    tg_vals, hdlc_vals, fg_vals = [], [], []
    filas_met, filas_hem, filas_hep, filas_otros = [], [], [], []

    es_f = p.sexo and 'femenin' in str(p.sexo).lower()
    for r in regs:
        v_glucemia = _safe_float(r.glucemia)
        v_colesterol = _safe_float(r.colesterol)
        v_trigliceridos = _safe_float(r.trigliceridos)
        v_hdlc = _safe_float(r.HDLC)  # 🌟 ¡AQUÍ PARSEAMOS TU VARIABLE CULPABLE!
        v_hb = _safe_float(r.hb)
        # Metabólico
        b_gluc = _badge_numerico(v_glucemia, (3.9, 6.99), (3.0, 9.9))
        b_col  = _badge_numerico(v_colesterol, (0, 5.19), (0, 6.19))
        b_tg   = _badge_numerico(v_trigliceridos, (0, 1.69), (0, 2.25))
        b_hdl  = (_badge_numerico(v_hdlc, (1.3, 99), (1.0, 99)) if es_f
                  else _badge_numerico(v_hdlc, (1.0, 99), (0.9, 99)))
        filas_met.append(
            f"| {_f(r.fecha_registro)} | {v_glucemia} {b_gluc} | "
            f"{v_colesterol} {b_col} | {v_trigliceridos} {b_tg} | "
            f"{v_hdlc} {b_hdl} | {r.calcio} | {r.fosforo} |"
        )
        glucemias.append(v_glucemia)
        colesteroles.append(v_colesterol)
        tg_vals.append(v_trigliceridos)
        hdlc_vals.append(v_hdlc)

        # Hematológico
        rng_hb = (120, 160) if es_f else (130, 170)
        b_hb   = _badge_numerico(v_hb, rng_hb, (110, 180))
        filas_hem.append(
            f"| {_f(r.fecha_registro)} | {v_hb} {b_hb} | {_f(r.hto)} | "
            f"{_f(r.eritro)} | {_f(r.conteo_plaquetas)} | "
            f"{_f(r.coagulacion)} | {_f(r.sangramiento)} |"
        )
        hb_vals.append(v_hb)

        # Hepático
        filas_hep.append(
            f"| {_f(r.fecha_registro)} | {_f(r.tgp)} | {_f(r.TGO)} | "
            f"{_f(r.proteinas_totales)} | {_f(r.albuminuria)} | {_f(r.globulina)} |"
        )

        # Campos personalizados
        for cp in r.campos_personalizados:
            filas_otros.append(
                f"| {_f(r.fecha_registro)} | {cp.nombre} | {cp.valor} | {_f(cp.unidad)} |"
            )

    ult = regs[-1]
    ultimo_hdlc=_safe_float(ult.HDLC)  # Aseguramos que el último valor sea numérico para alertas
    alertas.update({
        'glucemia':        ult.glucemia,
        'colesterol':      ult.colesterol,
        'tg':              ult.trigliceridos,
        'hdlc':            ultimo_hdlc if isinstance(ultimo_hdlc, (int, float)) else "No calculable",
        'hb':              ult.hb,
        'tend_glucemia':   _tendencia([v for v in glucemias if v]),
        'tend_colesterol': _tendencia([v for v in colesteroles if v]),
    })

    md  = "## Complementarios (Laboratorio)\n\n"
    md += f"> {len(regs)} resultado(s) en la historia\n\n"

    md += "### Metabolismo y Lípidos (mmol/L)\n\n"
    md += "| Fecha | Glucemia | Colesterol | Triglicéridos | HDL-C | Calcio | Fósforo |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_met)
    # Bloque estadístico metabólico
    md += _bloque_estadisticas("Análisis Estadístico — Metabolismo", [
        {'nombre': 'Glucemia (mmol/L)',       'valores': [v for v in glucemias   if v], 'normal': (3.9, 6.99),  'limite': (3.0, 9.9)},
        {'nombre': 'Colesterol (mmol/L)',     'valores': [v for v in colesteroles if v], 'normal': (0, 5.19),   'limite': (0, 6.19)},
        {'nombre': 'Triglicéridos (mmol/L)', 'valores': [v for v in tg_vals     if v], 'normal': (0, 1.69),    'limite': (0, 2.25)},
        {'nombre': 'HDL-C (mmol/L)',         'valores': [v for v in hdlc_vals   if v],
         'normal': (1.3, 99) if es_f else (1.0, 99), 'limite': (1.0, 99) if es_f else (0.9, 99)},
    ])
    md += "\n> Glucemia DM <7.0 mmol/L | Colesterol <5.2 | TG <1.7 | HDL-C ♀>1.3 ♂>1.0\n\n"

    md += "### Hematología\n\n"
    md += "| Fecha | Hb (g/L) | Hto | Eritrocitos | Plaquetas | Coagulación (min) | Sangramiento (min) |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_hem)
    md += _bloque_estadisticas("Análisis Estadístico — Hematología", [
        {'nombre': 'Hemoglobina (g/L)', 'valores': [v for v in hb_vals if v],
         'normal': (120, 160) if es_f else (130, 170), 'limite': (110, 180)},
    ])

    md += "\n### Hepático y Proteínas\n\n"
    md += "| Fecha | TGP (U/L) | TGO (U/L) | Proteínas Totales | Albuminuria | Globulina |\n|---|---|---|---|---|---|\n"
    md += "\n".join(filas_hep)

    # Pruebas especiales del último registro
    ult_r = regs[-1]
    especiales = []
    if ult_r.ultrasonido_abdominal:
        especiales.append(f"- **US Abdominal:** {ult_r.ultrasonido_abdominal}")
    if ult_r.prueba_conduccion_nerviosa_miembro_superior:
        especiales.append(f"- **Conducción nerviosa MS:** {ult_r.prueba_conduccion_nerviosa_miembro_superior}")
    if ult_r.prueba_conduccion_nerviosa_miembro_inferior:
        especiales.append(f"- **Conducción nerviosa MI:** {ult_r.prueba_conduccion_nerviosa_miembro_inferior}")
    if especiales:
        md += "\n\n### Pruebas Especiales (último registro)\n\n" + "\n".join(especiales)

    if filas_otros:
        md += "\n\n### Campos Adicionales\n\n"
        md += "| Fecha | Examen | Valor | Unidad |\n|---|---|---|---|\n"
        md += "\n".join(filas_otros)

    return md, alertas


def _sec_podologia(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.examen_miembros_inferiores)
    if not regs:
        return f"## Podología / Miembros Inferiores\n{_nd()}", alertas

    itb_d_vals = [r.ITB_derecho for r in regs]
    itb_i_vals = [r.ITB_izquierdo for r in regs]

    def _lista_rel(relacion):
        items = [x.padecimiento for x in relacion if x.padecimiento]
        return ", ".join(items) if items else "—"

    filas_itb, filas_neuro, filas_pulsos, filas_lesiones = [], [], [], []

    for r in regs:
        itb_d = r.ITB_derecho
        itb_i = r.ITB_izquierdo
       
        b_itb_d = _badge_numerico(itb_d, (0.9, 1.2), (0.4, 1.4)) if itb_d else "(desconocido)"
        b_itb_i = _badge_numerico(itb_i, (0.9, 1.2), (0.4, 1.4)) if itb_i else "(desconocido)"

        filas_itb.append(
            f"| {_f(r.fecha_registro)} | "
            f"{round(itb_d,2) if itb_d else '—'} {b_itb_d} ({_f(r.itb_clasificacion_derecho)}) | "
            f"{round(itb_i,2) if itb_i else '—'} {b_itb_i} ({_f(r.itb_clasificacion_izquierdo)}) | "
            f"{_f(r.LOPS_derecho)} {_badge_texto(r.LOPS_derecho,['no'])} | "
            f"{_f(r.LOPS_izquierdo)} {_badge_texto(r.LOPS_izquierdo,['no'])} | "
            f"{_f(r.EAP_derecho)} {_badge_texto(r.EAP_derecho,['no'])} | "
            f"{_f(r.EAP_izquierdo)} {_badge_texto(r.EAP_izquierdo,['no'])} |"
        )
        filas_neuro.append(
            f"| {_f(r.fecha_registro)} | "
            f"{_f(r.tactil_derecho)}/{_f(r.tactil_izquierdo)} | "
            f"{_f(r.termica_derecho)}/{_f(r.termica_izquierdo)} | "
            f"{_f(r.dolorosa_derecho)}/{_f(r.dolorosa_izquierdo)} | "
            f"{_f(r.palestesia_derecho)}/{_f(r.palestesia_izquierdo)} | "
            f"{_f(r.patelar_derecho)}/{_f(r.patelar_izquierdo)} | "
            f"{_f(r.aquileano_derecho)}/{_f(r.aquileano_izquierdo)} |"
        )
        filas_pulsos.append(
            f"| {_f(r.fecha_registro)} | "
            f"{_f(r.pulso_femoral_derecho)}/{_f(r.pulso_femoral_izquierdo)} | "
            f"{_f(r.pulso_popliteo_derecho)}/{_f(r.pulso_popliteo_izquierdo)} | "
            f"{_f(r.pulso_tibial_posterior_derecho)}/{_f(r.pulso_tibial_posterior_izquierdo)} | "
            f"{_f(r.pulso_pedeo_derecho)}/{_f(r.pulso_pedeo_izquierdo)} |"
        )
        filas_lesiones.append(
            f"| {_f(r.fecha_registro)} | {_lista_rel(r.defromidades_podalicas_derecho)} | "
            f"{_lista_rel(r.defromidades_podalicas_izquierdo)} | "
            f"{_lista_rel(r.lesiones_dermatologicas_derecho)} | "
            f"{_lista_rel(r.lesiones_dermatologicas_izquierdo)} | "
            f"{_f(r.impresion_diagnostica)} |"
        )

    ult = regs[-1]
    alertas.update({
        'itb_d':      ult.ITB_derecho,
        'itb_i':      ult.ITB_izquierdo,
        'lops_d':     ult.LOPS_derecho,
        'lops_i':     ult.LOPS_izquierdo,
        'eap_d':      ult.EAP_derecho,
        'tend_itb_d': _tendencia([v for v in itb_d_vals if v]),
    })

    md  = "## Podología / Miembros Inferiores\n\n"
    md += f"> {len(regs)} evaluación(es) registrada(s)\n\n"
    md += "### ITB, LOPS y EAP\n\n"
    md += "| Fecha | ITB Derecho | ITB Izquierdo | LOPS Der. | LOPS Izq. | EAP Der. | EAP Izq. |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_itb)
    md += _bloque_estadisticas("Análisis Estadístico — Índice Tobillo-Brazo", [
        {'nombre': 'ITB Derecho', 'valores': [v for v in itb_d_vals if v], 'normal': (0.9, 1.2), 'limite': (0.4, 1.4)},
        {'nombre': 'ITB Izquierdo', 'valores': [v for v in itb_i_vals if v], 'normal': (0.9, 1.2), 'limite': (0.4, 1.4)},
    ])
    md += "\n> ITB normal 0.9–1.2 | <0.9 isquemia periférica | >1.2 posible calcificación\n\n"
    md += "### Exploración Neurológica (Der./Izq.)\n\n"
    md += "| Fecha | Táctil | Térmica | Dolorosa | Palestesia | Patelar | Aquileano |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_neuro)
    md += "\n\n### Pulsos Periféricos\n\n"
    md += "| Fecha | Femoral | Poplíteo | Tibial Post. | Pedio |\n|---|---|---|---|---|\n"
    md += "\n".join(filas_pulsos)
    md += "\n\n### Lesiones del Pie\n\n"
    md += "| Fecha | Deform. Der. | Deform. Izq. | Lesiones Derm. Der. | Lesiones Derm. Izq. | Impresión Dx |\n|---|---|---|---|---|---|\n"
    md += "\n".join(filas_lesiones)
    return md, alertas


def _sec_oftalmologia(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.oftalmologia)
    if not regs:
        return f"## Oftalmología\n{_nd()}", alertas

    filas_ret, filas_comp = [], []

    for r in regs:
        b_ret_d  = _badge_texto(r.retinopatia_diabetica,  ['no'])
        b_ret_h  = _badge_texto(r.retinopatia_hipertensiva, ['no'])
        b_mac_od = _badge_texto(r.maculopatia_od, ['no'])
        b_mac_oi = _badge_texto(r.maculopatia_oi, ['no'])
        filas_ret.append(
            f"| {_f(r.fecha_registro)} | {_f(r.retinopatia_diabetica)} {b_ret_d} | "
            f"{_f(r.retinopatia_hipertensiva)} {b_ret_h} | "
            f"{_f(r.retinopatia_artereo_esclerosis)} | "
            f"{_f(r.maculopatia_od)} {b_mac_od} / {_f(r.maculopatia_oi)} {b_mac_oi} | "
            f"{_f(r.av_od)} | {_f(r.av_oi)} |"
        )
        b_cat_od  = _badge_texto(r.catarata_od, ['no'])
        b_cat_oi  = _badge_texto(r.catarata_oi, ['no'])
        b_glau_od = _badge_texto(r.glaucoma_od, ['no'])
        b_glau_oi = _badge_texto(r.glaucoma_oi, ['no'])
        filas_comp.append(
            f"| {_f(r.fecha_registro)} | "
            f"{_f(r.catarata_od)} {b_cat_od} | {_f(r.catarata_oi)} {b_cat_oi} | "
            f"{_f(r.glaucoma_od)} {b_glau_od} | {_f(r.glaucoma_oi)} {b_glau_oi} |"
        )

    ult = regs[-1]
    alertas.update({
        'retinopatia_dm': ult.retinopatia_diabetica,
        'av_od':          ult.av_od,
        'av_oi':          ult.av_oi,
    })

    md  = "## Oftalmología\n\n"
    md += f"> {len(regs)} evaluación(es) registrada(s)\n\n"
    md += "### Retinopatías y Agudeza Visual\n\n"
    md += "| Fecha | Ret. Diabética | Ret. Hipertensiva | Ret. Arteriosclerótica | Maculopatía OD/OI | AV OD | AV OI |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_ret)
    md += "\n\n### Catarata y Glaucoma\n\n"
    md += "| Fecha | Catarata OD | Catarata OI | Glaucoma OD | Glaucoma OI |\n|---|---|---|---|---|\n"
    md += "\n".join(filas_comp)
    return md, alertas

def _sec_nefrologia(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.nefrologia)
    if not regs:
        return f"## Nefrología\n{_nd()}", alertas

    fg_vals, creat_vals = [], []
    filas_func, filas_prot = [], []

    for r in regs:
        b_fg    = _badge_numerico(r.filtrado_glomerular_teorico, (90, 999), (60, 89))
        b_creat = _badge_numerico(r.creatinina, (50, 110), (111, 130))
        b_urea  = _badge_numerico(r.urea, (2, 7), (7, 10))
        b_nefro = _badge_texto(r.diagnostico_renal, ['Sano (Sin daño renal)'])
        
        # --- Lógica de Albuminuria Actualizada ---
        # Ahora concatenamos valor, unidad y categoría si existe
        albuminuria_str = ", ".join(
            f"{m.valor} {m.unidad or ''} ({m.categoria or ''})" 
            for m in r.mediciones_albuminuria
        ) if r.mediciones_albuminuria else (_f(r.albuminuria_categoria) if r.albuminuria_categoria else "—")
        # ----------------------------------------

        filas_func.append(
            f"| {_f(r.fecha_registro)} | {_f(r.filtrado_glomerular_teorico)} {b_fg} | "
            f"{r.clasificacion} | {_f(r.creatinina)} {b_creat} | "
            f"{_f(r.urea)} {b_urea} | {_f(r.ac_urico)} | "
            f"{_f(r.cituria)} | {_f(r.diagnostico_renal)} {b_nefro} |"
        )
        filas_prot.append(
            f"| {_f(r.fecha_registro)} | {_f(r.proteinuria_valor)} | "
            f"{_f(r.proteinuria)} | {albuminuria_str} | {_f(r.uts_renal)} |"
        )
        fg_vals.append(r.filtrado_glomerular_teorico)
        creat_vals.append(r.creatinina)

    ult = regs[-1]
    alertas.update({
        'fg':           ult.filtrado_glomerular_teorico,
        'fg_cls':       ult.clasificacion,
        'nefropatia_dm': ult.diagnostico_renal,
        'tend_fg':      _tendencia([v for v in fg_vals if v]),
    })

    md  = "## Nefrología\n\n"
    md += f"> {len(regs)} evaluación(es) registrada(s)\n\n"
    md += "### Función Renal\n\n"
    md += "| Fecha | FG (ml/min/1.73m²) | Clasif. KDIGO | Creatinina (μmol/L) | Urea (mmol/L) | Ác. Úrico | Cituria | Diagnóstico Renal |\n|---|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas_func)
    md += _bloque_estadisticas("Análisis Estadístico — Función Renal", [
        {'nombre': 'Filtrado Glomerular (ml/min)', 'valores': [v for v in fg_vals if v],    'normal': (90, 999), 'limite': (60, 89)},
        {'nombre': 'Creatinina (μmol/L)',          'valores': [v for v in creat_vals if v], 'normal': (50, 110), 'limite': (111, 130)},
    ])
    md += "\n> FG normal ≥90 | G2: 60-89 (vigilar) | G3A: 45-59 (alarma) | G4: 15-29 (grave) | G5: <15 (fallo)\n\n"
    md += "### Proteinuria y Ecografía\n\n"
    md += "| Fecha | Proteinuria (g/L) | Clasif. Proteinuria | Albuminuria (Categoría) | UTS Renal |\n|---|---|---|---|---|\n"
    md += "\n".join(filas_prot)
    return md, alertas
def _sec_estomatologia(p: Paciente) -> tuple[str, dict]:
    regs = _todos(p.estomatologia)
    if not regs:
        return f"## Estomatología\n{_nd()}", {}

    filas = []
    for r in regs:
        dx_cli = ", ".join(d.diagnostico for d in r.diagnosticos_clinico if d.diagnostico) or "—"
        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.examen_funcional)} | "
            f"{_f(r.diagnosticos_epidemiologicos)} | {dx_cli} | "
            f"{_f(r.pronostico)} | {_f(r.tratamiento)} |"
        )

    md  = "## Estomatología\n\n"
    md += f"> {len(regs)} evaluación(es) registrada(s)\n\n"
    md += "| Fecha | Examen Funcional | Dx Epidemiológico | Dx Clínico | Pronóstico | Tratamiento |\n|---|---|---|---|---|---|\n"
    md += "\n".join(filas)
    return md, {}


def _sec_cardiologia(p: Paciente) -> tuple[str, dict]:
    alertas = {}
    regs = _todos(p.cardiologia)
    if not regs:
        return f"## Cardiología / Riesgo CV\n{_nd()}", alertas

    riesgo_vals = [r.riesgo_oms for r in regs if r.riesgo_oms is not None]
    filas = []

    for r in regs:
        b_col  = _badge_numerico(r.colesterol_total, (0, 5.19), (0, 6.19))
        b_sist = _badge_numerico(r.presion_sistolica, (0, 129), (0, 139))
        riesgo_str = f"{_f(r.riesgo_oms)}%" if r.riesgo_oms else "—"
        if r.riesgo_oms:
            b_riesgo = "(normal)" if r.riesgo_oms < 10 else ("(límite)" if r.riesgo_oms < 20 else "(")
        else:
            b_riesgo = "(desconocido)"
        filas.append(
            f"| {_f(r.fecha_registro)} | {_f(r.presion_sistolica)} {b_sist} | "
            f"{_f(r.colesterol_total)} {b_col} | {_f(r.fuma)} | "
            f"{riesgo_str} {b_riesgo} | {_f(r.color_riesgo)} | {_f(r.ekg)} |"
        )

    ult = regs[-1]
    alertas.update({
        'riesgo_oms':  ult.riesgo_oms,
        'ta_cardio':   ult.presion_sistolica,
        'tend_riesgo': _tendencia(riesgo_vals),
    })

    md  = "## Cardiología / Riesgo Cardiovascular OMS\n\n"
    md += f"> {len(regs)} evaluación(es) registrada(s)\n\n"
    md += "| Fecha | TA Sistólica | Colesterol | Fuma | Riesgo 10a | Color | EKG |\n|---|---|---|---|---|---|---|\n"
    md += "\n".join(filas)
    md += _bloque_estadisticas("Análisis Estadístico — Riesgo Cardiovascular", [
        {'nombre': 'Riesgo OMS 10a (%)', 'valores': riesgo_vals,
         'normal': (0, 9), 'limite': (0, 19)},
    ])
    md += "\n> Riesgo <10%: bajo | 10–20%: moderado | >20%: alto | >30%: muy alto\n"
    return md, alertas


# ─── Mapa de secciones → extractores ────────────────────────────────────────

_EXTRACTORES: dict = {
    'datos_basicos':       _sec_datos_basicos,
    'indicaciones':        _sec_indicaciones,
    'app':                 _sec_app,
    'apf':                 _sec_apf,
    'apf_diabetes':        _sec_apf_diabetes,
    'habitos_toxicos':     _sec_habitos,
    'historia_obstetrica': _sec_obstetrica,
    'tratamiento_actual':  _sec_tratamiento_actual,
    'otros_tratamientos':  _sec_otros_tratamientos,
    'examen_fisico':       _sec_examen_fisico,
    'mensuraciones':       _sec_mensuraciones,
    'educacion':           _sec_educacion,
    'complementarios':     _sec_complementarios,
    'podologia':           _sec_podologia,
    'oftalmologia':        _sec_oftalmologia,
    'nefrologia':          _sec_nefrologia,
    'estomatologia':       _sec_estomatologia,
    'cardiologia':         _sec_cardiologia,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCLUSIÓN CLÍNICA — Análisis multifactorial avanzado
# ═══════════════════════════════════════════════════════════════════════════════

def _conclusion_python(alertas: dict) -> str:
    """
    Conclusión clínica avanzada: detección multifactorial, síndrome metabólico,
    análisis de tendencias y flagging de urgencias.
    """
    hallazgos:   list[str] = []
    urgencias:   list[str] = []
    favorables:  list[str] = []
    recomendaciones: list[str] = []

    nombre   = alertas.get('nombre', 'El/la paciente')
    edad     = alertas.get('edad', '?')
    evolucion = alertas.get('evolucion', 'tiempo no especificado')
    tipo_dm  = alertas.get('tipo_dm', 'Diabetes Mellitus')
    sexo     = str(alertas.get('sexo', '')).lower()
    es_f     = 'femenin' in sexo

    # ── Control glucémico ─────────────────────────────────────────────────────
    gluc      = alertas.get('glucemia')
    tend_gluc = alertas.get('tend_glucemia', '')
    if gluc is not None:
        if gluc >= 13.9:
            urgencias.append(f"descompensación glucémica severa ({gluc} mmol/L)")
            recomendaciones.append("evaluación y corrección urgente de la glucemia")
        elif gluc >= 10.0:
            hallazgos.append(f"control glucémico deficiente ({gluc} mmol/L)")
            recomendaciones.append("revisión del esquema terapéutico hipoglucemiante")
        elif gluc >= 7.0:
            if 'alza' in tend_gluc:
                hallazgos.append(f"glucemia en límite con tendencia ascendente ({gluc} mmol/L)")
                recomendaciones.append("ajuste del tratamiento ante tendencia al alza")
            else:
                hallazgos.append(f"hiperglucemia leve ({gluc} mmol/L)")
                recomendaciones.append("optimización del control glucémico")
        else:
            if 'bajada' in tend_gluc:
                favorables.append(f"mejoría sostenida del control glucémico ({gluc} mmol/L en descenso)")
            else:
                favorables.append(f"glucemia en objetivo terapéutico ({gluc} mmol/L)")

    # ── Tensión arterial ──────────────────────────────────────────────────────
    ta_s = alertas.get('ta_sist')
    ta_d = alertas.get('ta_diast')
    if ta_s and ta_d:
        if ta_s >= 180 or ta_d >= 110:
            urgencias.append(f"crisis hipertensiva ({ta_s}/{ta_d} mmHg)")
            recomendaciones.append("tratamiento antihipertensivo urgente")
        elif ta_s >= 140 or ta_d >= 90:
            hallazgos.append(f"hipertensión arterial ({ta_s}/{ta_d} mmHg)")
            recomendaciones.append("optimización del tratamiento antihipertensivo")
        elif ta_s >= 130 or ta_d >= 80:
            hallazgos.append(f"presión arterial en rango límite ({ta_s}/{ta_d} mmHg)")
            recomendaciones.append("monitorización tensional frecuente")
        else:
            favorables.append(f"presión arterial controlada ({ta_s}/{ta_d} mmHg)")

    # ── IMC ───────────────────────────────────────────────────────────────────
    imc     = alertas.get('imc')
    imc_cls = str(alertas.get('imc_cls', '')).lower()
    tend_imc = alertas.get('tend_imc', '')
    if imc and isinstance(imc, (int, float)):
        if imc >= 40:
            hallazgos.append(f"obesidad mórbida (IMC {imc})")
            recomendaciones.append("evaluación para cirugía metabólica y programa de pérdida de peso intensivo")
        elif imc >= 35:
            hallazgos.append(f"obesidad severa (IMC {imc})")
            recomendaciones.append("programa intensivo de reducción de peso")
        elif imc >= 30:
            hallazgos.append(f"obesidad (IMC {imc})")
            if 'alza' in tend_imc:
                recomendaciones.append("intervención urgente para frenar ganancia ponderal")
            else:
                recomendaciones.append("programa de reducción de peso con dieta y ejercicio")
        elif imc >= 25:
            hallazgos.append(f"sobrepeso (IMC {imc})")
            if 'bajada' in tend_imc:
                recomendaciones.append("intervención dietética y actividad física preventiva")
        elif 18.5 <= imc <= 24.9:
            favorables.append(f"IMC en rango normal ({imc})")

    # ── Lípidos ───────────────────────────────────────────────────────────────
    col  = alertas.get('colesterol')
    tg   = alertas.get('tg')
    hdlc = alertas.get('hdlc')
    dislipidemia = []
    if col and col > 5.2:
        dislipidemia.append(f"hipercolesterolemia ({col} mmol/L)")
    if tg and tg > 1.7:
        dislipidemia.append(f"hipertrigliceridemia ({tg} mmol/L)")
    if hdlc:
        umbral_hdl = 1.3 if es_f else 1.0
        if hdlc < umbral_hdl:
            dislipidemia.append(f"HDL-C bajo ({hdlc} mmol/L)")
    if dislipidemia:
        hallazgos.append("dislipidemia: " + ", ".join(dislipidemia))
        recomendaciones.append("tratamiento hipolipemiante y modificación dietética")
    elif col and col <= 5.2 and tg and tg <= 1.7:
        favorables.append("perfil lipídico en objetivo")

    # ── Nefrología ────────────────────────────────────────────────────────────
    fg      = alertas.get('fg')
    tend_fg = alertas.get('tend_fg', '')
    fg_cls  = alertas.get('fg_cls', '')
    if fg is not None:
        if fg < 15:
            urgencias.append(f"fallo renal terminal (FG {fg} ml/min — {fg_cls})")
            recomendaciones.append("evaluación urgente para terapia de reemplazo renal")
        elif fg < 30:
            urgencias.append(f"insuficiencia renal grave (FG {fg} ml/min — {fg_cls})")
            recomendaciones.append("evaluación nefrológica urgente y nefroprotección máxima")
        elif fg < 60:
            msg = f"deterioro renal moderado (FG {fg} ml/min — {fg_cls})"
            if 'bajada' in tend_fg:
                msg += " con deterioro progresivo"
                recomendaciones.append("nefroprotección intensiva y seguimiento nefrológico trimestral")
            else:
                recomendaciones.append("seguimiento nefrológico y ajuste de fármacos nefrotóxicos")
            hallazgos.append(msg)
        elif fg < 90 and 'bajada' in tend_fg:
            hallazgos.append(f"función renal levemente reducida con tendencia al deterioro (FG {fg})")
            recomendaciones.append("vigilancia de función renal cada 3 meses")

    # ── Oftalmología ──────────────────────────────────────────────────────────
    ret = alertas.get('retinopatia_dm', '')
    if ret and 'no' not in str(ret).lower() and ret not in ('—', '', None):
        hallazgos.append(f"retinopatía diabética ({ret})")
        recomendaciones.append("seguimiento oftalmológico especializado periódico")

    # ── Pie diabético ─────────────────────────────────────────────────────────
    itb_d = alertas.get('itb_d')
    itb_i = alertas.get('itb_i')
    lops_d = alertas.get('lops_d', '')
    eap_d  = alertas.get('eap_d', '')
    pie_hal = []
    if itb_d and itb_d < 0.9:
        pie_hal.append(f"isquemia D (ITB {round(itb_d,2)})")
    if itb_i and itb_i < 0.9:
        pie_hal.append(f"isquemia I (ITB {round(itb_i,2)})")
    if lops_d and 'si' in str(lops_d).lower():
        pie_hal.append("LOPS positivo (pérdida sensibilidad protectora)")
    if eap_d and 'si' in str(eap_d).lower():
        pie_hal.append("EAP confirmada")
    if pie_hal:
        hallazgos.append("riesgo de pie diabético: " + ", ".join(pie_hal))
        recomendaciones.append("cuidado preventivo intensivo del pie y evaluación vascular periférica")

    # ── Riesgo cardiovascular ─────────────────────────────────────────────────
    riesgo_cv = alertas.get('riesgo_oms')
    if riesgo_cv is not None:
        if riesgo_cv >= 30:
            hallazgos.append(f"riesgo cardiovascular muy alto a 10 años ({riesgo_cv}%)")
            recomendaciones.append("intervención cardiovascular intensiva y estatinas de alta potencia")
        elif riesgo_cv >= 20:
            hallazgos.append(f"riesgo cardiovascular alto a 10 años ({riesgo_cv}%)")
            recomendaciones.append("manejo agresivo de todos los factores de riesgo cardiovascular")
        elif riesgo_cv >= 10:
            hallazgos.append(f"riesgo cardiovascular moderado a 10 años ({riesgo_cv}%)")

    # ── Síndrome metabólico (detección automática) ────────────────────────────
    criterios_sm = 0
    cintura = alertas.get('cintura')
    if cintura:
        if (es_f and cintura > 80) or (not es_f and cintura > 94):
            criterios_sm += 1
    if ta_s and (ta_s >= 130 or (ta_d and ta_d >= 85)):
        criterios_sm += 1
    if gluc and gluc >= 5.6:
        criterios_sm += 1
    if tg and tg >= 1.7:
        criterios_sm += 1
    if hdlc and hdlc < (1.3 if es_f else 1.0):
        criterios_sm += 1

    if criterios_sm >= 4:
        hallazgos.append(f"síndrome metabólico confirmado ({criterios_sm}/5 criterios)")
        recomendaciones.append("manejo integral del síndrome metabólico")
    elif criterios_sm == 3:
        hallazgos.append(f"posible síndrome metabólico ({criterios_sm}/5 criterios)")

    # ── Tabaquismo ────────────────────────────────────────────────────────────
    fuma = alertas.get('fuma', '')
    if fuma and 'si' in str(fuma).lower():
        hallazgos.append("tabaquismo activo")
        recomendaciones.append("programa de cesación tabáquica")

    # ── Construcción del texto ────────────────────────────────────────────────
    intro = f"{nombre}, paciente de {edad} años con {tipo_dm} de {evolucion} de evolución"
    partes = []

    if urgencias:
        partes.append(
            f"SITUACIÓN DE ATENCIÓN PRIORITARIA: {intro} presenta: "
            f"{'; '.join(urgencias)}. Se requiere evaluación inmediata."
        )

    if hallazgos:
        partes.append(
            f"{intro} presenta los siguientes hallazgos clínicos relevantes: "
            f"{'; '.join(hallazgos)}."
        )
    elif not urgencias:
        partes.append(
            f"{intro} muestra parámetros dentro de rangos aceptables "
            f"en los exámenes disponibles."
        )

    if favorables:
        partes.append(f"Aspectos favorables: {'; '.join(favorables)}.")

    if recomendaciones:
        partes.append(f"Se recomienda: {'; '.join(recomendaciones)}.")
    elif not urgencias:
        partes.append(
            "Continuar con el seguimiento habitual y reforzar la adherencia "
            "al tratamiento actual."
        )

    return "\n\n".join(partes)


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def generar_informe(
    termino: str,
    secciones: list[str],
    medico: dict | None = None,
) -> tuple[str | None, str, dict]:
    """
    Genera el informe clínico completo en Markdown.

    Args:
        termino:   no_hc o ci del paciente
        secciones: lista de claves de SECCIONES_DISPONIBLES
        medico:    dict opcional con datos del médico firmante:
                   {'nombre': str, 'especialidad': str, 'no_registro': str}

    Returns:
        (markdown_str, nombre_paciente, alertas_totales)
        o (None, '', {}) si no se encuentra el paciente
    """
    p, db = buscar_paciente(termino)
    if not p:
        return None, "", {}

    try:
        nombre     = f"{p.nombres or ''} {p.apellidos or ''}".strip()
        fecha_gen  = datetime.now().strftime('%d/%m/%Y %H:%M')
        institucion = p.institucion.nombre if p.institucion else "Centro de Atención al Diabético"

        # ── Encabezado ───────────────────────────────────────────────────────
        md_partes = [
            "# RESUMEN DE HISTORIA CLÍNICA",
            f"**Institución:** {institucion}  ",
            f"**Fecha de generación:** {fecha_gen}  ",
            f"**Paciente:** {nombre}  ",
        ]
                

        md_partes.append("---")

        # ── Secciones ────────────────────────────────────────────────────────
        alertas_totales: dict = {}

        for clave in secciones:
            extractor = _EXTRACTORES.get(clave)
            if not extractor:
                continue
            try:
                bloque_md, alertas = extractor(p)
                if bloque_md:
                    md_partes.append(bloque_md)
                    alertas_totales.update(alertas)
            except Exception as exc:
                etiqueta = SECCIONES_DISPONIBLES.get(clave, clave)
                md_partes.append(f"## {etiqueta}\n\n> ⚠️ Error al extraer datos: {exc}\n")

        # ── Conclusión Clínica ────────────────────────────────────────────────
        md_partes.append("## Conclusión Clínica")
        md_partes.append(_conclusion_python(alertas_totales))

        # ── Pie de página ─────────────────────────────────────────────────────
        md_partes.append("\n---")
        md_partes.append(
            f"*Informe generado el {fecha_gen} | {institucion} | "
            f"Sistema de Gestión de Diabetes*"
        )

        return "\n\n".join(md_partes), nombre, alertas_totales

    except Exception as exc:
        print(f"[ERROR generar_informe] {exc}")
        import traceback
        traceback.print_exc()
        return None, "", {}
    finally:
        if db:
            db.close()
def _safe_float(valor: Any) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        # Limpia espacios y cambia comas por puntos por si viene en formato latino "1,57"
        return float(str(valor).strip().replace(',', '.'))
    except ValueError:
        return None