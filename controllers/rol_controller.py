# rol_controller.py
from models import Session, Rol, Permiso, Usuario

class RolController:
    def __init__(self):
        self.db = Session()

    def __del__(self):
        try:
            self.db.close()
        except:
            pass

    def obtener_roles(self):
        """Retorna todos los roles ordenados por nombre."""
        return self.db.query(Rol).order_by(Rol.nombre).all()

    def obtener_permisos(self):
        """Retorna el catálogo completo de permisos del sistema."""
        return self.db.query(Permiso).all()

    def obtener_rol_por_id(self, rol_id):
        """Obtiene un rol específico con sus relaciones cargadas."""
        return self.db.query(Rol).filter_by(id=rol_id).first()

    def crear_rol(self, nombre):
        """Registra un nuevo rol controlando duplicados."""
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            return False, "El nombre del rol es obligatorio."

        try:
            duplicado = self.db.query(Rol).filter(Rol.nombre.ilike(nombre_limpio)).first()
            if duplicado:
                return False, f'El rol "{nombre_limpio}" ya existe en el sistema.'

            nuevo_rol = Rol(nombre=nombre_limpio)
            self.db.add(nuevo_rol)
            self.db.commit()
            return True, nuevo_rol # Retornamos el objeto para seleccionarlo automáticamente
        except Exception as e:
            self.db.rollback()
            return False, f"Error al guardar en la base de datos: {str(e)}"

    def eliminar_rol(self, rol_id):
        """Aplica reglas estrictas antes de eliminar físicamente un rol."""
        try:
            rol = self.db.query(Rol).filter_by(id=rol_id).first()
            if not rol:
                return False, "El rol seleccionado ya no existe."

            # 1. Protección de roles Core de la aplicación médica
            if rol.nombre.lower() in ['admin', 'superadministrador', 'médico']:
                return False, f'El rol "{rol.nombre}" es un rol base del sistema y no puede ser eliminado.'

            # 2. Control de integridad referencial (Usuarios dependientes)
            usuarios_asignados = self.db.query(Usuario).filter_by(rol_id=rol_id).count()
            if usuarios_asignados > 0:
                return False, f'No se puede eliminar: existen {usuarios_asignados} usuarios asignados a este rol actualmente.'

            self.db.delete(rol)
            self.db.commit()
            return True, "Rol eliminado correctamente de los registros."
        except Exception as e:
            self.db.rollback()
            return False, f"Error de integridad: {str(e)}"

    def guardar_permisos_rol(self, rol_id, ids_permisos_seleccionados):
        """Sincroniza la tabla intermedia muchos a muchos (rol_permiso)."""
        try:
            rol = self.db.query(Rol).filter_by(id=rol_id).first()
            if not rol:
                return False, "Rol no encontrado."

            # Buscamos las entidades Permiso correspondientes a los IDs marcados en la UI
            nuevos_permisos = self.db.query(Permiso).filter(Permiso.id.in_(ids_permisos_seleccionados)).all()
            
            # SQLAlchemy gestiona automáticamente el INSERT/DELETE en la tabla asociativa
            rol.permisos = nuevos_permisos
            self.db.commit()
            return True, f"Permisos sincronizados correctamente para el rol: {rol.nombre}"
        except Exception as e:
            self.db.rollback()
            return False, f"Error al actualizar la matriz de permisos: {str(e)}"