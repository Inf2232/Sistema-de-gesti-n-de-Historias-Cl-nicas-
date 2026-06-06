# motor_informe_admin.py
# Motor de Informes Administrativos — v1.0
# ─────────────────────────────────────────────────────────────────────────────
# Genera informes estadísticos agregados sobre un listado de pacientes.
# No es un informe de paciente individual sino de cohorte.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any

from models import (
    Session, Paciente,
    AreaSalud, Municipio,
    Indicaciones,
    TratamientoActual,
    Complementarios,
    Mensuraciones,
    ExamenFisico,
    Oftalmologia,
    Nefrologia,
    ExamenMiembrosInferiores,
    ResultadoEducacionDiabetologica,
    AntecedentePatologicoPersonal,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ═══════════════════════════════════════════════════════════════════════════════

def _f(valor: Any, defecto: str = "—") -> str:
    if valor is None:
        return defecto
    if isinstance(valor, float):
        return str(round(valor, 2))
    return str(valor)


def _pct(num: int, den: int) -> str:
    if den == 0:
        return "0.0%"
    return f"{round(num / den * 100, 1)}%"


def _ultimo(lista: list, campo: str = 'fecha_registro'):
    """Devuelve el registro más reciente de una lista."""
    if not lista:
        return None
    con_fecha = sorted(
        [r for r in lista if getattr(r, campo, None)],
        key=lambda x: getattr(x, campo)
    )
    return con_fecha[-1] if con_fecha else lista[-1]


def _en_periodo(lista: list, fi: date | None, ff: date | None,
                campo: str = 'fecha_registro') -> list:
    """Filtra registros dentro de un rango de fechas."""
    result = list(lista)
    if fi:
        result = [r for r in result if getattr(r, campo, None) and getattr(r, campo) >= fi]
    if ff:
        result = [r for r in result if getattr(r, campo, None) and getattr(r, campo) <= ff]
    return result


def _avg(valores: list) -> float | None:
    nums = [v for v in valores if isinstance(v, (int, float)) and v is not None]
    return round(sum(nums) / len(nums), 2) if nums else None


def _tabla_md(encabezados: list[str], filas: list[list]) -> str:
    sep = "|" + "|".join(["---"] * len(encabezados)) + "|"
    cabecera = "| " + " | ".join(encabezados) + " |"
    cuerpo = "\n".join("| " + " | ".join(str(c) for c in fila) + " |" for fila in filas)
    return f"{cabecera}\n{sep}\n{cuerpo}"


def _barra(num: int, den: int, ancho: int = 10) -> str:
    """Barra de progreso ASCII."""
    if den == 0:
        return "░" * ancho
    llenos = round(num / den * ancho)
    return "█" * llenos + "░" * (ancho - llenos)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSULTA DE PACIENTES
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_opciones_filtro(provincia: str | None = None) -> dict:
    """
    Carga las listas de valores para los selectores de filtro.

    Si se pasa `provincia`, filtra municipios a los que pertenecen a esa
    provincia (campo Municipio.provincia). Las áreas se agrupan por municipio
    para el filtro en cascada de la UI.

    Retorna:
        areas            : list[str]        — todas las áreas (o las del prov.)
        municipios       : list[str]        — municipios del prov. (o todos)
        areas_por_municipio: dict[str,list] — {municipio: [area, ...]}
        estados          : list[str]
        tipos_dm         : list[str]
    """
    db = Session()
    try:
        # ── Municipios filtrados por provincia ────────────────────────────────
        q_mun = db.query(Municipio).order_by(Municipio.nombre)
        if provincia:
            if hasattr(Municipio, 'provincia'):
                q_mun = q_mun.filter(Municipio.provincia == provincia)
            elif hasattr(Municipio, 'provincia_nombre'):
                q_mun = q_mun.filter(Municipio.provincia_nombre == provincia)
        mun_objs   = [r for r in q_mun.all() if r.nombre]
        municipios = [r.nombre for r in mun_objs]
        mun_ids    = {r.id for r in mun_objs if hasattr(r, 'id') and r.id}

        # ── Áreas de salud con su municipio (para cascada) ────────────────────
        q_area = db.query(AreaSalud).order_by(AreaSalud.nombre)
        if provincia and mun_ids and hasattr(AreaSalud, 'municipio_id'):
            q_area = q_area.filter(AreaSalud.municipio_id.in_(mun_ids))
        area_objs = [r for r in q_area.all() if r.nombre]

        areas = [r.nombre for r in area_objs]

        # Agrupar áreas por nombre de municipio para el filtro cascada
        areas_por_municipio: dict[str, list[str]] = {}
        for a in area_objs:
            # Intentar obtener el nombre del municipio relacionado
            mun_nombre = None
            if hasattr(a, 'municipio_rel') and a.municipio_rel:
                mun_nombre = getattr(a.municipio_rel, 'nombre', None)
            elif hasattr(a, 'municipio'):
                mun_nombre = a.municipio
            if mun_nombre:
                areas_por_municipio.setdefault(mun_nombre, []).append(a.nombre)

        estados  = sorted(set(
            r[0] for r in db.query(Paciente.estado_actual).distinct().all() if r[0]
        ))
        tipos_dm = sorted(set(
            r[0] for r in db.query(Indicaciones.tipo_diabetes).distinct().all() if r[0]
        ))
        return {
            'areas':               areas,
            'municipios':          municipios,
            'areas_por_municipio': areas_por_municipio,
            'estados':             estados,
            'tipos_dm':            tipos_dm,
        }
    finally:
        db.close()


def _consultar_pacientes(filtros: dict, db) -> list[Paciente]:
    """Consulta pacientes activos aplicando los filtros categóricos."""
    q = db.query(Paciente).filter(Paciente.activo == True)

    areas = filtros.get('areas', [])
    if areas:
        q = q.join(Paciente.area_salud_rel).filter(AreaSalud.nombre.in_(areas))

    municipios = filtros.get('municipios', [])
    if municipios:
        q = q.join(Paciente.municipio_rel).filter(Municipio.nombre.in_(municipios))

    tipo_dm = filtros.get('tipo_dm')
    if tipo_dm:
        q = (q.join(Paciente.indicaciones)
               .filter(Indicaciones.tipo_diabetes == tipo_dm)
               .distinct())

    estado = filtros.get('estado')
    if estado:
        q = q.filter(Paciente.estado_actual == estado)
    fi = filtros.get('fecha_inicio')
    ff = filtros.get('fecha_fin')
    
    if fi:
        q = q.filter(Paciente.fecha_hc >= fi)
    if ff:
        q = q.filter(Paciente.fecha_hc <= ff)

    return q.all()



# ═══════════════════════════════════════════════════════════════════════════════
#  EXTRACTORES DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

def _metricas_demografia(pacientes: list[Paciente], fi: date | None, ff: date | None) -> dict:
    total = len(pacientes)
    sexo_c    = Counter()
    edad_c    = Counter()
    area_c    = Counter()
    mun_c     = Counter()
    nuevos    = 0

    for p in pacientes:
        # Sexo
        sx = str(p.sexo or '').strip().lower()
        if 'femenin' in sx:
            sexo_c['Femenino'] += 1
        elif 'masculin' in sx:
            sexo_c['Masculino'] += 1
        else:
            sexo_c['No especificado'] += 1

        # Edad
        edad = p.edad_actual
        if isinstance(edad, int):
            if edad < 18:
                edad_c['<18 años'] += 1
            elif edad < 40:
                edad_c['18–39 años'] += 1
            elif edad < 60:
                edad_c['40–59 años'] += 1
            elif edad < 75:
                edad_c['60–74 años'] += 1
            else:
                edad_c['≥75 años'] += 1
        else:
            edad_c['No disponible'] += 1

        # Área y municipio
        area = p.area_salud or 'Sin área'
        mun  = p.municipio  or 'Sin municipio'
        area_c[area] += 1
        mun_c[mun]   += 1

        # Nuevos en período
        if p.fecha_hc:
            fhc = p.fecha_hc if isinstance(p.fecha_hc, date) else p.fecha_hc.date()
            en_ini = (fi is None or fhc >= fi)
            en_fin = (ff is None or fhc <= ff)
            if en_ini and en_fin:
                nuevos += 1

    return {
        'total':   total,
        'nuevos':  nuevos,
        'sexo':    dict(sexo_c),
        'edad':    dict(edad_c),
        'areas':   dict(area_c.most_common(10)),
        'municipios': dict(mun_c.most_common(10)),
    }


def _metricas_evolucion_dm(pacientes: list[Paciente]) -> dict:
    grupos = Counter()
    tipo_c = Counter()

    for p in pacientes:
        # Tiempo de evolución en años
        anios = (p.tiempo_evolucion_anios or 0)
        if anios < 1:
            grupos['<1 año'] += 1
        elif anios < 5:
            grupos['1–4 años'] += 1
        elif anios < 10:
            grupos['5–9 años'] += 1
        elif anios < 20:
            grupos['10–19 años'] += 1
        else:
            grupos['≥20 años'] += 1

        # Tipo DM
        ult_ind = _ultimo(p.indicaciones)
        if ult_ind and ult_ind.tipo_diabetes:
            tipo_c[ult_ind.tipo_diabetes] += 1
        else:
            tipo_c['No especificado'] += 1

    return {'grupos': dict(grupos), 'tipos': dict(tipo_c)}


def _metricas_control_metabolico(pacientes: list[Paciente],
                                  fi: date | None, ff: date | None) -> dict:
    total = len(pacientes)
    con_dato = 0
    controlados    = 0   # glucemia <7.0
    limite         = 0   # 7.0–9.9
    descompensados = 0   # >=10.0
    glucemias      = []

    for p in pacientes:
        regs = _en_periodo(p.complementarios, fi, ff) or p.complementarios
        ult  = _ultimo(regs)
        if not ult or ult.glucemia is None:
            continue
        g = ult.glucemia
        if not isinstance(g, (int, float)):
            continue
        con_dato += 1
        glucemias.append(g)
        if g < 7.0:
            controlados += 1
        elif g < 10.0:
            limite += 1
        else:
            descompensados += 1

    return {
        'total': total, 'con_dato': con_dato,
        'controlados': controlados, 'limite': limite,
        'descompensados': descompensados,
        'promedio': _avg(glucemias),
    }


def _metricas_lipidos(pacientes: list[Paciente],
                      fi: date | None, ff: date | None) -> dict:
    es_f_map = {}
    for p in pacientes:
        es_f_map[p.id] = 'femenin' in str(p.sexo or '').lower()

    col_ok = col_lim = col_alto = 0
    tg_ok  = tg_alt  = 0
    hdl_ok = hdl_bajo = 0
    col_vals = []
    tg_vals  = []
    hdl_vals = []
    con_col = con_tg = con_hdl = 0

    for p in pacientes:
        regs = _en_periodo(p.complementarios, fi, ff) or p.complementarios
        ult  = _ultimo(regs)
        if not ult:
            continue
        es_f = es_f_map.get(p.id, False)

        if isinstance(ult.colesterol, (int, float)):
            con_col += 1
            col_vals.append(ult.colesterol)
            if ult.colesterol < 5.2:
                col_ok += 1
            elif ult.colesterol < 6.2:
                col_lim += 1
            else:
                col_alto += 1

        if isinstance(ult.trigliceridos, (int, float)):
            con_tg += 1
            tg_vals.append(ult.trigliceridos)
            if ult.trigliceridos < 1.7:
                tg_ok += 1
            else:
                tg_alt += 1

        if isinstance(ult.HDLC, (int, float)):
            con_hdl += 1
            hdl_vals.append(ult.HDLC)
            umbral = 1.3 if es_f else 1.0
            if ult.HDLC >= umbral:
                hdl_ok += 1
            else:
                hdl_bajo += 1

    return {
        'con_col': con_col, 'col_ok': col_ok,
        'col_lim': col_lim, 'col_alto': col_alto,
        'col_prom': _avg(col_vals),
        'con_tg': con_tg, 'tg_ok': tg_ok, 'tg_alt': tg_alt,
        'tg_prom': _avg(tg_vals),
        'con_hdl': con_hdl, 'hdl_ok': hdl_ok, 'hdl_bajo': hdl_bajo,
        'hdl_prom': _avg(hdl_vals),
    }


def _metricas_tension_arterial(pacientes: list[Paciente],
                                fi: date | None, ff: date | None) -> dict:
    controlada = 0   # <130/80
    limite     = 0   # 130-139/80-89
    hta_g1     = 0   # 140-159/90-99
    hta_g2     = 0   # >=160/>=100
    con_dato   = 0
    sist_vals  = []
    diast_vals = []

    for p in pacientes:
        regs = _en_periodo(p.examen_fisico, fi, ff) or p.examen_fisico
        ult  = _ultimo(regs)
        if not ult:
            continue
        s = ult.sistolica_sentado
        d = ult.diastolica_sentado
        if not isinstance(s, (int, float)) or not isinstance(d, (int, float)):
            continue
        con_dato += 1
        sist_vals.append(s)
        diast_vals.append(d)
        if s < 130 and d < 80:
            controlada += 1
        elif s < 140 and d < 90:
            limite += 1
        elif s < 160 and d < 100:
            hta_g1 += 1
        else:
            hta_g2 += 1

    return {
        'con_dato': con_dato,
        'controlada': controlada, 'limite': limite,
        'hta_g1': hta_g1, 'hta_g2': hta_g2,
        'sist_prom': _avg(sist_vals),
        'diast_prom': _avg(diast_vals),
    }


def _metricas_nutricionales(pacientes: list[Paciente],
                             fi: date | None, ff: date | None) -> dict:
    imc_normal = imc_sp = imc_ob1 = imc_ob2 = imc_ob3 = imc_bajo = 0
    con_dato   = 0
    imc_vals   = []
    peso_vals  = []

    for p in pacientes:
        regs = _en_periodo(p.mensuraciones, fi, ff) or p.mensuraciones
        ult  = _ultimo(regs)
        if not ult:
            continue
        imc = ult.IMC
        if not isinstance(imc, (int, float)):
            continue
        con_dato += 1
        imc_vals.append(imc)
        print(f"DEBUG: Paciente {p.id} - IMC: {imc}, Peso: {ult.peso}")
        if ult.peso and isinstance(ult.peso, (int, float)):
            peso_vals.append(ult.peso)

        if imc < 18.5:
            imc_bajo += 1
        elif imc < 25:
            imc_normal += 1
        elif imc < 30:
            imc_sp += 1
        elif imc < 35:
            imc_ob1 += 1
        elif imc < 40:
            imc_ob2 += 1
        else:
            imc_ob3 += 1
    # print(f"DEBUG: IMC vals: {imc_vals}")
    return {
        'con_dato': con_dato,
        'bajo': imc_bajo, 'normal': imc_normal, 'sobrepeso': imc_sp,
        'ob1': imc_ob1, 'ob2': imc_ob2, 'ob3': imc_ob3,
        'imc_prom': _avg(imc_vals),
        'peso_prom': _avg(peso_vals),
        'obesos': imc_ob1 + imc_ob2 + imc_ob3,
    }


def _metricas_complicaciones(pacientes: list[Paciente]) -> dict:
    ret_no_prol  = ret_prol  = ret_sin  = 0
    nefro_dm     = nefro_no_dm = nefro_sano = 0
    pie_g0 = pie_g1 = pie_g2 = pie_g3 = pie_sin = 0
    lops_si = eap_si = 0
    con_oftalmo = con_nefro = con_podologia = 0

    for p in pacientes:
        # Retinopatía
        ult_oft = _ultimo(p.oftalmologia)
        if ult_oft:
            con_oftalmo += 1
            ret = str(ult_oft.retinopatia_diabetica or '').lower()
            if 'no' in ret or ret == '':
                ret_sin += 1
            elif 'proliferativa' in ret and 'no pro' not in ret:
                ret_prol += 1
            else:
                ret_no_prol += 1
        else:
            ret_sin += 1

        # Nefropatía — nuevos valores: 'Sano (Sin daño renal)',
        #   'Enfermedad Renal Crónica NO Diabética', 'Enfermedad Renal Diabética'
        ult_nef = _ultimo(p.nefrologia)
        if ult_nef:
            con_nefro += 1
            nef = str(ult_nef.diagnostico_renal or '').strip()
            if nef == 'Enfermedad Renal Diabética':
                nefro_dm += 1
            elif nef == 'Enfermedad Renal Crónica NO Diabética':
                nefro_no_dm += 1
            else:
                # 'Sano (Sin daño renal)' o valor vacío/desconocido
                nefro_sano += 1

        # Pie diabético
        ult_pod = _ultimo(p.examen_miembros_inferiores)
        if ult_pod:
            con_podologia += 1
            imp = str(ult_pod.impresion_diagnostica or '').lower()
            if 'grado 0' in imp or 'riesgo 0' in imp:
                pie_g0 += 1
            elif 'grado 1' in imp or 'riesgo 1' in imp:
                pie_g1 += 1
            elif 'grado 2' in imp or 'riesgo 2' in imp:
                pie_g2 += 1
            elif 'grado 3' in imp or 'riesgo 3' in imp:
                pie_g3 += 1
            else:
                pie_sin += 1
            if ult_pod.LOPS_derecho and 'si' in str(ult_pod.LOPS_derecho).lower():
                lops_si += 1
            if ult_pod.EAP_derecho and 'si' in str(ult_pod.EAP_derecho).lower():
                eap_si += 1
        else:
            pie_sin += 1

    total = len(pacientes)
    return {
        'total': total,
        'ret_sin': ret_sin, 'ret_no_prol': ret_no_prol, 'ret_prol': ret_prol,
        'nefro_dm': nefro_dm, 'nefro_no_dm': nefro_no_dm, 'nefro_sano': nefro_sano,
        'pie_g0': pie_g0, 'pie_g1': pie_g1, 'pie_g2': pie_g2,
        'pie_g3': pie_g3, 'pie_sin': pie_sin,
        'lops_si': lops_si, 'eap_si': eap_si,
        'con_oftalmo': con_oftalmo,
        'con_nefro': con_nefro,
        'con_podologia': con_podologia,
    }


def _metricas_comorbilidades(pacientes: list[Paciente],
                              fi: date | None, ff: date | None) -> dict:
    hta_si = 0
    dislip = 0
    tabaco = 0
    obesos = 0

    for p in pacientes:
        # HTA en antecedentes personales
        for ant in p.antecedentes_personales:
            for pat in ant.patologias:
                tipo = str(pat.tipo_patologia or '').lower()
                if 'hipert' in tipo and 'art' in tipo:
                    hta_si += 1
                    break

        # Dislipidemia en complementarios
        regs = _en_periodo(p.complementarios, fi, ff) or p.complementarios
        ult  = _ultimo(regs)
        if ult:
            col_alto = isinstance(ult.colesterol, (int, float)) and ult.colesterol > 5.2
            tg_alto  = isinstance(ult.trigliceridos, (int, float)) and ult.trigliceridos > 1.7
            if col_alto or tg_alto:
                dislip += 1

        # Tabaquismo
        ult_hab = _ultimo(p.habitos_toxicos)
        if ult_hab and 'si' in str(ult_hab.fuma or '').lower():
            tabaco += 1

        # Obesidad (IMC >= 30)
        ult_mens = _ultimo(p.mensuraciones)
        if ult_mens and isinstance(ult_mens.IMC, (int, float)) and ult_mens.IMC >= 30:
            obesos += 1

    return {
        'total': len(pacientes),
        'hta': hta_si, 'dislipidemia': dislip,
        'tabaquismo': tabaco, 'obesidad': obesos,
    }


def _metricas_tratamiento(pacientes: list[Paciente]) -> dict:
    trat_c = Counter()
    via_cl_si = 0
    via_cl_con_dato = 0

    for p in pacientes:
        ult_trat = _ultimo(p.tratamiento_actual)
        if ult_trat:
            # ── LECTURA EXCLUSIVA DEL ESQUEMA JSON ──
            esquema = ult_trat.esquema_json or []
            
            if isinstance(esquema, list) and len(esquema) > 0:
                for item in esquema:
                    nombre_farmaco = item.get("tratamiento", "").strip()
                    if nombre_farmaco:
                        trat_c[nombre_farmaco] += 1
            else:
                trat_c['No registrado'] += 1
            # ────────────────────────────────────────

            if ult_trat.sigue_via_clinica is not None:
                via_cl_con_dato += 1
                sv = str(ult_trat.sigue_via_clinica).lower()
                if 'si' in sv or sv == 'true' or sv == '1':
                    via_cl_si += 1
        else:
            trat_c['No registrado'] += 1

    return {
        'total': len(pacientes),
        'distribucion': dict(trat_c.most_common(10)),
        'via_cl_con_dato': via_cl_con_dato,
        'via_cl_si': via_cl_si,
    }

def _metricas_educacion(pacientes: list[Paciente]) -> dict:
    nivel_c = Counter()
    con_edu = 0

    for p in pacientes:
        ult_edu = _ultimo(p.resultado_educacion_diabetologica)
        if ult_edu:
            con_edu += 1
            nivel = str(ult_edu.final or ult_edu.inicio or 'Sin nivel').strip()
            nivel_c[nivel] += 1

    return {
        'total': len(pacientes),
        'con_edu': con_edu,
        'niveles': dict(nivel_c.most_common()),
    }


def _metricas_cobertura(pacientes: list[Paciente],
                         fi: date | None, ff: date | None) -> dict:
    """Cobertura de evaluaciones especializadas en el período."""
    total = len(pacientes)
    con_oft = con_nef = con_pod = con_comp = con_ef = 0

    for p in pacientes:
        if _en_periodo(p.oftalmologia, fi, ff):
            con_oft += 1
        if _en_periodo(p.nefrologia, fi, ff):
            con_nef += 1
        if _en_periodo(p.examen_miembros_inferiores, fi, ff):
            con_pod += 1
        if _en_periodo(p.complementarios, fi, ff):
            con_comp += 1
        if _en_periodo(p.examen_fisico, fi, ff):
            con_ef += 1

    return {
        'total': total,
        'oftalmologia': con_oft,
        'nefrologia':   con_nef,
        'podologia':    con_pod,
        'laboratorio':  con_comp,
        'examen_fisico': con_ef,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERADORES DE SECCIONES MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════════

def _sec_resumen_ejecutivo(total: int, nuevos: int, filtros: dict,
                            fi: date | None, ff: date | None) -> str:
    periodo_str = "Todo el período disponible"
    if fi and ff:
        periodo_str = f"{fi.strftime('%d/%m/%Y')} al {ff.strftime('%d/%m/%Y')}"
    elif fi:
        periodo_str = f"Desde {fi.strftime('%d/%m/%Y')}"
    elif ff:
        periodo_str = f"Hasta {ff.strftime('%d/%m/%Y')}"

    areas = filtros.get('areas', [])
    muns  = filtros.get('municipios', [])
    tipo  = filtros.get('tipo_dm') or 'Todos'
    est   = filtros.get('estado') or 'Todos'

    filtros_str = []
    if areas:
        filtros_str.append(f"Áreas: {', '.join(areas)}")
    if muns:
        filtros_str.append(f"Municipios: {', '.join(muns)}")
    if filtros.get('tipo_dm'):
        filtros_str.append(f"Tipo DM: {tipo}")
    if filtros.get('estado'):
        filtros_str.append(f"Estado: {est}")
    filtros_aplicados = " | ".join(filtros_str) if filtros_str else "Sin filtros adicionales"

    md  = "## Resumen Ejecutivo\n\n"
    md += _tabla_md(
        ["Indicador", "Valor"],
        [
            ["Período analizado", periodo_str],
            ["Total de pacientes analizados", f"**{total}**"],
            ["Pacientes nuevos en el período", f"{nuevos} ({_pct(nuevos, total)})"],
            ["Filtros aplicados", filtros_aplicados],
            ["Fecha de generación", datetime.now().strftime('%d/%m/%Y %H:%M')],
        ]
    )
    return md


def _sec_demografia(dem: dict) -> str:
    total = dem['total']
    md  = "## 1. Perfil Demográfico\n\n"

    # Sexo
    md += "### Distribución por Sexo\n\n"
    filas_sexo = [
        [k, v, _pct(v, total)]
        for k, v in sorted(dem['sexo'].items())
    ]
    md += _tabla_md(["Sexo", "N", "%"], filas_sexo)

    # Edad
    md += "\n\n### Distribución por Grupos de Edad\n\n"
    orden_edad = ['<18 años', '18–39 años', '40–59 años', '60–74 años', '≥75 años', 'No disponible']
    filas_edad = []
    for k in orden_edad:
        v = dem['edad'].get(k, 0)
        if v:
            filas_edad.append([k, v, _pct(v, total)])
    md += _tabla_md(["Grupo edad", "N", "%"], filas_edad)

    # Área
    md += "\n\n### Por Área de Salud\n\n"
    filas_area = [[k, v, _pct(v, total)] for k, v in dem['areas'].items()]
    md += _tabla_md(["Área de salud", "N", "%"], filas_area)

    # Municipio
    md += "\n\n### Por Municipio\n\n"
    filas_mun = [[k, v, _pct(v, total)] for k, v in dem['municipios'].items()]
    md += _tabla_md(["Municipio", "N", "%"], filas_mun)

    return md


def _sec_evolucion_dm(ev: dict, total: int) -> str:
    md  = "## 2. Tipo y Evolución de la Diabetes\n\n"

    md += "### Tipo de Diabetes Mellitus\n\n"
    filas_tipo = [[k, v, _pct(v, total)] for k, v in ev['tipos'].items()]
    md += _tabla_md(["Tipo DM", "N", "%"], filas_tipo)

    md += "\n\n### Tiempo de Evolución\n\n"
    orden = ['<1 año', '1–4 años', '5–9 años', '10–19 años', '≥20 años']
    filas_ev = []
    for k in orden:
        v = ev['grupos'].get(k, 0)
        filas_ev.append([k, v, _pct(v, total)])
    md += _tabla_md(["Tiempo evolución", "N", "%"], filas_ev)

    return md


def _sec_control_metabolico(met: dict) -> str:
    total = met['total']
    cd    = met['con_dato']
    md  = "## 3. Control Glucémico\n\n"
    md += f"> Datos disponibles en **{cd}** de {total} pacientes ({_pct(cd, total)})\n\n"

    if cd == 0:
        md += "> Sin registros de glucemia en el período.\n"
        return md

    filas = [
        ["Controlado (< 7.0 mmol/L)",      met['controlados'],    _pct(met['controlados'], cd)],
        ["Límite (7.0 – 9.9 mmol/L)",      met['limite'],         _pct(met['limite'], cd)],
        ["Descompensado (≥ 10.0 mmol/L)",  met['descompensados'], _pct(met['descompensados'], cd)],
    ]
    md += _tabla_md(["Control glucémico", "N", "%"], filas)

    prom = met.get('promedio')
    if prom:
        md += f"\n\n> **Glucemia promedio del grupo:** {prom} mmol/L  \n"
        md += f"> Objetivo terapéutico: < 7.0 mmol/L\n"

    return md


def _sec_lipidos(lip: dict) -> str:
    md  = "## 4. Perfil Lipídico\n\n"

    if lip['con_col'] == 0 and lip['con_tg'] == 0:
        md += "> Sin registros de lípidos en el período.\n"
        return md

    # Colesterol
    cd = lip['con_col']
    if cd:
        md += f"### Colesterol Total — {cd} pacientes con dato\n\n"
        filas = [
            ["En objetivo (< 5.2 mmol/L)",  lip['col_ok'],   _pct(lip['col_ok'], cd)],
            ["Límite (5.2–6.2 mmol/L)",     lip['col_lim'],  _pct(lip['col_lim'], cd)],
            ["Elevado (> 6.2 mmol/L)",      lip['col_alto'], _pct(lip['col_alto'], cd)],
        ]
        md += _tabla_md(["Categoría", "N", "%"], filas)
        if lip['col_prom']:
            md += f"\n> **Promedio:** {lip['col_prom']} mmol/L\n"

    # Triglicéridos
    cd = lip['con_tg']
    if cd:
        md += f"\n\n### Triglicéridos — {cd} pacientes con dato\n\n"
        filas = [
            ["Normal (< 1.7 mmol/L)",   lip['tg_ok'],  _pct(lip['tg_ok'], cd)],
            ["Elevado (≥ 1.7 mmol/L)",  lip['tg_alt'], _pct(lip['tg_alt'], cd)],
        ]
        md += _tabla_md(["Categoría", "N", "%"], filas)
        if lip['tg_prom']:
            md += f"\n> **Promedio:** {lip['tg_prom']} mmol/L\n"

    # HDL-C
    cd = lip['con_hdl']
    if cd:
        md += f"\n\n### HDL-C — {cd} pacientes con dato\n\n"
        filas = [
            ["En objetivo (♀>1.3 / ♂>1.0)", lip['hdl_ok'],   _pct(lip['hdl_ok'], cd)],
            ["Bajo",                          lip['hdl_bajo'], _pct(lip['hdl_bajo'], cd)],
        ]
        md += _tabla_md(["Categoría", "N", "%"], filas)

    return md


def _sec_tension_arterial(ta: dict) -> str:
    cd    = ta['con_dato']
    md  = "## 5. Presión Arterial\n\n"
    md += f"> Datos disponibles en **{cd}** pacientes\n\n"

    if cd == 0:
        md += "> Sin registros de tensión arterial en el período.\n"
        return md

    filas = [
        ["Controlada (< 130/80 mmHg)",    ta['controlada'], _pct(ta['controlada'], cd)],
        ["Límite (130-139/80-89 mmHg)",   ta['limite'],     _pct(ta['limite'], cd)],
        ["HTA Grado 1 (140-159/90-99)",   ta['hta_g1'],     _pct(ta['hta_g1'], cd)],
        ["HTA Grado 2 (≥160/≥100 mmHg)", ta['hta_g2'],     _pct(ta['hta_g2'], cd)],
    ]
    md += _tabla_md(["Categoría TA", "N", "%"], filas)

    if ta.get('sist_prom') and ta.get('diast_prom'):
        md += f"\n\n> **TA promedio del grupo:** {ta['sist_prom']}/{ta['diast_prom']} mmHg\n"

    return md


def _sec_complicaciones(comp: dict) -> str:
    total = comp['total']
    md  = "## 6. Complicaciones Crónicas de la DM\n\n"

    # Retinopatía
    md += "### Retinopatía Diabética\n\n"
    md += f"> Evaluaciones oftalmológicas registradas: {comp['con_oftalmo']} de {total} ({_pct(comp['con_oftalmo'], total)})\n\n"
    filas = [
        ["Sin retinopatía",          comp['ret_sin'],    _pct(comp['ret_sin'], total)],
        ["Ret. no proliferativa",    comp['ret_no_prol'],_pct(comp['ret_no_prol'], total)],
        ["Ret. proliferativa",       comp['ret_prol'],   _pct(comp['ret_prol'], total)],
    ]
    md += _tabla_md(["Categoría", "N", "% del total"], filas)

    # Nefropatía
    md += "\n\n### Nefropatía / Enfermedad Renal\n\n"
    md += f"> Evaluaciones nefrológicas registradas: {comp['con_nefro']} de {total} ({_pct(comp['con_nefro'], total)})\n\n"
    filas = [
        ["Sano (Sin daño renal)",                comp['nefro_sano'],   _pct(comp['nefro_sano'],   total)],
        ["Enfermedad Renal Diabética",            comp['nefro_dm'],     _pct(comp['nefro_dm'],     total)],
        ["Enfermedad Renal Crónica NO Diabética", comp['nefro_no_dm'], _pct(comp['nefro_no_dm'], total)],
    ]
    md += _tabla_md(["Categoría", "N", "% del total"], filas)

    # Pie diabético
    md += "\n\n### Estratificación de Riesgo de Pie Diabético\n\n"
    md += f"> Evaluaciones podológicas registradas: {comp['con_podologia']} de {total} ({_pct(comp['con_podologia'], total)})\n\n"
    filas = [
        ["Grado 0 — Sin riesgo",           comp['pie_g0'], _pct(comp['pie_g0'], total)],
        ["Grado 1 — Riesgo bajo",          comp['pie_g1'], _pct(comp['pie_g1'], total)],
        ["Grado 2 — Riesgo moderado",      comp['pie_g2'], _pct(comp['pie_g2'], total)],
        ["Grado 3 — Riesgo alto / lesión", comp['pie_g3'], _pct(comp['pie_g3'], total)],
        ["Sin clasificar",                 comp['pie_sin'],_pct(comp['pie_sin'], total)],
    ]
    md += _tabla_md(["Categoría", "N", "% del total"], filas)

    md += f"\n\n> LOPS positivo: {comp['lops_si']} pacientes ({_pct(comp['lops_si'], total)})\n"
    md += f"> EAP confirmada: {comp['eap_si']} pacientes ({_pct(comp['eap_si'], total)})\n"

    return md


def _sec_comorbilidades(com: dict) -> str:
    total = com['total']
    md  = "## 7. Comorbilidades\n\n"

    filas = [
        ["Hipertensión arterial",    com['hta'],         _pct(com['hta'], total)],
        ["Obesidad (IMC ≥ 30)",      com['obesidad'],    _pct(com['obesidad'], total)],
        ["Dislipidemia",             com['dislipidemia'],_pct(com['dislipidemia'], total)],
        ["Tabaquismo activo",        com['tabaquismo'],  _pct(com['tabaquismo'], total)],
    ]
    md += _tabla_md(["Comorbilidad", "N", "%"], filas)

    return md


def _sec_nutricional(nut: dict) -> str:
    cd    = nut['con_dato']
    total = nut.get('total', cd)
    md  = "## 8. Evaluación Nutricional\n\n"
    md += f"> Mensuraciones disponibles: **{cd}** pacientes ({_pct(cd, total)})\n\n"

    if cd == 0:
        md += "> Sin registros de mensuraciones en el período.\n"
        return md

    filas = [
        ["Bajo peso (IMC < 18.5)",         nut['bajo'],      _pct(nut['bajo'], cd)],
        ["Normopeso (18.5–24.9)",           nut['normal'],    _pct(nut['normal'], cd)],
        ["Sobrepeso (25–29.9)",             nut['sobrepeso'], _pct(nut['sobrepeso'], cd)],
        ["Obesidad Grado 1 (30–34.9)",      nut['ob1'],       _pct(nut['ob1'], cd)],
        ["Obesidad Grado 2 (35–39.9)",      nut['ob2'],       _pct(nut['ob2'], cd)],
        ["Obesidad Grado 3 / Mórbida (≥40)",nut['ob3'],       _pct(nut['ob3'], cd)],
    ]
    md += _tabla_md(["Categoría IMC", "N", "%"], filas)

    prom_imc  = nut.get('imc_prom')
    prom_peso = nut.get('peso_prom')
    if prom_imc:
        md += f"\n\n> **IMC promedio:** {prom_imc}  \n"
    if prom_peso:
        md += f"> **Peso promedio:** {prom_peso} kg\n"

    return md


def _sec_tratamiento(trat: dict) -> str:
    total = trat['total']
    md  = "## 9. Tratamiento Actual\n\n"

    # Automáticamente pintará los medicamentos sacados del JSON
    filas = [[k, v, _pct(v, total)] for k, v in trat['distribucion'].items()]
    md += _tabla_md(["Tratamiento", "N", "%"], filas)

    # Vía clínica
    vcd = trat['via_cl_con_dato']
    if vcd:
        md += f"\n\n### Adherencia a Vía Clínica\n\n"
        md += f"> De {vcd} pacientes con dato registrado:\n\n"
        md += f"- Sigue vía clínica: **{trat['via_cl_si']}** ({_pct(trat['via_cl_si'], vcd)})\n"
        md += f"- No sigue vía clínica: **{vcd - trat['via_cl_si']}** ({_pct(vcd - trat['via_cl_si'], vcd)})\n"

  
    return md


def _sec_cobertura(cob: dict) -> str:
    total = cob['total']
    md  = "## 10. Cobertura de Evaluaciones Especializadas\n\n"
    md += f"> Cobertura de atención en el período analizado (N={total})\n\n"

    filas = [
        ["Laboratorio (Complementarios)", cob['laboratorio'],  _pct(cob['laboratorio'], total)],
        ["Examen Físico",                 cob['examen_fisico'],_pct(cob['examen_fisico'], total)],
        ["Oftalmología",                  cob['oftalmologia'], _pct(cob['oftalmologia'], total)],
        ["Podología / Miembros Inf.",     cob['podologia'],    _pct(cob['podologia'], total)],
        ["Nefrología",                    cob['nefrologia'],   _pct(cob['nefrologia'], total)],
    ]
    md += _tabla_md(["Evaluación", "N", "%"], filas)
    md += "\n\n> Una cobertura < 80% indica déficit de seguimiento en esa especialidad.\n"

    return md


def _sec_educacion(edu: dict) -> str:
    total    = edu['total']
    con_edu  = edu['con_edu']
    sin_edu  = total - con_edu
    md  = "## 11. Educación Diabetológica\n\n"
    md += f"> Pacientes con registro de educación: **{con_edu}** ({_pct(con_edu, total)})  \n"
    md += f"> Pacientes sin registro: **{sin_edu}** ({_pct(sin_edu, total)})\n\n"

    if edu['niveles']:
        filas = [[k, v, _pct(v, con_edu)] for k, v in edu['niveles'].items()]
        md += "### Nivel Educativo Final Registrado\n\n"
        md += _tabla_md(["Nivel", "N", "% con registro"], filas)

    return md


def _sec_conclusiones(
    met: dict, lip: dict, ta: dict, comp: dict,
    com: dict, nut: dict, trat: dict, cob: dict, total: int
) -> str:
    alertas    = []
    favorables = []
    recomend   = []

    # Control glucémico
    cd = met['con_dato']
    if cd:
        pct_control = met['controlados'] / cd * 100
        pct_descomp = met['descompensados'] / cd * 100
        if pct_descomp >= 20:
            alertas.append(f"{round(pct_descomp, 1)}% de los pacientes con glucemia ≥ 10 mmol/L (descompensados)")
            recomend.append("Revisión de esquemas terapéuticos en pacientes descompensados")
        elif pct_control >= 70:
            favorables.append(f"{round(pct_control, 1)}% de los pacientes con glucemia controlada (< 7.0 mmol/L)")

    # Tensión arterial
    cdt = ta['con_dato']
    if cdt:
        pct_ta = (ta['hta_g1'] + ta['hta_g2']) / cdt * 100
        if pct_ta >= 30:
            alertas.append(f"{round(pct_ta, 1)}% con HTA no controlada (Grado 1 o 2)")
            recomend.append("Reforzar tratamiento antihipertensivo y monitorización tensional")

    # Complicaciones: pie
    if comp['pie_g2'] + comp['pie_g3'] > 0:
        n = comp['pie_g2'] + comp['pie_g3']
        alertas.append(f"{n} pacientes con pie de riesgo Grado 2–3 (riesgo alto de amputación)")
        recomend.append("Priorizar atención podológica preventiva y vascular en pacientes de alto riesgo")

    # Retinopatía proliferativa
    if comp['ret_prol'] > 0:
        alertas.append(f"{comp['ret_prol']} pacientes con retinopatía diabética proliferativa")
        recomend.append("Derivación urgente a oftalmología para tratamiento de retinopatía proliferativa")

    # Nefropatía diabética
    if comp['nefro_dm'] > 0:
        pct_nefro = comp['nefro_dm'] / total * 100
        alertas.append(f"{comp['nefro_dm']} pacientes ({round(pct_nefro, 1)}%) con Enfermedad Renal Diabética confirmada")
        recomend.append("Intensificar nefroprotección y seguimiento nefrológico en pacientes con enfermedad renal diabética")
    if comp['nefro_no_dm'] > 0:
        alertas.append(f"{comp['nefro_no_dm']} pacientes con Enfermedad Renal Crónica NO Diabética — requieren evaluación de causa primaria")

    # Cobertura
    for nombre, clave in [("oftalmología", 'oftalmologia'), ("nefrología", 'nefrologia'), ("podología", 'podologia')]:
        pct_cob = cob[clave] / total * 100 if total else 0
        if pct_cob < 60:
            alertas.append(f"Baja cobertura de {nombre}: {round(pct_cob, 1)}%")
            recomend.append(f"Incrementar la captación de pacientes para evaluación de {nombre}")

    # Obesidad
    if nut['con_dato']:
        pct_ob = nut['obesos'] / nut['con_dato'] * 100
        if pct_ob >= 50:
            alertas.append(f"{round(pct_ob, 1)}% de los pacientes presenta obesidad (IMC ≥ 30)")
            recomend.append("Intensificar programa de reducción de peso y consejería nutricional")

    # Tabaquismo
    if total:
        pct_tab = com['tabaquismo'] / total * 100
        if pct_tab >= 15:
            alertas.append(f"{round(pct_tab, 1)}% de tabaquismo activo en la cohorte")
            recomend.append("Implementar o fortalecer programa de cesación tabáquica")

    
    md  = "## 12. Conclusiones y Alertas del Período\n\n"

    if alertas:
        md += "### Alertas Identificadas\n\n"
        for a in alertas:
            md += f"- {a}\n"

    if favorables:
        md += "\n### Aspectos Favorables\n\n"
        for f in favorables:
            md += f"- {f}\n"

    if recomend:
        md += "\n### Recomendaciones\n\n"
        for i, r in enumerate(recomend, 1):
            md += f"{i}. {r}\n"

    if not alertas and not recomend:
        md += "> Los indicadores globales de la cohorte se encuentran dentro de rangos aceptables.\n"

    return md


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def generar_informe_admin(
    filtros: dict,
    medico: dict | None = None,
) -> tuple[str, int]:
    """
    Genera el informe administrativo completo en Markdown.

    Args:
        filtros: dict con keys:
            fecha_inicio, fecha_fin: date | None
            areas:       list[str]
            municipios:  list[str]
            tipo_dm:     str | None
            estado:      str | None
        medico: dict opcional con nombre, especialidad, no_registro

    Returns:
        (markdown_str, total_pacientes)
    """
    db = Session()
    try:
        pacientes = _consultar_pacientes(filtros, db)
        total     = len(pacientes)

        if total == 0:
            return "", 0

        fi = filtros.get('fecha_inicio')
        ff = filtros.get('fecha_fin')

        institucion = "Centro de Atención al Diabético"
        if pacientes and pacientes[0].institucion:
            institucion = pacientes[0].institucion.nombre

        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')

        # Calcular todas las métricas
        dem  = _metricas_demografia(pacientes, fi, ff)
        ev   = _metricas_evolucion_dm(pacientes)
        met  = _metricas_control_metabolico(pacientes, fi, ff)
        lip  = _metricas_lipidos(pacientes, fi, ff)
        ta   = _metricas_tension_arterial(pacientes, fi, ff)
        nut  = _metricas_nutricionales(pacientes, fi, ff)
        nut['total'] = total
        comp = _metricas_complicaciones(pacientes)
        com  = _metricas_comorbilidades(pacientes, fi, ff)
        trat = _metricas_tratamiento(pacientes)
        edu  = _metricas_educacion(pacientes)
        cob  = _metricas_cobertura(pacientes, fi, ff)

        # Encabezado
        periodo_str = "Todo el período disponible"
        if fi and ff:
            periodo_str = f"{fi.strftime('%d/%m/%Y')} — {ff.strftime('%d/%m/%Y')}"
        elif fi:
            periodo_str = f"Desde {fi.strftime('%d/%m/%Y')}"
        elif ff:
            periodo_str = f"Hasta {ff.strftime('%d/%m/%Y')}"

        partes = [
            "# INFORME ADMINISTRATIVO — ESTADÍSTICAS DE COHORTE",
            f"**Institución:** {institucion}  ",
            f"**Período:** {periodo_str}  ",
            f"**Total pacientes analizados:** {total}  ",
            f"**Fecha de generación:** {fecha_gen}  ",
        ]
        if medico and medico.get('nombre'):
            partes.append(f"**Elaborado por:** {medico['nombre']}  ")

        partes.append("---")

        # Secciones
        partes.append(_sec_resumen_ejecutivo(total, dem['nuevos'], filtros, fi, ff))
        partes.append(_sec_demografia(dem))
        partes.append(_sec_evolucion_dm(ev, total))
        partes.append(_sec_control_metabolico(met))
        partes.append(_sec_lipidos(lip))
        partes.append(_sec_tension_arterial(ta))
        partes.append(_sec_complicaciones(comp))
        partes.append(_sec_comorbilidades(com))
        partes.append(_sec_nutricional(nut))
        partes.append(_sec_tratamiento(trat))
        partes.append(_sec_cobertura(cob))
        partes.append(_sec_educacion(edu))
        partes.append(_sec_conclusiones(met, lip, ta, comp, com, nut, trat, cob, total))

        partes.append("\n---")
        partes.append(
            f"*Informe generado el {fecha_gen} | {institucion} | "
            f"Sistema de Gestión de Diabetes*"
        )

        md = "\n\n".join(partes)
        return md, total

    except Exception as exc:
        print(f"[ERROR generar_informe_admin] {exc}")
        import traceback
        traceback.print_exc()
        return "", 0
    finally:
        db.close()