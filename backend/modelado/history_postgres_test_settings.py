"""Verifica bloqueos reales usando una base PostgreSQL temporal y única.

Se ejecuta dentro del contenedor con NODOBOARD_TEST_MODE=1. No utiliza ni
modifica las tablas del diagrama real. Django crea y destruye solo la base TEST.
"""
import os
from copy import deepcopy
from uuid import uuid4

if os.environ.get('NODOBOARD_TEST_MODE') != '1':
    raise RuntimeError('Las pruebas PostgreSQL requieren NODOBOARD_TEST_MODE=1.')

from core.settings import DATABASES as PROJECT_DATABASES
from core.settings_test import *  # noqa: F403,E402

DATABASES = deepcopy(PROJECT_DATABASES)
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise RuntimeError('Este módulo requiere PostgreSQL.')
DATABASES['default']['TEST'] = {'NAME': f'test_nodoboard_history_{uuid4().hex}'}
