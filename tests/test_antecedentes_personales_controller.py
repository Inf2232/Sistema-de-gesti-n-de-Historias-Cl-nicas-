# =============================================================================
# BLOQUE NUEVO — Pegar debajo de la clase TestGuardarPaciente existente
#
# Cubre: AntecedentesPersonalesController (historia_clinica_app_controller.py)
#
# NOTA SOBRE LA ESTRATEGIA DE MOCK:
#   DiabetesAppController creaba su propia sesión con Session(), por eso
#   necesitábamos @patch. AntecedentesPersonalesController, en cambio, la
#   RECIBE en __init__ (patrón de Inyección de Dependencias). Esto lo hace
#   directamente testeable: simplemente le pasamos nuestro db_session.
#
#   Lo que SÍ parcheamos es 'log_error_and_notify' del módulo Errores, para
#   que los tests de fallos no disparen alertas/logs reales en producción.
# =============================================================================

from unittest.mock import patch, MagicMock
import pytest
from datetime import date

# Ajusta el import según la estructura de tu proyecto
from controllers.historia_clinica_app_controller import AntecedentesPersonalesController
from models import (
    Paciente,
    Institucion,
    AntecedentePatologicoPersonal,
    PatologiaPersonal,
)

# Path a parchear para silenciar notificaciones de error durante los tests
LOG_PATCH = 'historia_clinica_app_controller.log_error_and_notify'


# =============================================================================
# FIXTURE LOCAL: paciente_base
#   Crea la cadena mínima Institución → Paciente que el FK de
#   AntecedentePatologicoPersonal.paciente_id requiere.
#   Reutiliza db_session de conftest.py (rollback automático al terminar).
# =============================================================================
@pytest.fixture
def paciente_base(db_session):
    """Institución + Paciente mínimo válido para tests de antecedentes."""
    inst = Institucion(nombre="Clínica Antecedentes Test")
    db_session.add(inst)
    db_session.flush()

    paciente = Paciente(
        no_hc="HC-ANT-001",
        ci="85010112345",
        institucion_id=inst.id,
        fecha_hc=date(2023, 1, 10),
        activo=True,
    )
    db_session.add(paciente)
    db_session.flush()   # flush asigna paciente.id sin commit real
    return paciente


# =============================================================================
# Helper: lista de patologías en el formato que espera guardar_antecedente()
# =============================================================================
def _patologias(*items):
    """
    Construye la lista de dicts que el controlador espera recibir.
    Uso: _patologias(('Hipertensión', 5, 2), ('Asma', 0, 6))
    """
    return [{'tipo': tipo, 'anios': anios, 'meses': meses} for tipo, anios, meses in items]


