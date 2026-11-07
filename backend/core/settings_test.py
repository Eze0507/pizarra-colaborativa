"""Settings aislados para las pruebas automatizadas de NodoBoard.

Este modulo solo puede cargarse mediante ``backend/run_tests.cmd`` o un
comando que habilite explicitamente NODOBOARD_TEST_MODE=1. No reutiliza la
base PostgreSQL, Redis, SMTP ni las credenciales de IA del entorno normal.
"""

import os


if os.environ.get("NODOBOARD_TEST_MODE") != "1":
    raise RuntimeError(
        "core.settings_test requiere NODOBOARD_TEST_MODE=1; "
        "use backend/run_tests.cmd para ejecutar las pruebas."
    )

# settings.py exige estas variables durante la importacion. Se fijan antes de
# importar y luego DATABASES se sustituye por completo por SQLite en memoria.
os.environ["DB_NAME"] = "nodoboard_test_guard"
os.environ["DB_USER"] = "nodoboard_test_guard"
os.environ["DB_PASSWORD"] = "nodoboard_test_guard"

# Una clave real heredada del proceso no debe habilitar llamadas externas.
os.environ["GEMINI_API_KEY"] = ""

from .settings import *  # noqa: F403,E402


SECRET_KEY = "nodoboard-test-only-secret-key"  # noqa: F405
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "nodoboard-tests",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "tests@nodoboard.invalid"

GEMINI_API_KEY = ""
GEMINI_MODEL = "fake-test-model"
NODOBOARD_EXTERNAL_AI_ENABLED = False

# Reduce el costo del baseline sin cambiar el comportamiento de autenticacion.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

