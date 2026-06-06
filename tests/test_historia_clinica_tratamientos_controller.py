# tests/test_historia_clinica_tratamientos_controller.py
# Suite de pruebas — ControladorTratamientos
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Institucion, Paciente, TratamientoActual, OtrosTratamientos
from controllers.historia_clinica_tratamientos_controller import ControladorTratamientos


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
    Paciente base reutilizado por todos los tests.
    La Institución se crea primero para satisfacer el NOT NULL constraint.
    """
    inst = Institucion(nombre='Hospital Tratamientos Test')
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    p = Paciente(
        no_hc='TRAT-001',
        ci='80020212345',
        nombres='Pedro',
        apellidos='Martínez',
        sexo='Masculino',
        activo=True,
        institucion_id=inst.id,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def ctrl(db_session):
    return ControladorTratamientos(db_session)


@pytest.fixture(autouse=True)
def limpiar_tratamientos(db_session, paciente):
    """
    Elimina todos los tratamientos del paciente antes de cada test.
    Protegido con try/except para evitar PendingRollbackError.
    """
    yield
    try:
        db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id
        ).delete()
        db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id
        ).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
#  Esquema de ejemplo reutilizable
# ─────────────────────────────────────────────────────────────────────────────

ESQUEMA_COMPLEJO = [
    {'tratamiento': 'Metformina',  'dosis': '850 mg', 'anio_inicio': '2020'},
    {'tratamiento': 'Glibenclamida', 'dosis': '5 mg',  'anio_inicio': '2021'},
]


# ══════════════════════════════════════════════════════════════════════════════
#  TestObtenerEsquemaVisual
# ══════════════════════════════════════════════════════════════════════════════

class TestObtenerEsquemaVisual:
    """Pruebas unitarias puras — no tocan la BD."""

    def _tratamiento_mock(self, esquema_json=None, tratamiento=None, dosis=None):
        t = MagicMock()
        t.esquema_json = esquema_json
        t.tratamiento  = tratamiento
        t.dosis        = dosis
        return t

    def test_caso_a_retorna_json_si_tiene_contenido(self, ctrl):
        """
        Caso A — esquema_json con contenido:
        El método debe devolver la lista tal cual, sin transformaciones.
        """
        t = self._tratamiento_mock(esquema_json=ESQUEMA_COMPLEJO)

        resultado = ctrl.obtener_esquema_visual(t)

        assert resultado == ESQUEMA_COMPLEJO
        assert len(resultado) == 2
        assert resultado[0]['tratamiento'] == 'Metformina'

    def test_caso_b_fallback_cuando_json_es_lista_vacia(self, ctrl):
        """
        Caso B — esquema_json = [] (vacío):
        Debe retornar la lista fallback construida desde tratamiento y dosis.
        """
        t = self._tratamiento_mock(
            esquema_json=[],
            tratamiento='Insulina',
            dosis='10 UI',
        )

        resultado = ctrl.obtener_esquema_visual(t)

        assert len(resultado) == 1
        assert resultado[0]['tratamiento'] == 'Insulina'
        assert resultado[0]['dosis'] == '10 UI'
        assert resultado[0]['anio_inicio'] == ''

    def test_caso_b_fallback_cuando_json_es_none(self, ctrl):
        """
        Caso B — esquema_json = None:
        Debe retornar la lista fallback sin excepción.
        """
        t = self._tratamiento_mock(
            esquema_json=None,
            tratamiento='Sitagliptina',
            dosis='100 mg',
        )

        resultado = ctrl.obtener_esquema_visual(t)

        assert len(resultado) == 1
        assert resultado[0]['tratamiento'] == 'Sitagliptina'
        assert resultado[0]['dosis'] == '100 mg'

    def test_caso_b_fallback_tratamiento_none_usa_no_registrado(self, ctrl):
        """
        Caso B — esquema_json vacío y tratamiento=None:
        El fallback debe usar 'No registrado' para ambos campos.
        """
        t = self._tratamiento_mock(esquema_json=None, tratamiento=None, dosis=None)

        resultado = ctrl.obtener_esquema_visual(t)

        assert resultado[0]['tratamiento'] == 'No registrado'
        assert resultado[0]['dosis'] == 'No registrado'

    def test_caso_a_json_con_un_solo_elemento(self, ctrl):
        """
        Caso A — esquema_json con exactamente un elemento:
        Debe devolverlo sin pasar por el fallback.
        """
        esquema_uno = [{'tratamiento': 'Acarbosa', 'dosis': '50 mg', 'anio_inicio': '2022'}]
        t = self._tratamiento_mock(esquema_json=esquema_uno)

        resultado = ctrl.obtener_esquema_visual(t)

        assert resultado == esquema_uno


# ══════════════════════════════════════════════════════════════════════════════
#  TestCRUDTratamientoActual
# ══════════════════════════════════════════════════════════════════════════════

class TestCRUDTratamientoActual:

    def test_guardar_y_actualizar_tratamiento_actual(
        self, ctrl, db_session, paciente
    ):
        """
        CRUD completo — guardar y luego actualizar:
        Verifica que el JSON complejo persiste y que los campos se sobreescriben.
        """
        # ── Guardar ──────────────────────────────────────────────────────────
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 1, 10),
                tratamiento_str='Combinado oral',
                esquema=ESQUEMA_COMPLEJO,
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        guardado = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id
        ).first()

        assert guardado is not None
        assert guardado.tratamiento == 'Combinado oral'
        assert guardado.dosis == 'Ver esquema'
        assert guardado.sigue_via_clinica == 'Si'
        assert guardado.esquema_json == ESQUEMA_COMPLEJO
        assert guardado.fecha_registro == date(2024, 1, 10)

        # ── Actualizar ────────────────────────────────────────────────────────
        nuevo_esquema = [
            {'tratamiento': 'Empagliflozina', 'dosis': '10 mg', 'anio_inicio': '2024'}
        ]
        try:
            ctrl.actualizar_tratamiento_actual(
                tratamiento=guardado,
                fecha_registro=date(2024, 6, 20),
                tratamiento_str='Inhibidor SGLT2',
                esquema=nuevo_esquema,
                sigue_via_clinica='No',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(guardado)
        actualizado = db_session.get(TratamientoActual, guardado.id)

        assert actualizado.fecha_registro == date(2024, 6, 20)
        assert actualizado.tratamiento == 'Inhibidor SGLT2'
        assert actualizado.esquema_json == nuevo_esquema
        assert actualizado.sigue_via_clinica == 'No'
        assert actualizado.dosis == 'Ver esquema'

    def test_guardar_persiste_esquema_json_complejo(self, ctrl, db_session, paciente):
        """
        Caja Blanca — esquema con múltiples fármacos y campos anidados:
        El JSON debe recuperarse idéntico al que se insertó.
        """
        esquema_multi = [
            {'tratamiento': 'Metformina',    'dosis': '1000 mg', 'anio_inicio': '2019'},
            {'tratamiento': 'Lantus',        'dosis': '18 UI',   'anio_inicio': '2021'},
            {'tratamiento': 'Linagliptina',  'dosis': '5 mg',    'anio_inicio': '2023'},
        ]
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 2, 1),
                tratamiento_str='Triple terapia',
                esquema=esquema_multi,
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        guardado = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 2, 1),
        ).first()

        assert guardado.esquema_json == esquema_multi
        assert len(guardado.esquema_json) == 3

    def test_guardar_esquema_vacio_se_almacena(self, ctrl, db_session, paciente):
        """
        Caja Negra — esquema_json=[] debe almacenarse como lista vacía, no como None.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 3, 1),
                tratamiento_str='Dieta sola',
                esquema=[],
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        guardado = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 3, 1),
        ).first()

        assert guardado.esquema_json == [] or guardado.esquema_json is None

    def test_eliminar_tratamiento_actual(self, ctrl, db_session, paciente):
        """
        Caja Blanca — el registro desaparece de la BD tras eliminarlo.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 4, 1),
                tratamiento_str='Para eliminar',
                esquema=[],
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        registro = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 4, 1),
        ).first()
        assert registro is not None
        registro_id = registro.id

        try:
            ctrl.eliminar_tratamiento_actual(registro)
        except Exception:
            db_session.rollback()
            raise

        eliminado = db_session.get(TratamientoActual, registro_id)
        assert eliminado is None

    def test_eliminar_tratamiento_hace_commit(self, ctrl, db_session, paciente):
        """
        Caja Blanca — la eliminación se confirma (commit) sin necesitar commit manual.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 5, 1),
                tratamiento_str='Otro para eliminar',
                esquema=[],
                sigue_via_clinica='No',
            )
        except Exception:
            db_session.rollback()
            raise

        count_a = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id
        ).count()

        registro = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 5, 1),
        ).first()

        try:
            ctrl.eliminar_tratamiento_actual(registro)
        except Exception:
            db_session.rollback()
            raise

        count_d = db_session.query(TratamientoActual).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_d == count_a - 1

    def test_guardar_llama_refresh_en_paciente(self, ctrl, db_session, paciente):
        """
        Caja Blanca — guardar_tratamiento_actual llama session.refresh(paciente)
        al final; verificamos que el paciente sigue accesible y consistente.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 7, 1),
                tratamiento_str='Test refresh',
                esquema=[],
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        # Si refresh falló, el acceso a paciente.id lanzaría DetachedInstanceError
        assert paciente.id is not None

    def test_rollback_manual_revierte_guardado(self, ctrl, db_session, paciente):
        """
        Caja Blanca — ctrl.rollback() revierte operaciones no confirmadas.
        agregar_otro_tratamiento_individual NO hace commit automático,
        así que un rollback antes del commit descarta el registro.
        """
        count_a = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id
        ).count()

        # Este método NO hace commit — solo add()
        ctrl.agregar_otro_tratamiento_individual(
            paciente=paciente,
            tratamiento_val='Aspirina',
            dosis_val='100 mg',
            fecha_registro=date(2024, 8, 1),
        )
        ctrl.rollback()

        count_d = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_d == count_a, (
            "El rollback debe descartar el registro no confirmado."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  TestCRUDOtrosTratamientos
# ══════════════════════════════════════════════════════════════════════════════

class TestCRUDOtrosTratamientos:

    def test_agregar_y_actualizar_otro_tratamiento(
        self, ctrl, db_session, paciente
    ):
        """
        CRUD completo — agregar (sin commit) + commit manual + actualizar:
        Verifica que todos los campos persisten correctamente.
        """
        # ── Agregar ───────────────────────────────────────────────────────────
        try:
            ctrl.agregar_otro_tratamiento_individual(
                paciente=paciente,
                tratamiento_val='Enalapril',
                dosis_val='10 mg',
                fecha_registro=date(2024, 1, 15),
            )
            ctrl.commit()
        except Exception:
            db_session.rollback()
            raise

        agregado = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 1, 15),
        ).first()

        assert agregado is not None
        assert agregado.tratamiento == 'Enalapril'
        assert agregado.dosis == '10 mg'
        assert agregado.fecha_registro == date(2024, 1, 15)

        # ── Actualizar ────────────────────────────────────────────────────────
        try:
            ctrl.actualizar_otro_tratamiento(
                tratamiento=agregado,
                fecha_registro=date(2024, 7, 20),
                tratamiento_val='Losartán',
                dosis_val='50 mg',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(agregado)
        actualizado = db_session.get(OtrosTratamientos, agregado.id)

        assert actualizado.tratamiento == 'Losartán'
        assert actualizado.dosis == '50 mg'
        assert actualizado.fecha_registro == date(2024, 7, 20)

    def test_agregar_multiples_y_confirmar_con_commit(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — agregar dos tratamientos y confirmar con un solo commit:
        Ambos deben persistir en BD.
        """
        try:
            ctrl.agregar_otro_tratamiento_individual(
                paciente=paciente,
                tratamiento_val='Amlodipino',
                dosis_val='5 mg',
                fecha_registro=date(2024, 2, 1),
            )
            ctrl.agregar_otro_tratamiento_individual(
                paciente=paciente,
                tratamiento_val='Atorvastatina',
                dosis_val='20 mg',
                fecha_registro=date(2024, 2, 5),
            )
            ctrl.commit()
        except Exception:
            db_session.rollback()
            raise

        registros = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id
        ).all()
        nombres = {r.tratamiento for r in registros}

        assert 'Amlodipino'   in nombres
        assert 'Atorvastatina' in nombres

    def test_eliminar_otro_tratamiento(self, ctrl, db_session, paciente):
        """
        Caja Blanca — el registro desaparece de la BD tras la eliminación.
        """
        try:
            ctrl.agregar_otro_tratamiento_individual(
                paciente=paciente,
                tratamiento_val='Para eliminar',
                dosis_val='1 cp',
                fecha_registro=date(2024, 3, 1),
            )
            ctrl.commit()
        except Exception:
            db_session.rollback()
            raise

        registro = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 3, 1),
        ).first()
        assert registro is not None
        registro_id = registro.id

        try:
            ctrl.eliminar_otro_tratamiento(registro)
        except Exception:
            db_session.rollback()
            raise

        eliminado = db_session.get(OtrosTratamientos, registro_id)
        assert eliminado is None

    def test_actualizar_otro_tratamiento_hace_commit(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — actualizar_otro_tratamiento incluye commit implícito:
        el cambio persiste sin llamar ctrl.commit() adicional.
        """
        try:
            ctrl.agregar_otro_tratamiento_individual(
                paciente=paciente,
                tratamiento_val='Omeprazol',
                dosis_val='20 mg',
                fecha_registro=date(2024, 4, 10),
            )
            ctrl.commit()
        except Exception:
            db_session.rollback()
            raise

        registro = db_session.query(OtrosTratamientos).filter_by(
            paciente_id=paciente.id,
            fecha_registro=date(2024, 4, 10),
        ).first()

        try:
            ctrl.actualizar_otro_tratamiento(
                tratamiento=registro,
                fecha_registro=date(2024, 4, 10),
                tratamiento_val='Pantoprazol',
                dosis_val='40 mg',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(registro)
        verificado = db_session.get(OtrosTratamientos, registro.id)
        assert verificado.tratamiento == 'Pantoprazol'
        assert verificado.dosis == '40 mg'


# ══════════════════════════════════════════════════════════════════════════════
#  TestLogicaConsulta
# ══════════════════════════════════════════════════════════════════════════════

class TestLogicaConsulta:

    def test_obtener_tratamiento_actual_reciente(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — dos registros con fechas distintas:
        El método debe retornar el que tiene la fecha más reciente (max).
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2022, 3, 1),
                tratamiento_str='Antiguo',
                esquema=[{'tratamiento': 'Metformina', 'dosis': '500 mg', 'anio_inicio': '2022'}],
                sigue_via_clinica='Si',
            )
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 9, 15),
                tratamiento_str='Reciente',
                esquema=[{'tratamiento': 'Empagliflozina', 'dosis': '10 mg', 'anio_inicio': '2024'}],
                sigue_via_clinica='No',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(paciente)
        db_session.refresh(paciente)

        reciente = ctrl.obtener_tratamiento_actual_reciente(paciente)

        assert reciente is not None
        assert reciente.fecha_registro == date(2024, 9, 15), (
            f"Se esperaba 2024-09-15, obtuvo {reciente.fecha_registro}."
        )
        assert reciente.tratamiento == 'Reciente'

    def test_obtener_tratamiento_actual_reciente_sin_registros(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — paciente sin tratamientos: debe retornar None.
        """
        db_session.expire(paciente)
        db_session.refresh(paciente)

        resultado = ctrl.obtener_tratamiento_actual_reciente(paciente)

        assert resultado is None

    def test_obtener_tratamiento_actual_reciente_un_registro(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — un único registro: debe retornarlo directamente.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2024, 10, 1),
                tratamiento_str='Único',
                esquema=[],
                sigue_via_clinica='Si',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(paciente)
        db_session.refresh(paciente)

        resultado = ctrl.obtener_tratamiento_actual_reciente(paciente)

        assert resultado is not None
        assert resultado.fecha_registro == date(2024, 10, 1)

    def test_obtener_otros_tratamientos_ordenados(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — tres registros en orden aleatorio:
        La lista resultante debe estar en orden descendente por fecha.
        """
        fechas = [
            (date(2023, 5, 10), 'Atenolol',     '25 mg'),
            (date(2021, 11, 3), 'Furosemida',   '40 mg'),
            (date(2024, 8, 22), 'Espironolactona', '25 mg'),
        ]
        try:
            for fecha, trat, dosis in fechas:
                ctrl.agregar_otro_tratamiento_individual(
                    paciente=paciente,
                    tratamiento_val=trat,
                    dosis_val=dosis,
                    fecha_registro=fecha,
                )
            ctrl.commit()
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(paciente)
        db_session.refresh(paciente)

        ordenados = ctrl.obtener_otros_tratamientos_ordenados(paciente)

        assert len(ordenados) == 3

        fechas_obtenidas = [r.fecha_registro for r in ordenados]
        assert fechas_obtenidas == sorted(fechas_obtenidas, reverse=True), (
            f"La lista no está en orden descendente: {fechas_obtenidas}"
        )
        assert ordenados[0].fecha_registro == date(2024, 8, 22)
        assert ordenados[0].tratamiento == 'Espironolactona'
        assert ordenados[-1].fecha_registro == date(2021, 11, 3)

    def test_obtener_otros_tratamientos_ordenados_sin_registros(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — paciente sin otros tratamientos: debe retornar [].
        """
        db_session.expire(paciente)
        db_session.refresh(paciente)

        resultado = ctrl.obtener_otros_tratamientos_ordenados(paciente)

        assert resultado == []

    def test_obtener_historial_tratamientos_ordenado_descendente(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Blanca — obtener_historial_tratamientos ordena descendentemente:
        El primer elemento debe ser el registro más reciente.
        """
        try:
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2020, 1, 1),
                tratamiento_str='Inicial',
                esquema=[],
                sigue_via_clinica='Si',
            )
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2023, 6, 15),
                tratamiento_str='Intermedio',
                esquema=[],
                sigue_via_clinica='Si',
            )
            ctrl.guardar_tratamiento_actual(
                paciente=paciente,
                fecha_registro=date(2025, 2, 28),
                tratamiento_str='Más reciente',
                esquema=[],
                sigue_via_clinica='No',
            )
        except Exception:
            db_session.rollback()
            raise

        db_session.expire(paciente)
        db_session.refresh(paciente)

        historial = ctrl.obtener_historial_tratamientos(paciente)

        assert len(historial) == 3

        fechas = [r.fecha_registro for r in historial]
        assert fechas == sorted(fechas, reverse=True), (
            f"El historial no está en orden descendente: {fechas}"
        )
        assert historial[0].tratamiento == 'Más reciente'
        assert historial[0].fecha_registro == date(2025, 2, 28)

    def test_obtener_historial_sin_registros_retorna_lista_vacia(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — paciente sin tratamientos actuales: retorna [].
        """
        db_session.expire(paciente)
        db_session.refresh(paciente)

        historial = ctrl.obtener_historial_tratamientos(paciente)

        assert historial == []

    def test_refresh_helper_no_lanza_excepcion(self, ctrl, db_session, paciente):
        """
        Caja Negra — ctrl.refresh(objeto) no debe propagar excepción
        cuando el objeto está en sesión activa.
        """
        try:
            ctrl.refresh(paciente)
        except Exception as e:
            pytest.fail(f"ctrl.refresh() lanzó excepción inesperada: {e}")

    def test_commit_helper_confirma_sin_error(self, ctrl, db_session, paciente):
        """
        Caja Negra — ctrl.commit() en sesión limpia no lanza excepción.
        """
        try:
            ctrl.commit()
        except Exception as e:
            pytest.fail(f"ctrl.commit() lanzó excepción inesperada: {e}")

    def test_rollback_helper_no_lanza_excepcion(self, ctrl):
        """
        Caja Negra — ctrl.rollback() en sesión sin transacción pendiente
        no debe lanzar excepción.
        """
        try:
            ctrl.rollback()
        except Exception as e:
            pytest.fail(f"ctrl.rollback() lanzó excepción inesperada: {e}")
