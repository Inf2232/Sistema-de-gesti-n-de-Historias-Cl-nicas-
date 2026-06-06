
from functools import wraps
from nicegui import ui
from models import Session, Usuario, Rol, Permiso
from sqlalchemy.orm import joinedload
from Errores import log_error_and_notify

def requiere_permiso(codename):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from authenticar import devolver_usuario_actual
            
            user_data = devolver_usuario_actual()
            
            # CASO 1: No hay sesión (El usuario cerró sesión o expiró)
            if not user_data:
                ui.notify('Sesión expirada. Inicie sesión nuevamente.', type='negative')
                ui.navigate.to('/')
                return

            db = Session()
            try:
                usuario = db.query(Usuario).options(
                    joinedload(Usuario.rol_relacion).joinedload(Rol.permisos)
                ).filter(Usuario.username == user_data['username']).first()

                # CASO 2: Usuario logueado pero sin rol asignado
                if not usuario or not usuario.rol_relacion:
                    ui.notify('Su cuenta no tiene un rol asignado. Contacte al administrador.', type='warning')
                    # No lo mandamos al login, lo mandamos al dashboard que es seguro
                    ui.navigate.to('/dashboard') 
                    return

                # Regla de Oro: Admins siempre pasan
                if usuario.rol_relacion.nombre.lower() in ['superadministrador', 'admin']:
                    return func(*args, **kwargs)

                # CASO 3: Verificación de permisos
                permisos_usuario = [p.codename for p in usuario.rol_relacion.permisos]
                
                if codename not in permisos_usuario:
                    # NOTIFICACIÓN SIN REDIRECCIÓN FORZADA AL LOGIN
                    ui.notify(f'🚫 Acceso Denegado: Requiere permiso [{codename}]', 
                              type='negative', 
                              position='top')
                    
                    # Si ya está en una página (como la HC) y trató de hacer algo prohibido,
                    # simplemente no hacemos nada para que no pierda lo que estaba viendo.
                    # Opcionalmente, puedes mandarlo al dashboard si la PÁGINA entera es prohibida.
                    return 

                # Si todo está bien, ejecutar la función
                return func(*args, **kwargs)

            except Exception as e:
                print(f"Error en verificación de permisos: {e}")
                log_error_and_notify(e, "Error en verificación de permisos", ui_notify=False)
                ui.notify('Error de validación de permisos', type='negative')
                return
            finally:
                db.close()
        return wrapper
    return decorador

def tiene_permiso(codename):
    """
    Función global para verificar si el usuario actual tiene un permiso.
    Ideal para usar en bloques 'if' dentro de la interfaz.
    """
    from authenticar import devolver_usuario_actual
    from models import Session, Usuario
    
    user_data = devolver_usuario_actual()
    if not user_data:
        return False
        
    db = Session()
    try:
        # Buscamos al usuario y cargamos su rol y permisos en una sola consulta
        usuario = db.query(Usuario).options(
            joinedload(Usuario.rol_relacion).joinedload(Rol.permisos)
        ).filter(Usuario.username == user_data['username']).first()

        if not usuario or not usuario.rol_relacion:
            return False

        # El administrador siempre tiene permiso
        if usuario.rol_relacion.nombre.lower() in ['admin', 'superadministrador']:
            return True

        # Verificamos si el codename está en su lista de permisos
        return any(p.codename == codename for p in usuario.rol_relacion.permisos)
    
    except Exception as e:
        print(f"Error en verificación de permisos 2: {e}")
        log_error_and_notify(e, "Error en verificación de permisos", ui_notify=False)
        print(f"Error en verificación de permisos: {e}")
        return False
    finally:
        db.close()