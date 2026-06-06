from docxtpl import DocxTemplate
from nicegui import ui
import os
from datetime import datetime
from models import Session, Paciente
import tempfile
from Errores import log_error_and_notify


class ExportadorHistoriaClinica:
    def __init__(self):
        self.session = Session()
        self.template_path = os.path.join(os.path.dirname(__file__), 'plantillas_informe', 'HISTORIA CLINICA DEFINITIVA.docx')
        
    def obtener_datos_paciente(self, no_hc):
        """Obtiene solo los datos básicos del paciente para la plantilla"""
        paciente = self.session.query(Paciente).filter(Paciente.no_hc == no_hc).first()
        if not paciente:
            return None       

        #App        
        patologias_set = set()

        if paciente.antecedentes_personales:
            for antecedente in paciente.antecedentes_personales:
                for patologia_personal in getattr(antecedente, 'patologias', []):
                    patologias_set.add((
                        getattr(patologia_personal, 'tipo_patologia', ''),
                        getattr(patologia_personal, 'tiempo_anios', ''),
                        getattr(patologia_personal, 'tiempo_meses', '')
                    ))
        #convertir el contjuto en lista xq jinja no lo esta leyendo bien 
        patologias_app_list = [
            {
                "tipo_patologia": tipo,
                "tiempo_anios": anios,
                "tiempo_meses": meses
            }
            for tipo, anios, meses in patologias_set
        ] if patologias_set else []
 
        #apf
        patologias_apf_set = set()

        if paciente.antecedentes_familiares:
            for antecedente in paciente.antecedentes_familiares:
                for patologia in getattr(antecedente, 'patologias', []):
                    patologias_apf_set.add((
                        getattr(patologia, 'tipo_patologia', ''),
                    ))
        #convertir el contjuto en lista xq jinja no lo esta leyendo bien 
        patologias_apf_list = [
            {
                "tipo_patologia": tipo,
            }
            for tipo in patologias_apf_set
        ] if patologias_apf_set else []

        #apf Diabetes
        grados_parentezco_set = set()

        if paciente.antecedentes_familiares_diabetes:
            for antecedente in paciente.antecedentes_familiares_diabetes:
                for grados_parentezco in getattr(antecedente, 'grados_parentezco', []):
                    grados_parentezco_set.add((
                        getattr(grados_parentezco, 'grado', ''),
                    ))
        #convertir el contjuto en lista xq jinja no lo esta leyendo bien 
        grados_parentezco_list = [
            {
                "grado": grado,
            }
            for grado in grados_parentezco_set
        ] if grados_parentezco_set else []         

        #habitos toxicos 
        ultimo_habito = next(iter(sorted(paciente.habitos_toxicos, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.habitos_toxicos else None
        
        habitos_list = [
            {
                "fecha_registro": ultimo_habito.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_habito, 'fecha_registro', None) else '',
                "fuma": getattr(ultimo_habito, 'fuma', ''),
                "consumo_excesivo_alcohol": getattr(ultimo_habito, 'consumo_excesivo_alcohol', '')
            }
        ] if ultimo_habito else [] 

        #historias obstetricas
        ultimo_historia_obs = next(iter(sorted(paciente.historia_obstetrica, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.historia_obstetrica else None

        historia_obstetrica_list = [
            {
                "fecha_registro": ultimo_historia_obs.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_historia_obs, 'fecha_registro', None) else '',
                "gestaciones": getattr(ultimo_historia_obs, 'gestaciones', ''),
                "partos": getattr(ultimo_historia_obs, 'partos', ''),
                "abortos_espontaneos": getattr(ultimo_historia_obs, 'abortos_espontaneos', ''),
                "abortos_provocados": getattr(ultimo_historia_obs, 'abortos_provocados', ''),
                "abortos": getattr(ultimo_historia_obs, 'abortos', ''),
                "macrofetos": getattr(ultimo_historia_obs, 'macrofetos', ''),
                "malformaciones": getattr(ultimo_historia_obs, 'malformaciones', ''),
                "muertes_perinatales": getattr(ultimo_historia_obs, 'muertes_perinatales', ''),
                "anticoncepcion": getattr(ultimo_historia_obs, 'anticoncepcion', ''),
                "fecha_diabetes_gestacionaria": getattr(ultimo_historia_obs, 'fecha_diabetes_gestacionaria', '').strftime('%d/%m/%Y') if getattr(ultimo_historia_obs, 'fecha_diabetes_gestacionaria', None) else "",
                "edad_menopausia": getattr(ultimo_historia_obs, 'edad_menopausia', ''),
                "preeclampsia": getattr(ultimo_historia_obs, 'preeclampsia', ''),
                "tipo_menopausia": getattr(ultimo_historia_obs, 'tipo_menopausia', ''),
            }
        ] if ultimo_historia_obs else []

        #tratamiento actual
        ultimo_tratamiento = next(iter(sorted(paciente.tratamiento_actual, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.tratamiento_actual else None
        
        tratamiento_list = [
            {
                "fecha_registro": ultimo_tratamiento.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_tratamiento, 'fecha_registro', None) else '',
                "tratamiento": getattr(ultimo_tratamiento, 'tratamiento', ''),
                "dosis": getattr(ultimo_tratamiento, 'dosis', ''),
        }] if ultimo_tratamiento else [] 

        #otros tratamientos
        otros_tratamientos_set = set()

        if paciente.otros_tratamientos:
            for tratamiento in paciente.otros_tratamientos:
                otros_tratamientos_set.add((
                    getattr(tratamiento, 'tratamiento', ''),
                    getattr(tratamiento, 'dosis', ''),
                ))
        #convertir el contjuto en lista xq jinja no lo esta leyendo bien 
        otros_tratamientos_list = [
            {
                "tratamiento": tratamiento,
                "dosis": dosis,
            }
            for tratamiento, dosis in otros_tratamientos_set
        ] if otros_tratamientos_set else [] 

        #examen fisico
        ultimo_examen = next(iter(sorted(paciente.examen_fisico, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.examen_fisico else None
        
        ultimo_examen_list = [
            {
                "fecha_registro": ultimo_examen.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_examen, 'fecha_registro', None) else '',
                "bocio": getattr(ultimo_examen, 'bocio', ''),
                "sistolica": getattr(ultimo_examen, 'sistolica', ''),
                "diastolica": getattr(ultimo_examen, 'diastolica', ''),
                "acantosis_nigricans": getattr(ultimo_examen, 'acantosis_nigricans', ''),
        }] if ultimo_examen else [] 

        #mensuraciones
        ultima_mensuracion = next(iter(sorted(paciente.mensuraciones, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.mensuraciones else None
        
        ultima_mensuracion_list = [
            {
                "fecha_registro": ultima_mensuracion.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_mensuracion, 'fecha_registro', None) else '',
                "talla": getattr(ultima_mensuracion, 'talla', ''),
                "peso": getattr(ultima_mensuracion, 'peso', ''),
                "cintura": getattr(ultima_mensuracion, 'cintura', ''),
                "cadera": getattr(ultima_mensuracion, 'cadera', ''),
                "dieta": getattr(ultima_mensuracion, 'dieta', ''),
                "IMC": getattr(ultima_mensuracion, 'IMC', ''),
                "clasificar_imc": getattr(ultima_mensuracion, 'clasificar_imc', ''),
                "PI": getattr(ultima_mensuracion, 'PI', ''),
                "ICC": getattr(ultima_mensuracion, 'ICC', ''),
                "ICaltura": getattr(ultima_mensuracion, 'ICaltura', ''),
        }] if ultima_mensuracion else [] 

       # Complementarios
        ultimo_complementario = next(iter(sorted(paciente.complementarios,key=lambda x: getattr(x, 'fecha_registro', datetime.min),reverse=True)),None) 

        # Construir la lista de último examen complementario
        ultimo_complementario_list = []

        if ultimo_complementario:
            # Preparar los campos fijos
            examen_dict = {
                "fecha_registro": ultimo_complementario.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_complementario, 'fecha_registro', None) else '',
                "hb": getattr(ultimo_complementario, 'hb', 0),
                "hto": getattr(ultimo_complementario, 'hto', 0),
                "eritro": getattr(ultimo_complementario, 'eritro', 0),
                "glucemia": getattr(ultimo_complementario, 'glucemia', 0),
                "colesterol": getattr(ultimo_complementario, 'colesterol', 0),
                "trigliceridos": getattr(ultimo_complementario, 'trigliceridos', 0),
                "HDLC": getattr(ultimo_complementario, 'HDLC', 0),
                "TGO": getattr(ultimo_complementario, 'TGO', 0),
                "tgp": getattr(ultimo_complementario, 'tgp',0),
                "proteinas_totales": getattr(ultimo_complementario, 'proteinas_totales', 0),
                "albuminuria": getattr(ultimo_complementario, 'albuminuria', 0),
                "globulina": getattr(ultimo_complementario, 'globulina', 0),
                "calcio": getattr(ultimo_complementario, 'calcio', 0),
                "fosforo": getattr(ultimo_complementario, 'fosforo', 0),
                "conteo_plaquetas": getattr(ultimo_complementario, 'conteo_plaquetas', 0),
                "coagulacion": getattr(ultimo_complementario, 'coagulacion', 0),
                "sangramiento": getattr(ultimo_complementario, 'sangramiento', 0),
                "ultrasonido_abdominal": getattr(ultimo_complementario, 'ultrasonido_abdominal', ''),
                "prueba_conduccion_nerviosa_miembro_superior": getattr(ultimo_complementario, 'prueba_conduccion_nerviosa_miembro_superior', ''),
                "prueba_conduccion_nerviosa_miembro_inferior": getattr(ultimo_complementario, 'prueba_conduccion_nerviosa_miembro_inferior', ''),
            }

            examen_dict["otros_campos"] = []
            if ultimo_complementario.campos_personalizados:
                for campo in ultimo_complementario.campos_personalizados:
                    examen_dict["otros_campos"].append({
                        "nombre": campo.nombre,
                        "valor": campo.valor,
                        "unidad": campo.unidad if campo.unidad else ""
                    })

            # Añadir el examen completo a la lista
            ultimo_complementario_list.append(examen_dict)
        #educacion diabetologica
        ultima_educacion = next(iter(sorted(paciente.resultado_educacion_diabetologica, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.resultado_educacion_diabetologica else None
       
        ultima_educacion_list = [
            {
                "fecha_registro": ultima_educacion.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_educacion, 'fecha_registro', None) else '',
                "inicio": getattr(ultima_educacion, 'inicio', ''),
                "fin": getattr(ultima_educacion, 'final', ''),
        }] if ultima_educacion else [] 
       
        #examenes podologicos
        if paciente.examen_miembros_inferiores:
            ultimo_examen_podologico = next(iter(sorted(paciente.examen_miembros_inferiores, 
                                                        key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                        reverse=True)), None)
            
            if ultimo_examen_podologico:
                deformidades_izquierdo = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'defromidades_podalicas_izquierdo', []) or []]
                deformidades_derecho = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'defromidades_podalicas_derecho', []) or []]
                lesiones_dermatologicas_izquierdo = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'lesiones_dermatologicas_izquierdo', []) or []]
                lesiones_dermatologicas_derecho = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'lesiones_dermatologicas_derecho', []) or []]
                lesiones_uñas_derecho = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'lesiones_uñas_derecho', []) or []]
                lesiones_uñas_izquierdo = [enfermedad.padecimiento for enfermedad in getattr(ultimo_examen_podologico, 'lesiones_uñas_izquierdo', []) or []]

                podologico_list = [
                    {
                        "fecha_registro": ultimo_examen_podologico.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_examen_podologico, 'fecha_registro', None) else '',
                        "pu_fem_der": getattr(ultimo_examen_podologico, 'pulso_femoral_derecho', ''),
                        "pu_fem_izq": getattr(ultimo_examen_podologico, 'pulso_femoral_izquierdo', ''),
                        "pu_popl_izq": getattr(ultimo_examen_podologico, 'pulso_popliteo_izquierdo', ''),
                        "pu_popl_der": getattr(ultimo_examen_podologico, 'pulso_popliteo_derecho', ''),
                        "pu_tib_izq": getattr(ultimo_examen_podologico, 'pulso_tibial_posterior_izquierdo', ''),
                        "pu_tib_der": getattr(ultimo_examen_podologico, 'pulso_tibial_posterior_derecho', ''),
                        "pu_ped_der": getattr(ultimo_examen_podologico, 'pulso_pedeo_derecho', ''),
                        "pu_ped_izq": getattr(ultimo_examen_podologico, 'pulso_pedeo_izquierdo', ''),
                        "tib_der": getattr(ultimo_examen_podologico, 'tibial_derecho', ''),
                        "tib_izq": getattr(ultimo_examen_podologico, 'tibial_izquierdo', ''),
                        "ped_der": getattr(ultimo_examen_podologico, 'pedia_derecho', ''),
                        "ped_izq": getattr(ultimo_examen_podologico, 'pedia_izquierdo', ''),
                        "hum_der": getattr(ultimo_examen_podologico, 'humeral_derecho', ''),
                        "hum_izq": getattr(ultimo_examen_podologico, 'humeral_izquierdo', ''),
                        "ITB_der": getattr(ultimo_examen_podologico, 'ITB_derecho', 0),
                        "ITB_izq": getattr(ultimo_examen_podologico, 'ITB_izquierdo', 0),
                        "EAP_der": getattr(ultimo_examen_podologico, 'EAP_derecho', ''),
                        "EAP_izq": getattr(ultimo_examen_podologico, 'EAP_izquierdo', ''),
                        "tac_der": getattr(ultimo_examen_podologico, 'tactil_derecho', ''),
                        "tac_izq": getattr(ultimo_examen_podologico, 'tactil_izquierdo', ''),
                        "ter_der": getattr(ultimo_examen_podologico, 'termica_derecho', ''),
                        "ter_izq": getattr(ultimo_examen_podologico, 'termica_izquierdo', ''),
                        "dol_der": getattr(ultimo_examen_podologico, 'dolorosa_derecho', ''),
                        "dol_izq": getattr(ultimo_examen_podologico, 'dolorosa_izquierdo', ''),
                        "pal_der": getattr(ultimo_examen_podologico, 'palestesia_derecho', ''),
                        "pal_izq": getattr(ultimo_examen_podologico, 'palestesia_izquierdo', ''),
                        "pat_der": getattr(ultimo_examen_podologico, 'patelar_derecho', ''),
                        "pat_izq": getattr(ultimo_examen_podologico, 'patelar_izquierdo', ''),
                        "aqui_der": getattr(ultimo_examen_podologico, 'aquileano_derecho', ''),
                        "aqui_izq": getattr(ultimo_examen_podologico, 'aquileano_izquierdo', ''),
                        "LOPS_der": getattr(ultimo_examen_podologico, 'LOPS_derecho', ''),
                        "LOPS_izq": getattr(ultimo_examen_podologico, 'LOPS_izquierdo', ''),
                        "imp_diag": getattr(ultimo_examen_podologico, 'impresion_diagnostica', ''),
                        "deformidades_podalicas_izquierdo": deformidades_izquierdo or "",
                        "deformidades_podalicas_derecho": deformidades_derecho or "",
                        "lesiones_dermatologicas_izquierdo": lesiones_dermatologicas_izquierdo or "",
                        "lesiones_dermatologicas_derecho": lesiones_dermatologicas_derecho or "",
                        "lesiones_uñas_derecho": lesiones_uñas_derecho or "",
                        "lesiones_uñas_izquierdo": lesiones_uñas_izquierdo or "",
                    }
                ]
            else:
                podologico_list = []
        else:
            podologico_list = []

        #oftalmologia
        ultimo_oftalmologia = next(iter(sorted(paciente.oftalmologia, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.oftalmologia else None
       
        ultimo_oftalmologia_list = [
            {
                "fecha_registro": ultimo_oftalmologia.fecha_registro.strftime('%d/%m/%Y') if getattr(ultimo_oftalmologia, 'fecha_registro', None) else '',
                "reti_dia": getattr(ultimo_oftalmologia, 'retinopatia_diabetica', ''),
                "reti_hipe": getattr(ultimo_oftalmologia, 'retinopatia_hipertensiva', ''),
                "reti_art_escl": getattr(ultimo_oftalmologia, 'retinopatia_artereo_esclerosis', ''),
                "vis_borr_od": getattr(ultimo_oftalmologia, 'vision_borrosa_od', ''),
                "vis_borr_oi": getattr(ultimo_oftalmologia, 'vision_borrosa_oi', ''),
                "av_od": getattr(ultimo_oftalmologia, 'av_od', ''),
                "av_oi": getattr(ultimo_oftalmologia, 'av_oi', ''),
                "rd_od": getattr(ultimo_oftalmologia, 'rd_od', ''),
                "rd_oi": getattr(ultimo_oftalmologia, 'rd_oi', ''),
                "a_od": getattr(ultimo_oftalmologia, 'a_od', ''),
                "a_oi": getattr(ultimo_oftalmologia, 'a_oi', ''),
                "sa_od": getattr(ultimo_oftalmologia, 'sa_od', ''),
                "sa_oi": getattr(ultimo_oftalmologia, 'sa_oi', ''),
                "m_od": getattr(ultimo_oftalmologia, 'm_od', ''),
                "m_oi": getattr(ultimo_oftalmologia, 'm_oi', ''),
                "fo_od": getattr(ultimo_oftalmologia, 'fo_od', ''),
                "fo_oi": getattr(ultimo_oftalmologia, 'fo_oi', ''),
                "hem_vit_od": getattr(ultimo_oftalmologia, 'hemorragia_vitrea_od', ''),
                "hem_vit_oi": getattr(ultimo_oftalmologia, 'hemorragia_vitrea_oi', ''),
                "macu_od": getattr(ultimo_oftalmologia, 'maculopatia_od', ''),
                "macu_oi": getattr(ultimo_oftalmologia, 'maculopatia_oi', ''),
                "cat_od": getattr(ultimo_oftalmologia, 'catarata_od', ''),
                "cat_oi": getattr(ultimo_oftalmologia, 'catarata_oi', ''),
                "glau_od": getattr(ultimo_oftalmologia, 'glaucoma_od', ''),
                "glau_oi": getattr(ultimo_oftalmologia, 'glaucoma_oi', ''),
        }] if ultimo_oftalmologia else [] 

        #cardiologia
        ultima_cardiologia = next(iter(sorted(paciente.cardiologia, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.cardiologia else None
       
        ultima_cardiologia_list = [
            {
                "fecha_registro": ultima_cardiologia.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_cardiologia, 'fecha_registro', None) else '',
                "ekg": getattr(ultima_cardiologia, 'ekg', ''),
                "riesgo_oms": getattr(ultima_cardiologia, 'riesgo_oms', ''),
        }] if ultima_cardiologia else []

        #nefrologia
        ultima_nefrologia = next(iter(sorted(paciente.nefrologia, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.nefrologia else None
       
        ultima_nefrologia_list = [
            {
                "fecha_registro": ultima_nefrologia.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_nefrologia, 'fecha_registro', None) else '',
                "fgt": getattr(ultima_nefrologia, 'filtrado_glomerular_teorico', ''),
                "crea": getattr(ultima_nefrologia, 'creatinina', ''),
                "protei_val": getattr(ultima_nefrologia, 'proteinuria_valor', ''),
                "protei": getattr(ultima_nefrologia, 'proteinuria', ''),
                "urea": getattr(ultima_nefrologia, 'urea', ''),
                "ac_u": getattr(ultima_nefrologia, 'ac_urico', ''),
                "cituria": getattr(ultima_nefrologia, 'cituria', ''),
                "microal": getattr(ultima_nefrologia, 'microalbuminuria', ''),
                "nefro_diabe": getattr(ultima_nefrologia, 'nefropatia_diabetica', ''),
                "clasi": getattr(ultima_nefrologia, 'clasificacion', ''),
        }] if ultima_nefrologia else []

        #estomatologia
        ultima_estomatologia = next(iter(sorted(paciente.estomatologia, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.estomatologia else None
        
        diagnosticos_clinico = []
        if ultima_estomatologia:
            diagnosticos_clinico = [getattr(enfermedad, 'diagnostico', '') for enfermedad in getattr(ultima_estomatologia, 'diagnosticos_clinico', [])]

        ultima_estomatologia_list = [
            {
                "fecha_registro": ultima_estomatologia.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_estomatologia, 'fecha_registro', None) else '',
                "exam_func": getattr(ultima_estomatologia, 'examen_funcional', ''),
                "diag_epid": getattr(ultima_estomatologia, 'diagnosticos_epidemiologicos', ''),
                "pronostico": getattr(ultima_estomatologia, 'pronostico', ''),
                "tratamiento": getattr(ultima_estomatologia, 'tratamiento', ''),
                "diag_cli": diagnosticos_clinico,
            }
        ] if ultima_estomatologia else []

        #indicaciones
        ultima_indicaciones = next(iter(sorted(paciente.indicaciones, 
                                                    key=lambda x: getattr(x, 'fecha_registro', datetime.min), 
                                                    reverse=True)), None) if paciente.indicaciones else None
       
        ultima_indicaciones_list = [
            {
                "fecha_registro": ultima_indicaciones.fecha_registro.strftime('%d/%m/%Y') if getattr(ultima_indicaciones, 'fecha_registro', None) else '',
                "tipo": getattr(ultima_indicaciones, 'tipo_diabetes', ''),
                "tratamiento": getattr(ultima_indicaciones, 'tratamiento', ''),
        }] if ultima_indicaciones else []

        datos = {
            'no_hc': paciente.no_hc or '',
            'ci': paciente.ci or '',
            'nombres': paciente.nombres or '',
            'apellidos': paciente.apellidos or '',
            'telefono': paciente.telefono or '',
            'area_salud': paciente.area_salud or '',
            'estado_actual': paciente.estado_actual or '',
            'calle': paciente.calle or '',
            'numero': paciente.numero or '',
            'entre_calles': paciente.entre_calles or '',
            'municipio': paciente.municipio or '',
            'provincia': paciente.provincia or '',
            'sexo': paciente.sexo or '',
            'color_piel': paciente.color_piel or '',
            'escolaridad': paciente.escolaridad or '',
            'ocupacion': paciente.ocupacion or '',
            'estado_civil': paciente.estado_civil or '',
            'fecha_hc': paciente.fecha_hc.strftime('%d/%m/%Y') if getattr(paciente, 'fecha_hc', None) else '',
            'edad_actual': getattr(paciente, 'edad_actual', ''),
            'tiempo_evolucion': getattr(paciente, 'tiempo_evolucion', ''),
            'forma_presentacion_diagnostico': getattr(paciente, 'forma_presentacion_diagnostico', ''),
            'glucemia_debut': getattr(paciente, 'glucemia_debut', ''),
            'obesidad_debut': getattr(paciente, 'obesidad_debut', ''),
            'remision': getattr(paciente, 'remision', ''),
            'tratamiento_inicial': getattr(paciente, 'tratamiento_inicial', ''),
            'dosis_tratamiento': getattr(paciente, 'dosis_tratamiento', ''),
            'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
            'hora_actual': datetime.now().strftime('%H:%M'),
            "patologias_app": patologias_app_list,
            "patologias_apf": patologias_apf_list,
            "grados_parentesco_apfd": grados_parentezco_list,
            "habitos_toxicos": habitos_list,
            "historia_obstetrica": historia_obstetrica_list,
            "tratamiento_actual": tratamiento_list,
            "otros_tratamientos": otros_tratamientos_list,
            "examen_fisico": ultimo_examen_list,
            "mensuraciones": ultima_mensuracion_list,
            "complementarios": ultimo_complementario_list,
            "educacion": ultima_educacion_list,
            "exam_podo": podologico_list[0] if podologico_list else {},
            "oftal": ultimo_oftalmologia_list[0] if ultimo_oftalmologia_list else {},
            "cardi": ultima_cardiologia_list[0] if ultima_cardiologia_list else {},
            "nefro": ultima_nefrologia_list[0] if ultima_nefrologia_list else {},
            "esto": ultima_estomatologia_list[0] if ultima_estomatologia_list else {},
            "indi": ultima_indicaciones_list[0] if ultima_indicaciones_list else {},
        }
        
        return datos
    
    def generar_documento(self, no_hc, ruta_guardado=None):
        """Genera el documento de Word con los datos del paciente"""
        try:
            # Verificar que existe la plantilla
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"No se encontró la plantilla en: {self.template_path}")
            
            # Obtener datos del paciente
            datos = self.obtener_datos_paciente(no_hc)
            if not datos:
                raise ValueError(f"No se encontró el paciente con número de HC: {no_hc}")
            
            # Cargar la plantilla
            doc = DocxTemplate(self.template_path)
            
            # Renderizar la plantilla con los datos
            doc.render(datos)
            
            # Generar nombre del archivo
            fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Historia_Clinica_{no_hc}_{fecha_actual}.docx"
            
            # Si no se especifica ruta, usar directorio temporal
            if not ruta_guardado:
                ruta_guardado = tempfile.gettempdir()
            
            ruta_completa = os.path.join(ruta_guardado, nombre_archivo)
            # Guardar el documento
            doc.save(ruta_completa)
            ui.download(ruta_completa)
            
            return ruta_completa
            
        except Exception as e:
            log_error_and_notify(e,f"Error al generar el documento de historia clínica para HC {no_hc}: {str(e)}")
            raise Exception(f"Error al generar el documento: {str(e)}")

def mostrar_interfaz_exportacion(no_hc):
    """Muestra la interfaz de NiceGUI para exportar la historia clínica"""
    exportador = ExportadorHistoriaClinica()
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-md').style("width:760px; max-width:none;"):

        ui.label('Exportar Historia Clínica').classes('text-h6 q-mb-md')
        
        # Información del paciente
        paciente = exportador.session.query(Paciente).filter(Paciente.no_hc == no_hc).first()
        if paciente:
            ui.label(f'Paciente: {paciente.nombres} {paciente.apellidos}').classes('text-body1')
            ui.label(f'No. HC: {paciente.no_hc}').classes('text-body2')
        
        # Campo para ruta de guardado"
        ruta_guardado = 'HC/'
        
        # Botones
        with ui.row():
            ui.button('Cancelar', on_click=dialog.close).classes('bg-grey')
            
            async def exportar():
                try:
                    ruta = ruta_guardado
                    ruta_generada = exportador.generar_documento(no_hc, ruta)
                    
                    # Mostrar mensaje de éxito
                    ui.notify(
                        f'Documento generado exitosamente en: {ruta_generada}',
                        type='positive',
                        timeout=5000
                    )
                    
                    # Opción para abrir la carpeta
                    with ui.dialog() as dialog_abrir:
                        with ui.card():
                            ui.label('¿Desea abrir la carpeta donde se guardó el archivo?')
                            with ui.row():
                                ui.button('Sí', on_click=lambda: ui.open_folder(os.path.dirname(ruta_generada)))
                                ui.button('No', on_click=dialog_abrir.close)
                    
                    dialog.close()
                    
                except Exception as e:
                    log_error_and_notify(e,f"Error al exportar la historia clínica para HC {no_hc}: {str(e)}")
                    ui.notify(
                        f'Error al generar el documento: {str(e)}',
                        type='negative',
                        timeout=5000
                    )
            
            ui.button('Exportar', on_click=exportar).classes('bg-blue')
    dialog.open()


# Función para usar directamente
def exportar_historia_clinica(no_hc, ruta_guardado=None):
    """Función simple para exportar una historia clínica"""
    exportador = ExportadorHistoriaClinica()
    return exportador.generar_documento(no_hc, ruta_guardado)

