# institucion_controller.py
from models import Session, Institucion

class InstitucionController:
    def __init__(self):
        self.db = Session()

    def __del__(self):
        try:
            self.db.close()
        except:
            pass

    def obtener_instituciones(self):
        try:
            return self.db.query(Institucion).order_by(Institucion.nombre).all()
        except Exception as e:
            raise Exception(f"Error al obtener instituciones: {e}")

    def obtener_institucion_por_id(self, inst_id):
        if not inst_id: 
            return None
        return self.db.query(Institucion).get(inst_id)

    def guardar_institucion(self, nombre, direccion, provincia_default, institucion_id=None):
        if not nombre or not nombre.strip():
            return False, "El nombre de la institución es obligatorio."

        # Limpiamos los datos de espacios vacíos
        nombre_limpio = nombre.strip()
        dir_limpia = direccion.strip() if direccion else None
        prov_limpia = provincia_default.strip() if provincia_default else None

        try:
            if institucion_id:
                # Editar existente
                inst = self.db.query(Institucion).get(institucion_id)
                if not inst:
                    return False, "La institución no existe."
                inst.nombre = nombre_limpio
                inst.direccion = dir_limpia
                inst.provincia_default = prov_limpia
                mensaje = "Institución actualizada con éxito."
            else:
                # Crear nueva
                duplicado = self.db.query(Institucion).filter_by(nombre=nombre_limpio).first()
                if duplicado:
                    return False, "Ya existe una institución con ese nombre."
                
                inst = Institucion(nombre=nombre_limpio, direccion=dir_limpia, provincia_default=prov_limpia)
                self.db.add(inst)
                mensaje = "Institución agregada con éxito."

            self.db.commit()
            return True, mensaje

        except Exception as e:
            self.db.rollback()
            return False, f"Error en BD: {str(e)}"