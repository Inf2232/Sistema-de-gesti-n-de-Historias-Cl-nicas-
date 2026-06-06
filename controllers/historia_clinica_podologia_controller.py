# historia_clinica_podologia_controller.py
from datetime import datetime
from models import ExamenMiembrosInferiores, EnfermedadesPodalicasIzquierdo, LesionesDermatologicasIzquierdo, LesionesUñasIzquierdo, EnfermedadesPodalicasDerecho, LesionesDermatologicasDerecho, LesionesUñasDerecho
from Errores import log_error_and_notify
import logging

class HistoriaClinicaPodologiaController:
    def __init__(self, session):
        self.session = session

    def obtener_examenes_paciente(self, paciente):
        """Retorna todos los exámenes de miembros inferiores de un paciente."""
        try:
            return paciente.examen_miembros_inferiores
        except Exception as e:
            logging.error(f"Error al obtener exámenes: {str(e)}")
            return []

    def obtener_ultimo_examen(self, paciente):
        """Retorna el examen más reciente o None si no existe."""
        examenes = self.obtener_examenes_paciente(paciente)
        if examenes:
            return max(examenes, key=lambda x: x.fecha_registro)
        return None
    def procesar_valor_columna(self, radio_value, input_value):
        """
        Si se selecciona 'AN', guarda el valor como 'AN:Texto explicativo'.
        Si el input_value está vacío, guarda 'AN'.
        Si se selecciona 'N' o 'NE', se guarda el valor del radio tal cual.
        """
        if radio_value == 'AN':
            if input_value and input_value.strip():
                return f"AN:{input_value.strip()}"
            return 'AN'
        return radio_value

    def descomponer_valor_columna(self, valor_guardado):
        """
        Función inversa para la edición.
        Recibe lo que está en la base de datos (ej: 'AN:Mucha información')
        Devuelve una tupla: (valor_del_radio, valor_del_input)
        Esto previene errores al editar registros viejos o en formatos previos.
        """
        if not valor_guardado:
            return ('N', '')  # Por defecto si está vacío
       
        if valor_guardado.startswith('AN:'):
            # Separa por el primer ':' encontrado
            partes = valor_guardado.split(':', 1)
            return ('AN', partes[1])
        elif valor_guardado == 'AN':
            return ('AN', '')
        elif valor_guardado in ['N', 'NE', 'Presente', 'Ausente', 'Conservada', 'No Conservada']:
            # Mapeo de compatibilidad con datos viejos:
            if valor_guardado in ['Presente', 'Conservada']:
                return ('N', '')
            if valor_guardado in ['Ausente', 'No Conservada']:
                return ('NE', '')
            return (valor_guardado, '')
        else:
            # Si contiene texto libre antiguo que no empieza con AN:, asumimos que era AN
            return ('AN', valor_guardado)
        
        
    def eliminar_examen(self, examen):
        """Elimina un examen de la base de datos."""
        try:
            self.session.delete(examen)
            self.session.commit()
            return True, "Examen eliminado correctamente"
        except Exception as e:
            self.session.rollback()
            return False, str(e)
        
    def guardar_examen_miembro_inferior(self,paciente_id, fecha_registro, 
                                    defromidades_podalicas_izquierdo, lesiones_dermatologicas_izquierdo, lesiones_uñas_izquierdo,
                                    pulso_femoral_izquierdo, pulso_popliteo_izquierdo, pulso_tibial_posterior_izquierdo,
                                    pulso_pedeo_izquierdo, EAP_izquierdo, tibial_izquierdo, pedia_izquierdo,
                                    humeral_izquierdo, patelar_izquierdo, aquileano_izquierdo, 
                                    LOPS_izquierdo, palestesia_izquierdo, tactil_izquierdo, termica_izquierdo, dolorosa_izquierdo,
                                    defromidades_podalicas_derecho, lesiones_dermatologicas_derecho, lesiones_uñas_derecho,
                                    pulso_femoral_derecho, pulso_popliteo_derecho, pulso_tibial_posterior_derecho, 
                                    pulso_pedeo_derecho, EAP_derecho, tibial_derecho, pedia_derecho,
                                    humeral_derecho, patelar_derecho, aquileano_derecho,
                                    LOPS_derecho, palestesia_derecho, tactil_derecho, termica_derecho, dolorosa_derecho,
                                    impresion_diagnostica,venoso_periferico_izquierdo, venoso_periferico_derecho,linfatico_izquierdo, linfatico_derecho, dialog):
        # Create the exam
        try:
            if fecha_registro:
                fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
                nuevo_examen = ExamenMiembrosInferiores(
                    paciente_id=paciente_id,
                    fecha_registro=fecha_registro,
                    pulso_femoral_izquierdo=pulso_femoral_izquierdo if pulso_femoral_izquierdo is not None else "No Registrado" ,
                    pulso_popliteo_izquierdo=pulso_popliteo_izquierdo if pulso_popliteo_izquierdo is not None else "No Registrado" ,
                    pulso_tibial_posterior_izquierdo=pulso_tibial_posterior_izquierdo if pulso_tibial_posterior_izquierdo is not None else "No Registrado" ,
                    pulso_pedeo_izquierdo=pulso_pedeo_izquierdo if pulso_pedeo_izquierdo is not None else "No Registrado" ,
                    EAP_izquierdo=EAP_izquierdo if EAP_izquierdo is not None else "No Registrado" ,
                    tibial_izquierdo=tibial_izquierdo if tibial_izquierdo is not None else 0,
                    pedia_izquierdo=pedia_izquierdo if pedia_izquierdo is not None else 0 ,
                    humeral_izquierdo=humeral_izquierdo if humeral_izquierdo is not None else 0,
                    patelar_izquierdo=patelar_izquierdo if patelar_izquierdo is not None else "No Registrado"  ,
                    aquileano_izquierdo=aquileano_izquierdo if aquileano_izquierdo is not None else "No Registrado" ,
                    LOPS_izquierdo=LOPS_izquierdo if LOPS_izquierdo is not None else "No Registrado" ,
                    palestesia_izquierdo=palestesia_izquierdo if palestesia_izquierdo is not None else "No Registrado" ,
                    tactil_izquierdo=tactil_izquierdo if tactil_izquierdo is not None else "No Registrado" ,
                    termica_izquierdo=termica_izquierdo if termica_izquierdo is not None else "No Registrado" ,
                    dolorosa_izquierdo=dolorosa_izquierdo if dolorosa_izquierdo is not None else "No Registrado" ,
                    pulso_femoral_derecho=pulso_femoral_derecho if pulso_femoral_derecho is not None else "No Registrado" ,
                    pulso_popliteo_derecho=pulso_popliteo_derecho if pulso_popliteo_derecho is not None else "No Registrado" ,
                    pulso_tibial_posterior_derecho=pulso_tibial_posterior_derecho if pulso_tibial_posterior_derecho is not None else "No Registrado" ,
                    pulso_pedeo_derecho=pulso_pedeo_derecho if pulso_pedeo_derecho is not None else "No Registrado" ,
                    EAP_derecho=EAP_derecho if EAP_derecho is not None else "No Registrado" ,
                    tibial_derecho=tibial_derecho if tibial_derecho is not None else 0 ,
                    pedia_derecho=pedia_derecho if pedia_derecho is not None else 0 ,
                    humeral_derecho=humeral_derecho if humeral_derecho is not None else 0 ,
                    patelar_derecho=patelar_derecho if patelar_derecho is not None else "No Registrado" ,
                    aquileano_derecho=aquileano_derecho if aquileano_derecho is not None else "No Registrado" ,
                    LOPS_derecho=LOPS_derecho if LOPS_derecho is not None else "No Registrado" ,
                    palestesia_derecho=palestesia_derecho if palestesia_derecho is not None else "No Registrado" ,
                    tactil_derecho=tactil_derecho if tactil_derecho is not None else "No Registrado" ,
                    termica_derecho=termica_derecho if termica_derecho is not None else "No Registrado" ,
                    dolorosa_derecho=dolorosa_derecho if dolorosa_derecho is not None else "No Registrado" ,
                    impresion_diagnostica=impresion_diagnostica if impresion_diagnostica is not None else "No Registrado" ,
                    venoso_periferico_izquierdo=venoso_periferico_izquierdo if venoso_periferico_izquierdo is not None else "No Registrado" ,
                    venoso_periferico_derecho=venoso_periferico_derecho if venoso_periferico_derecho is not None else "No Registrado" ,
                    linfatico_izquierdo=linfatico_izquierdo if linfatico_izquierdo is not None else "No Registrado" ,
                    linfatico_derecho=linfatico_derecho if linfatico_derecho is not None else "No Registrado",

                )
                
            
                for padecimiento in defromidades_podalicas_izquierdo:
                    nuevo_examen.defromidades_podalicas_izquierdo.append(EnfermedadesPodalicasIzquierdo(padecimiento=padecimiento))
                
                for padecimiento in lesiones_dermatologicas_izquierdo:
                    nuevo_examen.lesiones_dermatologicas_izquierdo.append(LesionesDermatologicasIzquierdo(padecimiento=padecimiento))
                
                for padecimiento in lesiones_uñas_izquierdo:
                    nuevo_examen.lesiones_uñas_izquierdo.append(LesionesUñasIzquierdo(padecimiento=padecimiento))
                
                for padecimiento in defromidades_podalicas_derecho:
                    nuevo_examen.defromidades_podalicas_derecho.append(EnfermedadesPodalicasDerecho(padecimiento=padecimiento)) 
                
                for padecimiento in lesiones_dermatologicas_derecho:
                    nuevo_examen.lesiones_dermatologicas_derecho.append(LesionesDermatologicasDerecho(padecimiento=padecimiento))
                
                for padecimiento in lesiones_uñas_derecho:
                    nuevo_examen.lesiones_uñas_derecho.append(LesionesUñasDerecho(padecimiento=padecimiento))   
                
                # Save the exam to the database
                self.session.add(nuevo_examen)
                self.session.commit()
                return True, "Examen guardado exitosamente."
            else:
                return False, "Debe introducir la fecha"
            # Close the dialog and refresh the view
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, "Error crítico al guardar examen de miembro inferior")
            return False, str(e)
        finally:
            dialog.close()
    def actualizar_examen_miembro_inferior(self, examen, fecha_registro, 
                                        defromidades_podalicas_izquierdo, lesiones_dermatologicas_izquierdo, lesiones_uñas_izquierdo,
                                        pulso_femoral_izquierdo, pulso_popliteo_izquierdo, pulso_tibial_posterior_izquierdo,
                                        pulso_pedeo_izquierdo, EAP_izquierdo, tibial_izquierdo, pedia_izquierdo,
                                        humeral_izquierdo, patelar_izquierdo, aquileano_izquierdo, 
                                        LOPS_izquierdo, palestesia_izquierdo, tactil_izquierdo, termica_izquierdo, dolorosa_izquierdo,
                                        defromidades_podalicas_derecho, lesiones_dermatologicas_derecho, lesiones_uñas_derecho,
                                        pulso_femoral_derecho, pulso_popliteo_derecho, pulso_tibial_posterior_derecho, 
                                        pulso_pedeo_derecho, EAP_derecho, tibial_derecho, pedia_derecho,
                                        humeral_derecho, patelar_derecho, aquileano_derecho,
                                        LOPS_derecho, palestesia_derecho, tactil_derecho, termica_derecho, dolorosa_derecho,
                                        impresion_diagnostica, venoso_periferico_izquierdo, venoso_periferico_derecho, linfatico_izquierdo, linfatico_derecho, dialog):
        try:
            # Si fecha_registro ya es un objeto date, no necesitamos parsearlo
            if isinstance(fecha_registro, str):
                examen.fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
            else:
                examen.fecha_registro = fecha_registro

            # Actualizar campos simples
            examen.pulso_femoral_izquierdo = pulso_femoral_izquierdo if pulso_femoral_izquierdo is not None else "No Registrado" 
            examen.pulso_popliteo_izquierdo = pulso_popliteo_izquierdo if pulso_popliteo_izquierdo is not None else "No Registrado" 
            examen.pulso_tibial_posterior_izquierdo = pulso_tibial_posterior_izquierdo if pulso_tibial_posterior_izquierdo is not None else "No Registrado"
            examen.pulso_pedeo_izquierdo = pulso_pedeo_izquierdo if pulso_pedeo_izquierdo is not None else "No Registrado" 
            examen.EAP_izquierdo = EAP_izquierdo if EAP_izquierdo is not None else "No Registrado" 
            examen.tibial_izquierdo = tibial_izquierdo if tibial_izquierdo is not None else 0 
            examen.pedia_izquierdo = pedia_izquierdo if pedia_izquierdo is not None else 0
            examen.humeral_izquierdo = humeral_izquierdo if humeral_izquierdo is not None else 0
            examen.patelar_izquierdo = patelar_izquierdo if patelar_izquierdo is not None else "No Registrado" 
            examen.aquileano_izquierdo = aquileano_izquierdo if aquileano_izquierdo is not None else "No Registrado" 
            examen.LOPS_izquierdo = LOPS_izquierdo if LOPS_izquierdo is not None else "No Registrado" 
            examen.palestesia_izquierdo = palestesia_izquierdo if palestesia_izquierdo is not None else "No Registrado" 
            examen.tactil_izquierdo = tactil_izquierdo if tactil_izquierdo is not None else "No Registrado" 
            examen.termica_izquierdo = termica_izquierdo if termica_izquierdo is not None else "No Registrado" 
            examen.dolorosa_izquierdo = dolorosa_izquierdo if dolorosa_izquierdo is not None else "No Registrado" 

            examen.pulso_femoral_derecho = pulso_femoral_derecho if pulso_femoral_derecho is not None else "No Registrado" 
            examen.pulso_popliteo_derecho = pulso_popliteo_derecho if pulso_popliteo_derecho is not None else "No Registrado" 
            examen.pulso_tibial_posterior_derecho = pulso_tibial_posterior_derecho if pulso_tibial_posterior_derecho is not None else "No Registrado"
            examen.pulso_pedeo_derecho = pulso_pedeo_derecho if pulso_pedeo_derecho is not None else "No Registrado" 
            examen.EAP_derecho = EAP_derecho if EAP_derecho is not None else "No Registrado" 
            examen.tibial_derecho = tibial_derecho if tibial_derecho is not None else 0
            examen.pedia_derecho = pedia_derecho if pedia_derecho is not None else 0
            examen.humeral_derecho = humeral_derecho if humeral_derecho is not None else 0
            examen.patelar_derecho = patelar_derecho if patelar_derecho is not None else "No Registrado" 
            examen.aquileano_derecho = aquileano_derecho if aquileano_derecho is not None else "No Registrado" 
            examen.LOPS_derecho = LOPS_derecho if LOPS_derecho is not None else "No Registrado" 
            examen.palestesia_derecho = palestesia_derecho if palestesia_derecho is not None else "No Registrado" 
            examen.tactil_derecho = tactil_derecho if tactil_derecho is not None else "No Registrado" 
            examen.termica_derecho = termica_derecho if termica_derecho is not None else "No Registrado" 
            examen.dolorosa_derecho = dolorosa_derecho if dolorosa_derecho is not None else "No Registrado" 

            examen.impresion_diagnostica = impresion_diagnostica if impresion_diagnostica is not None else "No Registrado" 
            examen.venoso_periferico_izquierdo = venoso_periferico_izquierdo if venoso_periferico_izquierdo is not None else "No Registrado"
            examen.venoso_periferico_derecho = venoso_periferico_derecho if venoso_periferico_derecho is not None else "No Registrado"
            examen.linfatico_izquierdo = linfatico_izquierdo if linfatico_izquierdo is not None else "No Registrado"
            examen.linfatico_derecho = linfatico_derecho if linfatico_derecho is not None else "No Registrado"

            # Limpiar las listas existentes
            examen.defromidades_podalicas_izquierdo.clear()
            examen.lesiones_dermatologicas_izquierdo.clear()
            examen.lesiones_uñas_izquierdo.clear()
            examen.defromidades_podalicas_derecho.clear()
            examen.lesiones_dermatologicas_derecho.clear()
            examen.lesiones_uñas_derecho.clear()

            # Agregar nuevos valores a las relaciones
            for padecimiento in defromidades_podalicas_izquierdo:
                examen.defromidades_podalicas_izquierdo.append(EnfermedadesPodalicasIzquierdo(padecimiento=padecimiento))

            for padecimiento in lesiones_dermatologicas_izquierdo:
                examen.lesiones_dermatologicas_izquierdo.append(LesionesDermatologicasIzquierdo(padecimiento=padecimiento))

            for padecimiento in lesiones_uñas_izquierdo:
                examen.lesiones_uñas_izquierdo.append(LesionesUñasIzquierdo(padecimiento=padecimiento))

            for padecimiento in defromidades_podalicas_derecho:
                examen.defromidades_podalicas_derecho.append(EnfermedadesPodalicasDerecho(padecimiento=padecimiento))

            for padecimiento in lesiones_dermatologicas_derecho:
                examen.lesiones_dermatologicas_derecho.append(LesionesDermatologicasDerecho(padecimiento=padecimiento))

            for padecimiento in lesiones_uñas_derecho:
                examen.lesiones_uñas_derecho.append(LesionesUñasDerecho(padecimiento=padecimiento))

            # Guardar cambios en la base de datos
            self.session.commit()
            dialog.close()
            return True, "Examen actualizado exitosamente."
            


        except Exception as e:
            log_error_and_notify(e, f'Error actulizando Miembros inferiores  {no_hc}')
            self.session.rollback()
            return False, str(e)