import os
from models import engine, Base, Session, Rol, Permiso, Usuario

def bootstrap_system():
    print("🛠️ Iniciando recuperación del sistema...")
    
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    session = Session()

    try:
        # 1. Definir Permisos Críticos
        permisos_nombres = [
            ('Ver Listado de Pacientes', 'pacientes_view', 'Permite acceder a la tabla general de pacientes'),
('Crear Nuevo Paciente', 'pacientes_add', 'Permite registrar nuevos pacientes en el sistema'),
('Editar Datos de Paciente', 'pacientes_edit', 'Permite modificar datos demográficos y de contacto'),
('Eliminar Paciente', 'pacientes_delete', 'Permite dar de baja o archivar un registro de paciente'),
('Ver Historia Clínica', 'hc_view', 'Acceso general a la ficha del paciente'),
('Ver Agenda', 'agenda_view', 'Permite ver el calendario de citas'),
('Agendar Citas', 'agenda_add', 'Permite crear nuevos turnos'),
('Cancelar Citas', 'agenda_cancel', 'Permite anular citas programadas'),
('Exportar Datos Médicos', 'export_data', 'Permite generar PDFs o Excels con información sensible'),
('Configuración', 'config_admin', 'Acceso a la configuración global del sistema'),
('Ver Panel Clínico', 'panel_clinico_view', 'Acceso al dashboard con estadísticas e indicadores clínicos'),
('Gestionar Antecedentes Personales', 'ant_personales_manage', 'Ver, editar y eliminar antecedentes personales'),
('Gestionar Antecedentes Familiares', 'ant_familiares_manage', 'Ver, editar y eliminar antecedentes familiares'),
('Gestionar Antecedentes Familiares Diabetes', 'ant_fam_diabetes_manage', 'Ver, editar y eliminar antecedentes de diabetes'),
('Gestionar Historia Obstétrica', 'hist_obstetrica_manage', 'Ver, editar y eliminar datos gineco-obstétricos'),
('Gestionar Hábitos Tóxicos', 'habitos_toxicos_manage', 'Ver, editar y eliminar hábitos (tabaquismo, alcohol, etc.)') ,      
('Gestionar Tratamiento Actual', 'tratamiento_actual_manage', 'Ver, editar y eliminar tratamientos farmacológicos actuales'),
('Gestionar Otros Tratamientos', 'otros_tratamientos_manage', 'Ver, editar y eliminar tratamientos no farmacológicos'),
('Gestionar Examen Físico', 'examen_fisico_manage', 'Ver, editar y eliminar hallazgos del examen físico'),
('Gestionar Mensuraciones', 'mensuraciones_manage', 'Ver, editar y eliminar peso, talla, IMC, TA'),
('Gestionar Examen Miembros Inferiores', 'miembros_inf_manage', 'Ver, editar y eliminar examen de pies y sensibilidad')     ,
('Gestionar Oftalmología', 'oftalmologia_manage', 'Ver, editar y eliminar fondo de ojo y agudeza visual'),
('Gestionar Nefrología', 'nefrologia_manage', 'Ver, editar y eliminar evaluación renal'),
('Gestionar Estomatología', 'estomatologia_manage', 'Ver, editar y eliminar salud bucal'),
('Gestionar Cardiología', 'cardiologia_manage', 'Ver, editar y eliminar ECG y evaluación cardíaca'),
('Gestionar Educación Diabetológica', 'educacion_diab_manage', 'Ver, editar y eliminar resultados de educación al paciente'),
('Gestionar Complementarios', 'complementarios_manage', 'Ver, editar y eliminar resultados de laboratorio y Rayos X'),
('Gestionar Indicaciones', 'indicaciones_manage', 'Ver, editar y eliminar órdenes médicas'),
('Gestionar Ingresos', 'ingresos_manage', 'Ver, editar y eliminar registros de hospitalización')   
        ]
        
        objetos_permiso = []
        for nombre, code, desc in permisos_nombres:
            p = session.query(Permiso).filter_by(codename=code).first()
            if not p:
                p = Permiso(nombre=nombre, codename=code, descripcion=desc)
                session.add(p)
                print(f"✅ Permiso creado: {code}")
            objetos_permiso.append(p)
        
        session.commit()

        # 2. Crear Rol SuperAdmin
        rol_admin = session.query(Rol).filter_by(nombre='SuperAdministrador').first()
        if not rol_admin:
            rol_admin = Rol(nombre='SuperAdministrador')
            rol_admin.permisos = objetos_permiso # Le asignamos todos los de arriba
            session.add(rol_admin)
            session.commit()
            print("✅ Rol 'SuperAdministrador' creado.")

        # 3. Crear Usuario Root (Aquí está la corrección)
        admin_user = session.query(Usuario).filter_by(username='root').first()
        if not admin_user:
            # USAMOS EL MÉTODO ESTÁTICO DE TU CLASE USUARIO
            hash_generado = Usuario.hash_password('admin1234')
            
            admin_user = Usuario(
                username='root',
                password_hash=hash_generado,
                rol_id=rol_admin.id
            )
            session.add(admin_user)
            session.commit()
            print("🚀 SISTEMA RESTAURADO: Usuario 'root' creado con éxito.")
            print("🔑 Contraseña provisional: admin1234")
        else:
            print("ℹ️ El usuario 'root' ya existe en la base de datos.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error crítico en la recuperación: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    bootstrap_system()