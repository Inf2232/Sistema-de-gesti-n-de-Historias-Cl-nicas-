
import traceback
from datetime import datetime
from nicegui import ui
import os

LOG_FILE = 'app_errors.log'

def log_error_and_notify(e: Exception, context: str, ui_notify: bool = True):
    """
    Registra el traceback del error en un archivo de log y notifica a la UI.

    :param e: La excepción capturada.
    :param context: Descripción de dónde ocurrió el error (ej. "Carga de Paciente").
    :param ui_notify: Si se debe mostrar una notificación en la UI.
    """
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_detail = traceback.format_exc()
    log_message = (
        f"[{error_time}] ERROR en {context}:\n"
        f"Tipo de Excepción: {type(e).__name__}\n"
        f"Mensaje: {str(e)}\n"
        f"--- TRACEBACK ---\n"
        f"{error_detail}\n"
        f"========================================\n\n"
    )

    # 1. Loggear el traceback en el archivo
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message)
    except Exception as io_e:
        print(f"ERROR: No se pudo escribir en el archivo de log: {io_e}")
        print(log_message) # Imprimir en consola si no se puede loggear

    # 2. Notificar al usuario
    if ui_notify:
        # Mostramos un mensaje genérico, pero el log tiene los detalles sensibles.
        ui.notify(
            f'❌ Error en {context}. Revise los logs para detalles técnicos.', 
            type='negative', 
            position='top', 
            timeout=5000
        )