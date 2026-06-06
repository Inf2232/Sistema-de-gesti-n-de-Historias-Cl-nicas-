# =============================================================================
# tests/test_historia_clinica_apf_diabetes_controller.py
#
# Pruebas de caja blanca y negra para AntecedentesDiabetesController.
#
# ESTRATEGIA:
#   Inyección de dependencias directa: pasamos db_session al constructor.
#   Se parcheamos log_error_and_notify para silenciar alertas en rutas de error.
# =============================================================================

import pytest
from datetime import date
from unittest.mock import patch

from controllers.historia_clinica_apf_diabetes_controller import AntecedentesDiabetesController
from models import (
    Paciente,
    Institucion,
    AntecedentePatologicoFamiliarDiabetes,
    GradoParentezco,
)

LOG_PATCH = 'controllers.historia_clinica_apf_diabetes_controller.log_error_and_notify'


# =============================================================================
# FIXTURES LOCALES
# =============================================================================

@pytest.fixture
def paciente_base(db_session):
    """Institución + Paciente mínimo para satisfacer el FK de paciente_id."""
    inst = Institucion(nombre="Clínica Diabetes Familiar Test")
    db_session.add(inst)
    db_session.flush()

    paciente = Paciente(
        no_hc="HC-DIAB-001",
        ci="70011512345",
        institucion_id=inst.id,
        fecha_hc=date(2023, 2, 20),
        activo=True,
    )
    db_session.add(paciente)
    db_session.flush()
    return paciente


@pytest.fixture
def ctrl(db_session):
    """Instancia limpia del controlador con la sesión en memoria."""
    return AntecedentesDiabetesController(session=db_session)


def _guardar(ctrl, paciente_id, fecha_str, grados):
    """Atajo para el Arrange de los tests."""
    return ctrl.guardar_antecedente(paciente_id, fecha_str, grados)


def _primer_antecedente(db_session, paciente_id):
    """Recupera el primer antecedente creado para un paciente."""
    return (
        db_session.query(AntecedentePatologicoFamiliarDiabetes)
        .filter_by(paciente_id=paciente_id)
        .first()
    )


# =============================================================================
# TestGuardarAntecedente
# =============================================================================

