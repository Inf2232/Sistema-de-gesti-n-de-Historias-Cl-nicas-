from zipfile import Path

from nicegui import ui, events, app
from authenticar import (
    verificar_login, 
    verificar_autenticacion, 
    es_medico, 
    es_admin, 
    esta_bloqueado, 
    cerrar_sesion,
)
import os
import sys
from views.diabetes_app import DiabetesApp
from models import *

from views.historia_clinica import HistoriaClinicaApp
from views.configuracionapp import ConfiguracionApp
from views.dashboard import Dashboard
from dotenv import load_dotenv
from Errores import log_error_and_notify 
from models import registrar_acceso_lectura
from seguridad_roles import requiere_permiso
import sqlite3
import shutil
from datetime import datetime

from views.informes_page import InformesApp


def ejecutar_backup_global_seguro():
    """Crea un backup en una ruta externa al programa al iniciar."""
    try:
        # 1. RUTA DE ORIGEN (donde está tu base de datos actual)
        base_dir = os.path.dirname(__file__)
        db_path = os.path.join(base_dir, 'data/diabetes_app.db')

        # 2. RUTA EXTERNA (Aquí eliges una carpeta fuera del proyecto)
        # Puedes usar una ruta absoluta como 'C:/Backups_Diabetes' o una carpeta en Documentos
        ruta_externa = os.path.join(os.path.expanduser('~'), 'Documents', 'Backups_Diabetes_App')
        
        if not os.path.exists(ruta_externa):
            os.makedirs(ruta_externa, exist_ok=True)

        # 3. NOMBRE DEL ARCHIVO
        fecha_hoy = datetime.now().strftime('%Y_%m_%d')
        nombre_backup = f"backup_seguro_{fecha_hoy}.db"
        destino_final = os.path.join(ruta_externa, nombre_backup)

        # 4. EJECUCIÓN 
        if not os.path.exists(destino_final):
            # Usamos el método nativo de sqlite3 para no bloquear el archivo
            conn = sqlite3.connect(db_path)
            dest = sqlite3.connect(destino_final)
            with dest:
                conn.backup(dest)
            dest.close()
            conn.close()
            print(f"✅ Respaldo diario creado en: {destino_final}")
        else:
            print("ℹ️ El respaldo de hoy ya existe en la carpeta externa.")

    except Exception as e:
        print(f"❌ Error en el backup automático: {e}")

# LANZAR EL BACKUP AL ARRANCAR EL PROGRAMA
ejecutar_backup_global_seguro()
# 1. Cargar las variables al iniciar la aplicación
load_dotenv()
def validar_seguridad():
    """Valida la presencia y robustez de la clave secreta."""
    key = os.getenv('NICEGUI_SECRET_KEY')
    
    try:
        if not key:
            raise ValueError("La variable NICEGUI_SECRET_KEY no existe en el archivo .env")
        
        if len(key) < 32:
            raise ValueError("La SECRET_KEY es demasiado corta (mínimo 32 caracteres para seguridad HCE)")
            
        return key

    except Exception as e:
        # Registramos el error en app_errors.log usando tu función existente
        log_error_and_notify(e, "Configuración de Seguridad Inicial", ui_notify=False)
        
    
        
        sys.exit(1) # Cierre forzoso de la aplicación

# Ejecutar validación
SECRET_KEY = validar_seguridad()

@ui.page('/', title="Login")
def login_page():
    # NiceGUI maneja el contexto de los elementos dentro de la función de la página
    with ui.column().classes('w-full h-screen justify-center items-center bg-gray-50'):
        ui.image('login.png').classes('absolute inset-0 w-full h-full object-cover z-0 opacity-20')
        
        with ui.card().classes('''
            w-96 z-10 bg-white/90 backdrop-blur-sm
            shadow-xl hover:shadow-2xl transition-shadow duration-300
            rounded-xl p-8 border border-gray-100
            '''):
            
            with ui.column().classes('w-full items-center mb-8'):
                ui.icon('account_circle', size='lg', color='primary').classes('text-4xl mb-2')
                ui.label('Bienvenido').classes('text-2xl font-bold text-gray-800')
                ui.label('Inicia sesión en tu cuenta').classes('text-sm text-gray-500')
            
            usuario_input = ui.input('Usuario').classes('w-full mb-4')
            password_input = ui.input('Contraseña', password=True, password_toggle_button=True).classes('w-full mb-6')
            
            async def manejar_intento_login():
                username = usuario_input.value.strip()
                
                # 1. Verificar si el usuario está bloqueado por demasiados intentos
                if esta_bloqueado(username):
                    ui.notify('Esta cuenta está bloqueada temporalmente. Intente más tarde.', type='negative')
                    return

                # 2. Llamar a la función de verificación (que ahora es asíncrona)
                exito =  verificar_login(usuario_input, password_input)
                if exito:
                    ui.navigate.to('/principal')
                # El "else" no es necesario porque verificar_login ya lanza sus propias notificaciones

            # Handler para la tecla Enter
            ui.keyboard(on_key=lambda e: manejar_intento_login() if e.key.enter and e.action.keydown else None)
            
            ui.button('Ingresar', on_click=manejar_intento_login).classes('''
                w-full py-2 rounded-lg bg-primary text-white font-medium 
                transition-colors duration-300 shadow hover:shadow-md
                ''')

@ui.page('/principal', title="Principal")
def pagina_principal():
    if not verificar_autenticacion():
        return ui.navigate.to('/')
    
    diabetes_app = DiabetesApp()
    diabetes_app.mostrar_lista_pacientes()


@ui.page('/historia_clinica/{no_hc}', title="Historia Clínica")
@requiere_permiso('hc_view')
def historia_clinica_page(no_hc):
    if not verificar_autenticacion():
        return ui.navigate.to('/')
    registrar_acceso_lectura(no_hc)
    
    historia_app = HistoriaClinicaApp(no_hc)
    historia_app.mostrar_datos_generales()

@ui.page('/configuracion')
@requiere_permiso('config_view')
def configuracion_page():
    if not verificar_autenticacion():
        return ui.navigate.to('/')

    configuracion_app = ConfiguracionApp()
    configuracion_app.setup_configuracion_ui()

@ui.page('/dashboard', title="Dashboard")

def dashboard_page():
    if not verificar_autenticacion():
        return ui.navigate.to('/')

    dashboardapp = Dashboard()
    F1 = date(2005, 1, 1).strftime('%Y-%m-%d')
    F2 = date.today().strftime('%Y-%m-%d')
    dashboardapp.setup_dashboard_filtrado(F1, F2)

@ui.page('/citas', title='Citas')
@requiere_permiso('agenda_view')
def page_citas():
    
    if not verificar_autenticacion():
        return ui.navigate.to('/')
    
    from views.citas import CitasPage
    citas_page = CitasPage()
    citas_page.mostrar_page()

@ui.page('/informes', title='Informes')
@requiere_permiso('informes_view')
def pagina_informes():

    if not verificar_autenticacion():
        return ui.navigate.to('/')
    
    InformesApp()

if __name__ in {"__main__", "__mp_main__"}:
    # Obtener el directorio actual para el reload
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    ui.run(
        host="0.0.0.0",
        port=8080,
        title="HCE Médica",
        storage_secret=SECRET_KEY, 
        reload=True,
        uvicorn_reload_dirs=app_dir,
        language='es-ES',
        favicon="🩺",
        )