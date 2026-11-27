@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Khoi dong Giao dien Web Caro 9x9 - Khong can Docker
echo ==========================================================

if exist ".venv\Scripts\python.exe" goto :check_deps

echo [1/2] Dang tao moi truong Python .venv lan dau...
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if %errorlevel% neq 0 goto :no_python

:check_deps
".venv\Scripts\python.exe" -c "import numpy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [2/2] Dang cai goi toi thieu numpy...
    ".venv\Scripts\python.exe" -m pip install --quiet numpy
)

if not exist "checkpoints\cnn_9x9.pt" goto :launch
".venv\Scripts\python.exe" -c "import torch" >nul 2>nul
if %errorlevel% neq 0 (
    echo Phat hien checkpoint CNN Level 5 - dang cai PyTorch ban CPU nhe...
    ".venv\Scripts\python.exe" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
)

:launch
echo Dang mo trinh duyet... Nhan Ctrl+C hoac dong cua so nay de tat.
".venv\Scripts\python.exe" -X utf8 -m ui.web_app %*
if %errorlevel% neq 0 pause
exit /b 0

:no_python
echo Loi: Khong tim thay Python 3.10+ tren may. Vui long cai Python truoc.
pause
exit /b 1