class TestGuardarAntecedente:

    def test_guardar_exitoso_multiples_grados(self, ctrl, db_session, paciente_base):
        """
        CAJA BLANCA: con una lista de grados válidos el método debe persistir
        el registro padre con la fecha correcta y un hijo por cada grado recibido.
        """
        grados = ['Madre', 'Padre', 'Abuela materna']

        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-05-10',
            grados_seleccionados=grados,
        )

        assert exito is True
        assert mensaje == 'Antecedente familiar de diabetes agregado correctamente'

        # Verificar registro padre
        antecedente = _primer_antecedente(db_session, paciente_base.id)
        assert antecedente is not None
        assert antecedente.fecha_registro == date(2024, 5, 10)
        assert antecedente.paciente_id == paciente_base.id

        # Verificar registros hijos
        grados_guardados = {g.grado for g in antecedente.grados_parentezco}
        assert len(grados_guardados) == 3
        assert grados_guardados == set(grados)

    def test_guardar_un_solo_grado_crea_exactamente_un_hijo(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — valor mínimo: una lista con un solo grado
        debe generar exactamente un registro en 'grados_parentezco'.
        """
        exito, _ = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-01-01',
            grados_seleccionados=['Madre'],
        )

        assert exito is True

        antecedente = _primer_antecedente(db_session, paciente_base.id)
        assert len(antecedente.grados_parentezco) == 1
        assert antecedente.grados_parentezco[0].grado == 'Madre'

    def test_guardar_fecha_vacia_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — valor límite: fecha vacía debe rechazarse antes de la BD."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='',
            grados_seleccionados=['Madre'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_guardar_fecha_none_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — entrada nula en fecha."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str=None,
            grados_seleccionados=['Padre'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_guardar_fecha_formato_incorrecto_captura_excepcion(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA — formato inválido: '20-05-2024' en lugar de '2024-05-20'.
        strptime lanza ValueError; el except debe capturarlo sin propagar.
        La BD no debe quedar con registros parciales.
        """
        with patch(LOG_PATCH):
            exito, mensaje = ctrl.guardar_antecedente(
                paciente_id=paciente_base.id,
                fecha_str='20-05-2024',
                grados_seleccionados=['Madre'],
            )

        assert exito is False
        assert 'error' in mensaje.lower() or 'Error' in mensaje

        count = (
            db_session.query(AntecedentePatologicoFamiliarDiabetes)
            .filter_by(paciente_id=paciente_base.id)
            .count()
        )
        assert count == 0

    def test_guardar_grados_vacios_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — lista vacía de grados rechazada por validación."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-06-01',
            grados_seleccionados=[],
        )

        assert exito is False
        assert mensaje == 'Debe especificar el parentesco'

    def test_guardar_grados_none_devuelve_error(self, ctrl, paciente_base):
        """CAJA NEGRA — None en grados rechazado por validación."""
        exito, mensaje = ctrl.guardar_antecedente(
            paciente_id=paciente_base.id,
            fecha_str='2024-06-01',
            grados_seleccionados=None,
        )

        assert exito is False
        assert mensaje == 'Debe especificar el parentesco'

    def test_fallo_no_deja_registros_huerfanos(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA — integridad transaccional: un fallo en guardar activa
        el rollback y no deja ningún registro parcial en la BD.
        """
        with patch(LOG_PATCH):
            ctrl.guardar_antecedente(
                paciente_id=paciente_base.id,
                fecha_str='fecha-invalida',
                grados_seleccionados=['Madre'],
            )

        count_padres = db_session.query(
            AntecedentePatologicoFamiliarDiabetes
        ).filter_by(paciente_id=paciente_base.id).count()
        count_hijos = db_session.query(GradoParentezco).count()

        assert count_padres == 0
        assert count_hijos == 0


# =============================================================================
# TestActualizarAntecedente
# =============================================================================

class TestActualizarAntecedente:

    def test_actualizar_reemplaza_grados_correctamente(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — diffing de relaciones:
        El método elimina los grados que ya no están en la nueva lista
        e inserta los que son nuevos, sin tocar los que se mantienen.

        Escenario:
          Antes:  {'Madre', 'Padre'}
          Nuevo:  {'Madre', 'Abuela materna'}
          Resultado esperado: se elimina 'Padre', se inserta 'Abuela materna',
                              'Madre' se conserva.
        """
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Madre', 'Padre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)
        antecedente_id = antecedente.id

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente_id,
            fecha_str='2024-08-15',
            grados_nuevos=['Madre', 'Abuela materna'],
        )

        assert exito is True
        assert mensaje == 'Antecedente familiar actualizado correctamente'

        actualizado = db_session.get(AntecedentePatologicoFamiliarDiabetes, antecedente_id)
        grados_finales = {g.grado for g in actualizado.grados_parentezco}

        assert grados_finales == {'Madre', 'Abuela materna'}
        assert 'Padre' not in grados_finales
        assert actualizado.fecha_registro == date(2024, 8, 15)

    def test_actualizar_agrega_grado_sin_duplicados(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — lógica de diffing (inserción):
        Si el nuevo grado ya existe en la colección, no debe duplicarse.
        """
        _guardar(ctrl, paciente_base.id, '2023-03-01', ['Madre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)

        ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2024-03-01',
            grados_nuevos=['Madre', 'Padre'],   # 'Madre' ya existía
        )

        actualizado = db_session.get(AntecedentePatologicoFamiliarDiabetes, antecedente.id)
        grados_finales = [g.grado for g in actualizado.grados_parentezco]

        # 'Madre' no debe aparecer duplicado
        assert grados_finales.count('Madre') == 1
        assert 'Padre' in grados_finales
        assert len(grados_finales) == 2

    def test_actualizar_limpia_regla_negocio_ninguno(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — regla de negocio crítica:
        Si el médico selecciona 'Ninguno' junto a otros grados reales,
        el sistema debe descartar 'Ninguno' y conservar solo los grados válidos.

        Escenario: grados_nuevos = ['Ninguno', 'Madre']
        Resultado: solo 'Madre' persiste; 'Ninguno' se elimina.
        """
        _guardar(ctrl, paciente_base.id, '2023-06-01', ['Padre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2024-06-01',
            grados_nuevos=['Ninguno', 'Madre'],
        )

        assert exito is True

        actualizado = db_session.get(AntecedentePatologicoFamiliarDiabetes, antecedente.id)
        grados_finales = {g.grado for g in actualizado.grados_parentezco}

        # 'Ninguno' debe haber sido purgado por la regla de negocio
        assert 'Ninguno' not in grados_finales
        assert 'Madre' in grados_finales
        assert len(grados_finales) == 1

    def test_actualizar_ninguno_solo_es_permitido(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — caso límite de la regla de negocio:
        'Ninguno' como ÚNICO grado no debe ser eliminado
        (la condición es len > 1, por lo tanto este caso debe persistir).
        """
        _guardar(ctrl, paciente_base.id, '2023-09-01', ['Madre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)

        ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2024-09-01',
            grados_nuevos=['Ninguno'],    # único grado → debe conservarse
        )

        actualizado = db_session.get(AntecedentePatologicoFamiliarDiabetes, antecedente.id)
        grados_finales = {g.grado for g in actualizado.grados_parentezco}

        assert grados_finales == {'Ninguno'}

    def test_actualizar_id_inexistente_devuelve_error(self, ctrl):
        """CAJA NEGRA: un ID que no existe retorna (False, mensaje) sin excepción."""
        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=9999,
            fecha_str='2024-01-01',
            grados_nuevos=['Madre'],
        )

        assert exito is False
        assert 'ya no existe' in mensaje.lower() or 'no existe' in mensaje.lower()

    def test_actualizar_fecha_vacia_devuelve_error(
        self, ctrl, db_session, paciente_base
    ):
        """CAJA NEGRA — validación: fecha vacía rechazada antes de la consulta."""
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Madre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='',
            grados_nuevos=['Padre'],
        )

        assert exito is False
        assert mensaje == 'Debe seleccionar una fecha'

    def test_actualizar_grados_vacios_devuelve_error(
        self, ctrl, db_session, paciente_base
    ):
        """CAJA NEGRA — lista vacía en actualización."""
        _guardar(ctrl, paciente_base.id, '2023-01-01', ['Madre'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)

        exito, mensaje = ctrl.actualizar_antecedente(
            antecedente_id=antecedente.id,
            fecha_str='2024-01-01',
            grados_nuevos=[],
        )

        assert exito is False
        assert mensaje == 'Debe especificar al menos un grado de parentesco'


# =============================================================================
# TestEliminarAntecedente
# =============================================================================

class TestEliminarAntecedente:

    def test_eliminar_borra_padre_y_hijos(self, ctrl, db_session, paciente_base):
        """
        CAJA BLANCA: eliminar el registro padre debe borrar en cascada
        (cascade='all, delete-orphan') todos sus hijos GradoParentezco.
        Ningún registro huérfano debe quedar en 'grados_parentezco'.
        """
        _guardar(ctrl, paciente_base.id, '2024-03-10', ['Madre', 'Padre', 'Hermano'])
        antecedente = _primer_antecedente(db_session, paciente_base.id)
        antecedente_id = antecedente.id

        exito, mensaje = ctrl.eliminar_antecedente(antecedente_id)

        assert exito is True
        assert mensaje == 'Antecedente familiar de diabetes eliminado correctamente'

        # El padre ya no existe
        assert (
            db_session.get(AntecedentePatologicoFamiliarDiabetes, antecedente_id)
            is None
        )

        # Ningún hijo huérfano en la tabla
        huerfanos = (
            db_session.query(GradoParentezco)
            .filter_by(antecedente_id=antecedente_id)
            .count()
        )
        assert huerfanos == 0

    def test_eliminar_id_inexistente_devuelve_error(self, ctrl):
        """CAJA NEGRA: ID inexistente retorna (False, mensaje) sin propagar excepción."""
        with patch(LOG_PATCH):
            exito, mensaje = ctrl.eliminar_antecedente(antecedente_id=9999)

        assert exito is False
        assert 'eliminado' in mensaje.lower() or 'ya fue' in mensaje.lower()

    def test_eliminar_no_afecta_otros_antecedentes_del_paciente(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — aislamiento: eliminar un antecedente no debe
        modificar los demás registros del mismo paciente.
        """
        _guardar(ctrl, paciente_base.id, '2022-01-01', ['Madre'])
        _guardar(ctrl, paciente_base.id, '2024-06-01', ['Padre'])

        antecedentes = (
            db_session.query(AntecedentePatologicoFamiliarDiabetes)
            .filter_by(paciente_id=paciente_base.id)
            .order_by(AntecedentePatologicoFamiliarDiabetes.fecha_registro)
            .all()
        )
        id_a_borrar = antecedentes[0].id
        id_a_conservar = antecedentes[1].id

        ctrl.eliminar_antecedente(id_a_borrar)

        assert (
            db_session.get(AntecedentePatologicoFamiliarDiabetes, id_a_borrar) is None
        )
        assert (
            db_session.get(AntecedentePatologicoFamiliarDiabetes, id_a_conservar)
            is not None
        )


# =============================================================================
# TestObtenerAntecedentesProcesados
# =============================================================================

class TestObtenerAntecedentesProcesados:

    def test_ordena_cronologicamente_y_extrae_ultimo(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA NEGRA: con tres antecedentes en fechas distintas, la lista
        devuelta debe estar en orden descendente y 'ultimo' debe apuntar
        al registro con la fecha más reciente.
        """
        fechas = ['2020-01-15', '2023-07-30', '2018-11-05']
        for f in fechas:
            _guardar(ctrl, paciente_base.id, f, ['Madre'])

        db_session.refresh(paciente_base)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert len(ordenados) == 3

        # Verificar orden descendente par a par
        for i in range(len(ordenados) - 1):
            assert ordenados[i].fecha_registro >= ordenados[i + 1].fecha_registro

        # 'ultimo' debe apuntar a la fecha más reciente
        assert ultimo is not None
        assert ultimo.fecha_registro == date(2023, 7, 30)

    def test_paciente_sin_antecedentes_devuelve_vacios(self, ctrl, paciente_base):
        """CAJA NEGRA — valor límite: sin antecedentes retorna ([], None)."""
        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert ordenados == []
        assert ultimo is None

    def test_paciente_none_devuelve_vacios(self, ctrl):
        """CAJA NEGRA — entrada nula: paciente=None no propaga excepción."""
        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(None)

        assert ordenados == []
        assert ultimo is None

    def test_un_solo_antecedente_es_tambien_el_ultimo(
        self, ctrl, db_session, paciente_base
    ):
        """CAJA NEGRA — caso borde: único antecedente coincide con 'ultimo'."""
        _guardar(ctrl, paciente_base.id, '2024-04-22', ['Padre'])
        db_session.refresh(paciente_base)

        ordenados, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        assert len(ordenados) == 1
        assert ultimo.fecha_registro == date(2024, 4, 22)

    def test_filtrado_excluye_antecedentes_sin_fecha(
        self, ctrl, db_session, paciente_base
    ):
        """
        CAJA BLANCA — lógica de filtrado de 'ultimo':
        los registros sin fecha_registro no deben ser candidatos a 'ultimo'
        aunque sean los únicos. La lista ordenada sí puede contenerlos
        (sorted no filtra), pero 'ultimo' usa antecedentes_validos.

        Si todos los antecedentes carecen de fecha, 'ultimo' debe ser None.
        """
        # Insertar directamente un antecedente sin fecha (edge case de datos corruptos)
        ant_sin_fecha = AntecedentePatologicoFamiliarDiabetes(
            paciente_id=paciente_base.id,
            fecha_registro=None,
        )
        db_session.add(ant_sin_fecha)
        db_session.flush()
        db_session.refresh(paciente_base)

        _, ultimo = ctrl.obtener_antecedentes_procesados(paciente_base)

        # El antecedente sin fecha no debe ser seleccionado como 'ultimo'
        assert ultimo is None
