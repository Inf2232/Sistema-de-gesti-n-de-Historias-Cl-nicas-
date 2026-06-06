from models import *
def generar_resumen_clinico_offline(paciente_no_hc):
    session = Session()

    paciente = session.query(Paciente).filter(Paciente.no_hc == paciente_no_hc).first()
    if not paciente:
        return "ERROR: Paciente no encontrado en la base de datos."

    # Registros más recientes
    ultima_mensuracion = next(iter(sorted(paciente.mensuraciones, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultima_nefrologia = next(iter(sorted(paciente.nefrologia, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultima_oftalmologia = next(iter(sorted(paciente.oftalmologia, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultima_cardiologia = next(iter(sorted(paciente.cardiologia, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultimo_examen_pies = next(iter(sorted(paciente.examen_miembros_inferiores, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultimo_examen_fisico = next(iter(sorted(paciente.examen_fisico, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultima_historia_obst = next(iter(sorted(paciente.historia_obstetrica, key=lambda x: x.fecha_registro, reverse=True)), None)
    ultima_educacion = next(iter(sorted(paciente.resultado_educacion_diabetologica, key=lambda x: x.fecha_registro, reverse=True)), None)

    hallazgos_criticos, acciones_prioritarias = [], []

    # 1. Evaluación antropométrica
    if ultima_mensuracion:
        imc = ultima_mensuracion.IMC
        clasificacion_imc = ultima_mensuracion.clasificar_imc[1]
        icc = ultima_mensuracion.ICC if ultima_mensuracion.cintura and ultima_mensuracion.cadera else None
        ica = ultima_mensuracion.ICaltura if ultima_mensuracion.talla and ultima_mensuracion.cintura else None
        pi = ultima_mensuracion.PI

        if "Obesidad" in clasificacion_imc:
            hallazgos_criticos.append(f"Obesidad ({clasificacion_imc}, IMC: {imc})")
            acciones_prioritarias.append("Intervención nutricional intensiva y reevaluación farmacológica")

    # 2. Riesgo CV
    if ultima_cardiologia and ultima_cardiologia.riesgo_oms is not None:
        riesgo = ultima_cardiologia.riesgo_oms
        if riesgo >= 20:
            hallazgos_criticos.append(f"Riesgo cardiovascular MUY ALTO ({riesgo}%)")
            acciones_prioritarias.append("Optimizar antihipertensivos, estatinas altas y evaluación cardiológica urgente")
        elif riesgo >= 10:
            hallazgos_criticos.append(f"Riesgo cardiovascular ALTO ({riesgo}%)")
            acciones_prioritarias.append("Ajustar estatinas y antihipertensivos; valorar aspirina")

    # 3. Función renal
    if ultima_nefrologia:
        fg = ultima_nefrologia.filtrado_glomerular_teorico
        clasif = ultima_nefrologia.clasificacion
        proteinuria = ultima_nefrologia.proteinuria_valor
        if any(stage in clasif for stage in ["G3B", "G4", "G5"]):
            desc = f"ERC estadio {clasif} (FG {fg} ml/min/1.73m²)"
            if proteinuria:
                desc += f", proteinuria {proteinuria} mg/dL"
            hallazgos_criticos.append(desc)
            acciones_prioritarias.append("Evitar nefrotóxicos y derivar a nefrología si G4-G5")

    # 4. Retinopatía
    if ultima_oftalmologia:
        rd = str(ultima_oftalmologia.retinopatia_diabetica).lower()
        if "proliferativa" in rd:
            hallazgos_criticos.append("Retinopatía diabética proliferativa")
            acciones_prioritarias.append("Derivación urgente a oftalmología")
        elif "no proliferativa" in rd:
            hallazgos_criticos.append("Retinopatía diabética no proliferativa")
            acciones_prioritarias.append("Control glucémico estricto y seguimiento oftalmológico")

    # 5. Examen de pies
    if ultimo_examen_pies:
        if ultimo_examen_pies.LOPS_derecho == "si" or ultimo_examen_pies.LOPS_izquierdo == "si":
            hallazgos_criticos.append("Neuropatía periférica (LOPS+)")
            acciones_prioritarias.append("Evaluación podológica + educación en autocuidado")

        if ultimo_examen_pies.ITB_derecho and ultimo_examen_pies.ITB_derecho < 0.9:
            hallazgos_criticos.append(f"Isquemia periférica derecha (ITB {ultimo_examen_pies.ITB_derecho:.2f})")
        if ultimo_examen_pies.ITB_izquierdo and ultimo_examen_pies.ITB_izquierdo < 0.9:
            hallazgos_criticos.append(f"Isquemia periférica izquierda (ITB {ultimo_examen_pies.ITB_izquierdo:.2f})")

    # 6. Examen físico
    if ultimo_examen_fisico:
        if ultimo_examen_fisico.sistolica and ultimo_examen_fisico.sistolica >= 140:
            hallazgos_criticos.append(f"Hipertensión arterial (TA {ultimo_examen_fisico.sistolica}/{ultimo_examen_fisico.diastolica})")

    # 7. Historia obstétrica (si mujer)
    if paciente.sexo.lower().startswith("f") and ultima_historia_obst:
        if ultima_historia_obst.fecha_diabetes_gestacionaria:
            hallazgos_criticos.append("Antecedente de diabetes gestacional")
        if ultima_historia_obst.macrofetos == "si":
            hallazgos_criticos.append("Antecedente de macrosomía fetal")

    # 8. Hábitos tóxicos
    if paciente.habitos_toxicos:
        ht = paciente.habitos_toxicos[-1]
        if ht.fuma == "si":
            hallazgos_criticos.append("Tabaquismo activo")
            acciones_prioritarias.append("Consejería intensiva para cesación tabáquica")
        if ht.consumo_excesivo_alcohol == "si":
            hallazgos_criticos.append("Consumo excesivo de alcohol")

    # 9. Educación diabetológica
    if ultima_educacion and ultima_educacion.estado:
        mantiene = ultima_educacion.estado[-1].mantiene_educacion
        if not mantiene:
            hallazgos_criticos.append("Pérdida de adherencia a educación diabetológica")
            acciones_prioritarias.append("Refuerzo inmediato en educación terapéutica")

    # 10. Antecedentes personales graves
    antecedentes_graves = []
    for antecedente in paciente.antecedentes_personales:
        antecedentes_graves += [p.tipo_patologia for p in antecedente.patologias]
    if antecedentes_graves:
        hallazgos_criticos.append(f"Antecedentes relevantes: {', '.join(antecedentes_graves)}")

    # Construcción del resumen
    nombre = f"{paciente.nombres} {paciente.apellidos}"
    resumen = (
        f"🔹 RESUMEN CLÍNICO AUTOMÁTICO\n"
        f"Paciente: {nombre} | Edad: {paciente.edad_actual} | HC: {paciente.no_hc}\n"
        f"Sexo: {paciente.sexo} | Raza: {paciente.raza} | Ocupación: {paciente.ocupacion}\n"
        f"Estado actual: {paciente.estado_actual_automatico} | Evolución: {paciente.tiempo_evolucion}\n"
        f"------------------------------------------------------------\n"
    )

    if hallazgos_criticos:
        resumen += "⚠️ HALLAZGOS CRÍTICOS:\n"
        for i, h in enumerate(hallazgos_criticos, 1):
            resumen += f"   {i}. {h}\n"
    else:
        resumen += "✅ Sin hallazgos críticos en última evaluación.\n"

    resumen += "------------------------------------------------------------\n"

    # Tratamiento
    tto = [t.tratamiento for t in paciente.tratamiento_actual]
    if tto:
        resumen += f"💊 TRATAMIENTO ACTUAL: {', '.join(tto)}\n"
    else:
        resumen += "💊 TRATAMIENTO ACTUAL: No registrado.\n"

    # Acciones
    if acciones_prioritarias:
        resumen += "📌 ACCIONES PRIORITARIAS:\n"
        for i, a in enumerate(acciones_prioritarias[:3], 1):
            resumen += f"   {i}. {a}\n"

    resumen += "------------------------------------------------------------\n"
    resumen += f"📅 Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    resumen += "ℹ️ Validar con historia clínica completa."

    return resumen
