# controllers/historia_clinica_complementarios_controller.py
from datetime import datetime
from Errores import log_error_and_notify
from models import Complementarios, CampoComplementarioPersonalizado

class ComplementariosController:
    def __init__(self, session):
        self.session = session

    def obtener_complementarios_procesados(self, paciente):
        """
        Retorna el historial de exámenes ordenados por fecha y el último examen registrado.
        """
        examenes = getattr(paciente, 'complementarios', [])
        if not examenes:
            return [], None
            
        ordenados = sorted(examenes, key=lambda x: getattr(x, 'fecha_registro', datetime.min.date()), reverse=True)
        ultimo = ordenados[0] if ordenados else None
        
        return ordenados, ultimo

    def _procesar_ultrasonido(self, selecciones_us, otros_input):
        """Lógica interna para formatear el string del ultrasonido abdominal."""
        selecciones = selecciones_us or []
        valor_ultrasonido = ""

        if isinstance(selecciones, list):
            selecciones_filtradas = [s for s in selecciones if s and s.strip()]
            
            if "Otros" in selecciones_filtradas:
                selecciones_filtradas = [s for s in selecciones_filtradas if s != "Otros"]
                if otros_input and otros_input.strip():
                    selecciones_filtradas.append(f"Otros: {otros_input.strip()}")
            
            valor_ultrasonido = "; ".join(selecciones_filtradas)
        else:
            valor_ultrasonido = str(selecciones) if selecciones else ""
            
        return valor_ultrasonido

    def _guardar_campos_personalizados(self, complementario_id, campos_raw):
        """Procesa la lista de componentes visuales (ui.input) para extraer y guardar los datos."""
        from nicegui import ui # Importado localmente solo para verificación de tipos
        
        for row in campos_raw:
            # Extraemos los inputs de la fila
            inputs = [child for child in row.default_slot.children if isinstance(child, ui.input)]
            if len(inputs) >= 3:
                nombre = inputs[0].value.strip() if inputs[0].value else ""
                valor = inputs[1].value.strip() if inputs[1].value else ""
                unidad = inputs[2].value.strip() if inputs[2].value else ""
                
                if nombre and valor:
                    campo = CampoComplementarioPersonalizado(
                        complementario_id=complementario_id,
                        nombre=nombre,
                        valor=valor,
                        unidad=unidad or None
                    )
                    self.session.add(campo)

    def guardar_examen(self, paciente_id, fecha_str, datos, campos_personalizados_raw):
        """Persiste un nuevo examen complementario y sus campos dinámicos."""
        try:
            fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            valor_us = self._procesar_ultrasonido(datos.get('ultrasonido_abdominal'), datos.get('otros_input'))

            nuevo_examen = Complementarios(
                paciente_id=paciente_id,
                fecha_registro=fecha_registro,
                hb=datos.get('hb'), hto=datos.get('hto'), eritro=datos.get('eritro'),
                glucemia=datos.get('glucemia'), colesterol=datos.get('colesterol'), trigliceridos=datos.get('trigliceridos'),
                HDLC=datos.get('HDLC'), tgp=datos.get('tgp'), TGO=datos.get('TGO'),
                ggt=datos.get('ggt'), HbA1c=datos.get('HbA1c'),
                proteinas_totales=datos.get('proteinas_totales'), albuminuria=datos.get('albuminuria'), globulina=datos.get('globulina'),
                calcio=datos.get('calcio'), fosforo=datos.get('fosforo'), conteo_plaquetas=datos.get('conteo_plaquetas'),
                coagulacion=datos.get('coagulacion'), sangramiento=datos.get('sangramiento'),
                ultrasonido_abdominal=valor_us,
                prueba_conduccion_nerviosa_miembro_superior=datos.get('prueba_cn_superior'),
                prueba_conduccion_nerviosa_miembro_inferior=datos.get('prueba_cn_inferior')
            )

            self.session.add(nuevo_examen)
            self.session.flush() # Importante para obtener el ID antes del commit

            # Guardar campos dinámicos
            self._guardar_campos_personalizados(nuevo_examen.id, campos_personalizados_raw)

            self.session.commit()
            return True, "Examen complementario agregado correctamente"
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al guardar examen complementario')
            return False, f"Error al guardar: {str(e)}"

    def actualizar_examen(self, examen, fecha_str, datos, campos_personalizados_raw):
        """Actualiza un examen existente, incluyendo la reconstrucción de campos personalizados."""
        try:
            examen.fecha_registro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            valor_us = self._procesar_ultrasonido(datos.get('ultrasonido_abdominal'), datos.get('otros_input'))

            # Actualizar campos fijos
            examen.hb = datos.get('hb')
            examen.hto = datos.get('hto')
            examen.eritro = datos.get('eritro')
            examen.glucemia = datos.get('glucemia')
            examen.colesterol = datos.get('colesterol')
            examen.trigliceridos = datos.get('trigliceridos')
            examen.HDLC = datos.get('HDLC')
            examen.tgp = datos.get('tgp')
            examen.TGO = datos.get('TGO')
            examen.proteinas_totales = datos.get('proteinas_totales')
            examen.albuminuria = datos.get('albuminuria')
            examen.globulina = datos.get('globulina')
            examen.calcio = datos.get('calcio')
            examen.fosforo = datos.get('fosforo')
            examen.conteo_plaquetas = datos.get('conteo_plaquetas')
            examen.coagulacion = datos.get('coagulacion')
            examen.sangramiento = datos.get('sangramiento')
            examen.ultrasonido_abdominal = valor_us
            examen.prueba_conduccion_nerviosa_miembro_superior = datos.get('prueba_cn_superior')
            examen.prueba_conduccion_nerviosa_miembro_inferior = datos.get('prueba_cn_inferior')
            examen.HbA1c = datos.get('HbA1c')
            examen.ggt = datos.get('ggt')

            # Manejo de campos personalizados: Eliminar los viejos y recrear
            for campo in examen.campos_personalizados:
                self.session.delete(campo)
                
            self.session.flush()
            
            self._guardar_campos_personalizados(examen.id, campos_personalizados_raw)

            self.session.commit()
            return True, "Examen complementario actualizado correctamente"
            
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al actualizar examen complementario')
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_examen(self, examen):
        """Elimina físicamente el examen de la base de datos."""
        try:
            self.session.delete(examen)
            self.session.commit()
            return True, "Examen complementario eliminado correctamente"
        except Exception as e:
            self.session.rollback()
            log_error_and_notify(e, 'Error al eliminar examen complementario')
            return False, f"Error al eliminar: {str(e)}"