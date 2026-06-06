# =============================================================================
# conftest.py  —  Fixtures globales de pytest para el sistema de historias clínicas
#
# ¿Qué es conftest.py?
#   Es un archivo especial que pytest detecta AUTOMÁTICAMENTE en tu proyecto.
#   No necesitas importarlo en ningún test. Cualquier fixture definido aquí
#   está disponible en todos los archivos de prueba de la misma carpeta y subcarpetas.
# =============================================================================

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# IMPORTANTE: Importa tu Base y tus modelos desde tu aplicación real.
# Ajusta las rutas según la estructura de tu proyecto MVC.
# Ejemplo de estructura esperada:
#   mi_proyecto/
#   ├── models/
#   │   ├── __init__.py   <-- exporta Base, Usuario, Rol, Permiso
#   │   └── usuario.py
#   ├── tests/
#   │   ├── conftest.py   <-- este archivo
#   │   └── test_login.py
# ---------------------------------------------------------------------------
from models import Base, Usuario, Rol, Permiso  # <-- Ajusta esta línea a tu proyecto


# =============================================================================
# FIXTURE 1: engine_en_memoria
# Scope: "session" → se crea UNA SOLA VEZ para toda la sesión de pruebas.
#
# ¿Qué hace?
#   - Crea un motor SQLAlchemy apuntando a una base de datos SQLite EN MEMORIA.
#   - Esa BD vive solo mientras corren los tests; se destruye al terminar.
#   - Base.metadata.create_all(engine) recorre TODOS tus modelos y crea
#     sus tablas en esa BD temporal (la misma operación que haces al iniciar
#     tu app, pero apuntando a :memory: en lugar de tu archivo .sqlite).
# =============================================================================
@pytest.fixture(scope="session")
def engine_en_memoria():
    """
    Motor SQLAlchemy con BD SQLite en memoria.
    Scope 'session': se crea una sola vez y es compartido por todos los tests.
    """
    # La URL especial "sqlite:///:memory:" le dice a SQLite que use RAM pura.
    # check_same_thread=False es necesario porque pytest puede usar hilos internamente.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,  # Cambia a True si quieres ver las sentencias SQL en consola
    )

    # Crea todas las tablas definidas en tus modelos (rol_permiso, config_roles,
    # config_permisos, usuarios, config_institucion, etc.)
    Base.metadata.create_all(engine)

    yield engine  # 'yield' pausa el fixture y entrega el motor al test

    # --- Teardown (limpieza tras TODOS los tests) ---
    # Elimina todas las tablas al final de la sesión. Opcional con :memory:
    # porque la BD desaparece igualmente, pero es buena práctica documentarlo.
    Base.metadata.drop_all(engine)


# =============================================================================
# FIXTURE 2: db_session
# Scope: "function" → se crea una sesión NUEVA para cada función de test.
#
# ¿Qué hace?
#   - Abre una TRANSACCIÓN anidada (SAVEPOINT) antes de cada test.
#   - Entrega la sesión al test para que inserte/consulte datos.
#   - Al terminar (pase o falle), hace ROLLBACK: deshace TODO lo que el test
#     hizo, dejando la BD limpia para el siguiente test.
#
# Esto garantiza AISLAMIENTO: los tests no se contaminan entre sí.
# =============================================================================
@pytest.fixture(scope="function")
def db_session(engine_en_memoria):
    """
    Sesión de BD limpia para cada test individual.
    Usa un SAVEPOINT para hacer rollback automático al terminar cada test.
    """
    # Abrimos una conexión y comenzamos una transacción externa
    connection = engine_en_memoria.connect()
    transaction = connection.begin()

    # Creamos la sesión vinculada a esa conexión (no al engine directamente)
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    # Comenzamos un SAVEPOINT anidado dentro de la transacción externa.
    # Esto permite que el código de la app pueda hacer commit() internamente
    # sin afectar la BD real (el commit quedará atrapado en el savepoint).
    nested = connection.begin_nested()

    # Cada vez que la sesión haga commit(), reiniciamos el savepoint
    # para mantener el aislamiento del test.
    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def reiniciar_savepoint(session, transaction_interno):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session  # El test recibe la sesión aquí y la usa

    # --- Teardown automático tras cada test ---
    session.close()
    transaction.rollback()  # DESHACE TODO lo que el test escribió
    connection.close()


# =============================================================================
# FIXTURE 3: usuario_admin
# Scope: "function" → se crea un usuario Admin NUEVO para cada test que lo pida.
#
# ¿Qué hace?
#   - Crea un Rol "Admin" y un Usuario "admin_test" con contraseña conocida.
#   - Lo persiste en la sesión temporal (que se limpiará con rollback al final).
#   - El test puede usar este usuario para probar login, permisos, etc.
#
# USO EN TUS TESTS:
#   def test_login_exitoso(db_session, usuario_admin):
#       resultado = mi_controlador.login("admin_test", "Password123!")
#       assert resultado is True
#
# NOTA: Este fixture es OPCIONAL. Solo se activa si lo declaras como
# parámetro en la firma del test.
# =============================================================================
@pytest.fixture(scope="function")
def usuario_admin(db_session):
    """
    Crea un usuario Admin de prueba en la BD temporal.
    Depende de db_session, por lo que se limpia automáticamente con rollback.

    Retorna una tupla (usuario, contraseña_plana) para que el test
    tenga acceso a la contraseña sin hashear (útil para probar el login).
    """
    PASSWORD_PLANA = "Password123!"  # Contraseña conocida para los tests

    # 1. Crear el Rol "Admin" ---------------------------------------------------
    rol_admin = Rol(nombre="Admin")
    db_session.add(rol_admin)
    db_session.flush()  # flush() envía a la BD SIN commit, asigna el ID al objeto

    # 2. Crear el Usuario con contraseña hasheada -------------------------------
    #    Usamos el método estático de tu propio modelo para hashear.
    usuario = Usuario(
        username="admin_test",
        password_hash=Usuario.hash_password(PASSWORD_PLANA),
        rol_id=rol_admin.id,
    )
    db_session.add(usuario)
    db_session.flush()  # Necesario para que usuario.id esté disponible

    # 3. Retornar el usuario y la contraseña plana para los tests ---------------
    #    El rollback en db_session limpiará este usuario al terminar el test.
    return usuario, PASSWORD_PLANA


# =============================================================================
# FIXTURE EXTRA: usuario_medico
# Ejemplo de un segundo rol para probar el sistema de PERMISOS.
# Solo se activa si lo declaras en la firma de tu test.
# =============================================================================
@pytest.fixture(scope="function")
def usuario_medico(db_session):
    """
    Crea un usuario con rol 'Médico de Guardia' para probar permisos restringidos.
    """
    PASSWORD_PLANA = "Medico456!"

    rol_medico = Rol(nombre="Médico de Guardia")
    db_session.add(rol_medico)
    db_session.flush()

    usuario = Usuario(
        username="medico_test",
        password_hash=Usuario.hash_password(PASSWORD_PLANA),
        rol_id=rol_medico.id,
    )
    db_session.add(usuario)
    db_session.flush()

    return usuario, PASSWORD_PLANA

