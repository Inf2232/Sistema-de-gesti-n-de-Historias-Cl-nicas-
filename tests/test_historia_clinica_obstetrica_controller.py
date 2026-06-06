# tests/test_historia_clinica_obstetrica_controller.py
# Suite de pruebas — HistoriaClinicaObstetricaController
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Institucion, Paciente, HistoriaObstetrica
from controllers.historia_clinica_obstetrica_controller import (
    HistoriaClinicaObstetricaController,
)


# ══════════════════════════════════════════════════════════════════════════════
#  FIXTURES
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
    session.rollback()
    session.close()


@pytest.fixture(scope='module')
def paciente(db_session):
    """
    Paciente base para todos los tests.
    Se crea primero la Institución para satisfacer el NOT NULL constraint.
    """
    inst = Institucion(nombre='Hospital Obstétrico Test')
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    p = Paciente(
        no_hc='OBS-001',
        ci='85010112345',
        nombres='María',
        apellidos='González',
        sexo='Femenino',
        activo=True,
        institucion_id=inst.id,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def ctrl(db_session):
    return HistoriaClinicaObstetricaController(db_session)


@pytest.fixture(autouse=True)
def limpiar_historias(db_session, paciente):
    """Elimina todos los registros obstétricos del paciente antes de cada test."""
    yield
    try:
        db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


def _datos_base(**overrides) -> dict:
    """
    Devuelve un dict completo con todos los campos requeridos por guardar/actualizar.
    Se puede sobreescribir cualquier campo pasándolo como kwarg.
    """
    base = {
        'fecha_registro':               '2024-03-15',
        'edad_menarca':                 12,
        'edad_primera_relacion_sexual': 18,
        'gestaciones':                  3,
        'partos':                       2,
        'abortos_espontaneos':          1,
        'abortos_provocados':           0,
        'anticoncepcion_actual':        'DIU',
        'tiempo_act_anos':              2,
        'tiempo_act_meses':             6,
        'anticoncepcion_previa':        'Píldora',
        'tiempo_prev_anos':             1,
        'tiempo_prev_meses':            0,
        'diabetes_gestacional':         'No',
        'diabetes_insulina':            'No',
        'historial_diabetes':           [],
        'edad_materna_al_diagnostico':  None,
        'fecha_db_input':               None,
        'ehe':                          'No',
        'historial_ehe':                [],
        'macrofetos':                   'No',
        'historial_macrofetos':         [],
        'malformaciones':               'No',
        'malformaciones_cuales':        None,
        'muertes_perinatales':          'No',
        'edad_menopausia':              None,
        'tipo_menopausia':              None,
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
#  TestGuardarRegistro
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardarRegistro:

    def test_guardar_exitoso_con_historiales_json(self, ctrl, db_session, paciente):
        """
        Caja Blanca — campos JSON y numéricos persisten correctamente.
        Verifica: listas JSON, enteros de gestaciones/partos,
        fecha_registro y fecha_diabetes_gestacionaria opcional.
        """
        datos = _datos_base(
            diabetes_gestacional='Si',
            fecha_db_input='2022-06-10',
            historial_diabetes=[{'anio': 2019, 'semanas': 32}],
            macrofetos='Si',
            historial_macrofetos=[{'anio': 2020, 'peso': 4200, 'complicaciones': 'Ninguna'}],
            ehe='Si',
            historial_ehe=[{'anio': 2021, 'tipo': 'Preeclampsia'}],
            gestaciones=4,
            partos=3,
        )

        ok, msg = ctrl.guardar_registro(paciente.id, datos)

        assert ok is True
        assert 'correctamente' in msg.lower()

        registro = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 3, 15),
        ).first()

        assert registro is not None
        assert registro.gestaciones == 4
        assert registro.partos == 3
        assert registro.diabetes_gestacional == 'Si'
        assert registro.fecha_diabetes_gestacionaria == date(2022, 6, 10)
        assert registro.diabetes_gestacional_historial == [{'anio': 2019, 'semanas': 32}]
        assert registro.macrofetos == 'Si'
        assert registro.macrofetos_historial == [
            {'anio': 2020, 'peso': 4200, 'complicaciones': 'Ninguna'}
        ]
        assert registro.ehe_historial == [{'anio': 2021, 'tipo': 'Preeclampsia'}]

    def test_propiedad_calculada_abortos(self, ctrl, db_session, paciente):
        """
        Caja Blanca — @property abortos = abortos_espontaneos + abortos_provocados.
        Con espontaneos=1 y provocados=2 el resultado debe ser 3.
        """
        datos = _datos_base(abortos_espontaneos=1, abortos_provocados=2)
        ctrl.guardar_registro(paciente.id, datos)

        registro = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).first()

        assert registro is not None
        assert registro.abortos_espontaneos == 1
        assert registro.abortos_provocados == 2
        assert registro.abortos == 3, (
            f"La propiedad abortos debe retornar 1+2=3, obtuvo {registro.abortos}."
        )

    def test_guardar_fecha_invalida_falla(self, ctrl, paciente):
        """
        Caja Negra — fecha_registro con formato incorrecto:
        strptime lanza ValueError; el controlador debe capturarlo,
        hacer rollback y retornar (False, mensaje).
        """
        datos = _datos_base(fecha_registro='15/03/2024')  # formato incorrecto

        ok, msg = ctrl.guardar_registro(paciente.id, datos)

        assert ok is False
        assert isinstance(msg, str) and len(msg) > 0

    def test_guardar_fecha_vacia_falla(self, ctrl, paciente):
        """
        Caja Negra — fecha_registro vacío:
        strptime('', ...) lanza ValueError; debe retornar (False, mensaje).
        """
        datos = _datos_base(fecha_registro='')

        ok, msg = ctrl.guardar_registro(paciente.id, datos)

        assert ok is False

    def test_guardar_sin_fecha_db_input_persiste_none(self, ctrl, db_session, paciente):
        """
        Caja Blanca — fecha_db_input=None:
        La columna fecha_diabetes_gestacionaria debe quedar NULL en BD.
        """
        datos = _datos_base(fecha_db_input=None)
        ctrl.guardar_registro(paciente.id, datos)

        registro = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).first()

        assert registro.fecha_diabetes_gestacionaria is None

    def test_guardar_fecha_db_input_invalida_falla(self, ctrl, paciente):
        """
        Caja Negra — fecha_db_input con formato incorrecto:
        Debe retornar (False, mensaje) sin propagar excepción.
        """
        datos = _datos_base(fecha_db_input='no-es-fecha')

        ok, msg = ctrl.guardar_registro(paciente.id, datos)

        assert ok is False

    def test_guardar_abortos_cero_por_defecto(self, ctrl, db_session, paciente):
        """
        Caja Blanca — gestaciones/partos/abortos con None:
        El operador `or 0` debe convertirlos a 0 en vez de None.
        """
        datos = _datos_base(
            gestaciones=None,
            partos=None,
            abortos_espontaneos=None,
            abortos_provocados=None,
        )
        ctrl.guardar_registro(paciente.id, datos)

        registro = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).first()

        assert registro.gestaciones == 0
        assert registro.partos == 0
        assert registro.abortos_espontaneos == 0
        assert registro.abortos_provocados == 0

    def test_guardar_tiempos_anticoncepcion_none_se_convierten_a_cero(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — tiempo_act_anos y demás tiempos con None:
        int(None or 0) = 0; deben guardarse como 0, no como None.
        """
        datos = _datos_base(
            tiempo_act_anos=None,
            tiempo_act_meses=None,
            tiempo_prev_anos=None,
            tiempo_prev_meses=None,
        )
        ctrl.guardar_registro(paciente.id, datos)

        registro = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).first()

        assert registro.tiempo_anticoncepcion_actual_anos == 0
        assert registro.tiempo_anticoncepcion_actual_meses == 0
        assert registro.tiempo_anticoncepcion_prev_anos == 0
        assert registro.tiempo_anticoncepcion_prev_meses == 0

    def test_guardar_hace_commit(self, ctrl, db_session, paciente):
        """
        Caja Blanca — el registro se persiste (contador aumenta en 1).
        """
        count_a = db_session.query(HistoriaObstetrica).count()
        ctrl.guardar_registro(paciente.id, _datos_base())
        count_d = db_session.query(HistoriaObstetrica).count()

        assert count_d == count_a + 1

    def test_guardar_error_hace_rollback(self, ctrl, db_session, paciente):
        """
        Caja Blanca — si commit falla, rollback es llamado y retorna (False, msg).
        """
        with patch.object(db_session, 'commit', side_effect=Exception('BD caída')):
            with patch.object(db_session, 'rollback') as mock_rb:
                ok, _ = ctrl.guardar_registro(paciente.id, _datos_base())

        assert ok is False
        mock_rb.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
#  TestActualizarRegistro
# ══════════════════════════════════════════════════════════════════════════════

class TestActualizarRegistro:

    @pytest.fixture
    def historia_inicial(self, ctrl, db_session, paciente):
        """Crea un registro y devuelve el objeto ORM para los tests de actualización."""
        ctrl.guardar_registro(paciente.id, _datos_base())
        obj = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).first()
        assert obj is not None, "El fixture no pudo crear la historia obstétrica."
        return obj

    def test_actualizar_modifica_campos_correctamente(
        self, ctrl, db_session, historia_inicial
    ):
        """
        Caja Blanca — se pasa un dict con partos aumentados y nueva anticoncepción:
        Los cambios deben persistirse en BD.
        """
        nuevos_datos = _datos_base(
            partos=4,
            gestaciones=5,
            anticoncepcion_actual='Implante',
            tiempo_act_anos=1,
            tiempo_act_meses=3,
            macrofetos='Si',
            historial_macrofetos=[{'anio': 2023, 'peso': 4500}],
        )

        ok, msg = ctrl.actualizar_registro(historia_inicial, nuevos_datos)

        assert ok is True
        assert 'correctamente' in msg.lower()

        db_session.expire(historia_inicial)
        actualizado = db_session.get(HistoriaObstetrica, historia_inicial.id)

        assert actualizado.partos == 4
        assert actualizado.gestaciones == 5
        assert actualizado.anticoncepcion_actual == 'Implante'
        assert actualizado.tiempo_anticoncepcion_actual_anos == 1
        assert actualizado.tiempo_anticoncepcion_actual_meses == 3
        assert actualizado.macrofetos == 'Si'
        assert actualizado.macrofetos_historial == [{'anio': 2023, 'peso': 4500}]

    def test_actualizar_fecha_registro(self, ctrl, db_session, historia_inicial):
        """
        Caja Negra — la nueva fecha se persiste correctamente.
        """
        datos = _datos_base(fecha_registro='2025-01-20')
        ctrl.actualizar_registro(historia_inicial, datos)

        db_session.expire(historia_inicial)
        actualizado = db_session.get(HistoriaObstetrica, historia_inicial.id)

        assert actualizado.fecha_registro == date(2025, 1, 20)

    def test_actualizar_agrega_fecha_diabetes_gestacionaria(
        self, ctrl, db_session, historia_inicial
    ):
        """
        Caja Blanca — pasar fecha_db_input válida actualiza la columna de fecha.
        """
        datos = _datos_base(
            diabetes_gestacional='Si',
            fecha_db_input='2023-08-05',
        )
        ctrl.actualizar_registro(historia_inicial, datos)

        db_session.expire(historia_inicial)
        actualizado = db_session.get(HistoriaObstetrica, historia_inicial.id)

        assert actualizado.fecha_diabetes_gestacionaria == date(2023, 8, 5)

    def test_actualizar_limpia_fecha_diabetes_cuando_none(
        self, ctrl, db_session, historia_inicial
    ):
        """
        Caja Blanca — fecha_db_input=None → columna queda NULL en BD.
        """
        datos = _datos_base(fecha_db_input=None)
        ctrl.actualizar_registro(historia_inicial, datos)

        db_session.expire(historia_inicial)
        actualizado = db_session.get(HistoriaObstetrica, historia_inicial.id)

        assert actualizado.fecha_diabetes_gestacionaria is None

    def test_actualizar_fecha_invalida_falla(self, ctrl, historia_inicial):
        """
        Caja Negra — fecha_registro con formato incorrecto en actualización:
        El controlador debe retornar (False, msg) sin propagar excepción.
        """
        datos = _datos_base(fecha_registro='01-20-2025')  # formato MM-DD-YYYY

        ok, msg = ctrl.actualizar_registro(historia_inicial, datos)

        assert ok is False
        assert isinstance(msg, str) and len(msg) > 0

    def test_actualizar_propiedad_abortos_recalculada(
        self, ctrl, db_session, historia_inicial
    ):
        """
        Caja Blanca — @property abortos se recalcula con los nuevos valores.
        """
        datos = _datos_base(abortos_espontaneos=3, abortos_provocados=1)
        ctrl.actualizar_registro(historia_inicial, datos)

        db_session.expire(historia_inicial)
        actualizado = db_session.get(HistoriaObstetrica, historia_inicial.id)

        assert actualizado.abortos == 4, (
            f"Esperado 3+1=4, obtuvo {actualizado.abortos}."
        )

    def test_actualizar_error_hace_rollback(self, ctrl, db_session, historia_inicial):
        """
        Caja Blanca — error en commit → rollback es llamado.
        """
        with patch.object(db_session, 'commit', side_effect=Exception('error commit')):
            with patch.object(db_session, 'rollback') as mock_rb:
                ok, _ = ctrl.actualizar_registro(historia_inicial, _datos_base())

        assert ok is False
        mock_rb.assert_called_once()

    def test_actualizar_no_propaga_excepcion(self, ctrl, db_session, historia_inicial):
        """
        Caja Negra — ninguna excepción debe llegar al llamador.
        """
        with patch.object(db_session, 'commit', side_effect=Exception('fallo')):
            with patch.object(db_session, 'rollback'):
                try:
                    ctrl.actualizar_registro(historia_inicial, _datos_base())
                except Exception as e:
                    pytest.fail(
                        f"actualizar_registro() propagó excepción al llamador: {e}"
                    )


# ══════════════════════════════════════════════════════════════════════════════
#  TestEliminarRegistro
# ══════════════════════════════════════════════════════════════════════════════

class TestEliminarRegistro:

    def test_eliminar_exitoso(self, ctrl, db_session, paciente):
        """
        Caja Blanca — se pasa el objeto ORM instanciado:
        El registro debe desaparecer de la BD tras la eliminación.
        """
        ctrl.guardar_registro(paciente.id, _datos_base(fecha_registro='2025-02-01'))
        historia = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 2, 1),
        ).first()
        assert historia is not None

        historia_id = historia.id
        ok, msg = ctrl.eliminar_registro(historia)

        assert ok is True
        assert 'eliminada' in msg.lower()

        eliminado = db_session.get(HistoriaObstetrica, historia_id)
        assert eliminado is None, "El registro debe haber sido eliminado de la BD."

    def test_eliminar_reduce_conteo(self, ctrl, db_session, paciente):
        """
        Caja Negra — el total de registros disminuye en 1.
        """
        ctrl.guardar_registro(paciente.id, _datos_base(fecha_registro='2025-03-01'))
        count_a = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).count()

        historia = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 3, 1),
        ).first()
        ctrl.eliminar_registro(historia)

        count_d = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_d == count_a - 1

    def test_eliminar_error_hace_rollback(self, ctrl, db_session, paciente):
        """
        Caja Blanca — si commit falla durante la eliminación, rollback es llamado.
        """
        ctrl.guardar_registro(paciente.id, _datos_base(fecha_registro='2025-04-01'))
        historia = db_session.query(HistoriaObstetrica).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 4, 1),
        ).first()

        with patch.object(db_session, 'commit', side_effect=Exception('error eliminar')):
            with patch.object(db_session, 'rollback') as mock_rb:
                ok, _ = ctrl.eliminar_registro(historia)

        assert ok is False
        mock_rb.assert_called_once()

    def test_eliminar_no_propaga_excepcion(self, ctrl, db_session, paciente):
        """
        Caja Negra — ninguna excepción debe llegar al llamador.
        """
        historia_mock = HistoriaObstetrica(
            paciente_id=paciente.id,
            fecha_registro=date(2025, 5, 1),
            gestaciones=0,
            partos=0,
            abortos_espontaneos=0,
            abortos_provocados=0,
        )
        db_session.add(historia_mock)
        db_session.commit()

        with patch.object(db_session, 'delete', side_effect=Exception('delete fail')):
            with patch.object(db_session, 'rollback'):
                try:
                    ok, _ = ctrl.eliminar_registro(historia_mock)
                except Exception as e:
                    pytest.fail(f"eliminar_registro() propagó excepción: {e}")

        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
#  TestObtenerHistoriasProcesadas
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerHistoriasProcesadas:

    def test_ordena_descendente_y_extrae_ultimo(self, ctrl, db_session, paciente):
        """
        Caja Blanca — tres registros en fechas distintas:
        La lista debe estar en orden descendente y el segundo elemento
        de la tupla debe ser el registro más reciente.
        """
        fechas_y_partos = [
            ('2022-01-10', 1),
            ('2023-06-20', 2),
            ('2024-11-05', 3),
        ]
        for fecha_str, partos in fechas_y_partos:
            ctrl.guardar_registro(
                paciente.id,
                _datos_base(fecha_registro=fecha_str, partos=partos),
            )

        db_session.expire(paciente)
        db_session.refresh(paciente)

        lista, ultima = ctrl.obtener_historias_procesadas(paciente)

        assert len(lista) == 3, f"Se esperaban 3 historias, se obtuvieron {len(lista)}."

        fechas_obtenidas = [h.fecha_registro for h in lista]
        assert fechas_obtenidas == sorted(fechas_obtenidas, reverse=True), (
            f"La lista no está en orden descendente: {fechas_obtenidas}"
        )

        assert ultima is lista[0]
        assert ultima.fecha_registro == date(2024, 11, 5), (
            f"El más reciente debe ser 2024-11-05, obtuvo {ultima.fecha_registro}."
        )
        assert ultima.partos == 3

    def test_lista_vacia_y_ultima_none_sin_registros(self, ctrl, db_session):
        """
        Caja Negra — paciente sin historias obstétricas:
        Debe retornar ([], None) sin excepción.
        """
        inst = db_session.query(Institucion).first()
        paciente_vacio = Paciente(
            no_hc='OBS-VACIO',
            ci='00020212345',
            nombres='Sin',
            apellidos='Historias',
            activo=True,
            institucion_id=inst.id,
        )
        db_session.add(paciente_vacio)
        db_session.commit()
        db_session.refresh(paciente_vacio)

        lista, ultima = ctrl.obtener_historias_procesadas(paciente_vacio)

        assert lista == []
        assert ultima is None

    def test_registros_sin_fecha_son_excluidos(self, ctrl, db_session, paciente):
        """
        Caja Blanca — la implementación filtra `h.fecha_registro is not None`:
        Un registro sin fecha no debe aparecer en la lista ordenada.
        """
        # Insertar directamente un registro sin fecha
        sin_fecha = HistoriaObstetrica(
            paciente_id=paciente.id,
            fecha_registro=None,
            gestaciones=0,
            partos=0,
            abortos_espontaneos=0,
            abortos_provocados=0,
        )
        db_session.add(sin_fecha)
        db_session.commit()

        # Insertar uno con fecha válida
        ctrl.guardar_registro(
            paciente.id,
            _datos_base(fecha_registro='2025-07-01'),
        )

        db_session.expire(paciente)
        db_session.refresh(paciente)

        lista, ultima = ctrl.obtener_historias_procesadas(paciente)

        fechas = [h.fecha_registro for h in lista]
        assert None not in fechas, (
            "Los registros sin fecha deben ser excluidos de la lista ordenada."
        )
        assert ultima is not None
        assert ultima.fecha_registro == date(2025, 7, 1)

    def test_un_solo_registro_es_el_ultimo(self, ctrl, db_session, paciente):
        """
        Caja Negra — con un único registro con fecha:
        lista tiene un elemento y ese elemento es también 'ultima'.
        """
        ctrl.guardar_registro(
            paciente.id,
            _datos_base(fecha_registro='2025-08-01'),
        )
        db_session.expire(paciente)
        db_session.refresh(paciente)

        lista, ultima = ctrl.obtener_historias_procesadas(paciente)

        registros_con_fecha = [h for h in lista if h.fecha_registro is not None]
        assert len(registros_con_fecha) >= 1
        assert ultima is lista[0]

    def test_orden_estable_con_dos_fechas_iguales(self, ctrl, db_session, paciente):
        """
        Caja Blanca — dos registros con la misma fecha:
        No debe lanzar excepción y la lista debe tener ambos.
        """
        for partos in (1, 2):
            ctrl.guardar_registro(
                paciente.id,
                _datos_base(fecha_registro='2025-09-01', partos=partos),
            )
        db_session.expire(paciente)
        db_session.refresh(paciente)

        try:
            lista, ultima = ctrl.obtener_historias_procesadas(paciente)
            registros_misma_fecha = [
                h for h in lista if h.fecha_registro == date(2025, 9, 1)
            ]
            assert len(registros_misma_fecha) == 2
            assert ultima is not None
        except Exception as e:
            pytest.fail(
                f"obtener_historias_procesadas() con fechas iguales lanzó: {e}"
            )
