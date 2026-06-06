from datetime import datetime
from models import Session, Paciente, Institucion, Provincia, Municipio, IngresoDiab


class HistoriaClinicaController:
    """Capa de lógica de negocio para Historia Clínica (sin UI)."""

    def __init__(self, session=None):
        self.session = session or Session()

    def cargar_paciente_con_acceso(self, no_hc, institucion_id_usuario=None, es_superadmin=False):
        query = self.session.query(Paciente).filter(Paciente.no_hc == no_hc)
        if not es_superadmin:
            if institucion_id_usuario is None:
                return None
            query = query.filter(Paciente.institucion_id == institucion_id_usuario)
        return query.first()

    def obtener_nombre_institucion(self, institucion_id):
        if not institucion_id:
            return ""
        inst = self.session.query(Institucion).filter_by(id=institucion_id).first()
        return inst.nombre if inst else ""

    def obtener_municipios_por_provincia(self, nombre_provincia):
        """Devuelve lista de nombres (strings) para mostrar en el selector."""
        if not nombre_provincia:
            return []
        prov = self.session.query(Provincia).filter_by(nombre=nombre_provincia).first()
        if not prov:
            return []
        return [m.nombre for m in prov.municipios]

    def obtener_areas_por_municipio(self, nombre_municipio, nombre_provincia):
        """Devuelve lista de nombres (strings) para mostrar en el selector."""
        if not nombre_municipio or not nombre_provincia:
            return []
        muni = self.session.query(Municipio).join(Provincia).filter(
            Municipio.nombre == nombre_municipio,
            Provincia.nombre == nombre_provincia,
        ).first()
        if not muni:
            return []
        return [a.nombre for a in muni.areas_salud]

    def resolver_municipio_id(self, nombre_municipio, nombre_provincia):
        """Dado el nombre seleccionado en la UI, devuelve el municipio_id."""
        if not nombre_municipio or not nombre_provincia:
            return None
        muni = self.session.query(Municipio).join(Provincia).filter(
            Municipio.nombre == nombre_municipio,
            Provincia.nombre == nombre_provincia,
        ).first()
        return muni.id if muni else None

    def resolver_area_salud_id(self, nombre_area, nombre_municipio, nombre_provincia):
        """Dado el nombre seleccionado en la UI, devuelve el area_salud_id."""
        if not nombre_area or not nombre_municipio or not nombre_provincia:
            return None
        muni = self.session.query(Municipio).join(Provincia).filter(
            Municipio.nombre == nombre_municipio,
            Provincia.nombre == nombre_provincia,
        ).first()
        if not muni:
            return None
        area = next((a for a in muni.areas_salud if a.nombre == nombre_area), None)
        return area.id if area else None

    def actualizar_paciente_desde_payload(self, paciente, payload, ingresos_temporales, mapa_instituciones, original_hc):
        nombre_inst = payload.get("institucion")
        nuevo_institucion_id = mapa_instituciones.get(nombre_inst)
        if nuevo_institucion_id is None:
            raise ValueError(f'La institución "{nombre_inst}" no es válida.')

        ci_val = str(payload.get("ci") or "")
        if not (ci_val.isdigit() and len(ci_val) == 11):
            raise ValueError("El carnet debe contener exactamente 11 dígitos numéricos.")

        forma_presentacion = payload.get("forma_presentacion_diagnostico")
        if forma_presentacion == "Otros":
            forma_presentacion = payload.get("otros_forma_presentacion_diagnostico")

        tratamiento_inicial = payload.get("tratamiento_inicial")
        if tratamiento_inicial == "Otros":
            tratamiento_inicial = payload.get("otros_tratamiento")

        hc_cambio = payload.get("no_hc") != original_hc

        for ing_viejo in paciente.ingresos_diab[:]:
            self.session.delete(ing_viejo)

        for item in ingresos_temporales:
            fecha_dt = item["fecha"]
            if isinstance(fecha_dt, str):
                fecha_dt = datetime.strptime(fecha_dt, "%Y-%m-%d").date()
            nuevo_ingreso = IngresoDiab(
                no_hc=paciente.no_hc,
                motivo=item["motivo"],
                especificacion_otro=item.get("especificacion", ""),
                fecha_ingreso=fecha_dt,
            )
            paciente.ingresos_diab.append(nuevo_ingreso)

        paciente.no_hc            = payload.get("no_hc") or ""
        paciente.ci               = payload.get("ci") or ""
        paciente.nombres          = payload.get("nombres") or ""
        paciente.apellidos        = payload.get("apellidos") or ""
        paciente.telefono         = payload.get("telefono") or ""
        paciente.tel_emergencia   = payload.get("tel_emergencia") or ""
        paciente.fecha_hc         = datetime.strptime(payload.get("fecha_hc"), "%Y-%m-%d").date() if payload.get("fecha_hc") else None
        paciente.estado_actual    = "Defunción" if payload.get("estado_actual") else ""
        paciente.calle            = payload.get("calle") or ""
        paciente.numero           = payload.get("numero") or ""
        paciente.entre_calles     = payload.get("entre_calles") or ""
        paciente.sexo             = payload.get("sexo") or ""
        paciente.color_piel       = payload.get("color_piel") or ""
        paciente.escolaridad      = payload.get("escolaridad") or ""
        paciente.ocupacion        = payload.get("ocupacion") or ""
        paciente.estado_civil     = payload.get("estado_civil") or ""

        # -- Ubicacion geografica: resolver IDs desde los nombres del payload ----
        # La UI sigue enviando texto (municipio, provincia, area_salud) igual que antes.
        nombre_provincia = payload.get("provincia") or ""
        nombre_municipio = payload.get("municipio") or ""
        nombre_area      = payload.get("area_salud") or ""

        paciente.municipio_id  = self.resolver_municipio_id(nombre_municipio, nombre_provincia)
        paciente.area_salud_id = self.resolver_area_salud_id(nombre_area, nombre_municipio, nombre_provincia)

        paciente.tiempo_evolucion_anios       = payload.get("tiempo_evolucion_anios") or 0
        paciente.tiempo_evolucion_meses       = payload.get("tiempo_evolucion_meses") or 0
        paciente.tiempo_evolucion_dias        = payload.get("tiempo_evolucion_dias") or 0
        paciente.forma_presentacion_diagnostico = forma_presentacion or ""
        paciente.glucemia_debut               = float(payload.get("glucemia_debut")) if payload.get("glucemia_debut") else 0
        paciente.exceso_peso_diagnostico      = payload.get("exceso_peso_diagnostico") or ""
        paciente.tiempo_exceso_peso_anios     = payload.get("tiempo_exceso_peso_anios") or 0
        paciente.tiempo_exceso_peso_meses     = payload.get("tiempo_exceso_peso_meses") or 0
        paciente.remision                     = payload.get("remision") or ""
        paciente.tratamiento_inicial_json       = payload.get("tratamiento_inicial_json") or []
        paciente.tratamiento_inicial          = tratamiento_inicial or ""
        paciente.dosis_tratamiento            = payload.get("dosis_tratamiento") or ""
        paciente.ano_inicio_tratamiento       = payload.get("ano_inicio_tratamiento")
        paciente.prediabetes                  = payload.get("prediabetes") or ""
        paciente.tiempo_prediabetes_anios     = payload.get("tiempo_prediabetes_anios") or 0
        paciente.tiempo_prediabetes_meses     = payload.get("tiempo_prediabetes_meses") or 0
        paciente.causa_fallecimiento          = payload.get("causa_fallecimiento") if payload.get("estado_actual") else ""
        paciente.institucion_id               = nuevo_institucion_id

        self.session.commit()
        return {"hc_cambio": hc_cambio}

    def eliminar_paciente(self, no_hc):
        paciente = self.session.query(Paciente).filter_by(no_hc=no_hc).first()
        if not paciente:
            return False
        self.session.delete(paciente)
        self.session.commit()
        return True