import os
from datetime import date, datetime
from sqlalchemy import extract, func, case, exists, and_, text
from sqlalchemy.orm import joinedload
from models import Session, Paciente, Institucion, Provincia, Municipio, AreaSalud, IngresoDiab, Ingreso

class DiabetesAppController:
    """
    Controlador con lógica de negocio y persistencia de datos.
    Versión optimizada: resuelve el problema N+1 que bloqueaba SQLite con 2000+ pacientes.
    """

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTODOS SIN CAMBIOS (se mantienen idénticos)
    # ──────────────────────────────────────────────────────────────────────────

    def get_institucion_info(self, rol: str, inst_id: int) -> dict:
        db = Session()
        try:
            institucion_nombre = 'Clínica del Diabético'
            provincia_default = None
            has_institucion = False

            if rol == 'superadministrador':
                institucion_nombre = 'Gestión Nacional (SuperAdministrador)'
                if inst_id:
                    inst = db.query(Institucion).filter_by(id=inst_id).first()
                    if inst:
                        provincia_default = inst.provincia_default
                        has_institucion = True
            elif inst_id:
                inst = db.query(Institucion).filter_by(id=inst_id).first()
                if inst:
                    institucion_nombre = inst.nombre
                    provincia_default = inst.provincia_default
                    has_institucion = True
                else:
                    institucion_nombre = 'Institución Desconocida'
            else:
                institucion_nombre = 'Clínica del Diabético'

            return {
                'institucion_nombre': institucion_nombre,
                'provincia_default': provincia_default,
                'has_institucion': has_institucion
            }
        finally:
            db.close()

    def get_provincias(self) -> list:
        db = Session()
        try:
            provincias = db.query(Provincia).all()
            return [p.nombre for p in provincias]
        finally:
            db.close()

    def get_municipios(self, nombre_provincia: str) -> list:
        if not nombre_provincia:
            return []
        db = Session()
        try:
            provincia = db.query(Provincia).filter_by(nombre=nombre_provincia).first()
            if provincia:
                return [m.nombre for m in provincia.municipios]
            return []
        finally:
            db.close()

    def get_areas_salud(self, nombre_provincia: str, nombre_municipio: str) -> list:
        if not nombre_municipio or not nombre_provincia:
            return []
        db = Session()
        try:
            municipio = db.query(Municipio).join(Provincia).filter(
                Municipio.nombre == nombre_municipio,
                Provincia.nombre == nombre_provincia
            ).first()
            if municipio:
                return [a.nombre for a in municipio.areas_salud]
            return []
        finally:
            db.close()

    def validar_existencia(self, no_hc: str, ci: str) -> dict:
        db = Session()
        try:
            existe_hc = db.query(Paciente).filter_by(no_hc=no_hc).first() is not None
            existe_ci = db.query(Paciente).filter_by(ci=ci).first() is not None
            return {'existe_hc': existe_hc, 'existe_ci': existe_ci}
        finally:
            db.close()

    def guardar_paciente(self, data: dict, ingresos_temporales: list, inst_id: int) -> tuple:
        db = Session()
        try:
            if db.query(Paciente).filter_by(no_hc=data['no_hc']).first():
                return False, 'El número de Historia Clínica ya está registrado.'
            if db.query(Paciente).filter_by(ci=data['ci']).first():
                return False, 'El número de Carnet de Identidad ya está registrado.'

            municipio_obj = (
                db.query(Municipio).join(Provincia)
                .filter(
                    Municipio.nombre == data['nombre_municipio'],
                    Provincia.nombre == data['nombre_provincia']
                ).first()
            )
            municipio_id_resuelto = municipio_obj.id if municipio_obj else None

            area_salud_id_resuelto = None
            if municipio_obj and data['nombre_area']:
                area = next((a for a in municipio_obj.areas_salud if a.nombre == data['nombre_area']), None)
                area_salud_id_resuelto = area.id if area else None

            for ing in ingresos_temporales:
                nuevo_ingreso = IngresoDiab(
                    no_hc=data['no_hc'],
                    motivo=ing['motivo'],
                    especificacion_otro=ing['especificacion'],
                    fecha_ingreso=datetime.strptime(ing['fecha'], '%Y-%m-%d').date()
                )
                db.add(nuevo_ingreso)

            nuevo_paciente = Paciente(
                institucion_id                  = inst_id,
                no_hc                           = data['no_hc'],
                ci                              = data['ci'],
                nombres                         = data['nombres'],
                apellidos                       = data['apellidos'],
                telefono                        = data['telefono'],
                nombre_contacto_emergencia      = data['nombre_contacto_emergencia'],
                tel_emergencia                  = data['tel_emergencia'],
                municipio_id                    = municipio_id_resuelto,
                area_salud_id                   = area_salud_id_resuelto,
                fecha_hc                        = data['fecha_hc'],
                estado_actual                   = data['estado_actual'],
                calle                           = data['calle'],
                numero                          = data['numero'],
                entre_calles                    = data['entre_calles'],
                sexo                            = data['sexo'],
                color_piel                      = data['color_piel'],
                escolaridad                     = data['escolaridad'],
                ocupacion                       = data['ocupacion'],
                estado_civil                    = data['estado_civil'],
                tiempo_evolucion_anios          = data['tiempo_evolucion_anios'],
                tiempo_evolucion_meses          = data['tiempo_evolucion_meses'],
                forma_presentacion_diagnostico  = data['forma_presentacion_diagnostico'],
                glucemia_debut                  = data['glucemia_debut'],
                exceso_peso_diagnostico         = data['exceso_peso_diagnostico'],
                tiempo_exceso_peso_anios        = data['tiempo_exceso_peso_anios'],
                tiempo_exceso_peso_meses        = data['tiempo_exceso_peso_meses'],
                remision                        = data['remision'],
                tratamiento_inicial             = "Ver esquema dinámico",
                dosis_tratamiento               = "Ver esquema dinámico",
                ano_inicio_tratamiento          = 0,
                tratamiento_inicial_json        = data['tratamiento_inicial_json'],
                prediabetes                     = data['prediabetes'],
                tiempo_prediabetes_anios        = data['tiempo_prediabetes_anios'],
                tiempo_prediabetes_meses        = data['tiempo_prediabetes_meses'],
                causa_fallecimiento             = data['causa_fallecimiento']
            )

            db.add(nuevo_paciente)
            db.commit()
            return True, data['no_hc']
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTODO NUEVO: obtiene TODOS los pacientes en UNA SOLA QUERY con su estado
    # Reemplaza completamente a get_pacientes_por_estado + get_estadisticas
    # ──────────────────────────────────────────────────────────────────────────

    def get_todos_los_pacientes(self, rol: str, inst_id: int, year_value: str) -> dict:
        """
        Devuelve en UNA sola query todos los pacientes con su estado calculado,
        la edad calculada en Python y los datos para las estadísticas.

        Retorna un dict con las claves:
          'todos', 'Ingresado', 'Seguimiento', 'No Ingresado', 'Defunción',
          'inactivos', 'stats'
        """
        db = Session()
        try:
            # ── 1. Subquery: para cada paciente, ¿tiene algún ingreso abierto? ──
            # Un ingreso "abierto" = fecha_egreso IS NULL
            # Usamos una subquery correlacionada que devuelve True/False.
            tiene_ingreso_abierto = (
                db.query(Ingreso.id)
                .filter(
                    Ingreso.paciente_id == Paciente.id,
                    Ingreso.fecha_egreso == None  # noqa: E711
                )
                .correlate(Paciente)
                .exists()
            )

            tiene_algun_ingreso = (
                db.query(Ingreso.id)
                .filter(Ingreso.paciente_id == Paciente.id)
                .correlate(Paciente)
                .exists()
            )

            # ── 2. CASE: calcula estado_automatico en SQL (cero queries extra) ──
            estado_sql = case(
                (Paciente.estado_actual == 'Defunción', 'Defunción'),
                (tiene_ingreso_abierto, 'Ingresado'),
                (and_(~tiene_ingreso_abierto, tiene_algun_ingreso), 'Seguimiento'),
                else_='No Ingresado'
            ).label('estado_automatico')

            # ── 3. LEFT OUTER JOIN con área de salud (un solo JOIN, no N queries) ──
            query = (
                db.query(
                    Paciente.no_hc,
                    Paciente.ci,
                    Paciente.nombres,
                    Paciente.apellidos,
                    Paciente.telefono,
                    Paciente.activo,
                    Paciente.estado_actual,
                    Paciente.fecha_hc,
                    AreaSalud.nombre.label('area_salud_nombre'),
                    estado_sql
                )
                .outerjoin(AreaSalud, Paciente.area_salud_id == AreaSalud.id)
            )

            # ── 4. Filtros ──
            if rol != 'superadministrador' and inst_id is not None:
                query = query.filter(Paciente.institucion_id == inst_id)

            if year_value and year_value != 'Todos':
                query = query.filter(
                    extract('year', Paciente.fecha_hc) == int(year_value)
                )

            filas = query.all()

            # ── 5. Calcular edad en Python (rápido, sin DB) ──
            def calcular_edad(ci: str):
                try:
                    if not ci or len(ci) != 11 or not ci.isdigit():
                        return 'N/D'
                    year_2d = int(ci[0:2])
                    month   = int(ci[2:4])
                    day     = int(ci[4:6])
                    siglo   = int(ci[6])
                    year = (2000 + year_2d) if siglo in (6, 7, 8) else (1900 + year_2d)
                    fn = datetime(year, month, day)
                    hoy = datetime.now()
                    if fn > hoy:
                        return 'N/D'
                    return (hoy.year - fn.year
                            - ((hoy.month, hoy.day) < (fn.month, fn.day)))
                except Exception:
                    return 'N/D'

            # ── 6. Clasificar en buckets en memoria (ya no hay queries) ──
            resultado = {
                'todos':        [],
                'Ingresado':    [],
                'Seguimiento':  [],
                'No Ingresado': [],
                'Defunción':    [],
                'inactivos':    [],
            }

            for fila in filas:
                entrada = {
                    'no_hc':      fila.no_hc,
                    'ci':         fila.ci,
                    'nombres':    fila.nombres,
                    'apellidos':  fila.apellidos,
                    'edad':       calcular_edad(fila.ci),
                    'area_salud': fila.area_salud_nombre or 'No asignada',
                    'telefono':   fila.telefono,
                }

                if not fila.activo:
                    resultado['inactivos'].append(entrada)
                    continue  # Los inactivos no van a ningún tab activo

                resultado['todos'].append(entrada)
                estado = fila.estado_automatico
                if estado in resultado:
                    resultado[estado].append(entrada)

            # ── 7. Estadísticas directamente de los buckets (sin query extra) ──
            activos = resultado['todos']
            resultado['stats'] = {
                'total':       len(activos),
                'ingresados':  len(resultado['Ingresado']),
                'seguimiento': len(resultado['Seguimiento']),
                'no_ingresado':len(resultado['No Ingresado']),
                'defunciones': len(resultado['Defunción']),
            }

            return resultado

        finally:
            db.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Los métodos viejos se mantienen por compatibilidad con otras partes
    # del sistema que puedan usarlos, pero la vista principal ya no los llama.
    # ──────────────────────────────────────────────────────────────────────────

    def get_pacientes_por_estado(self, rol: str, inst_id: int, year_value: str,
                                  estado: str = None, solo_inactivos: bool = False) -> list:
        """
        Mantenido por compatibilidad. Internamente delega al método optimizado.
        Si necesitas llamarlo directamente, funciona igual que antes.
        """
        todos = self.get_todos_los_pacientes(rol, inst_id, year_value)
        if solo_inactivos:
            return todos['inactivos']
        if estado is None:
            return todos['todos']
        return todos.get(estado, [])

    def get_estadisticas(self, rol: str, inst_id: int) -> dict:
        """
        Mantenido por compatibilidad. Calcula estadísticas de TODOS los años.
        """
        todos = self.get_todos_los_pacientes(rol, inst_id, 'Todos')
        return todos['stats']