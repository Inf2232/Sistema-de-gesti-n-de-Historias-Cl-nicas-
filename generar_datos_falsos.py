import random
from datetime import datetime, timedelta
from faker import Faker
from models import Session, Paciente, Institucion, Provincia, Municipio, AreaSalud

fake = Faker('es_ES')

def generar_ci_cubano(fecha_nacimiento):
    """Genera un CI válido de 11 dígitos respetando el séptimo dígito para el siglo."""
    yy = str(fecha_nacimiento.year)[-2:]
    mm = f"{fecha_nacimiento.month:02d}"
    dd = f"{fecha_nacimiento.day:02d}"
    
    if fecha_nacimiento.year < 2000:
        digito_siglo = random.choice([0, 1, 2, 3, 4, 5])
    else:
        digito_siglo = random.choice([6, 7, 8])
        
    resto = f"{random.randint(0, 9999):04d}"
    return f"{yy}{mm}{dd}{digito_siglo}{resto}"

def configurar_entorno_geografico(db):
    """Crea la institución base y asegura que existan municipios con áreas de salud."""
    print("🏥 Verificando Institución y Geografía...")
    
    institucion = db.query(Institucion).first()
    if not institucion:
        institucion = Institucion(nombre="Clínica del Diabético - Cienfuegos", provincia_default="Cienfuegos")
        db.add(institucion)
        db.commit()

    provincia = db.query(Provincia).filter_by(nombre="Cienfuegos").first()
    if not provincia:
        provincia = Provincia(nombre="Cienfuegos", codigo="CFG")
        db.add(provincia)
        db.commit()
        
    # FIX: Verificamos explícitamente si hay áreas de salud en la base de datos, no solo la provincia.
    areas_existentes = db.query(AreaSalud).count()
    if areas_existentes == 0:
        print("   ⚠️ No se encontraron áreas de salud. Creando geografía de prueba...")
        nombres_municipios = ["Cienfuegos", "Palmira", "Cruces", "Aguada de Pasajeros", "Cumanayagua"]
        for nom in nombres_municipios:
            mun = Municipio(nombre=nom, codigo=nom[:3].upper(), provincia_id=provincia.id)
            db.add(mun)
            db.commit() # Commit intermedio para obtener el ID del municipio
            
            db.add(AreaSalud(nombre=f"Policlínico Área I - {nom}", municipio_id=mun.id))
            db.add(AreaSalud(nombre=f"Policlínico Área II - {nom}", municipio_id=mun.id))
        db.commit()
    
    return institucion

def sembrar_pacientes(cantidad=5000):
    db = Session()
    try:
        institucion = configurar_entorno_geografico(db)
        
        # FIX PARA EL INDEX ERROR: Emparejar previamente los municipios con sus áreas reales
        todas_areas = db.query(AreaSalud).all()
        municipios_validos = []
        
        for mun in db.query(Municipio).all():
            areas_del_mun = [a for a in todas_areas if a.municipio_id == mun.id]
            if areas_del_mun:
                # Guardamos una tupla con el municipio y su lista de áreas
                municipios_validos.append((mun, areas_del_mun))
                
        if not municipios_validos:
            raise ValueError("Tu base de datos está corrupta geográficamente: Hay municipios pero no tienen áreas de salud asociadas.")
        
        print(f"🚀 Iniciando generación masiva de {cantidad} pacientes...")
        
        lote_pacientes = []
        lote_size = 2000 
        total_insertados = 0

        opciones_sexo = ['Masculino', 'Femenino']
        opciones_piel = ['Blanco', 'Negro', 'Mestizo']
        opciones_escolaridad = ['6to Grado', '9no Grado', '12mo Grado', 'Universitario', 'No especificado']
        opciones_ocupacion = ['Estudiante', 'Con vínculo laboral: Trabajador Estatal', 'Con vínculo laboral: Trabajador No Estatal', 'Sin vínculo laboral']
        opciones_estado_civil = ['Acompañado', 'No acompañado']
        opciones_debut = ['Sintomas Clinicos', 'Asintomatico', 'Cetoacidosis(Probada)', 'Durante el embarazo']
        opciones_tratamiento = ['Tratamiento No Farmacologico', 'SUR', 'Metformina', 'Insulina', 'Insulina + SUR']
        cis_generados = set()
        for i in range(cantidad):
            while True:
                edad = random.randint(15, 90)
                fecha_nac = datetime.now() - timedelta(days=edad * 365)
                ci_nuevo = generar_ci_cubano(fecha_nac)
                
                # Solo salimos del while si el CI no existe en nuestra memoria
                if ci_nuevo not in cis_generados:
                    cis_generados.add(ci_nuevo)
                    break
            
            dias_atras = random.randint(0, 365 * 5)
            fecha_historia = datetime.now() - timedelta(days=dias_atras)

            # SELECCIÓN SEGURA DE GEOGRAFÍA
            mun_asignado, areas_disponibles = random.choice(municipios_validos)
            area_asignada = random.choice(areas_disponibles)

            peso_exceso = random.choice(['Si', 'No'])
            glucemia = round(random.uniform(5.0, 25.0), 1)

            paciente = Paciente(
                institucion_id=institucion.id,
                no_hc=f"HC-MOCK-{int(datetime.now().timestamp())}-{i}",
                ci=ci_nuevo,
                nombres=fake.first_name(),
                apellidos=f"{fake.last_name()} {fake.last_name()}",
                telefono=f"5{random.randint(1000000, 9999999)}",
                calle=fake.street_name(),
                numero=str(random.randint(1, 999)),
                municipio_id=mun_asignado.id,
                area_salud_id=area_asignada.id,
                sexo=random.choice(opciones_sexo),
                color_piel=random.choice(opciones_piel),
                escolaridad=random.choice(opciones_escolaridad),
                ocupacion=random.choice(opciones_ocupacion),
                estado_civil=random.choice(opciones_estado_civil),
                fecha_hc=fecha_historia.date(),
                tiempo_evolucion_anios=random.randint(0, 20),
                tiempo_evolucion_meses=random.randint(0, 11),
                forma_presentacion_diagnostico=random.choice(opciones_debut),
                glucemia_debut=glucemia,
                exceso_peso_diagnostico=peso_exceso,
                tratamiento_inicial=random.choice(opciones_tratamiento),
                prediabetes=random.choice(["Si", "No"]),
                activo=True
            )
            
            lote_pacientes.append(paciente)

            if len(lote_pacientes) >= lote_size:
                db.bulk_save_objects(lote_pacientes)
                db.commit()
                total_insertados += len(lote_pacientes)
                print(f"✅ {total_insertados} pacientes insertados...")
                lote_pacientes = []

        if lote_pacientes:
            db.bulk_save_objects(lote_pacientes)
            db.commit()
            total_insertados += len(lote_pacientes)
            print(f"✅ {total_insertados} pacientes insertados...")

        print("\n🎉 ¡Sembrado de datos finalizado con éxito!")

    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la generación: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sembrar_pacientes(10000)