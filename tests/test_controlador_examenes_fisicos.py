# tests/test_controlador_examenes_fisicos.py
# Suite de pruebas — ControladorExamenesFisicos
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Institucion, Paciente, ExamenFisico
from controllers.controlador_examenes_fisicos import ControladorExamenesFisicos


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
    """Institución → Paciente asociado. Reutilizado por todo el módulo."""
    inst = Institucion(nombre='Hospital Examen Físico Test')
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    p = Paciente(
        no_hc='EF-001',
        ci='75030312345',
        nombres='Laura',
        apellidos='Sánchez',
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
    return ControladorExamenesFisicos(db_session)


@pytest.fixture(autouse=True)
def limpiar_examenes(db_session, paciente):
    """Elimina todos los exámenes físicos del paciente antes de cada test."""
    yield
    try:
        db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
#  Dict de datos completo reutilizable
# ─────────────────────────────────────────────────────────────────────────────

DATOS_COMPLETOS = {
    'sistolica_acostado':          110,
    'diastolica_acostado':          70,
    'sistolica_sentado':           125,
    'diastolica_sentado':           80,
    'sistolica_de_pie':            128,
    'diastolica_de_pie':            82,
    'bocio':                       'No',
    'acantosis_nigricans':         'Si',
    'frecuencia_cardiaca_acostado': 62.0,
    'frecuencia_cardiaca_sentado':  68.5,
}


# ══════════════════════════════════════════════════════════════════════════════
#  TestCrearExamenFisico
# ══════════════════════════════════════════════════════════════════════════════

class TestCrearExamenFisico:

    def test_crear_examen_completo(self, ctrl, db_session, paciente):
        """
        Caja Blanca — diccionario con todos los campos:
        Cada columna debe persistirse con el valor exacto enviado.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 3, 10),
            datos=DATOS_COMPLETOS,
        )

        assert examen is not None
        assert examen.id is not None

        guardado = db_session.get(ExamenFisico, examen.id)

        assert guardado.paciente_id              == paciente.id
        assert guardado.fecha_registro           == date(2024, 3, 10)
        assert guardado.sistolica_acostado       == 110
        assert guardado.diastolica_acostado      == 70
        assert guardado.sistolica_sentado        == 125
        assert guardado.diastolica_sentado       == 80
        assert guardado.sistolica_de_pie         == 128
        assert guardado.diastolica_de_pie        == 82
        assert guardado.bocio                    == 'No'
        assert guardado.acantosis_nigricans      == 'Si'
        assert guardado.frecuencia_cardiaca_acostado == pytest.approx(62.0)
        assert guardado.frecuencia_cardiaca_sentado  == pytest.approx(68.5)

    def test_crear_examen_retorna_objeto_orm(self, ctrl, paciente):
        """
        Caja Negra — crear_examen_fisico devuelve el objeto ORM recién creado,
        no None ni un entero.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 4, 1),
            datos=DATOS_COMPLETOS,
        )

        assert isinstance(examen, ExamenFisico)
        assert examen.id is not None

    def test_crear_examen_datos_incompletos_es_seguro(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — dict solo con presión arterial sentada, sin frecuencias ni bocio:
        Los campos omitidos deben guardarse como None sin lanzar excepción.
        """
        datos_parciales = {
            'sistolica_sentado':  130,
            'diastolica_sentado':  85,
        }

        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 5, 1),
            datos=datos_parciales,
        )

        assert examen is not None
        guardado = db_session.get(ExamenFisico, examen.id)

        assert guardado.sistolica_sentado  == 130
        assert guardado.diastolica_sentado == 85
        assert guardado.sistolica_acostado         is None
        assert guardado.diastolica_acostado        is None
        assert guardado.sistolica_de_pie           is None
        assert guardado.diastolica_de_pie          is None
        assert guardado.bocio                      is None
        assert guardado.acantosis_nigricans        is None
        assert guardado.frecuencia_cardiaca_acostado is None
        assert guardado.frecuencia_cardiaca_sentado  is None

    def test_crear_examen_dict_vacio_guarda_todo_none(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — dict vacío: todos los campos clínicos deben quedar None.
        La fecha y paciente_id siguen siendo válidos.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 6, 1),
            datos={},
        )

        assert examen is not None
        guardado = db_session.get(ExamenFisico, examen.id)

        assert guardado.paciente_id    == paciente.id
        assert guardado.fecha_registro == date(2024, 6, 1)
        for campo in (
            'sistolica_acostado', 'diastolica_acostado',
            'sistolica_sentado',  'diastolica_sentado',
            'sistolica_de_pie',   'diastolica_de_pie',
            'bocio', 'acantosis_nigricans',
            'frecuencia_cardiaca_acostado', 'frecuencia_cardiaca_sentado',
        ):
            assert getattr(guardado, campo) is None, (
                f"El campo '{campo}' debe ser None con dict vacío."
            )

    def test_crear_falla_por_error_de_bd(self, ctrl, db_session, paciente):
        """
        Caja Blanca — el controlador NO tiene try/except interno:
        Si commit lanza excepción, esta sube al llamador.
        El test verifica que la excepción se propague y aplica rollback manual.
        """
        with patch.object(db_session, 'commit', side_effect=Exception('BD caída')):
            with pytest.raises(Exception, match='BD caída'):
                ctrl.crear_examen_fisico(
                    paciente_id=paciente.id,
                    fecha=date(2024, 7, 1),
                    datos=DATOS_COMPLETOS,
                )
        # Rollback manual — responsabilidad del llamador
        db_session.rollback()

    def test_crear_incrementa_conteo(self, ctrl, db_session, paciente):
        """
        Caja Negra — tras crear un examen, el total de registros aumenta en 1.
        """
        count_a = db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).count()

        ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 8, 1),
            datos=DATOS_COMPLETOS,
        )

        count_d = db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_d == count_a + 1

    def test_crear_multiples_examenes_mismo_paciente(
        self, ctrl, db_session, paciente
    ):
        """
        Caja Negra — un paciente puede tener varios exámenes en fechas distintas.
        """
        fechas = [date(2024, 9, 1), date(2024, 9, 15), date(2024, 10, 1)]
        for f in fechas:
            ctrl.crear_examen_fisico(
                paciente_id=paciente.id,
                fecha=f,
                datos=DATOS_COMPLETOS,
            )

        total = db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).count()
        assert total == 3


# ══════════════════════════════════════════════════════════════════════════════
#  TestActualizarExamenFisico
# ══════════════════════════════════════════════════════════════════════════════

class TestActualizarExamenFisico:

    @pytest.fixture
    def examen_inicial(self, ctrl, db_session, paciente):
        """Crea un examen completo y devuelve el objeto ORM."""
        return ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 3, 20),
            datos=DATOS_COMPLETOS,
        )

    def test_actualizar_modifica_valores_correctamente(
        self, ctrl, db_session, examen_inicial
    ):
        """
        Caja Blanca — se pasan nuevas presiones arteriales y nueva fecha:
        Todos los campos deben actualizarse en BD.
        """
        nuevos_datos = {
            'sistolica_acostado':          118,
            'diastolica_acostado':          74,
            'sistolica_sentado':           138,
            'diastolica_sentado':           90,
            'sistolica_de_pie':            140,
            'diastolica_de_pie':            92,
            'bocio':                       'Si',
            'acantosis_nigricans':         'No',
            'frecuencia_cardiaca_acostado': 55.0,
            'frecuencia_cardiaca_sentado':  72.0,
        }

        ctrl.actualizar_examen_fisico(
            examen=examen_inicial,
            fecha=date(2024, 6, 15),
            datos=nuevos_datos,
        )

        db_session.expire(examen_inicial)
        actualizado = db_session.get(ExamenFisico, examen_inicial.id)

        assert actualizado.fecha_registro            == date(2024, 6, 15)
        assert actualizado.sistolica_acostado        == 118
        assert actualizado.diastolica_acostado       == 74
        assert actualizado.sistolica_sentado         == 138
        assert actualizado.diastolica_sentado        == 90
        assert actualizado.sistolica_de_pie          == 140
        assert actualizado.diastolica_de_pie         == 92
        assert actualizado.bocio                     == 'Si'
        assert actualizado.acantosis_nigricans       == 'No'
        assert actualizado.frecuencia_cardiaca_acostado == pytest.approx(55.0)
        assert actualizado.frecuencia_cardiaca_sentado  == pytest.approx(72.0)

    def test_actualizar_con_dict_vacio_pone_campos_en_none(
        self, ctrl, db_session, examen_inicial
    ):
        """
        Caja Blanca — datos.get() con dict vacío devuelve None para todo:
        Los campos clínicos quedan en None tras la actualización.
        """
        ctrl.actualizar_examen_fisico(
            examen=examen_inicial,
            fecha=date(2024, 7, 1),
            datos={},
        )

        db_session.expire(examen_inicial)
        actualizado = db_session.get(ExamenFisico, examen_inicial.id)

        assert actualizado.fecha_registro == date(2024, 7, 1)
        for campo in (
            'sistolica_acostado', 'diastolica_acostado',
            'sistolica_sentado',  'diastolica_sentado',
            'bocio', 'acantosis_nigricans',
        ):
            assert getattr(actualizado, campo) is None, (
                f"'{campo}' debe ser None tras actualizar con dict vacío."
            )

    def test_actualizar_solo_fecha(self, ctrl, db_session, examen_inicial):
        """
        Caja Negra — solo se cambia la fecha; los campos clínicos pasan a None
        porque el dict está vacío (comportamiento de datos.get()).
        """
        ctrl.actualizar_examen_fisico(
            examen=examen_inicial,
            fecha=date(2025, 1, 1),
            datos={},
        )

        db_session.expire(examen_inicial)
        actualizado = db_session.get(ExamenFisico, examen_inicial.id)
        assert actualizado.fecha_registro == date(2025, 1, 1)

    def test_actualizar_hace_commit_sin_llamada_extra(
        self, ctrl, db_session, examen_inicial
    ):
        """
        Caja Blanca — actualizar_examen_fisico llama commit internamente:
        el cambio persiste sin necesitar commit adicional.
        """
        ctrl.actualizar_examen_fisico(
            examen=examen_inicial,
            fecha=date(2025, 2, 1),
            datos={'bocio': 'No', 'sistolica_sentado': 119},
        )

        # Nueva sesión de verificación — si no hubo commit, no encontraría el cambio
        db_session.expire(examen_inicial)
        verificado = db_session.get(ExamenFisico, examen_inicial.id)
        assert verificado.bocio == 'No'
        assert verificado.sistolica_sentado == 119

    def test_actualizar_falla_por_error_de_bd(self, ctrl, db_session, examen_inicial):
        """
        Caja Blanca — sin try/except en el controlador, la excepción sube al llamador.
        """
        with patch.object(db_session, 'commit', side_effect=Exception('commit fail')):
            with pytest.raises(Exception, match='commit fail'):
                ctrl.actualizar_examen_fisico(
                    examen=examen_inicial,
                    fecha=date(2025, 3, 1),
                    datos=DATOS_COMPLETOS,
                )
        db_session.rollback()


# ══════════════════════════════════════════════════════════════════════════════
#  TestEliminarExamenFisico
# ══════════════════════════════════════════════════════════════════════════════

class TestEliminarExamenFisico:

    def test_eliminar_borra_registro_de_bd(self, ctrl, db_session, paciente):
        """
        Caja Blanca — se pasa el objeto ORM instanciado:
        El registro debe desaparecer de la BD tras la eliminación.
        """
        # 1. Creamos y confirmamos
        examen = ctrl.crear_examen_fisico(paciente_id=paciente.id, fecha=date(2025, 5, 1), datos={})
        examen_id = examen.id
        
        # 2. Eliminamos
        ctrl.eliminar_examen_fisico(examen)
        
        # 3. Limpiamos la sesión para forzar la sincronización y evitar el SAWarning
        db_session.expire_all() 

        # 4. Verificamos
        assert db_session.get(ExamenFisico, examen_id) is None

    def test_eliminar_reduce_conteo(self, ctrl, db_session, paciente):
        """
        Caja Negra — el total de exámenes disminuye en 1 tras la eliminación.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2024, 12, 1),
            datos=DATOS_COMPLETOS,
        )
        count_a = db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).count()

        ctrl.eliminar_examen_fisico(examen)

        count_d = db_session.query(ExamenFisico).filter_by(
            paciente_id=paciente.id
        ).count()
        assert count_d == count_a - 1

    def test_eliminar_hace_commit_sin_llamada_extra(self, ctrl, db_session, paciente):
        """
        Caja Blanca — eliminar_examen_fisico incluye commit interno:
        la eliminación persiste sin commit adicional del llamador.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2025, 1, 15),
            datos=DATOS_COMPLETOS,
        )
        examen_id = examen.id

        ctrl.eliminar_examen_fisico(examen)

        # Verificar con get() que ya no existe en la sesión activa
        assert db_session.get(ExamenFisico, examen_id) is None

    def test_eliminar_no_afecta_otros_examenes(self, ctrl, db_session, paciente):
        """
        Caja Negra — eliminar un examen no elimina los demás del mismo paciente.
        """
        e1 = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2025, 2, 1),
            datos=DATOS_COMPLETOS,
        )
        e2 = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2025, 2, 15),
            datos=DATOS_COMPLETOS,
        )
        e2_id = e2.id

        ctrl.eliminar_examen_fisico(e1)

        assert db_session.get(ExamenFisico, e2_id) is not None, (
            "Eliminar e1 no debe afectar a e2."
        )

    def test_eliminar_falla_por_error_de_bd(self, ctrl, db_session, paciente):
        """
        Caja Blanca — sin try/except, el error en commit sube al llamador.
        """
        examen = ctrl.crear_examen_fisico(
            paciente_id=paciente.id,
            fecha=date(2025, 3, 1),
            datos=DATOS_COMPLETOS,
        )

        with patch.object(db_session, 'commit', side_effect=Exception('delete fail')):
            with pytest.raises(Exception, match='delete fail'):
                ctrl.eliminar_examen_fisico(examen)
        db_session.rollback()