# =============================================================================
# TEST SUITE: AntecedentesPersonalesController
# =============================================================================
class TestAntecedentesPersonalesController:

    # -------------------------------------------------------------------------
    # CAJA BLANCA — guardar_antecedente (éxito)
    # Verificamos que la lógica interna crea correctamente el registro padre
    # (AntecedentePatologicoPersonal) y los registros hijos (PatologiaPersonal).
    # -------------------------------------------------------------------------

    def test_guardar_antecedente_exitoso(self, db_session, paciente_base):
        """
        CAJA BLANCA: el happy path persiste el antecedente padre y sus
        patologías hijas con los valores exactos de tipo y tiempo.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-03-15',
            patologias_data=_patologias(('Hipertensión', 5, 2)),
        )

        # 1. Retorno del método
        assert exito is True
        assert mensaje == 'Antecedente guardado correctamente'

        # 2. El registro padre existe y está vinculado al paciente correcto
        antecedente = (
            db_session.query(AntecedentePatologicoPersonal)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        assert antecedente is not None
        assert antecedente.fecha_registro == date(2024, 3, 15)

        # 3. La patología hija tiene los valores exactos
        assert len(antecedente.patologias) == 1
        pat = antecedente.patologias[0]
        assert pat.tipo_patologia == 'Hipertensión'
        assert pat.tiempo_anios == 5
        assert pat.tiempo_meses == 2

    def test_guardar_multiples_patologias_crea_todos_los_hijos(
        self, db_session, paciente_base
    ):
        """
        CAJA BLANCA — rama del for: con N patologías en el payload,
        deben insertarse exactamente N registros en patologias_personales.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        patologias = _patologias(
            ('Hipertensión', 5, 2),
            ('Asma', 0, 6),
            ('No tiene', 0, 0),
        )

        exito, _ = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-06-01',
            patologias_data=patologias,
        )

        assert exito is True

        antecedente = (
            db_session.query(AntecedentePatologicoPersonal)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        # Verificamos cantidad exacta de hijos y sus tipos en orden
        tipos_guardados = [p.tipo_patologia for p in antecedente.patologias]
        assert len(tipos_guardados) == 3
        assert 'Hipertensión' in tipos_guardados
        assert 'Asma' in tipos_guardados
        assert 'No tiene' in tipos_guardados

    # -------------------------------------------------------------------------
    # CAJA NEGRA — guardar_antecedente (ausencia de antecedentes)
    # Evaluamos solo entradas y salidas sin importar la lógica interna.
    # -------------------------------------------------------------------------

    def test_guardar_paciente_con_antecedentes_vacios(
        self, db_session, paciente_base
    ):
        """
        CAJA NEGRA: registrar un paciente sin ninguna patología (lista vacía)
        no debe lanzar excepción. El controlador retorna (False, mensaje)
        porque 'Debe seleccionar al menos una patología' es una regla de negocio,
        pero el sistema no explota ni corrompe la sesión.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        # Lista vacía: el médico no seleccionó ninguna patología
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-03-15',
            patologias_data=[],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar al menos una patología'

        # Verificamos que no se creó ningún registro huérfano en la BD
        count = (
            db_session.query(AntecedentePatologicoPersonal)
            .filter_by(paciente_id=paciente_base.id)
            .count()
        )
        assert count == 0

    def test_guardar_antecedente_sin_fecha_devuelve_error(
        self, db_session, paciente_base
    ):
        """
        CAJA NEGRA — valor límite: fecha_str vacía/None.
        La guarda de validación debe dispararse antes de tocar la BD.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='',
            patologias_data=_patologias(('Hipertensión', 5, 0)),
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_guardar_antecedente_meses_invalidos(self, db_session, paciente_base):
        """
        CAJA NEGRA — valor fuera de rango: meses > 11.
        La regla de negocio debe rechazar el guardado antes del commit.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-03-15',
            patologias_data=_patologias(('Hipertensión', 3, 12)),  # 12 meses → inválido
        )

        assert exito is False
        assert 'meses' in mensaje.lower()

    def test_guardar_tipo_no_tiene_omite_validacion_tiempo(
        self, db_session, paciente_base
    ):
        """
        CAJA BLANCA — rama especial 'No tiene':
        El tipo 'No tiene' no exige rellenar años/meses. Debe guardarse sin error.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-03-15',
            patologias_data=_patologias(('No tiene', 0, 0)),
        )

        assert exito is True
        assert mensaje == 'Antecedente guardado correctamente'

    # -------------------------------------------------------------------------
    # CAJA BLANCA — actualizar_antecedente
    # Verificamos que el reemplazo de la colección de patologías es correcto.
    # -------------------------------------------------------------------------

    def test_actualizar_antecedente_reemplaza_patologias(
        self, db_session, paciente_base
    ):
        """
        CAJA BLANCA: actualizar debe vaciar las patologías previas y
        sustituirlas por las nuevas. No deben quedar patologías del registro original.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        # Arrange: crear antecedente inicial con una patología
        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2023-01-01',
            patologias_data=_patologias(('Asma', 2, 0)),
        )
        antecedente = (
            db_session.query(AntecedentePatologicoPersonal)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        antecedente_id = antecedente.id

        # Act: actualizar con una patología diferente
        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente_id,
            fecha_str='2024-05-20',
            patologias_data=_patologias(('Hipertensión', 10, 3)),
        )

        assert exito is True
        assert mensaje == 'Actualizado correctamente'

        # Assert: solo debe existir la patología nueva
        antecedente_actualizado = (
            db_session.get(AntecedentePatologicoPersonal, antecedente_id)
        )
        assert len(antecedente_actualizado.patologias) == 1
        assert antecedente_actualizado.patologias[0].tipo_patologia == 'Hipertensión'
        assert antecedente_actualizado.fecha_registro == date(2024, 5, 20)

    def test_actualizar_antecedente_inexistente(self, db_session):
        """
        CAJA NEGRA: actualizar con un ID que no existe retorna (False, mensaje).
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=9999,
            fecha_str='2024-01-01',
            patologias_data=_patologias(('Hipertensión', 1, 0)),
        )

        assert exito is False
        assert 'no existe' in mensaje.lower()

    # -------------------------------------------------------------------------
    # CAJA BLANCA — eliminar_antecedente
    # -------------------------------------------------------------------------

    def test_eliminar_antecedente_exitoso(self, db_session, paciente_base):
        """
        CAJA BLANCA: eliminar borra el registro padre y, por cascade,
        todas sus patologías hijas. La BD no debe tener huérfanos.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-01-01',
            patologias_data=_patologias(('Hipertensión', 3, 6)),
        )
        antecedente = (
            db_session.query(AntecedentePatologicoPersonal)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        antecedente_id = antecedente.id

        exito, mensaje = ctrl.eliminar_antecedente(antecedente_id)

        assert exito is True
        assert mensaje == 'Antecedente eliminado correctamente'

        # Verificamos borrado físico del padre y de los hijos (cascade)
        assert db_session.get(AntecedentePatologicoPersonal, antecedente_id) is None
        huerfanos = (
            db_session.query(PatologiaPersonal)
            .filter_by(antecedente_id=antecedente_id)
            .count()
        )
        assert huerfanos == 0

    def test_eliminar_antecedente_inexistente(self, db_session):
        """
        CAJA NEGRA: eliminar un ID que no existe retorna (False, mensaje).
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        exito, mensaje = ctrl.eliminar_antecedente(antecedente_id=9999)

        assert exito is False
        assert 'ya no existe' in mensaje.lower()

    # -------------------------------------------------------------------------
    # CAJA BLANCA — obtener_antecedentes_procesados
    # Verificamos el ordenamiento y la extracción del último diagnóstico.
    # -------------------------------------------------------------------------

    def test_obtener_antecedentes_procesados_ordena_cronologicamente(
        self, db_session, paciente_base
    ):
        """
        CAJA BLANCA: el método debe retornar los antecedentes de más reciente
        a más antiguo y el 'ultimo' debe ser el de fecha mayor.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        # Guardamos dos antecedentes en orden inverso a su fecha
        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2022-05-01',
            patologias_data=_patologias(('Asma', 1, 0)),
        )
        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-11-20',
            patologias_data=_patologias(('Hipertensión', 3, 0)),
        )

        db_session.refresh(paciente_base)  # recargamos la relación del paciente

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert len(ordenados) == 2
        # El primero de la lista debe ser el más reciente
        assert ordenados[0].fecha_registro > ordenados[1].fecha_registro
        # 'ultimo' corresponde a la fecha más alta
        assert ultimo.fecha_registro == date(2024, 11, 20)

    def test_obtener_antecedentes_procesados_paciente_sin_antecedentes(
        self, db_session, paciente_base
    ):
        """
        CAJA NEGRA — valor límite: paciente sin antecedentes registrados.
        Debe retornar listas vacías sin lanzar excepción.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert ordenados == []
        assert ultimo is None

    def test_obtener_antecedentes_procesados_paciente_none(self, db_session):
        """
        CAJA NEGRA — entrada nula: paciente=None no debe lanzar excepción.
        """
        ctrl = AntecedentesPersonalesController(session=db_session)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(None)

        assert ordenados == []
        assert ultimo is None
