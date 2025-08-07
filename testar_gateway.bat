@echo off
echo ========================================
echo    TESTANDO GATEWAY SIMPLES
echo ========================================
echo.

echo 🟢 Testando versao JavaScript...
echo.
node gateway.js
echo.
echo ========================================
echo.

echo 🟡 Testando versao Python...
echo.

REM Tenta diferentes comandos do Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python encontrado com 'python'
    python gateway.py
    goto :fim
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python encontrado com 'py'
    py gateway.py
    goto :fim
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python encontrado com 'python3'
    python3 gateway.py
    goto :fim
)

echo ❌ Python nao encontrado!
echo.
echo Para instalar Python:
echo 1. Acesse: https://www.python.org/downloads/
echo 2. Baixe e instale
echo 3. IMPORTANTE: Marque "Add Python to PATH"
echo 4. Reinicie o terminal
echo.

:fim
echo.
echo ========================================
echo    TESTE CONCLUIDO!
echo ========================================
pause
