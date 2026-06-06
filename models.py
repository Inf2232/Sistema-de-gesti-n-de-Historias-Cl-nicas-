
from Errores import log_error_and_notify
from sqlalchemy import Column, Integer,JSON ,Table,String, Boolean, Date,UniqueConstraint, ForeignKey, Time, create_engine, Float, DateTime,event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, with_loader_criteria
from datetime import datetime,date,UTC
import math
import bcrypt
import os
from tablas_oms import obtener_riesgo_oms
import json
import traceback
from dateutil.relativedelta import relativedelta
db_path = os.path.join(os.path.dirname(__file__), 'data/diabetes_app.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)  

engine = create_engine(f'sqlite:///{db_path}')

Base = declarative_base()

# Tabla intermedia Muchos-a-Muchos para asignar múltiples permisos a un rol
rol_permiso = Table('rol_permiso', Base.metadata,
    Column('rol_id', Integer, ForeignKey('config_roles.id'), primary_key=True),
    Column('permiso_id', Integer, ForeignKey('config_permisos.id'), primary_key=True)
)
class Permiso(Base):
    __tablename__ = 'config_permisos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)        # Ej: "Crear Pacientes"
    codename = Column(String, unique=True, nullable=False) # Ej: "add_paciente"
    descripcion = Column(String, nullable=True)

class Rol(Base):
    __tablename__ = 'config_roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False) # Ej: "Médico de Guardia"
    
    # Relación M:M con Permisos
    permisos = relationship("Permiso", secondary=rol_permiso, backref="roles")
    # Relación inversa con usuarios
    usuarios = relationship("Usuario", back_populates="rol_relacion")

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    ultimo_acceso = Column(DateTime, nullable=True)

    rol_id = Column(Integer, ForeignKey('config_roles.id'), nullable=True)
    rol_relacion = relationship("Rol", back_populates="usuarios")
 
    @property
    def rol(self):
        """
        Permite que usuario.rol devuelva un string (ej: 'admin' o 'medico')
        sin romper la lógica existente en la UI.
        """
        if self.rol_relacion:
            return self.rol_relacion.nombre.lower() # Retorna 'admin', 'medico', etc.
        return 'sin_rol' # Valor por defecto si no tiene rol asignado
    institucion_id = Column(Integer, ForeignKey('config_institucion.id'), nullable=True)
    institucion = relationship("Institucion", back_populates="usuarios")
    
    @staticmethod
    def hash_password(password):
        if not password:
            raise ValueError("La contraseña no puede ser nula")
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')

    def verificar_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Paciente(Base):
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True, autoincrement=True,index=True)
    activo = Column(Boolean, default=True, index=True)

    # Un paciente SIEMPRE debe pertenecer a una institución (nullable=False)
    institucion_id = Column(Integer, ForeignKey('config_institucion.id'), nullable=False)
    institucion = relationship("Institucion", back_populates="pacientes")
    
    no_hc = Column(String, unique=True , index=True, nullable=False)
    ci = Column(String(11), unique=True, nullable=False, index=True)
    nombres = Column(String)
    apellidos = Column(String)
    telefono = Column(String ,nullable=True)
    tel_emergencia=Column(String ,nullable=True)
    nombre_contacto_emergencia=Column(String ,nullable=True)
    
    estado_actual = Column(String) 
    #dirección
    calle = Column(String)
    numero = Column(String)
    entre_calles = Column(String)
    municipio_id  = Column(Integer, ForeignKey('config_municipios.id'),  nullable=True, index=True)
    area_salud_id = Column(Integer, ForeignKey('config_areas_salud.id'), nullable=True, index=True)

    sexo = Column(String)
    color_piel = Column(String)#claro , oscuro , mestizo
    escolaridad = Column(String)
    ocupacion = Column(String)
    estado_civil = Column(String)#acompañado y no acompañado
    fecha_hc = Column(Date  ,index=True)
    tiempo_evolucion_anios = Column(Integer)
    tiempo_evolucion_meses= Column(Integer)
    tiempo_evolucion_dias= Column(Integer)
    forma_presentacion_diagnostico = Column(String) # Antes modo_debut
    glucemia_debut = Column(Float)
    exceso_peso_diagnostico = Column(String)#si o no
    tiempo_exceso_peso_anios= Column(Integer)
    tiempo_exceso_peso_meses= Column(Integer)
    remision = Column(String)
    tratamiento_inicial = Column(String)
    tratamiento_inicial_json = Column(JSON, default=list)
    ano_inicio_tratamiento = Column(Integer)
    dosis_tratamiento=Column(String)
    causa_fallecimiento = Column(String)
    prediabetes = Column(String, default="No")
    tiempo_prediabetes_anios = Column(Integer, nullable=True)
    tiempo_prediabetes_meses = Column(Integer, nullable=True)
    municipio_rel  = relationship("Municipio",  foreign_keys=[municipio_id])
    area_salud_rel = relationship("AreaSalud",  foreign_keys=[area_salud_id])
    antecedentes_personales = relationship(
        "AntecedentePatologicoPersonal", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    antecedentes_familiares = relationship(
        "AntecedentePatologicoFamiliarNoDiabetesMellitus", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    antecedentes_familiares_diabetes = relationship(
        "AntecedentePatologicoFamiliarDiabetes", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    historia_obstetrica = relationship(
        "HistoriaObstetrica", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    habitos_toxicos = relationship(
        "HabitosToxicos", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    tratamiento_actual = relationship(
        "TratamientoActual", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    otros_tratamientos = relationship(
        "OtrosTratamientos", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    examen_fisico = relationship(
        "ExamenFisico", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    mensuraciones = relationship(
        "Mensuraciones", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    resultado_educacion_diabetologica = relationship(
        "ResultadoEducacionDiabetologica", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    examen_miembros_inferiores = relationship(
        "ExamenMiembrosInferiores", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    oftalmologia = relationship(
        "Oftalmologia", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    nefrologia = relationship(
        "Nefrologia", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    complementarios = relationship(
        "Complementarios", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    estomatologia = relationship(
        "Estomatologia", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    indicaciones = relationship(
        "Indicaciones", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    registros = relationship(
        "Registro_consulta", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    cardiologia = relationship(
        "Cardiologia", 
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    ingresos = relationship("Ingreso", back_populates="paciente", cascade="all, delete-orphan")
    ingresos_diab = relationship("IngresoDiab", back_populates="paciente", cascade="all, delete-orphan")


    @property
    def municipio(self):
        """Nombre del municipio (lectura hacia atrás compatible)."""
        return self.municipio_rel.nombre if self.municipio_rel else None

    @property
    def provincia(self):
        """Nombre de la provincia, derivado del municipio (no necesita columna propia)."""
        if self.municipio_rel and self.municipio_rel.provincia:
            return self.municipio_rel.provincia.nombre
        return None

    @property
    def area_salud(self):
        """Nombre del área de salud (lectura hacia atrás compatible)."""
        return self.area_salud_rel.nombre if self.area_salud_rel else None



    @property
    def edad_actual(self):
        try:
            ci = self.ci
            # Cuba exige exactamente 11 caracteres numéricos
            if not ci or not isinstance(ci, str) or len(ci) != 11 or not ci.isdigit():
                return 'No disponible'

            year_2d = int(ci[0:2])
            month   = int(ci[2:4])
            day     = int(ci[4:6])
            digito_siglo = int(ci[6]) # El séptimo dígito determina el siglo

            # Determinación del siglo según el estándar del carnet cubano
            if digito_siglo in [6, 7, 8]:
                year = 2000 + year_2d   # Siglo XXI (Nacidos desde el año 2000)
            else:
                year = 1900 + year_2d   # Siglo XX (Nacidos antes del año 2000)

            # Validar mes y día construyendo la fecha
            fecha_nacimiento = datetime(year, month, day)
            hoy = datetime.now()

            # Evitar cálculos si la fecha de nacimiento es del futuro
            if fecha_nacimiento > hoy:
                return 'No disponible'

            edad = (
                hoy.year - fecha_nacimiento.year
                - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            )
            return edad

        except (ValueError, TypeError):
            return 'No disponible'


    @property
    def tiempo_evolucion(self):
        try:
            if not self.fecha_hc:
                return "Sin fecha de registro"

            # 1. El tiempo inicial que el médico ingresó (lo que el paciente ya traía)
            # Usamos 'or 0' para evitar errores si los campos están vacíos en la DB
            anios_ini = int(self.tiempo_evolucion_anios or 0)
            meses_ini = int(self.tiempo_evolucion_meses or 0)
            dias_ini = int(self.tiempo_evolucion_dias or 0)

            # 2. Calculamos cuánto tiempo ha pasado desde que se creó la HC hasta hoy
            hoy = datetime.now().date()
            # Aseguramos que fecha_hc sea tipo date
            fecha_hc_dt = self.fecha_hc if isinstance(self.fecha_hc, date) else self.fecha_hc.date()
            tiempo_desde_registro = relativedelta(hoy, fecha_hc_dt)

            # 3. Sumamos ambos periodos
            # Primero creamos el periodo inicial y luego le sumamos el transcurrido
            evolucion_total = relativedelta(years=anios_ini, months=meses_ini, days=dias_ini)
            evolucion_total += tiempo_desde_registro
            
            # El método .normalized() acomoda los días excedentes (ej: 40 días -> 1 mes y 10 días)
            t = evolucion_total.normalized()

            # 4. Construir la cadena de texto gramaticalmente correcta
            partes = []
            if t.years > 0:
                partes.append(f"{t.years} {'año' if t.years == 1 else 'años'}")
            
            if t.months > 0:
                partes.append(f"{t.months} {'mes' if t.months == 1 else 'meses'}")
            
            if t.days > 0 or not partes:
                partes.append(f"{t.days} {'día' if t.days == 1 else 'días'}")

            return " , ".join(partes)

        except Exception as e:
            print(f"Error en tiempo_evolucion: {e}")
            return "Error de cálculo"  
    @property
    def estado_actual_automatico(self):
        # 1. Prioridad Absoluta: Si está fallecido, es un estado terminal.
        if self.estado_actual == "Defunción":
            return "Defunción"
            
        # 2. Si la lista de ingresos está vacía o es None
        if not self.ingresos:
            return "No Ingresado"
            
        # 3. Obtener el ingreso más reciente (más eficiente que sorted)
        ultimo_ingreso = max(self.ingresos, key=lambda x: x.fecha_ingreso)
        
        # 4. Si el ingreso más reciente no tiene fecha de alta, sigue ingresado
        if ultimo_ingreso.fecha_egreso is None:
            return "Ingresado"
            
        # 5. Si tiene ingresos históricos pero el último ya está cerrado
        return "Seguimiento"
        

class IngresoDiab(Base):
    __tablename__ = 'ingresos_diab'
    id = Column(Integer, primary_key=True)
    no_hc = Column(String, ForeignKey('pacientes.no_hc'), index=True)
    motivo = Column(String)
    especificacion_otro = Column(String)
    fecha_ingreso = Column(Date , index=True)

    # Relación inversa
    paciente = relationship("Paciente", back_populates="ingresos_diab")

class AntecedentePatologicoPersonal(Base):
    __tablename__ = 'antecedentes_patologicos_personales'
    
    id = Column(Integer, primary_key=True,autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro = Column(Date)
    patologias = relationship("PatologiaPersonal", 
                            back_populates="antecedente", 
                            cascade="all, delete-orphan")
    paciente = relationship("Paciente", back_populates="antecedentes_personales")


class AntecedentePatologicoFamiliarNoDiabetesMellitus(Base):
    __tablename__ = 'antecedentes_patologicos_familiares_no_diabetes_mellitus'
    
    id = Column(Integer, primary_key=True,autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro = Column(Date)
    patologias = relationship("PatologiaFamiliarNoDiabetes", 
                            back_populates="antecedente", 
                            cascade="all, delete-orphan")
    paciente = relationship("Paciente", back_populates="antecedentes_familiares")

class AntecedentePatologicoFamiliarDiabetes(Base):
    __tablename__ = 'antecedentes_patologicos_familiares_diabetes'
    
    id = Column(Integer, primary_key=True,autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro = Column(Date)
    
    grados_parentezco = relationship("GradoParentezco", 
                                   back_populates="antecedente", 
                                   cascade="all, delete-orphan")
    paciente = relationship("Paciente", back_populates="antecedentes_familiares_diabetes")

class GradoParentezco(Base):
    __tablename__ = 'grados_parentezco'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    antecedente_id = Column(Integer, ForeignKey('antecedentes_patologicos_familiares_diabetes.id'))
    grado = Column(String)  # no, grado 1, grado 2, grado 3
    antecedente = relationship("AntecedentePatologicoFamiliarDiabetes", back_populates="grados_parentezco")

class PatologiaPersonal(Base):
    __tablename__ = 'patologias_personales'
    id = Column(Integer, primary_key=True, autoincrement=True)
    antecedente_id = Column(Integer, ForeignKey('antecedentes_patologicos_personales.id'))
    tipo_patologia = Column(String ,nullable=True)
    tiempo_anios = Column(Integer,nullable=True)
    tiempo_meses= Column(Integer,nullable=True) 
    antecedente = relationship("AntecedentePatologicoPersonal", back_populates="patologias")


class PatologiaFamiliarNoDiabetes(Base):
    __tablename__ = 'patologias_familiares_no_diabetes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    antecedente_id = Column(Integer, ForeignKey('antecedentes_patologicos_familiares_no_diabetes_mellitus.id'))
    tipo_patologia = Column(String ,nullable=True)

    antecedente = relationship("AntecedentePatologicoFamiliarNoDiabetesMellitus", back_populates="patologias")

class HistoriaObstetrica(Base):
    __tablename__ = 'historia_obstetrica'
    
    id = Column(Integer, primary_key=True,autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)

    edad_menarca = Column(Integer, nullable=True)
    edad_primera_relacion_sexual = Column(Integer, nullable=True)

    gestaciones = Column(Integer)  # Número de gestaciones
    partos = Column(Integer)  # Número de partos
    abortos_espontaneos = Column(Integer)  # Número de abortos
    abortos_provocados = Column(Integer)  # Número de abortos
    macrofetos = Column(String)  # si o no  
    macrofetos_historial = Column(JSON, default=list)  # Lista de detalles de cada macrófeto (ej: año, peso, complicaciones)
    malformaciones = Column(String)   # si o no  
    malformaciones_cuales = Column(String, nullable=True) # Se llena solo si es "Si"

    muertes_perinatales = Column(String)   # si o no  


    anticoncepcion_actual = Column(String, default="Ninguna")
    anticoncepcion_previa = Column(String, default="Ninguna")
    tiempo_anticoncepcion_prev_anos = Column(Integer, default=0)
    tiempo_anticoncepcion_prev_meses = Column(Integer, default=0)
    tiempo_anticoncepcion_actual_anos = Column(Integer, default=0)
    tiempo_anticoncepcion_actual_meses = Column(Integer, default=0)



    diabetes_gestacional = Column(String, default="No") # Presencia
    fecha_diabetes_gestacionaria=Column(Date,nullable=True)
    diabetes_gestacional_historial = Column(JSON, default=list)
    diabetes_insulina = Column(String, default="No")
    edad_menopausia = Column(Integer ,nullable=True)  # Edad de menopausia

    preeclampsia=Column(String)
    tipo_menopausia = Column(String,nullable=True)  # Tipo de menopausia

    # 3. EHE (Enfermedad Hipertensiva del Embarazo)
    ehe = Column(String, default="No")
    ehe_historial = Column(JSON, default=list)
    edad_materna_al_diagnostico = Column(Integer, nullable=True)  # Edad materna al diagnóstico de diabetes
    paciente = relationship("Paciente", back_populates="historia_obstetrica")  # Relación con Paciente
    @property
    def abortos(self):
        return self.abortos_espontaneos + self.abortos_provocados


class HabitosToxicos(Base):
        __tablename__ = 'habitos_toxicos'
    
        id = Column(Integer, primary_key=True,autoincrement=True)  # ID
        paciente_id = Column(Integer, ForeignKey('pacientes.id'))

        fecha_registro=Column(Date)

        fuma=Column(String)
        cant_cigarros=Column(String)
        cant_tabacos=Column(String)
        tiempo_sin_fumar=Column(String)
        consumo_excesivo_alcohol=Column(String)

    
        paciente = relationship("Paciente", back_populates="habitos_toxicos")




class TratamientoActual(Base):
    __tablename__ = 'tratamiento_actual'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)
    tratamiento=Column(String)
    dosis=Column(String)  
    sigue_via_clinica = Column(String, default="Si")
    esquema_json = Column(JSON, default=list)
    paciente = relationship("Paciente", back_populates="tratamiento_actual")

class OtrosTratamientos(Base):
    __tablename__ = 'otros_tratamientos'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)
    tratamiento=Column(String)
    dosis=Column(String)  # 
    paciente = relationship("Paciente", back_populates="otros_tratamientos")
    
class ExamenFisico(Base):
    __tablename__ = 'examen_fisico'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    fecha_registro=Column(Date)
    bocio=Column(String)
    sistolica_sentado=Column(Integer)
    diastolica_sentado=Column(Integer)
    sistolica_de_pie=Column(Integer)
    diastolica_de_pie=Column(Integer)
    sistolica_acostado=Column(Integer)
    diastolica_acostado=Column(Integer)
    frecuencia_cardiaca_sentado=Column(Float)
    frecuencia_cardiaca_acostado=Column(Float)

    acantosis_nigricans=Column(String)
    paciente = relationship("Paciente", back_populates="examen_fisico")

class Mensuraciones(Base):
    __tablename__ = 'mensuraciones'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    talla=Column(Integer)
    fecha_registro=Column(Date)
    peso=Column(Float)
    cintura=Column(Integer)
    cadera=Column(Integer)
    dieta=Column(String)
    cuello=Column(Integer)
    paciente = relationship("Paciente", back_populates="mensuraciones")


    @property
    def IMC(self):
        if not self.talla or not self.peso or self.talla <= 0 or self.peso <= 0:
            return "Datos insuficientes o inválidos para calcular el IMC"
    
        # Convertir talla de cm a m
        talla_en_metros = self.talla / 100
        
        imc = self.peso / (talla_en_metros ** 2)
        return round(imc, 2)

        

    @property
    def clasificar_imc(self):
            
            if isinstance(self.IMC, str):
                return 'gray', self.IMC
            if self.IMC < 18.5:
                return 'amber', 'Bajo peso'
            elif 18.5 <= self.IMC < 25:
                return 'green', 'Normal'
            elif 25 <= self.IMC < 30:
                return 'orange', 'Sobrepeso'
            elif 30<=self.IMC <35:
                return 'red', 'Obesidad Grado 1'
            elif 35 <= self.IMC < 40:
                return 'red', 'Obesidad Grado 2'
            else:
                return 'red', 'Obesidad Grado 3'
    
    @property
    def peso_ideal(self):
        if not self.talla or self.talla <= 0 or not self.paciente:
            return 0  # Retornamos 0 para evitar errores en cálculos posteriores
        """Calcula el peso ideal según sexo y talla"""
            
        talla_metros = self.talla / 100
        
        # Accedemos al sexo del paciente a través de la relación
        if not hasattr(self, 'paciente') or not self.paciente:
            raise ValueError("No se puede determinar el peso ideal sin información del paciente")
            
        sexo = getattr(self.paciente, 'sexo', '').lower() if self.paciente.sexo else None
        
        if sexo in ('masculino', 'hombre', 'h', 'm', 'male'):
            return 22 * (talla_metros ** 2)
        else:  # Por defecto asumimos femenino
            return 21 * (talla_metros ** 2)
    
    @property
    def PI(self):
      
        """Calcula el peso ideal ajustado según estado nutricional"""
        if isinstance(self.IMC, str) or self.peso_ideal == 0 or not self.peso:
            return "Datos insuficientes o inválidos para calcular el peso ideal ajustado"
            
        imc = self.IMC
        peso_ideal_base = self.peso_ideal
        if isinstance(imc, str):  # Si IMC devolvió un mensaje de error
            return "No se puede calcular el PI sin un IMC válido"
        if isinstance(peso_ideal_base, str):  # Si peso_ideal devolvió un mensaje de error
            return "No se puede calcular el PI sin un peso ideal válido"
        
        
        if 18.5 <= imc < 25:
            return round(peso_ideal_base, 2)
        
      
        elif imc >= 25:
            ajuste = 0.25 * (self.peso - peso_ideal_base)
            return round(peso_ideal_base + ajuste, 2)
        
        # Para bajo peso (IMC < 18.5)
        else:
            return round(peso_ideal_base, 2)
    
    
    @property
    def ICC(self):
        if not self.cintura or not self.cadera or self.cadera <= 0 or self.cintura <= 0:
            return "Datos insuficientes o inválidos"
        return round(self.cintura / self.cadera, 2)
    

    @property
    def ICaltura(self):
        if not self.cintura or not self.talla or self.cintura <= 0 or self.talla <= 0:
            return "Datos insuficientes o inválidos"
       
    
        ica = self.cintura / self.talla
        return round(ica, 2)
    @property
    def grasa_deurenberg(self):
        """Cálculo basado en el estudio de PubMed (Adultos y Niños)"""
        imc = self.IMC
        if isinstance(imc, str):  # Si IMC devolvió un mensaje de error
            return "No se puede calcular la grasa corporal sin un IMC válido"
        if imc == 0 or not self.paciente: return 0

        edad = self.paciente.edad_actual 
        es_hombre = self.paciente.sexo.lower() in ('masculino')
        sex_val = 1 if es_hombre else 0

        if edad <= 15:
            return round((1.51 * imc) - (0.70 * edad) - (3.6 * sex_val) + 1.4, 1)
        return round((1.20 * imc) + (0.23 * edad) - (10.8 * sex_val) - 5.4, 1)

    @property
    def grasa_marina(self):
        """U.S. Navy Method con manejo de errores y validación estricta"""
        # 1. Verificación básica de existencia
        if not self.paciente or not self.talla or not self.cintura or not self.cuello:
            return "Datos insuficientes"

        # 2. Normalizar el sexo
        sexo_str = str(self.paciente.sexo).lower()
        es_hombre = sexo_str in ('masculino', 'hombre', 'h', 'm')

        try:
            # Convertir a float por seguridad si vienen de un input de texto
            talla = float(self.talla)
            cintura = float(self.cintura)
            cuello = float(self.cuello)

            if es_hombre:
                diff = cintura - cuello
                if diff <= 0: return "Error medidas"
                # Fórmula Hombres
                denominador = 1.0324 - 0.19077 * math.log10(diff) + 0.15456 * math.log10(talla)
            else:
                # Si es mujer, la cadera es OBLIGATORIA
                if not self.cadera or float(self.cadera) <= 0:
                    return "Datos insuficientes"
                
                cadera = float(self.cadera)
                suma = cintura + cadera - cuello
                if suma <= 0: return "Error medidas"
                # Fórmula Mujeres
                denominador = 1.29579 - 0.35004 * math.log10(suma) + 0.22100 * math.log10(talla)

            porcentaje = (495 / denominador) - 450
            return round(porcentaje, 1)

        except (ValueError, ZeroDivisionError, TypeError):
            return "Error de cálculo"

    @property
    def clasificar_composicion_corporal(self):
        grasa = self.grasa_marina
        
        # Si no es un número (es un string de error), salimos rápido
        if isinstance(grasa, str):
            return 'gray', grasa
            
        if not self.paciente: 
            return 'gray', 'Sin paciente'

        edad = self.paciente.edad_actual
        sexo_str = str(self.paciente.sexo).lower()
        es_hombre = sexo_str in ('masculino', 'hombre', 'h', 'm')

        # Lógica de límites (Unificada)
        if es_hombre:
            if edad < 40: limites = [8, 20, 25]
            elif edad < 60: limites = [11, 22, 28]
            else: limites = [13, 25, 30]
        else:
            if edad < 40: limites = [16, 28, 39]
            elif edad < 60: limites = [18, 30, 40]
            else: limites = [20, 32, 42]

        if grasa < limites[0]: return 'blue', 'Bajo en grasa'
        if grasa <= limites[1]: return 'green', 'Saludable'
        if grasa <= limites[2]: return 'orange', 'Sobrepeso'
        return 'red', 'Obesidad'



class ResultadoEducacionDiabetologica(Base):
    __tablename__ = 'resultado_educacion_diabetologica'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    fecha_registro=Column(Date)
    inicio=Column(String)
    final=Column(String)

    paciente = relationship("Paciente", back_populates="resultado_educacion_diabetologica")

    estado = relationship("EstadoEducacionDiabetologica", cascade="all, delete-orphan")
class  EstadoEducacionDiabetologica(Base):
    __tablename__ = 'estado_educacion_diabetologica'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    educacion_id=Column(Integer,ForeignKey('resultado_educacion_diabetologica.id'),nullable=False)

    fecha_registro=Column(Date)
    mantiene_educacion=Column(Boolean,nullable=False)

    estado = relationship("ResultadoEducacionDiabetologica", back_populates="estado")


class ExamenMiembrosInferiores(Base):
    __tablename__ = 'examen_miembros_inferiores'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)

   
    defromidades_podalicas_derecho = relationship("EnfermedadesPodalicasDerecho", 
        back_populates="examen",
        cascade="all, delete-orphan")
    defromidades_podalicas_izquierdo = relationship("EnfermedadesPodalicasIzquierdo", 
        back_populates="examen",
        cascade="all, delete-orphan")

    lesiones_dermatologicas_derecho = relationship("LesionesDermatologicasDerecho", 
        back_populates="examen",
        cascade="all, delete-orphan")
    lesiones_dermatologicas_izquierdo = relationship("LesionesDermatologicasIzquierdo", back_populates="examen",
        cascade="all, delete-orphan")
    
    lesiones_uñas_derecho=relationship("LesionesUñasDerecho",  back_populates="examen",
        cascade="all, delete-orphan")
    lesiones_uñas_izquierdo=relationship("LesionesUñasIzquierdo", back_populates="examen",
        cascade="all, delete-orphan")

    #examen arterial
    pulso_femoral_derecho=Column(String)
    pulso_femoral_izquierdo=Column(String)
    pulso_popliteo_izquierdo=Column(String)
    pulso_popliteo_derecho=Column(String)
    pulso_tibial_posterior_izquierdo=Column(String)
    pulso_tibial_posterior_derecho=Column(String)
    pulso_pedeo_derecho=Column(String)
    pulso_pedeo_izquierdo=Column(String)
  

   
    #ITB
    tibial_derecho = Column(Integer)   # Presión sistólica tibial
    tibial_izquierdo = Column(Integer)   # Presión sistólica tibial

    pedia_derecho = Column(Integer)    # Presión sistólica pedia
    pedia_izquierdo = Column(Integer)    # Presión sistólica pedia

    humeral_derecho = Column(Integer)  # Presión sistólica humeral (brazo)
    humeral_izquierdo = Column(Integer)  # Presión sistólica humeral (brazo)
    
    
    EAP_derecho=Column(String)
    EAP_izquierdo=Column(String)
    #examen neurologico 
    #sensibilidad superficial
    tactil_derecho=Column(String)
    tactil_izquierdo=Column(String)
    
    termica_derecho=Column(String)
    termica_izquierdo=Column(String)

    dolorosa_derecho=Column(String)
    dolorosa_izquierdo=Column(String)
    #sensibuilidad profunda
    palestesia_derecho=Column(String)# conservada o no conservada
    palestesia_izquierdo=Column(String)# conservada o no conservada

    #exploraciones de reflejos osteotendinosos 
    patelar_derecho=Column(String)#presente o ausente
    patelar_izquierdo=Column(String)#presente o ausente
    aquileano_derecho=Column(String)#presente o ausente
    aquileano_izquierdo=Column(String)#presente o ausente
    venoso_periferico_izquierdo=Column(String)#presente o ausente
    linfatico_izquierdo=Column(String)#presente o ausente
    venoso_periferico_derecho=Column(String)#presente o ausente
    linfatico_derecho=Column(String)#presente o ausente
    LOPS_derecho=Column(String)#si o no 
    LOPS_izquierdo=Column(String)#si o no 
    
    impresion_diagnostica=Column(String)
    
    paciente = relationship("Paciente", back_populates="examen_miembros_inferiores")

    @property
    def ITB_derecho(self):
     
        """
        Calcula el índice tobillo-brazo (ITB) usando las presiones tibial, pedia y humeral.
        ITB = (mayor de tibial o pedia) / humeral
        """
        if self.humeral_derecho and self.humeral_derecho != 0:
            return max(self.tibial_derecho or 0, self.pedia_derecho or 0) / self.humeral_derecho
        return None
    @property
    def ITB_izquierdo(self):
        
        if self.humeral_izquierdo and self.humeral_izquierdo != 0:
            return max(self.tibial_izquierdo or 0, self.pedia_izquierdo or 0) / self.humeral_izquierdo
        return None
    @property
    def itb_clasificacion_izquierdo(self):
        valor = self.ITB_izquierdo
        if valor is None:
            return "Valor no disponible"
        if valor <= 0.4:
            return "Estenosis grave"
        elif 0.4 < valor < 0.9:
            return "Estenosis leve/moderada"
        elif 0.9 <= valor <= 1.2:
            return "Normal"
        elif valor > 1.2:
            return "Posible calcificación arterial"
        else:
            return "Valor fuera de rango"
    @property
    def itb_clasificacion_derecho(self):
        valor = self.ITB_derecho
        if valor is None:
            return "Valor no disponible"
        if valor <= 0.4:
            return "Estenosis grave"
        elif 0.4 < valor < 0.9:
            return "Estenosis leve/moderada"
        elif 0.9 <= valor <= 1.2:
            return "Normal"
        elif valor > 1.2:
            return "Posible calcificación arterial"
        else:
            return "Valor fuera de rango"
        


class EnfermedadesPodalicasDerecho(Base):
    __tablename__ = 'enfermedades_podalicas_derecho'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)

    examen = relationship("ExamenMiembrosInferiores", back_populates="defromidades_podalicas_derecho")

class EnfermedadesPodalicasIzquierdo(Base):
    __tablename__ = 'enfermedades_podalicas_izquierdo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)

    examen = relationship("ExamenMiembrosInferiores", back_populates="defromidades_podalicas_izquierdo")

class LesionesDermatologicasDerecho(Base):
    __tablename__ = 'lesiones_dermatologicas_derecho'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)
    
    examen = relationship("ExamenMiembrosInferiores", back_populates="lesiones_dermatologicas_derecho")

class LesionesDermatologicasIzquierdo(Base):
    __tablename__ = 'lesiones_dermatologicas_izquierdo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)
    
    examen = relationship("ExamenMiembrosInferiores", back_populates="lesiones_dermatologicas_izquierdo")



class LesionesUñasDerecho(Base):
    __tablename__ = 'lesiones_uñas_derecho'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)
    examen = relationship("ExamenMiembrosInferiores", back_populates="lesiones_uñas_derecho")
    

class LesionesUñasIzquierdo(Base):
    __tablename__ = 'lesiones_uñas_izquierdo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('examen_miembros_inferiores.id'))
    padecimiento=Column(String)
    examen = relationship("ExamenMiembrosInferiores", back_populates="lesiones_uñas_izquierdo")

    

class Oftalmologia(Base):
    __tablename__ = 'oftalmologia'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)
    
    retinopatia_diabetica=Column(String)#no , no proliferativa  , proliferativa , no precisada
    retinopatia_hipertensiva=Column(String)#no , grado1 , grado 2 , grado3 , grado4 , no precisada
    retinopatia_artereo_esclerosis=Column(String)#no , grado1 , grado 2 , grado3 , grado4 , no precisad
    vision_borrosa_od=Column(String)
    vision_borrosa_oi=Column(String)
    av_od=Column(Float)
    av_oi=Column(Float)
    rd_od=Column(Float)
    rd_oi=Column(Float)
    a_od=Column(Float)
    a_oi=Column(Float)
    sa_od=Column(Float)
    sa_oi=Column(Float)
    m_od=Column(Float)
    m_oi=Column(Float)
    fo_od=Column(Float)
    fo_oi=Column(Float)
    
    hemorragia_vitrea_od=Column(String)#no ,si , no precisado 
    hemorragia_vitrea_oi=Column(String)#no ,si , no precisado 
    maculopatia_od=Column(String)#no ,si , no precisado 
    maculopatia_oi=Column(String)#no ,si , no precisado 
    catarata_od=Column(String)#no ,metabolica , senil , otras ,no precisada
    catarata_oi=Column(String)#no ,metabolica , senil , otras ,no precisada
    glaucoma_od=Column(String)#no , angulo abierto , secundario, angulo estrecho , no precisado
    glaucoma_oi=Column(String)#no , angulo abierto , secundario, angulo estrecho , no precisado

    paciente = relationship("Paciente", back_populates="oftalmologia")

class MedicionAlbuminuria(Base):            # antes: Microalbuminuria
     __tablename__ = 'medicion_albuminuria'  # antes: 'microalbuminuria'
     id            = Column(Integer, primary_key=True)
     nefrologia_id = Column(Integer, ForeignKey('nefrologia.id', ondelete='CASCADE'), index=True)
     valor         = Column(Float, nullable=False)
     unidad        = Column(String(32), nullable=False)   # 'mg/g' preferido
     categoria     = Column(String(8), nullable=True)     # ← CAMPO NUEVO
     nefrologia    = relationship('Nefrologia', back_populates='mediciones_albuminuria')
     
class Nefrologia(Base):
    __tablename__ = 'nefrologia'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)
    filtrado_glomerular_teorico=Column(Float)#clasificarlo
    creatinina=Column(Integer)
    proteinuria_valor=Column(Float)
    proteinuria=Column(String)
    urea=Column(Integer)
    ac_urico=Column(Integer)
    cituria=Column(String)#normal o patologica
    albuminuria_categoria = Column(String, nullable=True)
    diagnostico_renal=Column(String)#si o no 
    uts_renal=Column(String) # multiples valores
    mediciones_albuminuria = relationship("MedicionAlbuminuria", cascade="all, delete-orphan")

    paciente = relationship("Paciente", back_populates="nefrologia")
    @property
    def clasificacion(self):
        if self.filtrado_glomerular_teorico is None:
            return "No disponible"
        
        fg = self.filtrado_glomerular_teorico
        
        if fg >= 90:
            return "G1 - Función renal normal (FG ≥ 90)"
        elif 60 <= fg < 90:
            return "G2 - Disminución leve del FG (60-89)"
        elif 45 <= fg < 60:
            return "G3A - Disminución moderada del FG (45-59)"
        elif 30 <= fg < 45:
            return "G3B - Disminución moderada a grave del FG (30-44)"
        elif 15 <= fg < 30:
            return "G4 - Disminución grave del FG (15-29)"
        elif fg < 15:
            return "G5 - Insuficiencia renal terminal (FG < 15)"
        else:
            return "Valor no clasificable"


class Complementarios(Base):
    __tablename__ = 'complementarios'
    id = Column(Integer, primary_key=True,autoincrement=True)  # ID
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)
    hb=Column(Float)
    hto=Column(Float)
    eritro=Column(Float)
    glucemia=Column(Float)
    colesterol=Column(Float)
    trigliceridos=Column(Float)
    HDLC=Column(Float)
    tgp=Column(Float)
    TGO=Column(Float) 
    proteinas_totales=Column(Float)
    albuminuria=Column(Float)
    globulina=Column(Float)
    calcio=Column(Float)
    fosforo=Column(Float)
    conteo_plaquetas=Column(Float)
    coagulacion=Column(Float)
    sangramiento=Column(Float)
    ultrasonido_abdominal=Column(String)
    prueba_conduccion_nerviosa_miembro_superior=Column(String)
    prueba_conduccion_nerviosa_miembro_inferior=Column(String)
    ggt=Column(Float)
    HbA1c=Column(Float)

    campos_personalizados = relationship(
        "CampoComplementarioPersonalizado",
        back_populates="examen",
        cascade="all, delete-orphan")
    paciente = relationship("Paciente", back_populates="complementarios")

class CampoComplementarioPersonalizado(Base):
    __tablename__ = 'campos_complementarios_personalizados'
    id = Column(Integer, primary_key=True, autoincrement=True)
    complementario_id = Column(Integer, ForeignKey('complementarios.id'), nullable=False)
    nombre = Column(String, nullable=False)   
    valor = Column(String, nullable=False)  
    unidad = Column(String, nullable=True)    

    examen = relationship("Complementarios", back_populates="campos_personalizados")

class Estomatologia(Base):
    __tablename__ = 'estomatologia'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro = Column(Date)
    examen_funcional = Column(String)
    diagnosticos_epidemiologicos = Column(String)
    diagnosticos_clinico = relationship(  # Nombre consistente
        "DiagnosticosClinico",  # Ahora coincide con el nombre real de la clase
        back_populates="examen",
        cascade="all, delete-orphan"
    )
    pronostico = Column(String)
    tratamiento = Column(String)
    paciente = relationship("Paciente", back_populates="estomatologia")

class DiagnosticosClinico(Base):  
    __tablename__ = 'diagnosticos_clinico'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examen_id = Column(Integer, ForeignKey('estomatologia.id'))
    diagnostico = Column(String)  # Nombre más simple y consistente
    examen = relationship("Estomatologia", back_populates="diagnosticos_clinico")

class Indicaciones(Base):
    __tablename__ = 'indicaciones'
    id = Column(Integer, primary_key=True,autoincrement=True)  # IDS
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro=Column(Date)

    tipo_diabetes=Column(String, nullable=True)
    tratamiento=Column(String)

    paciente = relationship("Paciente", back_populates="indicaciones")

class Registro_consulta(Base):
    __tablename__ = 'registro_consulta'
    id = Column(Integer, primary_key=True,autoincrement=True)  # IDS
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_consulta=Column(Date)
    hora=Column(Time)
    notas=Column(String)
    paciente = relationship('Paciente', back_populates='registros')

    __table_args__ = (
        UniqueConstraint('fecha_consulta', 'hora', name='_fecha_hora_uc'),
    )

class Cardiologia(Base):
    __tablename__ = 'cardiologia'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_registro = Column(Date)
    ekg = Column(String)
    sexo = Column(String)  
    edad = Column(Integer)
    colesterol_total = Column(Float)  # mmol/L
    presion_sistolica = Column(Integer)  # mmHg
    fuma = Column(String)  # 'Si' o 'No'
    diabetes = Column(String)  # 'Si' o 'No'
    riesgo_oms = Column(Integer, nullable=True)
    color_riesgo = Column(String, nullable=True)
    paciente = relationship("Paciente", back_populates="cardiologia")

    def calcular_riesgo_coronario(self):
        """
        Calcula el riesgo coronario a 10 años usando las tablas OMS del Caribe.
        Devuelve un diccionario con el valor de riesgo y el color asociado.
        """
        try:
            # Validar campos requeridos
            if self.sexo is None or self.edad is None or self.colesterol_total is None or \
               self.presion_sistolica is None or self.fuma is None or self.diabetes is None:
                raise ValueError("Faltan datos requeridos para el cálculo de riesgo OMS")

            # Convertir campos a los formatos esperados
            sexo = self.sexo.capitalize()
            edad = int(self.edad)
            colesterol = float(self.colesterol_total)
            presion_sistolica = int(self.presion_sistolica)
            fuma = True if str(self.fuma).lower() in ['si', 'sí', 'true', '1'] else False
            diabetes = True if str(self.diabetes).lower() in ['si', 'sí', 'true', '1'] else False

            # Calcular riesgo usando la función de tablas_oms
            riesgo = obtener_riesgo_oms(
                diabetes=diabetes,
                sexo=sexo,
                fuma=fuma,
                edad=edad,
                presion_sistolica=presion_sistolica,
                colesterol=colesterol
            )

            # Determinar el color según el valor de riesgo
            if 1 <= riesgo <= 4:
                color = "#18C93B"
            elif 5 <= riesgo <= 9:
                color = "#EBEB0E"
            elif 10 <= riesgo <= 19:
                color = "#F23916"
            elif 20 <= riesgo <= 29:
                color = "#E50505"
            elif riesgo >= 30:
                color = "#5C0505"
            else:
                color = "#A1AB9F"

           
            self.riesgo_oms = riesgo
            self.color_riesgo = color

            return {
                "riesgo": riesgo,
                "color": color
            }
        except Exception as e:
            return {
                "riesgo": None,
                "color": "#A1AB9F",
                "error": str(e)
            }


class Ingreso(Base):
    __tablename__ = 'ingresos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))
    fecha_ingreso = Column(Date, nullable=False)
    fecha_egreso = Column(Date, nullable=True)
    motivo = Column(String, nullable=True)  # opcional
    observaciones_egreso = Column(String, nullable=True)
    paciente = relationship("Paciente", back_populates="ingresos")
    

""" Modelos de configuracion del sistema """
class Institucion(Base):
    __tablename__ = 'config_institucion'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, default="Mi Institución")
    direccion = Column(String, nullable=True)
    provincia_default = Column(String, nullable=True)
    # Relaciones inversas (para acceder desde la institución a sus usuarios/pacientes)
    usuarios = relationship("Usuario", back_populates="institucion")
    pacientes = relationship("Paciente", back_populates="institucion")

class Provincia(Base):
    __tablename__ = 'config_provincias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False)
    codigo = Column(String, unique=True, nullable=False)
    # Relación con municipios
    municipios = relationship("Municipio", back_populates="provincia", cascade="all, delete-orphan")
class Municipio(Base):
    __tablename__ = 'config_municipios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    codigo = Column(String, unique=True, nullable=False)
    provincia_id = Column(Integer, ForeignKey('config_provincias.id'))
    
    provincia = relationship("Provincia", back_populates="municipios")
    areas_salud = relationship("AreaSalud", back_populates="municipio", cascade="all, delete-orphan")


class AreaSalud(Base):
    __tablename__ = 'config_areas_salud'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    municipio_id = Column(Integer, ForeignKey('config_municipios.id'))
    
    municipio = relationship("Municipio", back_populates="areas_salud")


#log de auditoria 
class LogAuditoria(Base):
    __tablename__ = 'logs_auditoria'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(DateTime, default=datetime.now(UTC), nullable=False)
    usuario = Column(String, nullable=False)  # username del usuario que realizó la acción
    accion = Column(String, nullable=False)   # 'crear', 'actualizar', 'eliminar', 'login', etc.
    tabla = Column(String, nullable=False)    # nombre de la tabla afectada
    registro_id = Column(Integer, nullable=True)  # ID del registro afectado 
    detalles = Column(String, nullable=True)  # JSON con datos antiguos/nuevos o descripción
    ip = Column(String, nullable=True)        # opcional: IP del cliente

    def __repr__(self):
        return f"<LogAuditoria {self.accion} en {self.tabla} por {self.usuario} el {self.fecha}>"


# Configuración de la base de datos
Base.metadata.create_all(engine)
Base.metadata.create_all(engine, tables=[Institucion.__table__])        
Base.metadata.create_all(engine, tables=[Usuario.__table__])
Base.metadata.create_all(engine, tables=[Paciente.__table__])


Session = sessionmaker(bind=engine)




def serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    # Si es un objeto SQLAlchemy con método to_dict
    if hasattr(value, 'to_dict') and callable(value.to_dict):
        return value.to_dict()
    # Si es lista o similar, serializar cada ítem
    if isinstance(value, (list, tuple, set)):
        return [serialize_value(i) for i in value]
    # si es tipo primitivo compatible o None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # fallback: convertir a string para evitar error
    return str(value)

def obtener_usuario_actual():
    import authenticar
    try:
        usuario_actual = authenticar.devolver_usuario_actual()
        if usuario_actual and isinstance(usuario_actual, dict) and 'username' in usuario_actual:
            return usuario_actual['username']
        else:
            return 'anonimo'
    except Exception:
        return 'sistema'
def obtener_id_registro(target):
    """Busca el identificador principal del registro."""
    # Prioridad: no_hc (pacientes), id (otros), ci (identidad)
    for campo in ['no_hc', 'id', 'ci', 'id_usuario']:
        val = getattr(target, campo, None)
        if val is not None:
            return str(val)
    return "N/A"

@event.listens_for(Base, 'after_insert', propagate=True)
def recibir_insert(mapper, connection, target):
    try:
        tabla = target.__tablename__
        usuario = obtener_usuario_actual()
        detalles = {c.name: serialize_value(getattr(target, c.name)) for c in target.__table__.columns if c.name != 'id'}
        detalles_json = json.dumps(detalles, ensure_ascii=False)
        connection.execute(
            LogAuditoria.__table__.insert().values(
                fecha=datetime.now(UTC),
                usuario=usuario,
                accion='crear',
                tabla=tabla,
                registro_id=getattr(target, 'id', None),
                detalles=detalles_json,
                ip=None
            )
        )
    except Exception:
        print(f"Error en recibir_insert: {traceback.format_exc()}")

@event.listens_for(Base, 'after_update', propagate=True)
def recibir_update(mapper, connection, target):
    if target.__tablename__ == 'log_auditoria': return
    try:
        usuario = obtener_usuario_actual() 
        
        insp = inspect(target)
        cambios = {}
        for attr in insp.attrs:
            hist = attr.history
            if hist.has_changes():
                cambios[attr.key] = {
                    'antes': serialize_value(hist.deleted[0]) if hist.deleted else None,
                    'despues': serialize_value(hist.added[0]) if hist.added else None
                }

        if not cambios: return

        # Lógica para detectar archivado/desarchivado
        accion = 'actualizar'
        if 'activo' in cambios:
            antes = cambios['activo']['antes']
            despues = cambios['activo']['despues']
            if antes is True and despues is False:
                accion = 'archivar'
            elif antes is False and despues is True:
                accion = 'desarchivar'

        connection.execute(
            LogAuditoria.__table__.insert().values(
                fecha=datetime.now(UTC),
                usuario=usuario, # Ahora 'usuario' ya está definido arriba
                accion=accion,
                tabla=target.__tablename__,
                registro_id=obtener_id_registro(target),
                detalles=json.dumps(cambios, ensure_ascii=False),
                ip=None
            )
        )
    except Exception:
        print(f"Error en recibir_update: {traceback.format_exc()}")

@event.listens_for(Base, 'after_delete', propagate=True)
def recibir_delete(mapper, connection, target):
    try:
        tabla = target.__tablename__
        usuario = obtener_usuario_actual()
        detalles = {c.name: serialize_value(getattr(target, c.name)) for c in target.__table__.columns if c.name != 'id'}
        detalles_json = json.dumps(detalles, ensure_ascii=False)
        connection.execute(
            LogAuditoria.__table__.insert().values(
                fecha=datetime.now(UTC),
                usuario=usuario,
                accion='eliminar',
                tabla=tabla,
                registro_id=getattr(target, 'id', None),
                detalles=detalles_json,
                ip=None
            )
        )
    except Exception:
        print(f"Error en recibir_delete: {traceback.format_exc()}")

def registrar_acceso_lectura(no_hc):
    """
    Registra el evento de lectura vinculando al usuario autenticado.
    """
    # Creamos una sesión interna para asegurar que el log se guarde 
    # incluso si hay errores en la carga de la página
    db = Session() 
    try:
        # Importación dentro de la función para evitar importaciones circulares
        from authenticar import devolver_usuario_actual
        
        usuario_dict = devolver_usuario_actual()
        nombre_usuario = usuario_dict.get('username', 'anonimo') if usuario_dict else 'sistema'
        
       

        nuevo_log = LogAuditoria(
            fecha=datetime.now(UTC),
            usuario=nombre_usuario, 
            accion='ACCESO_LECTURA',
            tabla='pacientes',
            registro_id=str(no_hc),
            detalles=json.dumps({
                "evento": "Apertura de ficha clínica detallada",
            }, ensure_ascii=False),
            ip=None
        )
        
        db.add(nuevo_log)
        db.commit()
    except Exception as e:
        print(f"Error crítico en log de lectura: {e}")
        db.rollback()
    finally:
        db.close()

def cerrar_conexiones():
    """Cierra el engine para liberar el archivo .db y permitir su manipulación."""
    engine.dispose()