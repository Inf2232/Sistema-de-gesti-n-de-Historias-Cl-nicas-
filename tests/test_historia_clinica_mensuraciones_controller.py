# tests/test_historia_clinica_mensuraciones_controller.py
# Suite de pruebas — MensuracionesController + @property de Mensuraciones
# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA:
#   • Tests de @property (IMC, grasa, etc.): usan Mensuraciones() sin BD,
#     con un MagicMock como paciente para evitar la carga de la sesión.
#   • Tests CRUD: usan la BD en memoria con pacientes y sesión reales.
#   • Todos los valores matemáticos se calcularon de forma exacta
#     (ver comentarios inline) y se validan con pytest.approx.
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Institucion, Paciente, Mensuraciones
from controllers.historia_clinica_mensuraciones_controller import MensuracionesController


# ══════════════════════════════════════════════════════════════════════════════
#  FIXTURES DE SESIÓN Y PACIENTE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def engine():
    eng = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope='module')
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Teardown seguro: rollback + expunge_all para evitar SAWarning
    session.rollback()
    session.expunge_all()
    session.close()


@pytest.fixture(scope='module')
def paciente_masculino(db_session):
    """
    Paciente masculino, 35 años.
    CI: "910301XXXXX" → nacido 1 mar 1991 (91 > 26 → 1900+91=1991).
    Como hoy es mayo 2026 y su cumpleaños fue en marzo → edad = 35.
    """
    inst = Institucion(nombre='Hospital Mensuraciones Test')
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    p = Paciente(
        no_hc='MENS-M001',
        ci='910301XXXXX'[:11].ljust(11, '0'),   # "91030100000"
        nombres='Carlos',
        apellidos='Masculino',
        sexo='Masculino',
        activo=True,
        institucion_id=inst.id,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope='module')
def paciente_femenino(db_session, paciente_masculino):
    """
    Paciente femenino, 45 años.
    CI: "810301XXXXX" → nacido 1 mar 1981 (81 > 26 → 1981). Edad = 45.
    Reutiliza la institución del paciente masculino.
    """
    inst_id = paciente_masculino.institucion_id
    p = Paciente(
        no_hc='MENS-F001',
        ci='810301' + '0' * 5,   # "81030100000"
        nombres='Laura',
        apellidos='Femenina',
        sexo='Femenino',
        activo=True,
        institucion_id=inst_id,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope='module')
