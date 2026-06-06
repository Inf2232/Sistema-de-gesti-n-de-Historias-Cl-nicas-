# =============================================================================
# tests/test_historia_clinica_apf_controller.py
#
# Pruebas de caja blanca y negra para AntecedentesFamiliaresController.
#
# ESTRATEGIA:
#   El controlador usa Inyección de Dependencias (recibe session en __init__),
#   por lo que pasamos db_session directamente sin necesidad de @patch.
#   Solo parcheamos log_error_and_notify para silenciar alertas en tests de error.
#
# REQUISITOS:
#   - conftest.py con los fixtures: engine_en_memoria, db_session
#   - Los modelos deben estar registrados en Base.metadata
# =============================================================================

import pytest
from datetime import date
from unittest.mock import patch

from controllers.historia_clinica_apf_controller import AntecedentesFamiliaresController
from models import (
    Paciente,
    Institucion,
    AntecedentePatologicoFamiliarNoDiabetesMellitus,
    PatologiaFamiliarNoDiabetes,
)

LOG_PATCH = 'controllers.historia_clinica_apf_controller.log_error_and_notify'


# =============================================================================
# FIXTURES LOCALES
# =============================================================================

@pytest.fixture
def paciente_base(db_session):
    """
    Cadena mínima Institución → Paciente para satisfacer el FK
    de AntecedentePatologicoFamiliarNoDiabetesMellitus.paciente_id.
    El rollback de db_session limpia todo al terminar cada test.
    """
    inst = Institucion(nombre="Clínica APF Test")
    db_session.add(inst)
    db_session.flush()

    paciente = Paciente(
        no_hc="HC-APF-001",
        ci="78042312345",
        institucion_id=inst.id,
        fecha_hc=date(2023, 4, 10),
        activo=True,
    )
    db_session.add(paciente)
    db_session.flush()
    return paciente


@pytest.fixture
def ctrl(db_session):
    """Instancia limpia del controlador con la sesión en memoria."""
    return AntecedentesFamiliaresController(session=db_session)


def _guardar(ctrl, paciente_id, fecha_str, patologias):
    """Atajo para guardar un antecedente en los tests de Arrange."""
    return ctrl.guardar_antecedente(paciente_id, fecha_str, patologias)


# =============================================================================
# guardar_antecedente — CAJA BLANCA
# =============================================================================

