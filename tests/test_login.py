from models import Usuario, Rol
import pytest
    ## # tests/test_autenticacion.py
class TestLoginCajaBlanca:
    """Pruebas de caja blanca: verificamos la lógica interna del login."""

    def test_hash_password_no_es_nulo(self, db_session, usuario_admin):
        usuario, _ = usuario_admin
        assert usuario.password_hash is not None
        assert len(usuario.password_hash) > 0

    def test_verificar_password_correcto(self, db_session, usuario_admin):
        usuario, password_plana = usuario_admin
        assert usuario.verificar_password(password_plana) is True

    def test_verificar_password_incorrecto(self, db_session, usuario_admin):
        usuario, _ = usuario_admin
        assert usuario.verificar_password("contraseña_incorrecta") is False

    def test_rol_property_retorna_string(self, db_session, usuario_admin):
        usuario, _ = usuario_admin
        assert isinstance(usuario.rol, str)
        assert usuario.rol == "admin"

class TestLoginCajaNegra:
    """Pruebas de caja negra: solo evaluamos entradas y salidas."""

    def test_login_password_vacio_lanza_excepcion(self):
        with pytest.raises(ValueError):
            Usuario.hash_password("")

    def test_login_password_none_lanza_excepcion(self):
        with pytest.raises(ValueError):
            Usuario.hash_password(None)

    def test_usuario_sin_rol_retorna_sin_rol(self, db_session):
        usuario = Usuario(
            username="sin_rol_test",
            password_hash=Usuario.hash_password("Test789!"),
        )
        db_session.add(usuario)
        db_session.flush()
        assert usuario.rol == "sin_rol"

class TestPermisos:
    def test_admin_tiene_acceso_total(self, db_session, usuario_admin):
        usuario, _ = usuario_admin
        assert usuario.rol == "admin"

    def test_medico_no_es_admin(self, db_session, usuario_medico):
        usuario, _ = usuario_medico
        assert usuario.rol != "admin"
        assert usuario.rol == "médico de guardia"
