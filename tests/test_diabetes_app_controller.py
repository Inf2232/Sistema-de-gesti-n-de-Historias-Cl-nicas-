# =============================================================================
# test_diabetes_app_controller.py
#
# Pruebas de caja blanca y negra para DiabetesAppController.
#
# ESTRATEGIA DE MOCK:
#   El controlador crea su propia sesión internamente con `db = Session()`.
#   Para redirigir esas llamadas a nuestra BD en memoria del fixture `db_session`,
#   usamos @patch sobre el símbolo 'Session' dentro del módulo del controlador.
#   Esto hace que Session() retorne nuestro db_session real en lugar de abrir
#   una conexión al archivo SQLite de producción.
#
#   Si tu controlador está en controllers/diabetes_app_controller.py, ajusta:
#   PATCH_TARGET = 'controllers.diabetes_app_controller.Session'
# =============================================================================

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from controllers.diabetes_app_controller import DiabetesAppController
from models import Institucion, Provincia, Municipio, AreaSalud, Paciente

# Ajusta este path al lugar real donde vive el módulo en tu proyecto
PATCH_TARGET = 'controllers.diabetes_app_controller.Session'


# =============================================================================
# FIXTURES LOCALES  (complementan al db_session de conftest.py)
# =============================================================================

@pytest.fixture
def controller():
    """Instancia limpia del controlador para cada test."""
    return DiabetesAppController()


@pytest.fixture
def institucion(db_session):
    """
    Inserta una Institución de prueba y la retorna.
    El rollback de db_session la limpiará al terminar el test.
    """
    inst = Institucion(nombre="Clínica Test", provincia_default="La Habana")
    db_session.add(inst)
    db_session.flush()   # flush asigna el id sin hacer commit real
    return inst


@pytest.fixture
def geografia(db_session):
    """
    Crea la cadena geográfica completa:
        Provincia  →  Municipio  →  AreaSalud

    Necesaria para que guardar_paciente pueda resolver las FK de ubicación
    sin devolver None en las consultas internas del controlador.
    """
    provincia = Provincia(nombre="La Habana", codigo="LH")
    db_session.add(provincia)
    db_session.flush()

    municipio = Municipio(
        nombre="Centro Habana",
        codigo="CH",
        provincia_id=provincia.id
    )
    db_session.add(municipio)
    db_session.flush()

    area = AreaSalud(nombre="Policlínico Central", municipio_id=municipio.id)
    db_session.add(area)
    db_session.flush()

    return provincia, municipio, area


# -----------------------------------------------------------------------------
# Función auxiliar (no es fixture): retorna un dict de datos de paciente válido.
# Acepta parámetros para poder variar no_hc y ci en distintos tests.
# -----------------------------------------------------------------------------
def _datos_paciente(no_hc: str = "HC-TEST-001", ci: str = "85010112345") -> dict:
    """
    Genera un diccionario con todos los campos que guardar_paciente() espera.
    El CI '85010112345' se interpreta como nacido el 01/01/1985 por edad_actual.
    """
    return {
        "no_hc": no_hc,
        "ci": ci,
        "nombres": "Juan Carlos",
        "apellidos": "García López",
        "telefono": "55551234",
        "nombre_contacto_emergencia": "María García",
        "tel_emergencia": "55554321",
        "nombre_provincia": "La Habana",
        "nombre_municipio": "Centro Habana",
        "nombre_area": "Policlínico Central",
        "fecha_hc": date(2023, 5, 15),
        "estado_actual": "Activo",
        "calle": "Obispo",
        "numero": "123",
        "entre_calles": "O'Reilly y Obrapía",
        "sexo": "Masculino",
        "color_piel": "Claro",
        "escolaridad": "Universitario",
        "ocupacion": "Ingeniero",
        "estado_civil": "Acompañado",
        "tiempo_evolucion_anios": 5,
        "tiempo_evolucion_meses": 3,
        "forma_presentacion_diagnostico": "Casual",
        "glucemia_debut": 7.5,
        "exceso_peso_diagnostico": "No",
        "tiempo_exceso_peso_anios": 0,
        "tiempo_exceso_peso_meses": 0,
        "remision": "No",
        "tratamiento_inicial": "Metformina",
        "dosis_tratamiento": "500mg",
        "ano_inicio_tratamiento": 2018,
        "prediabetes": "No",
        "tiempo_prediabetes_anios": None,
        "tiempo_prediabetes_meses": None,
        "causa_fallecimiento": None,
    }


# =============================================================================
# HELPER DE MOCK  —  evita repetir el mismo boilerplate en cada test
# =============================================================================

def _parchear_session(mock_cls, db_session):
    """
    Configura el MagicMock de Session para que:
      - Session()   →  devuelve nuestro db_session real
      - db.close()  →  no-op (evita que el controlador cierre la sesión
                        antes de que el test pueda verificar los resultados)
    """
    mock_cls.return_value = db_session
    db_session.close = MagicMock()   # <-- clave: neutralizamos el finally: db.close()


