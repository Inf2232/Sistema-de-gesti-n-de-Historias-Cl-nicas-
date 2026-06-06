from nicegui import ui
from authenticar import *

class SidebarReutilizable:
    def __init__(self, app_instance):
        self.app = app_instance
        self.drawer = None
    
    def crear_sidebar(self):
        self.drawer = ui.left_drawer().classes('''
            bg-gradient-to-b from-indigo-700 to-blue-800 
            p-4 w-20 shadow-xl
            transition-all duration-300 ease-in-out
        ''').props('width=180 bordered')
        
        with self.drawer:
            
            self._agregar_botones_base()
            self._agregar_seccion_inferior()
        
        return self.drawer
    
    def _agregar_botones_base(self):
        

            
            self._crear_boton_sidebar(
                icon='people',
                text='Pacientes',
                target='/principal',
                color='from-blue-600 to-blue-500'
            )
            self._crear_boton_sidebar(
                icon='calendar_month',
                text='Citas',
                target='/citas',
                color='from-blue-600 to-blue-500'

            )
            self._crear_boton_sidebar(
                icon='receipt',
                text='Informes',
                target='/informes',
                color='from-blue-600 to-blue-500'

            )

            
    
    def _crear_boton_sidebar(self, icon, text, target, color):
        """Método auxiliar para crear botones consistentes"""
        with ui.button(on_click=lambda: ui.navigate.to(target)).classes(f'''
            w-full mb-1 rounded-xl p-3 
            transition-all duration-200 
            bg-gradient-to-r {color}
            hover:shadow-md hover:scale-[1.02]
            text-white
        '''):
            with ui.row().classes('items-center gap-3'):
                ui.icon(icon).classes('text-lg')
                ui.label(text).classes('text-sm font-medium')
    


    
    def _agregar_seccion_inferior(self):
        ui.separator().classes('my-4 opacity-50')
        ui.space().classes('flex-grow')
        ui.element('div').classes('flex-grow')
        with ui.row().classes('w-full gap-2'):
            ui.button(icon="dashboard" ,on_click=lambda: ui.navigate.to('/dashboard')).classes('w-full bg-gray-700 from-gray-600 to-gray-500 hover:bg-gray-600 text-white rounded-lg p-3 transition-all duration-300').tooltip('Dashboard')
            ui.button(icon='settings', on_click=lambda: ui.navigate.to('/configuracion')).classes('w-full bg-gray-700 from-gray-600 to-gray-500 hover:bg-gray-600 text-white rounded-lg p-3 transition-all duration-300').tooltip('Configuracion del sistema')
            