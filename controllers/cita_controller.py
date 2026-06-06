from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from models import Session, Registro_consulta, Paciente

class CitaController:
    def __init__(self):
        # El controlador maneja su propia sesión
        self.db = Session()

    def __del__(self):
        # Nos aseguramos de cerrar la sesión para no dejar conexiones colgadas
        try:
            self.db.close()
        except:
            pass

    def obtener_pacientes_activos(self, institucion_id):
        """Devuelve los pacientes de la institución seleccionada."""
        try:
            query = self.db.query(Paciente).filter(Paciente.activo == True)
            if institucion_id is not None:
                query = query.filter(Paciente.institucion_id == institucion_id)
            return query.order_by(Paciente.apellidos, Paciente.nombres).all()
        except Exception as e:
            raise Exception(f"Error DB al obtener pacientes: {e}")

    def buscar_citas(self, fecha_seleccionada, institucion_id, search_text=None):
        """Devuelve una tupla: (citas_del_dia, proximas_citas)"""
        try:
            query_base = self.db.query(Registro_consulta).join(Paciente).options(joinedload(Registro_consulta.paciente))
            
            if institucion_id is not None:
                query_base = query_base.filter(Paciente.institucion_id == institucion_id)

            if search_text:
                like = f'%{search_text}%'
                query_base = query_base.filter(
                    or_(
                        Paciente.ci.ilike(like),
                        Paciente.nombres.ilike(like),
                        Paciente.apellidos.ilike(like),
                    )
                )

            # Citas del día seleccionado
            citas_dia = query_base.filter(Registro_consulta.fecha_consulta == fecha_seleccionada)\
                                  .order_by(Registro_consulta.hora).all()

            # Próximas citas (7 días desde hoy)
            hoy = date.today()
            fecha_fin = hoy + timedelta(days=7)
            proximas = query_base.filter(
                and_(
                    Registro_consulta.fecha_consulta > hoy,
                    Registro_consulta.fecha_consulta <= fecha_fin,
                )
            ).order_by(Registro_consulta.fecha_consulta, Registro_consulta.hora).all()

            return citas_dia, proximas
        except Exception as e:
            raise Exception(f"Error DB en la búsqueda de citas: {e}")

    def crear_cita(self, paciente_id, fecha, hora, notas):
        """Intenta crear una cita. Aplica reglas de negocio antes de tocar la DB."""
        try:
            # Regla de negocio: Evitar duplicados exactos
            duplicado = self.db.query(Registro_consulta).filter(
                Registro_consulta.paciente_id == paciente_id,
                Registro_consulta.fecha_consulta == fecha,
                Registro_consulta.hora == hora
            ).first()

            if duplicado:
                return False, "Ya existe una cita para ese paciente en esa fecha y hora."

            nueva_cita = Registro_consulta(
                paciente_id=paciente_id,
                fecha_consulta=fecha,
                hora=hora,
                notas=(notas or '').strip() or None
            )
            self.db.add(nueva_cita)
            self.db.commit()
            return True, "Cita guardada correctamente."
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error DB al guardar cita: {e}")