def paciente_mayor(db_session, paciente_masculino):
    """
    Paciente masculino, 65 años.
    CI: "610301XXXXX" → nacido 1 mar 1961 (61 > 26 → 1961). Edad = 65.
    """
    inst_id = paciente_masculino.institucion_id
    p = Paciente(
        no_hc='MENS-M065',
        ci='610301' + '0' * 5,
        nombres='Miguel',
        apellidos='Mayor',
        sexo='Masculino',
        activo=True,
        institucion_id=inst_id,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def ctrl(db_session):
    return MensuracionesController(db_session)


@pytest.fixture(autouse=True)
def limpiar_mensuraciones(db_session):
    """Elimina todas las mensuraciones entre cada test."""
    yield
    try:
        db_session.query(Mensuraciones).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS PARA TESTS DE PROPIEDADES (SIN BD)
# ─────────────────────────────────────────────────────────────────────────────

def _mens(talla=None, peso=None, cintura=None, cadera=None,
          cuello=None, dieta=None, sexo='Masculino', edad=35):
    """
    Crea un objeto Mensuraciones sin BD, con un MagicMock como paciente.
    Ideal para tests de @property que no necesitan persistencia.
    """
    m = Mensuraciones()
    m.talla   = talla
    m.peso    = peso
    m.cintura = cintura
    m.cadera  = cadera
    m.cuello  = cuello
    m.dieta   = dieta

    pac = MagicMock()
    pac.sexo        = sexo
    pac.edad_actual = edad
    m.paciente = pac
    return m


# ══════════════════════════════════════════════════════════════════════════════
#  TestIMC
# ══════════════════════════════════════════════════════════════════════════════

class TestIMC:
    """Validación matemática de la propiedad IMC."""

    def test_imc_calculado_correctamente(self):
        """80 kg / (1.80 m)² = 24.69."""
        m = _mens(peso=80.0, talla=180)
        assert m.IMC == pytest.approx(24.69, abs=0.01)

    def test_imc_bajo_peso(self):
        """50 kg / (1.75 m)² = 16.33 → IMC < 18.5."""
        m = _mens(peso=50.0, talla=175)
        assert isinstance(m.IMC, float)
        assert m.IMC < 18.5

    def test_imc_sobrepeso(self):
        """85 kg / (1.75 m)² = 27.76 → 25 <= IMC < 30."""
        m = _mens(peso=85.0, talla=175)
        assert 25 <= m.IMC < 30

    def test_imc_obesidad(self):
        """100 kg / (1.75 m)² = 32.65 → IMC >= 30."""
        m = _mens(peso=100.0, talla=175)
        assert m.IMC >= 30

    def test_imc_talla_cero_retorna_string(self):
        """talla=0 → mensaje de error (string)."""
        m = _mens(peso=80.0, talla=0)
        assert isinstance(m.IMC, str)

    def test_imc_talla_none_retorna_string(self):
        """talla=None → mensaje de error."""
        m = _mens(peso=80.0, talla=None)
        assert isinstance(m.IMC, str)

    def test_imc_peso_none_retorna_string(self):
        """peso=None → mensaje de error."""
        m = _mens(peso=None, talla=180)
        assert isinstance(m.IMC, str)

    def test_imc_peso_cero_retorna_string(self):
        """peso=0 → mensaje de error."""
        m = _mens(peso=0, talla=180)
        assert isinstance(m.IMC, str)

    def test_imc_es_redondeado_a_2_decimales(self):
        """El resultado tiene máximo 2 decimales."""
        m = _mens(peso=80.0, talla=180)
        imc = m.IMC
        assert isinstance(imc, float)
        assert round(imc, 2) == imc


# ══════════════════════════════════════════════════════════════════════════════
#  TestClasificarIMC
# ══════════════════════════════════════════════════════════════════════════════

class TestClasificarIMC:
    """Clasificación IMC — todos los rangos del modelo."""

    def _clasificar(self, peso, talla):
        return _mens(peso=peso, talla=talla).clasificar_imc

    def test_clasificar_bajo_peso(self):
        """50 kg / 1.75² = 16.33 → 'Bajo peso'."""
        color, clasif = self._clasificar(50.0, 175)
        assert color == 'amber'
        assert clasif == 'Bajo peso'

    def test_clasificar_normal(self):
        """70 kg / 1.75² = 22.86 → 'Normal'."""
        color, clasif = self._clasificar(70.0, 175)
        assert color == 'green'
        assert clasif == 'Normal'

    def test_clasificar_sobrepeso(self):
        """85 kg / 1.75² = 27.76 → 'Sobrepeso'."""
        color, clasif = self._clasificar(85.0, 175)
        assert color == 'orange'
        assert clasif == 'Sobrepeso'

    def test_clasificar_obesidad_grado_1(self):
        """100 kg / 1.75² = 32.65 → 'Obesidad Grado 1'."""
        color, clasif = self._clasificar(100.0, 175)
        assert color == 'red'
        assert clasif == 'Obesidad Grado 1'

    def test_clasificar_obesidad_grado_2(self):
        """115 kg / 1.75² = 37.55 → 'Obesidad Grado 2'."""
        color, clasif = self._clasificar(115.0, 175)
        assert color == 'red'
        assert clasif == 'Obesidad Grado 2'

    def test_clasificar_obesidad_grado_3(self):
        """130 kg / 1.75² = 42.45 → 'Obesidad Grado 3'."""
        color, clasif = self._clasificar(130.0, 175)
        assert color == 'red'
        assert clasif == 'Obesidad Grado 3'

    def test_clasificar_sin_datos_retorna_gray(self):
        """Sin talla → IMC es string → clasificación 'gray'."""
        color, clasif = _mens(peso=80.0, talla=None).clasificar_imc
        assert color == 'gray'

    def test_limite_exacto_18_5_es_normal(self):
        """IMC = 18.5 exacto → 'Normal' (boundary 18.5 <= IMC < 25)."""
        # peso = 18.5 * (1.0)² = 18.5 kg con talla=100cm
        m = _mens(peso=18.5, talla=100)
        _, clasif = m.clasificar_imc
        assert clasif == 'Normal'

    def test_limite_exacto_25_es_sobrepeso(self):
        """IMC = 25 exacto → 'Sobrepeso' (boundary 25 <= IMC < 30)."""
        # peso = 25 * (1.0)² = 25 kg con talla=100cm
        m = _mens(peso=25.0, talla=100)
        _, clasif = m.clasificar_imc
        assert clasif == 'Sobrepeso'


# ══════════════════════════════════════════════════════════════════════════════
#  TestPesoIdeal
# ══════════════════════════════════════════════════════════════════════════════

class TestPesoIdeal:
    """@property peso_ideal — fórmula 22*(talla_m²) H, 21*(talla_m²) M."""

    def test_peso_ideal_masculino_180cm(self):
        """22 × (1.80)² = 71.28 kg."""
        m = _mens(talla=180, peso=80.0, sexo='Masculino')
        assert m.peso_ideal == pytest.approx(71.28, abs=0.01)

    def test_peso_ideal_femenino_165cm(self):
        """21 × (1.65)² = 57.17 kg."""
        m = _mens(talla=165, peso=60.0, sexo='Femenino')
        assert m.peso_ideal == pytest.approx(57.17, abs=0.01)

    def test_peso_ideal_hombre_es_mayor_que_mujer_misma_talla(self):
        """Con la misma talla, el peso ideal masculino > femenino."""
        m_h = _mens(talla=170, peso=75.0, sexo='Masculino')
        m_f = _mens(talla=170, peso=65.0, sexo='Femenino')
        assert m_h.peso_ideal > m_f.peso_ideal

    def test_peso_ideal_sin_talla_retorna_0(self):
        """talla=None → retorna 0 (sin lanzar excepción)."""
        m = _mens(talla=None, peso=80.0, sexo='Masculino')
        assert m.peso_ideal == 0

    def test_peso_ideal_talla_cero_retorna_0(self):
        """talla=0 → retorna 0."""
        m = _mens(talla=0, peso=80.0, sexo='Masculino')
        assert m.peso_ideal == 0

    def test_peso_ideal_sexo_femenino_por_defecto(self):
        """Sexo no reconocido → usa fórmula femenina (21)."""
        m = _mens(talla=170, peso=65.0, sexo='Otro')
        pi_f_esperado = 21 * (1.70 ** 2)
        assert m.peso_ideal == pytest.approx(pi_f_esperado, abs=0.01)


# ══════════════════════════════════════════════════════════════════════════════
#  TestPI  (Peso Ideal Ajustado)
# ══════════════════════════════════════════════════════════════════════════════

class TestPI:
    """@property PI — peso ideal ajustado según estado nutricional."""

    def test_pi_normal_igual_al_peso_ideal(self):
        """IMC normal (24.69): PI = peso_ideal = 71.28."""
        m = _mens(peso=80.0, talla=180, sexo='Masculino')
        assert m.PI == pytest.approx(71.28, abs=0.01)

    def test_pi_sobrepeso_incluye_ajuste(self):
        """
        IMC 30.86 (100 kg / 1.80²), sexo M:
        peso_ideal = 71.28
        ajuste = 0.25 × (100 - 71.28) = 7.18
        PI = 71.28 + 7.18 = 78.46
        """
        m = _mens(peso=100.0, talla=180, sexo='Masculino')
        assert m.PI == pytest.approx(78.46, abs=0.05)

    def test_pi_bajo_peso_igual_al_peso_ideal(self):
        """IMC < 18.5: PI = peso_ideal (sin ajuste)."""
        m = _mens(peso=50.0, talla=175, sexo='Masculino')
        pi_esperado = 22 * (1.75 ** 2)
        assert m.PI == pytest.approx(pi_esperado, abs=0.01)

    def test_pi_sin_datos_retorna_string(self):
        """Sin talla → IMC inválido → PI = string de error."""
        m = _mens(peso=80.0, talla=None, sexo='Masculino')
        assert isinstance(m.PI, str)


# ══════════════════════════════════════════════════════════════════════════════
#  TestICC  e  TestICaltura
# ══════════════════════════════════════════════════════════════════════════════

class TestICC:
    """@property ICC — Índice Cintura-Cadera."""

    def test_icc_calculado_correctamente(self):
        """90 / 100 = 0.9."""
        m = _mens(cintura=90, cadera=100)
        assert m.ICC == pytest.approx(0.9, abs=0.01)

    def test_icc_sin_cadera_retorna_string(self):
        m = _mens(cintura=90, cadera=None)
        assert isinstance(m.ICC, str)

    def test_icc_cadera_cero_retorna_string(self):
        m = _mens(cintura=90, cadera=0)
        assert isinstance(m.ICC, str)

    def test_icc_sin_cintura_retorna_string(self):
        m = _mens(cintura=None, cadera=100)
        assert isinstance(m.ICC, str)

    def test_icc_redondeado_2_decimales(self):
        """85 / 95 = 0.894... → 0.89."""
        m = _mens(cintura=85, cadera=95)
        assert m.ICC == pytest.approx(0.89, abs=0.01)


class TestICaltura:
    """@property ICaltura — Índice Cintura-Talla."""

    def test_icaltura_calculado_correctamente(self):
        """90 / 180 = 0.5."""
        m = _mens(cintura=90, talla=180)
        assert m.ICaltura == pytest.approx(0.5, abs=0.01)

    def test_icaltura_sin_datos_retorna_string(self):
        m = _mens(cintura=None, talla=180)
        assert isinstance(m.ICaltura, str)

    def test_icaltura_talla_cero_retorna_string(self):
        m = _mens(cintura=90, talla=0)
        assert isinstance(m.ICaltura, str)


# ══════════════════════════════════════════════════════════════════════════════
#  TestGrasaDeurenberg
# ══════════════════════════════════════════════════════════════════════════════

class TestGrasaDeurenberg:
    """
    @property grasa_deurenberg — Fórmula PubMed.
    Adultos (>15):  (1.20×IMC) + (0.23×edad) - (10.8×sex_val) - 5.4
    """

    def test_grasa_deurenberg_hombre_35_anos(self):
        """
        IMC=24.69, edad=35, hombre (sex_val=1):
        (1.20×24.69)+(0.23×35)-(10.8×1)-5.4 = 21.5
        """
        m = _mens(peso=80.0, talla=180, sexo='Masculino', edad=35)
        assert m.grasa_deurenberg == pytest.approx(21.5, abs=0.2)

    def test_grasa_deurenberg_mujer_45_anos(self):
        """
        IMC=24.69, edad=45, mujer (sex_val=0):
        (1.20×24.69)+(0.23×45)-(10.8×0)-5.4 = 34.6
        """
        m = _mens(peso=80.0, talla=180, sexo='Femenino', edad=45)
        assert m.grasa_deurenberg == pytest.approx(34.6, abs=0.2)

    def test_grasa_deurenberg_hombre_mayor_que_mujer_mismo_imc(self):
        """Con el mismo IMC, la mujer tiene mayor % grasa (sex_val=0 vs 1)."""
        m_h = _mens(peso=80.0, talla=180, sexo='Masculino', edad=40)
        m_f = _mens(peso=80.0, talla=180, sexo='Femenino',  edad=40)
        assert m_f.grasa_deurenberg > m_h.grasa_deurenberg

    def test_grasa_deurenberg_sin_imc_valido_retorna_string(self):
        """Sin talla → IMC es string → grasa_deurenberg = string de error."""
        m = _mens(peso=80.0, talla=None, sexo='Masculino', edad=35)
        assert isinstance(m.grasa_deurenberg, str)

    def test_grasa_deurenberg_edad_mayor_produce_valor_mayor(self):
        """Mayor edad → mayor grasa (0.23×edad aumenta el resultado)."""
        m_joven  = _mens(peso=80.0, talla=180, sexo='Masculino', edad=25)
        m_mayor  = _mens(peso=80.0, talla=180, sexo='Masculino', edad=55)
        assert m_mayor.grasa_deurenberg > m_joven.grasa_deurenberg


# ══════════════════════════════════════════════════════════════════════════════
#  TestGrasaMarina
# ══════════════════════════════════════════════════════════════════════════════

class TestGrasaMarina:
    """@property grasa_marina — U.S. Navy Method."""

    def test_marina_hombre_produce_float(self):
        """
        talla=180, cintura=90, cuello=38 → 19.8 %
        diff=52 > 0, fórmula masculina válida.
        """
        m = _mens(talla=180, cintura=90, cuello=38, sexo='Masculino')
        resultado = m.grasa_marina
        assert isinstance(resultado, float), f"Esperado float, obtuvo: {resultado!r}"
        assert resultado == pytest.approx(19.8, abs=0.5)

    def test_marina_mujer_con_cadera_produce_float(self):
        """
        talla=165, cintura=80, cadera=100, cuello=33 → 31.9 %
        suma=147 > 0, fórmula femenina válida.
        """
        m = _mens(talla=165, cintura=80, cadera=100, cuello=33, sexo='Femenino')
        resultado = m.grasa_marina
        assert isinstance(resultado, float), f"Esperado float, obtuvo: {resultado!r}"
        assert resultado == pytest.approx(31.9, abs=0.5)

    def test_marina_mujer_sin_cadera_retorna_datos_insuficientes(self):
        """Para mujer, cadera es obligatoria. Sin ella → 'Datos insuficientes'."""
        m = _mens(talla=165, cintura=80, cadera=None, cuello=33, sexo='Femenino')
        assert m.grasa_marina == 'Datos insuficientes'

    def test_marina_mujer_cadera_cero_retorna_datos_insuficientes(self):
        """cadera=0 → 'Datos insuficientes'."""
        m = _mens(talla=165, cintura=80, cadera=0, cuello=33, sexo='Femenino')
        assert m.grasa_marina == 'Datos insuficientes'

    def test_marina_sin_cuello_retorna_datos_insuficientes(self):
        """cuello=None → falta dato obligatorio."""
        m = _mens(talla=180, cintura=90, cuello=None, sexo='Masculino')
        assert m.grasa_marina == 'Datos insuficientes'

    def test_marina_sin_talla_retorna_datos_insuficientes(self):
        """talla=None → falta dato obligatorio."""
        m = _mens(talla=None, cintura=90, cuello=38, sexo='Masculino')
        assert m.grasa_marina == 'Datos insuficientes'

    def test_marina_hombre_cintura_menor_cuello_retorna_error_medidas(self):
        """
        diff = cintura - cuello <= 0 → 'Error medidas'.
        cintura=35, cuello=38 → diff=-3
        """
        m = _mens(talla=180, cintura=35, cuello=38, sexo='Masculino')
        assert m.grasa_marina == 'Error medidas'


# ══════════════════════════════════════════════════════════════════════════════
#  TestClasificarComposicionCorporal
# ══════════════════════════════════════════════════════════════════════════════

class TestClasificarComposicionCorporal:
    """
    Clasificación por edad y sexo.
    Se mockea grasa_marina para aislar la lógica de clasificación pura.

    Límites reales del modelo:
      Hombre <40:  [8, 20, 25]   — bajo / saludable / sobrepeso / obesidad
      Hombre <60:  [11, 22, 28]
      Hombre >=60: [13, 25, 30]
      Mujer  <40:  [16, 28, 39]
      Mujer  <60:  [18, 30, 40]
      Mujer  >=60: [20, 32, 42]
    """

    def _clasificar_con_grasa(self, grasa_val, sexo, edad):
        """Helper: crea Mensuraciones con grasa_marina mockeada."""
        m = _mens(sexo=sexo, edad=edad)
        with patch.object(
            type(m), 'grasa_marina',
            new_callable=PropertyMock,
            return_value=grasa_val,
        ):
            return m.clasificar_composicion_corporal

    # ── Hombre < 40 (limites=[8,20,25]) ─────────────────────────────────────

    def test_hombre_35_bajo_en_grasa(self):
        """4.6 < 8 → 'Bajo en grasa' (azul)."""
        color, clasif = self._clasificar_con_grasa(4.6, 'Masculino', 35)
        assert color == 'blue'
        assert clasif == 'Bajo en grasa'

    def test_hombre_35_saludable(self):
        """19.8 <= 20 → 'Saludable' (verde)."""
        color, clasif = self._clasificar_con_grasa(19.8, 'Masculino', 35)
        assert color == 'green'
        assert clasif == 'Saludable'

    def test_hombre_35_sobrepeso(self):
        """23.2 > 20, <= 25 → 'Sobrepeso' (naranja)."""
        color, clasif = self._clasificar_con_grasa(23.2, 'Masculino', 35)
        assert color == 'orange'
        assert clasif == 'Sobrepeso'

    def test_hombre_35_obesidad(self):
        """26.4 > 25 → 'Obesidad' (rojo)."""
        color, clasif = self._clasificar_con_grasa(26.4, 'Masculino', 35)
        assert color == 'red'
        assert clasif == 'Obesidad'

    # ── Hombre >= 60 (limites=[13,25,30]) ───────────────────────────────────

    def test_hombre_65_saludable_con_grasa_mayor(self):
        """
        24.0: con hombre <40 sería sobrepeso, pero con >=60
        limites=[13,25,30] → 24.0 <= 25 → 'Saludable'.
        """
        color, clasif = self._clasificar_con_grasa(24.0, 'Masculino', 65)
        assert color == 'green'
        assert clasif == 'Saludable'

    def test_hombre_65_sobrepeso_con_grasa_moderada(self):
        """28.0: con >=60 → 25 < 28.0 <= 30 → 'Sobrepeso'."""
        color, clasif = self._clasificar_con_grasa(28.0, 'Masculino', 65)
        assert color == 'orange'
        assert clasif == 'Sobrepeso'

    # ── Mujer < 60 (limites=[18,30,40]) ─────────────────────────────────────

    def test_mujer_45_sobrepeso(self):
        """31.9 > 30, <= 40 → 'Sobrepeso' (naranja)."""
        color, clasif = self._clasificar_con_grasa(31.9, 'Femenino', 45)
        assert color == 'orange'
        assert clasif == 'Sobrepeso'

    def test_mujer_45_saludable(self):
        """25.0: limites=[18,30,40] → 18 <= 25.0 <= 30 → 'Saludable'."""
        color, clasif = self._clasificar_con_grasa(25.0, 'Femenino', 45)
        assert color == 'green'
        assert clasif == 'Saludable'

    # ── Mujer >= 60 (limites=[20,32,42]) ────────────────────────────────────

    def test_mujer_65_saludable_con_grasa_alta(self):
        """31.9: con <60 → sobrepeso; con >=60 limites=[20,32,42] → saludable."""
        color, clasif = self._clasificar_con_grasa(31.9, 'Femenino', 65)
        assert color == 'green'
        assert clasif == 'Saludable'

    def test_clasificar_con_error_en_grasa_marina_retorna_gray(self):
        """grasa_marina = string de error → 'gray'."""
        color, clasif = self._clasificar_con_grasa('Datos insuficientes', 'Masculino', 35)
        assert color == 'gray'


# ══════════════════════════════════════════════════════════════════════════════
#  TestCRUDMensuraciones  (controlador con BD real)
# ══════════════════════════════════════════════════════════════════════════════

class TestCRUDMensuraciones:
    """Tests del controlador contra SQLite en memoria."""

    # ── guardar_mensuracion ──────────────────────────────────────────────────

    def test_guardar_persiste_floats_correctamente(
        self, ctrl, db_session, paciente_masculino
    ):
        """Todos los campos numéricos se guardan como float en BD."""
        ok, msg = ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-04-15',
            peso=80.5,
            talla=180,
            cintura=90,
            cadera=100,
            cuello=38,
            dieta='Hipocalórica',
        )

        assert ok is True
        assert 'correctamente' in msg.lower()

        guardado = (
            db_session.query(Mensuraciones)
            .filter_by(paciente_id=paciente_masculino.id)
            .first()
        )
        assert guardado is not None
        assert guardado.peso    == pytest.approx(80.5, abs=0.01)
        assert guardado.talla   == 180
        assert guardado.cintura == 90
        assert guardado.cadera  == 100
        assert guardado.cuello  == 38
        assert guardado.dieta   == 'Hipocalórica'
        assert guardado.fecha_registro == date(2024, 4, 15)

    def test_guardar_campos_vacios_quedan_none(
        self, ctrl, db_session, paciente_masculino
    ):
        """Campos con '' → None en BD (no lanza excepción)."""
        ok, _ = ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-05-01',
            peso='',
            talla='',
            cintura=None,
            cadera=None,
            cuello=None,
            dieta=None,
        )
        assert ok is True
        guardado = (
            db_session.query(Mensuraciones)
            .filter_by(paciente_id=paciente_masculino.id)
            .first()
        )
        assert guardado.peso    is None
        assert guardado.talla   is None
        assert guardado.cintura is None

    def test_guardar_fecha_invalida_falla(self, ctrl, paciente_masculino):
        """Fecha mal formateada → (False, mensaje) sin crash."""
        ok, msg = ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='15/04/2024',
            peso=80.0,
            talla=180,
            cintura=90, cadera=100, cuello=38, dieta=None,
        )
        assert ok is False
        assert isinstance(msg, str) and len(msg) > 0

    def test_guardar_fecha_vacia_falla(self, ctrl, paciente_masculino):
        """Fecha vacía → (False, mensaje)."""
        ok, msg = ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='',
            peso=80.0,
            talla=180,
            cintura=90, cadera=100, cuello=38, dieta=None,
        )
        assert ok is False

    def test_guardar_valor_no_numerico_falla(self, ctrl, paciente_masculino):
        """peso='abc' → ValueError capturado → (False, mensaje)."""
        ok, msg = ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-06-01',
            peso='abc',
            talla=180,
            cintura=90, cadera=100, cuello=38, dieta=None,
        )
        assert ok is False
        assert 'numéric' in msg.lower() or 'error' in msg.lower()

    def test_guardar_error_hace_rollback(self, ctrl, db_session, paciente_masculino):
        """Fallo en commit → rollback es llamado y retorna (False, msg)."""
        with patch.object(db_session, 'commit', side_effect=Exception('BD caída')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('controllers.historia_clinica_mensuraciones_controller.log_error_and_notify'):
                    ok, _ = ctrl.guardar_mensuracion(
                        paciente_id=paciente_masculino.id,
                        fecha_str='2024-07-01',
                        peso=80.0, talla=180,
                        cintura=90, cadera=100, cuello=38, dieta=None,
                    )
        assert ok is False
        mock_rb.assert_called_once()

    # ── actualizar_mensuracion ───────────────────────────────────────────────

    def test_actualizar_modifica_campos_en_bd(
        self, ctrl, db_session, paciente_masculino
    ):
        """Los nuevos valores persisten correctamente tras la actualización."""
        ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-08-01',
            peso=80.0, talla=180,
            cintura=90, cadera=100, cuello=38, dieta='Normal',
        )
        m = db_session.query(Mensuraciones).filter_by(
            paciente_id=paciente_masculino.id
        ).first()

        ok, msg = ctrl.actualizar_mensuracion(
            mensuracion=m,
            fecha_str='2024-09-01',
            peso=85.0, talla=180,
            cintura=92, cadera=102, cuello=39, dieta='Hipocalórica',
        )

        assert ok is True
        db_session.expire(m)
        actualizado = db_session.get(Mensuraciones, m.id)

        assert actualizado.fecha_registro == date(2024, 9, 1)
        assert actualizado.peso    == pytest.approx(85.0, abs=0.01)
        assert actualizado.cintura == 92
        assert actualizado.dieta   == 'Hipocalórica'

    def test_actualizar_error_hace_rollback(
        self, ctrl, db_session, paciente_masculino
    ):
        """Fallo en commit durante actualización → rollback llamado."""
        ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-10-01',
            peso=80.0, talla=180,
            cintura=90, cadera=100, cuello=38, dieta=None,
        )
        m = db_session.query(Mensuraciones).filter_by(
            paciente_id=paciente_masculino.id
        ).first()

        with patch.object(db_session, 'commit', side_effect=Exception('commit fail')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('controllers.historia_clinica_mensuraciones_controller.log_error_and_notify'):
                    ok, _ = ctrl.actualizar_mensuracion(
                        mensuracion=m,
                        fecha_str='2024-11-01',
                        peso=90.0, talla=180,
                        cintura=95, cadera=105, cuello=40, dieta=None,
                    )
        assert ok is False
        mock_rb.assert_called_once()

    # ── eliminar_mensuracion ─────────────────────────────────────────────────

    def test_eliminar_borra_registro_de_bd(
        self, ctrl, db_session, paciente_masculino
    ):
        """El objeto ORM desaparece de la BD tras la eliminación."""
        ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-11-15',
            peso=78.0, talla=178,
            cintura=88, cadera=98, cuello=37, dieta=None,
        )
        m = db_session.query(Mensuraciones).filter_by(
            paciente_id=paciente_masculino.id
        ).first()
        m_id = m.id

        ok, msg = ctrl.eliminar_mensuracion(m)

        assert ok is True
        assert 'eliminada' in msg.lower()
        assert db_session.get(Mensuraciones, m_id) is None

    def test_eliminar_none_retorna_false_con_mensaje(self, ctrl):
        """eliminar_mensuracion(None) → (False, mensaje) sin excepción."""
        ok, msg = ctrl.eliminar_mensuracion(None)
        assert ok is False
        assert 'existe' in msg.lower() or 'error' in msg.lower()

    def test_eliminar_error_hace_rollback(
        self, ctrl, db_session, paciente_masculino
    ):
        """Fallo en commit → rollback llamado."""
        ctrl.guardar_mensuracion(
            paciente_id=paciente_masculino.id,
            fecha_str='2024-12-01',
            peso=80.0, talla=180,
            cintura=90, cadera=100, cuello=38, dieta=None,
        )
        m = db_session.query(Mensuraciones).filter_by(
            paciente_id=paciente_masculino.id
        ).first()

        with patch.object(db_session, 'commit', side_effect=Exception('delete fail')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('controllers.historia_clinica_mensuraciones_controller.log_error_and_notify'):
                    ok, _ = ctrl.eliminar_mensuracion(m)
        assert ok is False
        mock_rb.assert_called_once()

    # ── obtener_mensuraciones_procesadas ─────────────────────────────────────

    def test_obtener_ordena_descendente_y_extrae_ultima(
        self, ctrl, db_session, paciente_masculino
    ):
        """
        Tres mensuraciones en fechas distintas:
        la lista debe estar en orden descendente y 'ultima' ser el
        registro más reciente.
        """
        fechas_pesos = [
            ('2022-01-10', 82.0),
            ('2023-06-15', 80.0),
            ('2024-11-20', 77.5),
        ]
        for fecha_str, peso in fechas_pesos:
            ctrl.guardar_mensuracion(
                paciente_id=paciente_masculino.id,
                fecha_str=fecha_str,
                peso=peso, talla=180,
                cintura=90, cadera=100, cuello=38, dieta=None,
            )

        db_session.expire(paciente_masculino)
        db_session.refresh(paciente_masculino)

        lista, ultima = ctrl.obtener_mensuraciones_procesadas(paciente_masculino)

        assert len(lista) == 3

        fechas = [m.fecha_registro for m in lista]
        assert fechas == sorted(fechas, reverse=True), (
            f"Lista no está en orden descendente: {fechas}"
        )
        assert ultima is lista[0]
        assert ultima.fecha_registro == date(2024, 11, 20)
        assert ultima.peso == pytest.approx(77.5, abs=0.01)

    def test_obtener_sin_mensuraciones_retorna_lista_vacia_y_none(
        self, ctrl, db_session, paciente_femenino
    ):
        """Paciente sin mensuraciones → ([], None)."""
        db_session.expire(paciente_femenino)
        db_session.refresh(paciente_femenino)

        lista, ultima = ctrl.obtener_mensuraciones_procesadas(paciente_femenino)

        assert lista  == []
        assert ultima is None

    def test_obtener_paciente_none_retorna_lista_vacia_y_none(self, ctrl):
        """paciente=None → ([], None) sin excepción."""
        lista, ultima = ctrl.obtener_mensuraciones_procesadas(None)
        assert lista  == []
        assert ultima is None
