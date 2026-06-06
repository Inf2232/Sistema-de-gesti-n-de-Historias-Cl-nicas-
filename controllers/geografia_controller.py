# geografia_controller.py
from models import Session, Provincia, Municipio, AreaSalud, Paciente, Institucion

class GeografiaController:
    def __init__(self):
        self.db = Session()

    def __del__(self):
        try:
            self.db.close()
        except:
            pass

    # ==========================================
    # LÓGICA DE PROVINCIAS
    # ==========================================
    def obtener_provincias(self):
        try:
            return self.db.query(Provincia).order_by(Provincia.nombre).all()
        except Exception as e:
            raise Exception(f"Error al obtener provincias: {e}")

    def guardar_provincia(self, nombre, codigo, provincia_id=None):
        if not nombre or not nombre.strip() or not codigo or not codigo.strip():
            return False, "Faltan datos obligatorios para la provincia."
        
        nombre_limpio = nombre.strip()
        codigo_limpio = codigo.strip()

        try:
            if provincia_id:
                prov = self.db.query(Provincia).get(provincia_id)
                if not prov:
                    return False, "La provincia no existe."
                prov.nombre = nombre_limpio
                prov.codigo = codigo_limpio
                mensaje = "Provincia actualizada con éxito."
            else:
                # Evitar duplicados
                duplicado = self.db.query(Provincia).filter_by(codigo=codigo_limpio).first()
                if duplicado:
                    return False, "Ya existe una provincia con ese código."
                
                prov = Provincia(nombre=nombre_limpio, codigo=codigo_limpio)
                self.db.add(prov)
                mensaje = "Provincia agregada con éxito."

            self.db.commit()
            return True, mensaje
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"

    def eliminar_provincia(self, provincia_id):
        if not provincia_id:
            return False, "Seleccione una provincia."
        try:
            # Regla de Tesis: No romper la integridad si hay municipios vinculados
            tiene_municipios = self.db.query(Municipio).filter_by(provincia_id=provincia_id).first()
            if tiene_municipios:
                return False, "No se puede eliminar: tiene municipios asociados."
            
            prov = self.db.query(Provincia).get(provincia_id)
            if prov:
                self.db.delete(prov)
                self.db.commit()
                return True, "Provincia eliminada."
            return False, "Provincia no encontrada."
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"

    # ==========================================
    # LÓGICA DE MUNICIPIOS
    # ==========================================
    def obtener_municipios_por_provincia(self, provincia_id):
        if not provincia_id: return []
        return self.db.query(Municipio).filter_by(provincia_id=provincia_id).order_by(Municipio.nombre).all()

    def guardar_municipio(self, nombre, codigo, provincia_id, municipio_id=None):
        if not provincia_id:
            return False, "Debe seleccionar una provincia."
        if not nombre or not nombre.strip():
            return False, "El nombre del municipio es obligatorio."
        
        nombre_limpio = nombre.strip()
        codigo_limpio = codigo.strip() if codigo else None

        try:
            if municipio_id:
                mun = self.db.query(Municipio).get(municipio_id)
                if not mun: return False, "El municipio no existe."
                mun.nombre = nombre_limpio
                mun.codigo = codigo_limpio
                mensaje = "Municipio actualizado."
            else:
                mun = Municipio(nombre=nombre_limpio, codigo=codigo_limpio, provincia_id=provincia_id)
                self.db.add(mun)
                mensaje = "Municipio agregado."

            self.db.commit()
            return True, mensaje
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"

    def eliminar_municipio(self, municipio_id):
        if not municipio_id: return False, "Seleccione municipio."
        try:
            # Regla de Tesis: Validar áreas de salud asociadas
            tiene_areas = self.db.query(AreaSalud).filter_by(municipio_id=municipio_id).first()
            if tiene_areas:
                return False, "No se puede eliminar: tiene áreas de salud asociadas."
            
            mun = self.db.query(Municipio).get(municipio_id)
            if mun:
                self.db.delete(mun)
                self.db.commit()
                return True, "Municipio eliminado."
            return False, "Municipio no encontrado."
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"

    # ==========================================
    # LÓGICA DE ÁREAS DE SALUD
    # ==========================================
    def obtener_areas_por_municipio(self, municipio_id):
        if not municipio_id: return []
        return self.db.query(AreaSalud).filter_by(municipio_id=municipio_id).order_by(AreaSalud.nombre).all()

    def obtener_area_por_id(self, area_id):
        return self.db.query(AreaSalud).get(area_id) if area_id else None

    def guardar_area_salud(self, nombre, municipio_id, area_id=None):
        if not nombre or not nombre.strip() or not municipio_id:
            return False, "Datos de área incompletos."
        nombre_limpio = nombre.strip()
        try:
            if area_id:
                area = self.db.query(AreaSalud).get(area_id)
                if not area: return False, "El área no existe."
                area.nombre = nombre_limpio
                mensaje = "Área de salud actualizada."
            else:
                duplicado = self.db.query(AreaSalud).filter_by(nombre=nombre_limpio, municipio_id=municipio_id).first()
                if duplicado: return False, "Ya existe un área con ese nombre en este municipio."
                
                area = AreaSalud(nombre=nombre_limpio, municipio_id=municipio_id)
                self.db.add(area)
                mensaje = "Área de salud agregada."
            self.db.commit()
            return True, mensaje
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"

    def eliminar_area_salud(self, area_id):
        if not area_id: return False, "Seleccione un área."
        try:
            tiene_pacientes = self.db.query(Paciente).filter_by(area_salud_id=area_id).first()
            if tiene_pacientes:
                return False, "No se puede eliminar: existen historias clínicas vinculadas."
            
            area = self.db.query(AreaSalud).get(area_id)
            if area:
                self.db.delete(area)
                self.db.commit()
                return True, "Área de salud eliminada."
            return False, "Área no encontrada."
        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"