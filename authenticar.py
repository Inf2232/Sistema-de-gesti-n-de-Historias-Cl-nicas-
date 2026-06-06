from nicegui import ui, app
from datetime import datetime, timedelta
from models import Session, Usuario, LogAuditoria 
import bcrypt  

TIMEOUT_MINUTOS = 15
MAX_INTENTOS = 5
TIEMPO_BLOQUEO_MINS = 10

# Diccionario en memoria para bloqueo (clave: username, valor: dict con contador y timestamp de bloqueo)
intentos_fallidos = {}

def iniciar_sesion(usuario_obj):
    app.storage.user.update({
        'autenticado': True,
        'username': usuario_obj.username,
        'rol': usuario_obj.rol,
        'user_id': usuario_obj.id,
        'institucion_id': usuario_obj.institucion_id,
        'last_access': datetime.now().isoformat()
    })

def cerrar_sesion():
 
    app.storage.user.clear() # Borra todos los datos de sesión de ESTE usuario
    ui.navigate.to('/')

def verificar_autenticacion():
    
    # 1. ¿Existe registro de sesión?
    if not app.storage.user.get('autenticado'):
        return False
    
    # 2. Obtener último acceso
    last_access_str = app.storage.user.get('last_access')
    if not last_access_str:
        cerrar_sesion()
        return False
        
    last_access = datetime.fromisoformat(last_access_str)
    
    # 3. Calcular tiempo de inactividad
    inactividad = datetime.now() - last_access
    
    if inactividad > timedelta(minutes=TIMEOUT_MINUTOS):
        # DETECCIÓN AUTOMÁTICA: Si pasó más del tiempo permitido, fuera.
        
        
        ui.notify('Sesión cerrada por inactividad por su seguridad', type='warning')
        cerrar_sesion()
        return False
    
    # 4. Si es válida, actualizamos la hora para "renovar" otros 15 minutos
    app.storage.user['last_access'] = datetime.now().isoformat()
    return True

def manejar_intento_fallido(username):
   
    ahora = datetime.now()
    
    if username not in intentos_fallidos:
        intentos_fallidos[username] = {'contador': 1, 'bloqueado_hasta': None}
    else:
        intentos_fallidos[username]['contador'] += 1
        
    # Si llega al máximo, bloqueamos por 10 min
    if intentos_fallidos[username]['contador'] >= MAX_INTENTOS:
        intentos_fallidos[username]['bloqueado_hasta'] = ahora + timedelta(minutes=TIEMPO_BLOQUEO_MINS)
        return True # Está bloqueado
    return False

def esta_bloqueado(username):
    """Verifica si el usuario está en periodo de penalización."""
    if username in intentos_fallidos:
        bloqueo = intentos_fallidos[username]['bloqueado_hasta']
        if bloqueo and datetime.now() < bloqueo:
            return True
        elif bloqueo and datetime.now() > bloqueo:
            # El tiempo de bloqueo ya pasó, reseteamos
            del intentos_fallidos[username]
    return False

def devolver_usuario_actual():
  
    if not verificar_autenticacion():
        return None
    
    return {
        "username": app.storage.user.get('username'),
        "rol": app.storage.user.get('rol'),
        "user_id": app.storage.user.get('user_id'),
        "institucion_id": app.storage.user.get('institucion_id')
    }

#  Funciones de Rol 

def es_admin():
    user = devolver_usuario_actual()
    return user is not None and user['rol'] in ['SuperAdministrador', 'superadmin']

def es_superadmin():
    user = devolver_usuario_actual()
    return user is not None and user['institucion_id'] is None

def es_medico():
    user = devolver_usuario_actual()
    return user is not None and user['rol'] == 'medico'

def verificar_login(usuario_input, password_input):
    """
    Valida las credenciales, maneja el bloqueo por intentos y arranca la sesión.
    """
    session = Session()
    try:
        username = usuario_input.value.strip()
        password = password_input.value.strip()
        
        # 1. Verificar si el usuario ya está bloqueado localmente
        if esta_bloqueado(username):
            ui.notify(f'Cuenta bloqueada. Intente más tarde.', type='negative')
            return False

        # 2. Buscar usuario en la DB
        user = session.query(Usuario).filter(Usuario.username == username).first()
        
        # 3. Validar contraseña con Bcrypt (usando el método del modelo)
        if user and user.verificar_password(password):
            # --- LOGIN EXITOSO ---
            iniciar_sesion(user) 
            
            # Resetear intentos fallidos al entrar con éxito
            if username in intentos_fallidos:
                del intentos_fallidos[username]
            
            # Auditoría de login
            user.ultimo_acceso = datetime.now()
            session.commit()
            
            ui.notify(f'Bienvenido, {user.username}', type='positive')
            # Registro de auditoría
            nuevo_log = LogAuditoria(
                usuario=user.username,
                accion='login',
                tabla='usuarios',
                registro_id=user.id,
                detalles=f'Inicio de sesión exitoso. Institución ID: {user.institucion_id}'
            )
            session.add(nuevo_log)
            session.commit()
            return True
        
        
        else:
            # --- LOGIN FALLIDO ---
            bloqueado = manejar_intento_fallido(username)
            if bloqueado:
                ui.notify('Demasiados intentos. Cuenta bloqueada por 10 min.', type='negative')
            else:
                ui.notify('Usuario o contraseña incorrectos', type='negative')
            return False

    except Exception as e:
        ui.notify(f'Error de sistema: {str(e)}', type='negative')
        return False
    finally:
        session.close()