# =============================================================================
# TEST 1 — get_institucion_info
# CAJA NEGRA: evaluamos las salidas ante distintos roles de entrada.
# =============================================================================
class TestGetInstitucionInfo:

    def test_superadmin_sin_institucion_asignada(self, controller, db_session):
        """
        Un superadministrador sin inst_id válido recibe el nombre especial
        'Gestión Nacional (SuperAdministrador)' y has_institucion=False.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.get_institucion_info("superadministrador", None)

        assert resultado["institucion_nombre"] == "Gestión Nacional (SuperAdministrador)"
        assert resultado["has_institucion"] is False
        assert resultado["provincia_default"] is None

    def test_superadmin_con_institucion_valida(self, controller, db_session, institucion):
        """
        Un superadministrador CON inst_id recibe el nombre especial más
        los datos de provincia y has_institucion=True.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.get_institucion_info("superadministrador", institucion.id)

        # El nombre sigue siendo el especial aunque tenga institución
        assert resultado["institucion_nombre"] == "Gestión Nacional (SuperAdministrador)"
        assert resultado["provincia_default"] == "La Habana"
        assert resultado["has_institucion"] is True

    def test_rol_normal_con_institucion_valida(self, controller, db_session, institucion):
        """
        Un médico u otro rol normal recibe el nombre REAL de la institución.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.get_institucion_info("medico", institucion.id)

        assert resultado["institucion_nombre"] == "Clínica Test"
        assert resultado["has_institucion"] is True
        assert resultado["provincia_default"] == "La Habana"

    def test_rol_normal_sin_inst_id_devuelve_nombre_generico(self, controller, db_session):
        """
        CAJA NEGRA — valor límite: inst_id=None con rol normal.
        Debe caer en la rama else y devolver el nombre genérico hardcoded.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.get_institucion_info("medico", None)

        assert resultado["institucion_nombre"] == "Clínica del Diabético"
        assert resultado["has_institucion"] is False

    def test_rol_normal_inst_id_inexistente(self, controller, db_session):
        """
        CAJA BLANCA — rama 'inst no encontrada':
        Si inst_id no corresponde a ningún registro, devuelve 'Institución Desconocida'.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.get_institucion_info("medico", 9999)

        assert resultado["institucion_nombre"] == "Institución Desconocida"
        assert resultado["has_institucion"] is False


# =============================================================================
# TEST 2 — validar_existencia
# CAJA BLANCA: verificamos que las consultas a BD detectan duplicados.
# =============================================================================
class TestValidarExistencia:

    def test_detecta_hc_y_ci_existentes(self, controller, db_session, institucion):
        """
        Si ya existe un paciente con el mismo no_hc y ci,
        ambos flags deben ser True.
        """
        # Arrange: insertar paciente directamente en la sesión de prueba
        paciente_existente = Paciente(
            no_hc="HC-EXISTENTE",
            ci="90010212345",
            institucion_id=institucion.id,
            fecha_hc=date(2022, 1, 1),
            activo=True,
        )
        db_session.add(paciente_existente)
        db_session.flush()

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            # Act
            resultado = controller.validar_existencia("HC-EXISTENTE", "90010212345")

        # Assert
        assert resultado["existe_hc"] is True
        assert resultado["existe_ci"] is True

    def test_hc_existente_ci_nuevo(self, controller, db_session, institucion):
        """
        Solo el no_hc existe; el ci es nuevo. Solo existe_hc debe ser True.
        """
        paciente_existente = Paciente(
            no_hc="HC-SOLO-HC",
            ci="75050612345",
            institucion_id=institucion.id,
            fecha_hc=date(2021, 6, 1),
            activo=True,
        )
        db_session.add(paciente_existente)
        db_session.flush()

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.validar_existencia("HC-SOLO-HC", "99999999999")

        assert resultado["existe_hc"] is True
        assert resultado["existe_ci"] is False

    def test_ambos_nuevos_devuelve_false(self, controller, db_session):
        """
        CAJA NEGRA — camino feliz: no_hc y ci que no existen → ambos False.
        """
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            resultado = controller.validar_existencia("HC-NUEVO-99", "00000000001")

        assert resultado["existe_hc"] is False
        assert resultado["existe_ci"] is False


# =============================================================================
# TEST 3 — guardar_paciente (exitoso)
# CAJA BLANCA: el happy path resuelve FK geográficas y persiste el paciente.
# =============================================================================
class TestGuardarPaciente:

    def test_guardar_paciente_exitoso(
        self, controller, db_session, institucion, geografia
    ):
        """
        Con todos los datos válidos y la geografía existente en BD,
        el método debe retornar (True, no_hc) y el paciente debe existir.
        """
        data = _datos_paciente()

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            exito, valor = controller.guardar_paciente(
                data=data,
                ingresos_temporales=[],
                inst_id=institucion.id,
            )

        # Assert retorno
        assert exito is True
        assert valor == data["no_hc"]

        # Assert persistencia: el paciente debe estar en la sesión de prueba
        paciente_guardado = (
            db_session.query(Paciente).filter_by(no_hc=data["no_hc"]).first()
        )
        assert paciente_guardado is not None
        assert paciente_guardado.nombres == "Juan Carlos"
        assert paciente_guardado.ci == data["ci"]

    def test_guardar_paciente_con_ingresos_temporales(
        self, controller, db_session, institucion, geografia
    ):
        """
        CAJA BLANCA — rama de ingresos:
        Si se pasan ingresos_temporales, deben insertarse como IngresoDiab.
        """
        from models import IngresoDiab

        data = _datos_paciente(no_hc="HC-CON-INGRESO", ci="80030712345")
        ingresos = [
            {"motivo": "Descompensación", "especificacion": "", "fecha": "2023-03-01"},
        ]

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            exito, valor = controller.guardar_paciente(
                data=data,
                ingresos_temporales=ingresos,
                inst_id=institucion.id,
            )

        assert exito is True

        ingreso_guardado = (
            db_session.query(IngresoDiab).filter_by(no_hc="HC-CON-INGRESO").first()
        )
        assert ingreso_guardado is not None
        assert ingreso_guardado.motivo == "Descompensación"

    def test_guardar_paciente_resuelve_municipio_y_area(
        self, controller, db_session, institucion, geografia
    ):
        """
        CAJA BLANCA — verificamos que los FK de municipio y área de salud
        se resolvieron correctamente (no quedan en None).
        """
        _, municipio, area = geografia
        data = _datos_paciente(no_hc="HC-GEO", ci="91120512345")

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)

            exito, _ = controller.guardar_paciente(
                data=data,
                ingresos_temporales=[],
                inst_id=institucion.id,
            )

        assert exito is True

        p = db_session.query(Paciente).filter_by(no_hc="HC-GEO").first()
        assert p.municipio_id == municipio.id
        assert p.area_salud_id == area.id


# =============================================================================
# TEST 4 — guardar_paciente (fallos por duplicado)
# CAJA NEGRA: probamos las guardas de validación del controlador.
# =============================================================================
class TestGuardarPacienteDuplicado:

    def test_falla_por_no_hc_duplicado(
        self, controller, db_session, institucion, geografia
    ):
        """
        Si ya existe un paciente con el mismo no_hc, debe retornar
        (False, 'El número de Historia Clínica ya está registrado.').
        """
        # Arrange: guardar el primer paciente
        data_original = _datos_paciente(no_hc="HC-DUP", ci="76060612345")
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            controller.guardar_paciente(data_original, [], institucion.id)

        # Act: intentar guardar otro paciente con el MISMO no_hc pero CI distinto
        data_duplicado = _datos_paciente(no_hc="HC-DUP", ci="99120101234")
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            exito, mensaje = controller.guardar_paciente(data_duplicado, [], institucion.id)

        # Assert
        assert exito is False
        assert mensaje == "El número de Historia Clínica ya está registrado."

    def test_falla_por_ci_duplicado(
        self, controller, db_session, institucion, geografia
    ):
        """
        Si ya existe un paciente con el mismo CI, debe retornar
        (False, 'El número de Carnet de Identidad ya está registrado.').
        """
        # Arrange: guardar el primer paciente
        data_original = _datos_paciente(no_hc="HC-CI-ORIG", ci="85010112345")
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            controller.guardar_paciente(data_original, [], institucion.id)

        # Act: nuevo no_hc pero MISMO ci
        data_duplicado = _datos_paciente(no_hc="HC-CI-DUP", ci="85010112345")
        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            exito, mensaje = controller.guardar_paciente(data_duplicado, [], institucion.id)

        # Assert
        assert exito is False
        assert mensaje == "El número de Carnet de Identidad ya está registrado."

    def test_primer_guardado_exitoso_segundo_falla(
        self, controller, db_session, institucion, geografia
    ):
        """
        CAJA NEGRA — flujo completo de dos intentos:
        El primero debe tener éxito; el segundo (mismo no_hc) debe fallar.
        Verifica que el rollback interno del controlador no afecta la sesión.
        """
        data = _datos_paciente(no_hc="HC-SEQ", ci="88091512345")

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            exito_1, val_1 = controller.guardar_paciente(data, [], institucion.id)

        with patch(PATCH_TARGET) as MockSession:
            _parchear_session(MockSession, db_session)
            exito_2, val_2 = controller.guardar_paciente(data, [], institucion.id)

        assert exito_1 is True
        assert val_1 == "HC-SEQ"
        assert exito_2 is False
        assert "Historia Clínica" in val_2