class TestGuardarAntecedente:

    def test_exitoso_asocia_paciente_y_fecha(self, ctrl, db_session, paciente_base):
        """
        CAJA BLANCA: el registro padre debe quedar vinculado al paciente correcto
        y con la fecha exacta que se le pasó.
        """
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-07-15',
            nombres_patologias=['Hipertensión', 'Cardiopatía'],
        )

        assert exito is True
        assert mensaje == 'Antecedente familiar guardado correctamente'

        registro = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        assert registro is not None
        assert registro.fecha_registro == date(2024, 7, 15)
        assert registro.paciente_id == paciente_base.id

    def test_crea_patologias_hijas_con_nombres_correctos(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA: por cada nombre en la lista debe crearse un registro
        hijo en 'patologias_familiares_no_diabetes' con el tipo correcto.
        """
        nombres = ['Hipertensión', 'Asma', 'Cáncer de colon']

        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-08-01',
            nombres_patologias=nombres,
        )

        registro = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )

        tipos_guardados = [p.tipo_patologia for p in registro.patologias]
        assert len(tipos_guardados) == 3
        for nombre in nombres:
            assert nombre in tipos_guardados

    def test_una_sola_patologia_crea_exactamente_un_hijo(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — valor mínimo de la colección:
        una sola patología debe generar exactamente un registro hijo.
        """
        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-01-01',
            nombres_patologias=['Cardiopatía'],
        )

        registro = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        assert len(registro.patologias) == 1
        assert registro.patologias[0].tipo_patologia == 'Cardiopatía'

    def test_multiples_antecedentes_mismo_paciente(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA: un paciente puede tener varios antecedentes históricos.
        Cada guardado debe crear un registro padre independiente.
        """
        _guardar(ctrl, paciente_base.id, '2022-03-10', ['Hipertensión'])
        _guardar(ctrl, paciente_base.id, '2024-06-20', ['Asma'])

        total = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .count()
        )
        assert total == 2


# =============================================================================
# guardar_antecedente — CAJA NEGRA (validaciones de entrada)
# =============================================================================

class TestGuardarAntecedenteValidaciones:

    def test_fecha_vacia_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — valor límite: fecha vacía debe rechazarse antes de tocar la BD."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='',
            nombres_patologias=['Hipertensión'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_fecha_none_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — entrada nula: None en fecha_str."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str=None,
            nombres_patologias=['Asma'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_patologias_vacias_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — lista vacía: debe rechazarse con mensaje de validación."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-05-10',
            nombres_patologias=[],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar o escribir al menos una patología'

    def test_patologias_none_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — None en la lista de patologías."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-05-10',
            nombres_patologias=None,
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar o escribir al menos una patología'

    def test_fecha_formato_incorrecto_captura_excepcion(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA — formato inválido: '15-07-2024' en lugar de '2024-07-15'.
        strptime lanzará ValueError; el except debe capturarlo sin propagar.
        """
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='15-07-2024',        # formato DD-MM-YYYY incorrecto
            nombres_patologias=['Hipertensión'],
        )

        assert exito is False
        assert 'error' in mensaje.lower() or 'Error' in mensaje

        # Ningún registro debe haberse creado en la BD
        count = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .count()
        )
        assert count == 0

    def test_fallo_no_deja_registros_huerfanos(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA — integridad transaccional: un fallo en guardar no debe
        dejar ningún registro parcial en la BD (el rollback debe limpiar todo).
        """
        ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='fecha-invalida',
            nombres_patologias=['Hipertensión'],
        )

        count_padres = db_session.query(
            AntecedentePatologicoFamiliarNoDiabetesMellitus
        ).filter_by(paciente_id=paciente_base.id).count()
        count_hijos = db_session.query(PatologiaFamiliarNoDiabetes).count()

        assert count_padres == 0
        assert count_hijos == 0


# =============================================================================
# actualizar_antecedente — CAJA BLANCA
# =============================================================================

class TestActualizarAntecedente:

    def test_reemplaza_patologias_sin_huerfanos(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA: el reemplazo atómico (patologias = [...]) debe eliminar
        las patologías anteriores y crear solo las nuevas. Ningún registro
        antiguo debe quedar en 'patologias_familiares_no_diabetes'.
        """
        # Arrange: antecedente inicial con dos patologías
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Asma', 'Cardiopatía'])
        antecedente = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        antecedente_id = antecedente.id

        # Act: actualizar con una patología diferente
        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente_id,
            fecha_str='2024-09-05',
            nombres_patologias=['Hipertensión'],
        )

        assert exito is True
        assert mensaje == 'Antecedente familiar actualizado con éxito'

        # Assert: solo debe quedar UNA patología y debe ser la nueva
        actualizado = db_session.get(
            AntecedentePatologicoFamiliarNoDiabetesMellitus, antecedente_id
        )
        assert len(actualizado.patologias) == 1
        assert actualizado.patologias[0].tipo_patologia == 'Hipertensión'

        # Assert: ningún registro de las patologías anteriores sobrevive
        total_hijos = (
            db_session.query(PatologiaFamiliarNoDiabetes)
            .filter_by(antecedente_id=antecedente_id)
            .count()
        )
        assert total_hijos == 1   # exactamente la nueva

    def test_actualiza_fecha_correctamente(self, ctrl, db_session, paciente_base):
        """
        CAJA BLANCA: la nueva fecha debe quedar persistida tras el commit.
        """
        _guardar(ctrl, paciente_base.id, '2023-05-01', ['Asma'])
        antecedente = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )

        ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2025-12-31',
            nombres_patologias=['Asma'],
        )

        db_session.refresh(antecedente)
        assert antecedente.fecha_registro == date(2025, 12, 31)

    def test_actualizar_id_inexistente_devuelve_error(self, ctrl):
        """
        CAJA NEGRA: un ID que no existe debe retornar (False, mensaje)
        sin propagar excepciones.
        """
        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=9999,
            fecha_str='2024-01-01',
            nombres_patologias=['Hipertensión'],
        )

        assert exito is False
        assert 'ya no existe' in mensaje.lower() or 'no existe' in mensaje.lower()

    def test_actualizar_sin_fecha_devuelve_error(self, ctrl, db_session, paciente_base):
        """CAJA NEGRA — validación: fecha vacía debe rechazarse antes de la consulta."""
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Asma'])
        antecedente = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='',
            nombres_patologias=['Hipertensión'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_actualizar_sin_patologias_devuelve_error(
        self, ctrl, db_session, paciente_base
    ):
        """CAJA NEGRA — lista vacía en actualización."""
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Asma'])
        antecedente = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2024-01-01',
            nombres_patologias=[],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar al menos una patología'


# =============================================================================
# eliminar_antecedente — CAJA BLANCA
# =============================================================================

class TestEliminarAntecedente:

    def test_exitoso_elimina_padre_y_hijos_en_cascada(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA: eliminar el registro padre debe borrar en cascada
        todos sus hijos (cascade='all, delete-orphan').
        Verificamos que ni el padre ni los hijos queden en la BD.
        """
        _guardar(ctrl, paciente_base.id, '2024-02-14', ['Hipertensión', 'Asma'])
        antecedente = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .first()
        )
        antecedente_id = antecedente.id

        exito, mensaje = ctrl.eliminar_antecedente(antecedente_id)

        assert exito is True
        assert mensaje == 'Antecedente eliminado correctamente'

        # El registro padre ya no existe
        assert (
            db_session.get(AntecedentePatologicoFamiliarNoDiabetesMellitus, antecedente_id)
            is None
        )

        # Ningún hijo huérfano sobrevive gracias al cascade
        huerfanos = (
            db_session.query(PatologiaFamiliarNoDiabetes)
            .filter_by(antecedente_id=antecedente_id)
            .count()
        )
        assert huerfanos == 0

    def test_eliminar_id_inexistente_devuelve_error(self, ctrl):
        """
        CAJA NEGRA: intentar eliminar un ID que no existe retorna (False, mensaje)
        con el texto esperado del controlador.
        """
        with patch(LOG_PATCH):  # silenciar log solo si la excepción llega al except
            exito, mensaje = ctrl.eliminar_antecedente(antecedente_id=9999)

        assert exito is False
        assert 'removido' in mensaje.lower() or 'no existe' in mensaje.lower()

    def test_eliminar_no_afecta_otros_antecedentes(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — aislamiento: eliminar un antecedente no debe tocar
        los otros antecedentes del mismo paciente.
        """
        _guardar(ctrl, paciente_base.id, '2022-01-01', ['Asma'])
        _guardar(ctrl, paciente_base.id, '2023-06-15', ['Cardiopatía'])

        antecedentes = (
            db_session.query(AntecedentePatologicoFamiliarNoDiabetesMellitus)
            .filter_by(paciente_id=paciente_base.id)
            .order_by(AntecedentePatologicoFamiliarNoDiabetesMellitus.fecha_registro)
            .all()
        )
        id_a_borrar = antecedentes[0].id   # el más antiguo
        id_a_conservar = antecedentes[1].id

        ctrl.eliminar_antecedente(id_a_borrar)

        assert (
            db_session.get(AntecedentePatologicoFamiliarNoDiabetesMellitus, id_a_borrar)
            is None
        )
        assert (
            db_session.get(AntecedentePatologicoFamiliarNoDiabetesMellitus, id_a_conservar)
            is not None
        )


# =============================================================================
# obtener_antecedentes_procesados — CAJA NEGRA
# =============================================================================

class TestObtenerAntecedentesProcesados:

    def test_ordena_descendente_y_extrae_ultimo(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA: con tres antecedentes en fechas distintas, la lista
        devuelta debe estar en orden descendente y 'ultimo' debe apuntar
        al registro con la fecha más reciente.
        """
        fechas_insercion = ['2021-03-01', '2024-11-20', '2019-07-15']
        for f in fechas_insercion:
            _guardar(ctrl, paciente_base.id, f, ['Hipertensión'])

        db_session.refresh(paciente_base)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert len(ordenados) == 3

        # Verificar orden descendente par a par
        for i in range(len(ordenados) - 1):
            assert ordenados[i].fecha_registro >= ordenados[i + 1].fecha_registro

        # 'ultimo' debe corresponder a la fecha más reciente
        assert ultimo.fecha_registro == date(2024, 11, 20)

    def test_paciente_sin_antecedentes_devuelve_vacios(
        self, ctrl, paciente_base
    ):
        """
        CAJA NEGRA — valor límite: paciente sin ningún antecedente registrado.
        Debe retornar ([], None) sin lanzar excepción.
        """
        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert ordenados == []
        assert ultimo is None

    def test_paciente_none_devuelve_vacios(self, ctrl):
        """CAJA NEGRA — entrada nula: paciente=None no debe propagar excepción."""
        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(None)

        assert ordenados == []
        assert ultimo is None

    def test_un_solo_antecedente_es_tambien_el_ultimo(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA — caso borde: con un único antecedente,
        ordenados[0] y ultimo deben ser el mismo objeto.
        """
        _guardar(ctrl, paciente_base.id, '2023-08-08', ['Asma'])
        db_session.refresh(paciente_base)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert len(ordenados) == 1
        assert ultimo is not None
        assert ultimo.fecha_registro == date(2023, 8, 8)

    def test_filtrado_excluye_antecedentes_sin_patologias(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — lógica de filtrado interno:
        los antecedentes que existan en BD pero sin patologías NO deben
        aparecer como candidatos a 'ultimo' (aunque sí en la lista ordenada,
        que usa antecedentes_familiares sin filtrar).
        Creamos un antecedente más reciente pero vacío y verificamos que
        'ultimo' apunte al antecedente con patologías.
        """
        # Antecedente válido con patologías
        _guardar(ctrl, paciente_base.id, '2023-05-01', ['Hipertensión'])

        # Antecedente más reciente pero sin patologías (insertado directo en BD)
        ant_vacio = AntecedentePatologicoFamiliarNoDiabetesMellitus(
            paciente_id=paciente_base.id,
            fecha_registro=date(2025, 1, 1),   # fecha más reciente
        )
        db_session.add(ant_vacio)
        db_session.flush()
        db_session.refresh(paciente_base)

        _, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        # 'ultimo' debe ser el que SÍ tiene patologías (2023-05-01),
        # no el vacío más reciente (2025-01-01)
        assert ultimo is not None
        assert ultimo.fecha_registro == date(2023, 5, 1)
