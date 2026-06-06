# usuario_controller.py
from models import Session, Usuario, Rol, Institucion

class UsuarioController:
    def __init__(self):
        self.db = Session()

    def __del__(self):
        try:
            self.db.close()
        except:
            pass

    def obtener_todos_los_usuarios(self):
        """Devuelve la lista completa de usuarios."""
        try:
            return self.db.query(Usuario).all()
        except Exception as e:
            raise Exception(f"Error al obtener usuarios: {e}")

    def obtener_roles(self):
        """Obtiene todos los roles disponibles para el selector."""
        return self.db.query(Rol).all()

    def obtener_instituciones(self):
        """Obtiene todas las instituciones para el selector."""
        return self.db.query(Institucion).all()

    def guardar_usuario(self, username, password, rol_id, institucion_id, user_id=None):
        """Crea o edita un usuario aplicando las reglas de seguridad de contraseñas."""
        if not username or not username.strip():
            return False, "El nombre de usuario es obligatorio."
        if not rol_id:
            return False, "Debe seleccionar un rol para el usuario."

        username_limpio = username.strip()

        try:
            if user_id:
                # --- MODO EDICIÓN ---
                user = self.db.query(Usuario).filter_by(id=user_id).first()
                if not user:
                    return False, "Usuario no encontrado."
                
                # Validar que el nuevo username no esté duplicado en otro usuario
                duplicado = self.db.query(Usuario).filter(
                    Usuario.username == username_limpio, 
                    Usuario.id != user_id
                ).first()
                if duplicado:
                    return False, "Ya existe otro usuario con ese nombre."

                user.username = username_limpio
                user.rol_id = rol_id
                user.institucion_id = institucion_id
                
                # Si escribió algo en la contraseña, se actualiza su hash
                if password and password.strip():
                    user.password_hash = Usuario.hash_password(password.strip())
                
                mensaje = "Usuario actualizado con éxito."
            else:
                # --- MODO CREACIÓN ---
                if not password or not password.strip():
                    return False, "La contraseña es obligatoria para nuevos usuarios."
                
                duplicado = self.db.query(Usuario).filter_by(username=username_limpio).first()
                if duplicado:
                    return False, "Ya existe un usuario con ese nombre."

                nuevo = Usuario(
                    username=username_limpio,
                    password_hash=Usuario.hash_password(password.strip()),
                    rol_id=rol_id,
                    institucion_id=institucion_id
                )
                self.db.add(nuevo)
                mensaje = "Usuario registrado con éxito."

            self.db.commit()
            return True, mensaje

        except Exception as e:
            self.db.rollback()
            return False, f"Error en la base de datos: {str(e)}"

    def eliminar_usuario(self, user_id):
        """Elimina físicamente un usuario validando que no sea el último Administrador."""
        try:
            usuario = self.db.query(Usuario).filter_by(id=user_id).first()
            if not usuario:
                return False, "Usuario no encontrado."

            # Regla de Tesis: Validar si es el último administrador del sistema
            if usuario.rol_relacion and usuario.rol_relacion.nombre.lower() == 'admin':
                admins_restantes = self.db.query(Usuario).join(Rol).filter(Rol.nombre.ilike('admin')).count()
                if admins_restantes <= 1:
                    return False, "Operación denegada: Debe existir al menos un administrador en el sistema."

            self.db.delete(usuario)
            self.db.commit()
            return True, "Usuario eliminado exitosamente."

        except Exception as e:
            self.db.rollback()
            return False, f"No se pudo eliminar debido a restricciones de integridad: {str(e)}"