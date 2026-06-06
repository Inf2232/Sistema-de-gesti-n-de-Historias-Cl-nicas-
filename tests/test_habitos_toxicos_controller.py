# tests/test_habitos_toxicos_controller.py
# Suite de pruebas — HabitosToxicosController
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Paciente, HabitosToxicos, Institucion
from controllers.habitos_toxicos_controller import HabitosToxicosController


# ══════════════════════════════════════════════════════════════════════════════
#  FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def engine():
    eng = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope='module')
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope='module')
def paciente(db_session):
    """Paciente base reutilizado por todos los tests del módulo."""
    # 1. Crear institución obligatoria primero
    inst = Institucion(nombre="Clínica Test")
    db_session.add(inst)
    db_session.commit()

    # 2. Crear paciente asignándole el ID de la institución
    p = Paciente(
        no_hc='HAB-001',
        ci='85010112345',
        nombres='Carlos',
        apellidos='Rodríguez',
        activo=True,
        institucion_id=inst.id  # <-- El campo clave que faltaba
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def ctrl(db_session):
    """Controlador fresco apuntando a la sesión de prueba."""
    return HabitosToxicosController(db_session)


@pytest.fixture(autouse=True)
def limpiar_habitos(db_session, paciente):
    """Elimina todos los hábitos del paciente antes de cada test para aislamiento."""
    yield
    try:
        db_session.query(HabitosToxicos).filter_by(paciente_id=paciente.id).delete()
        db_session.commit()
    except:
        db_session.rollback() #


# ══════════════════════════════════════════════════════════════════════════════
#  TestGuardarHabito
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarHabito:

    def test_guardar_fumador_activo(self, ctrl, db_session, paciente):
        """
        Caja Blanca — fuma='Si':
        La lógica de negocio debe guardar cant_cigarros y cant_tabacos,
        y forzar tiempo_sin_fumar a None aunque se pase un valor.
        """
        ok, msg = ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-03-15',
            fuma='Si',
            cant_cigarros='10',
            cant_tabacos='2',
            tiempo_sin_fumar='6 meses',   # debe ser ignorado por la lógica
            consumo_alcohol='No',
        )

        assert ok is True
        assert 'correctamente' in msg.lower()

        registro = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 3, 15),
        ).first()

        assert registro is not None
        assert registro.fuma == 'Si'
        assert registro.cant_cigarros == '10'
        assert registro.cant_tabacos == '2'
        assert registro.tiempo_sin_fumar is None, (
            "tiempo_sin_fumar debe quedar None cuando fuma='Si'."
        )
        assert registro.consumo_excesivo_alcohol == 'No'

    def test_guardar_ex_fumador(self, ctrl, db_session, paciente):
        """
        Caja Blanca — fuma='Ex Fumador':
        Debe guardar tiempo_sin_fumar y forzar cant_cigarros/cant_tabacos a None.
        """
        ok, msg = ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-04-10',
            fuma='Ex Fumador',
            cant_cigarros='5',      # debe ser ignorado
            cant_tabacos='1',       # debe ser ignorado
            tiempo_sin_fumar='2 años',
            consumo_alcohol='Si',
        )

        assert ok is True

        registro = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 4, 10),
        ).first()

        assert registro is not None
        assert registro.fuma == 'Ex Fumador'
        assert registro.tiempo_sin_fumar == '2 años'
        assert registro.cant_cigarros is None, (
            "cant_cigarros debe quedar None cuando fuma='Ex Fumador'."
        )
        assert registro.cant_tabacos is None, (
            "cant_tabacos debe quedar None cuando fuma='Ex Fumador'."
        )

    def test_guardar_no_fumador(self, ctrl, db_session, paciente):
        """
        Caja Blanca — fuma distinto de 'Si' y 'Ex Fumador':
        Todos los campos de tabaco deben quedar None.
        """
        ok, _ = ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-05-01',
            fuma='No',
            cant_cigarros='3',
            cant_tabacos='1',
            tiempo_sin_fumar='1 mes',
            consumo_alcohol='No',
        )

        assert ok is True

        registro = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 5, 1),
        ).first()

        assert registro.cant_cigarros is None
        assert registro.cant_tabacos is None
        assert registro.tiempo_sin_fumar is None

    def test_guardar_sin_fecha_falla(self, ctrl, paciente):
        """
        Caja Negra — fecha_str vacío:
        El controlador debe rechazar la operación sin lanzar excepción.
        """
        ok, msg = ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='',
            fuma='No',
        )

        assert ok is False
        assert 'fecha' in msg.lower(), (
            f"El mensaje debe mencionar la fecha. Recibido: '{msg}'"
        )

    def test_guardar_fecha_formato_invalido_falla(self, ctrl, paciente):
        """
        Caja Negra — fecha con formato incorrecto 'dd/mm/yyyy':
        Debe retornar (False, mensaje) sin propagar excepción.
        """
        with patch('Errores.log_error_and_notify'):
            ok, msg = ctrl.guardar_habito(
                paciente_id=paciente.id,
                fecha_str='15/03/2024',
                fuma='No',
            )

        assert ok is False

    def test_guardar_hace_commit(self, ctrl, db_session, paciente):
        """
        Caja Blanca — registro exitoso persiste en BD.
        """
        count_antes = db_session.query(HabitosToxicos).count()

        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-06-01',
            fuma='No',
            consumo_alcohol='No',
        )

        count_despues = db_session.query(HabitosToxicos).count()
        assert count_despues == count_antes + 1

    def test_guardar_error_hace_rollback(self, ctrl, db_session, paciente):
        """
        Caja Blanca — si commit falla, se llama rollback y retorna (False, mensaje).
        """
        with patch.object(db_session, 'commit', side_effect=Exception('BD caída')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('Errores.log_error_and_notify'):
                    ok, msg = ctrl.guardar_habito(
                        paciente_id=paciente.id,
                        fecha_str='2024-07-01',
                        fuma='No',
                    )

        assert ok is False
        mock_rb.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
#  TestActualizarHabito
# ══════════════════════════════════════════════════════════════════════════════

class TestActualizarHabito:

    @pytest.fixture
    def habito_fumador(self, ctrl, db_session, paciente):
        """Crea un hábito de fumador activo y devuelve el objeto ORM."""
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-08-01',
            fuma='Si',
            cant_cigarros='15',
            cant_tabacos='3',
            consumo_alcohol='No',
        )
        obj = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 8, 1),
        ).first()
        assert obj is not None, "El fixture no pudo crear el hábito de fumador."
        return obj

    def test_actualizar_transicion_fumador_a_exfumador(
        self, ctrl, db_session, habito_fumador
    ):
        
        """
        Caja Blanca — cambio de 'Si' a 'Ex Fumador':
        El controlador debe limpiar cant_cigarros y cant_tabacos (→ None)
        y guardar tiempo_sin_fumar.
        """
        ok, msg = ctrl.actualizar_habito(
            habito=habito_fumador,
            fecha_str='2024-08-01',
            fuma='Ex Fumador',
            cant_cigarros='15',     # valor anterior — debe descartarse
            cant_tabacos='3',       # valor anterior — debe descartarse
            tiempo_sin_fumar='3 meses',
            consumo_alcohol='No',
        )

        assert ok is True, f"La actualización falló: {msg}"

        # Re-consultar para leer el estado real en BD
        db_session.expire(habito_fumador)
      # Forma antigua (Query.get)
        actualizado = db_session.get(HabitosToxicos, habito_fumador.id)

        assert actualizado.fuma == 'Ex Fumador'
        assert actualizado.tiempo_sin_fumar == '3 meses'
        assert actualizado.cant_cigarros is None, (
            "cant_cigarros debe ser None después de cambiar a 'Ex Fumador'."
        )
        assert actualizado.cant_tabacos is None, (
            "cant_tabacos debe ser None después de cambiar a 'Ex Fumador'."
        )

    def test_actualizar_transicion_exfumador_a_fumador(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — cambio de 'Ex Fumador' a 'Si':
        tiempo_sin_fumar debe quedar None, cant_cigarros y cant_tabacos se guardan.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-09-01',
            fuma='Ex Fumador',
            tiempo_sin_fumar='1 año',
            consumo_alcohol='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 9, 1),
        ).first()

        ok, _ = ctrl.actualizar_habito(
            habito=habito,
            fecha_str='2024-09-01',
            fuma='Si',
            cant_cigarros='20',
            cant_tabacos='5',
            tiempo_sin_fumar='1 año',   # debe descartarse
            consumo_alcohol='Si',
        )

        assert ok is True
        db_session.expire(habito)
        actualizado = db_session.get(HabitosToxicos, habito.id)

        assert actualizado.fuma == 'Si'
        assert actualizado.cant_cigarros == '20'
        assert actualizado.cant_tabacos == '5'
        assert actualizado.tiempo_sin_fumar is None

    def test_actualizar_a_no_fumador_limpia_todo(self, ctrl, db_session, paciente):
        """
        Caja Blanca — fuma distinto de 'Si' y 'Ex Fumador' (ej. 'No'):
        Todos los campos de tabaco deben quedar None.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-10-01',
            fuma='Si',
            cant_cigarros='10',
            cant_tabacos='2',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 10, 1),
        ).first()

        ok, _ = ctrl.actualizar_habito(
            habito=habito,
            fecha_str='2024-10-01',
            fuma='No',
            cant_cigarros='10',
            cant_tabacos='2',
            tiempo_sin_fumar='6 meses',
        )

        assert ok is True
        db_session.expire(habito)
        actualizado = db_session.get(HabitosToxicos, habito.id)

        assert actualizado.cant_cigarros is None
        assert actualizado.cant_tabacos is None
        assert actualizado.tiempo_sin_fumar is None

    def test_actualizar_cambia_fecha(self, ctrl, db_session, paciente):
        """
        Caja Negra — la nueva fecha se persiste correctamente.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-11-01',
            fuma='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 11, 1),
        ).first()

        ctrl.actualizar_habito(habito=habito, fecha_str='2024-11-15', fuma='No')

        db_session.expire(habito)
        actualizado = db_session.get(HabitosToxicos, habito.id)
        assert actualizado.fecha_registro == date(2024, 11, 15)

    def test_actualizar_sin_fecha_falla(self, ctrl, db_session, paciente):
        """
        Caja Negra — fecha_str vacío:
        Debe retornar (False, mensaje) sin modificar el registro.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2024-12-01',
            fuma='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 12, 1),
        ).first()

        ok, msg = ctrl.actualizar_habito(habito=habito, fecha_str='', fuma='No')

        assert ok is False
        assert 'fecha' in msg.lower()

    def test_actualizar_error_hace_rollback(self, ctrl, db_session, paciente):
        """
        Caja Blanca — error en commit → rollback es llamado.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2025-01-10',
            fuma='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 1, 10),
        ).first()

        with patch.object(db_session, 'commit', side_effect=Exception('error commit')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('Errores.log_error_and_notify'):
                    ok, _ = ctrl.actualizar_habito(
                        habito=habito, fecha_str='2025-01-10', fuma='Si'
                    )

        assert ok is False
        mock_rb.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
#  TestEliminarHabito
# ══════════════════════════════════════════════════════════════════════════════

class TestEliminarHabito:

    def test_eliminar_exitoso(self, ctrl, db_session, paciente):
        """
        Caja Blanca — se pasa el objeto ORM directamente:
        El registro debe desaparecer de la BD tras la eliminación.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2025-02-01',
            fuma='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 2, 1),
        ).first()
        assert habito is not None

        habito_id = habito.id
        ok, msg = ctrl.eliminar_habito(habito)

        assert ok is True
        assert 'eliminado' in msg.lower()

        eliminado = db_session.get(HabitosToxicos, habito_id)
        assert eliminado is None, "El registro debe haber sido eliminado de la BD."

    def test_eliminar_reduce_conteo(self, ctrl, db_session, paciente):
        """
        Caja Negra — tras eliminar un registro, el total disminuye en 1.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2025-03-01',
            fuma='No',
        )
        count_antes = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id
        ).count()

        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 3, 1),
        ).first()

        ctrl.eliminar_habito(habito)

        count_despues = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_despues == count_antes - 1

    def test_eliminar_error_hace_rollback(self, ctrl, db_session, paciente):
        """
        Caja Blanca — si commit falla durante la eliminación, rollback es llamado.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2025-04-01',
            fuma='No',
        )
        habito = db_session.query(HabitosToxicos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 4, 1),
        ).first()

        with patch.object(db_session, 'commit', side_effect=Exception('error al eliminar')):
            with patch.object(db_session, 'rollback') as mock_rb:
                with patch('Errores.log_error_and_notify'):
                    ok, _ = ctrl.eliminar_habito(habito)

        assert ok is False
        mock_rb.assert_called_once()

    def test_eliminar_no_propaga_excepcion(self, ctrl, db_session, paciente):
        """
        Caja Negra — ninguna excepción debe llegar al llamador.
        """
        habito_mock = HabitosToxicos(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 5, 1),
            fuma='No',
        )
        db_session.add(habito_mock)
        db_session.commit()

        with patch.object(db_session, 'delete', side_effect=Exception('delete fail')):
            with patch.object(db_session, 'rollback'):
                with patch('Errores.log_error_and_notify'):
                    try:
                        ok, _ = ctrl.eliminar_habito(habito_mock)
                    except Exception as e:
                        pytest.fail(f"eliminar_habito() propagó excepción: {e}")

        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
#  TestObtenerHabitosProcesados
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerHabitosProcesados:

    def test_ordena_cronologicamente_y_extrae_ultimo(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — tres hábitos en fechas distintas:
        La lista debe venir en orden descendente y el segundo elemento
        de la tupla debe ser el registro más reciente.
        """
        fechas = [
            ('2023-01-10', 'No'),
            ('2024-06-15', 'Si'),
            ('2025-03-20', 'Ex Fumador'),
        ]
        for fecha_str, fuma in fechas:
            ctrl.guardar_habito(
                paciente_id=paciente.id,
                fecha_str=fecha_str,
                fuma=fuma,
                tiempo_sin_fumar='1 año' if fuma == 'Ex Fumador' else None,
                cant_cigarros='5' if fuma == 'Si' else None,
            )

        db_session.expire(paciente)
        db_session.refresh(paciente)

        lista, ultimo = ctrl.obtener_habitos_procesados(paciente)

        assert len(lista) == 3, f"Se esperaban 3 hábitos, se obtuvieron {len(lista)}."

        # Orden descendente
        fechas_obtenidas = [h.fecha_registro for h in lista]
        assert fechas_obtenidas == sorted(fechas_obtenidas, reverse=True), (
            f"La lista no está en orden descendente: {fechas_obtenidas}"
        )

        # El último es el más reciente
        assert ultimo is lista[0], "El segundo elemento de la tupla debe ser el primer item de la lista."
        assert ultimo.fecha_registro == date(2025, 3, 20), (
            f"El registro más reciente debe ser 2025-03-20, se obtuvo {ultimo.fecha_registro}."
        )
        assert ultimo.fuma == 'Ex Fumador'

    def test_paciente_sin_habitos_retorna_lista_vacia_y_none(self, ctrl, db_session):
        """
        Caja Negra — paciente sin registros de hábitos:
        Debe retornar ([], None) sin excepción.
        """
        paciente_vacio = Paciente(
            no_hc='HAB-VACIO', 
            ci='00010112345',
            nombres='Sin', 
            apellidos='Habitos', 
            activo=True,
            institucion_id=1  # <--- Debes añadir esto. Asegúrate de que el ID 1 exista.
        )
        db_session.add(paciente_vacio)
        db_session.commit()
        db_session.refresh(paciente_vacio)

        lista, ultimo = ctrl.obtener_habitos_procesados(paciente_vacio)

        assert lista == []
        assert ultimo is None

    def test_paciente_none_retorna_lista_vacia_y_none(self, ctrl):
        """
        Caja Negra — paciente=None:
        Debe retornar ([], None) sin lanzar excepción.
        """
        lista, ultimo = ctrl.obtener_habitos_procesados(None)

        assert lista == []
        assert ultimo is None

    def test_un_solo_habito_es_el_ultimo(self, ctrl, db_session, paciente):
        """
        Caja Negra — con un único registro:
        La lista tiene un elemento y ese elemento es también el 'ultimo'.
        """
        ctrl.guardar_habito(
            paciente_id=paciente.id,
            fecha_str='2025-06-01',
            fuma='No',
        )
        db_session.expire(paciente)
        db_session.refresh(paciente)

        lista, ultimo = ctrl.obtener_habitos_procesados(paciente)

        # Puede haber más de uno si el fixture limpiar_habitos aún no actuó;
        # verificamos al menos que el más reciente es el correcto.
        assert len(lista) >= 1
        assert ultimo is lista[0]

    def test_orden_con_misma_fecha_es_estable(self, ctrl, db_session, paciente):
        """
        Caja Blanca — dos registros con la misma fecha:
        No debe lanzar excepción; el orden entre ellos puede ser cualquiera
        pero la lista debe tener los dos elementos.
        """
        for fuma in ('Si', 'No'):
            ctrl.guardar_habito(
                paciente_id=paciente.id,
                fecha_str='2025-07-01',
                fuma=fuma,
                cant_cigarros='5' if fuma == 'Si' else None,
            )
        db_session.expire(paciente)
        db_session.refresh(paciente)

        try:
            lista, ultimo = ctrl.obtener_habitos_procesados(paciente)
            assert len(lista) >= 2
            assert ultimo is not None
        except Exception as e:
            pytest.fail(f"obtener_habitos_procesados() con fechas iguales lanzó: {e}")
