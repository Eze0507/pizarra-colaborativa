@echo off
setlocal

set "BACKEND_ROOT=%~dp0"
set "PYTHON_EXE=%BACKEND_ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: No existe el Python local "%PYTHON_EXE%". 1>&2
    echo Cree backend/.venv con las dependencias declaradas antes de ejecutar el baseline. 1>&2
    exit /b 2
)

set "NODOBOARD_TEST_MODE=1"
set "DJANGO_SETTINGS_MODULE=core.settings_test"
set "GEMINI_API_KEY="

pushd "%BACKEND_ROOT%"
"%PYTHON_EXE%" manage.py test %*
set "TEST_EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %TEST_EXIT_CODE%
