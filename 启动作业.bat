@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo ReGrow AI - 作业 3
echo ========================================
echo.

set "PYTHON_COMMAND="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_COMMAND=py -3"

if not defined PYTHON_COMMAND (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_COMMAND=python"
)

if not defined PYTHON_COMMAND (
    echo [错误] 没有找到 Python。
    echo 请先安装 Python 3.11 或更高版本，并在安装时勾选 Add Python to PATH。
    echo 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

set "VENV_PYTHON=%~dp0backend\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [1/3] 正在创建 Python 运行环境……
    %PYTHON_COMMAND% -m venv "%~dp0backend\.venv"
    if errorlevel 1 goto :failed
)

"%VENV_PYTHON%" -c "import fastapi, uvicorn, pydantic, agno, openai, httpx" >nul 2>nul
if errorlevel 1 (
    echo [2/3] 首次启动，正在安装项目依赖……
    "%VENV_PYTHON%" -m pip install -r "%~dp0backend\requirements.txt"
    if errorlevel 1 goto :failed
) else (
    echo [2/3] 项目依赖已就绪。
)

echo [3/3] 正在启动项目……
echo.
echo 浏览器地址：http://127.0.0.1:8000
echo 这个窗口需要保持打开。按 Ctrl+C 可以停止项目。
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"
cd /d "%~dp0backend"
"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:failed
echo.
echo [启动失败] 请检查网络和 Python 版本，再重新双击“启动作业.bat”。
echo.
pause
exit /b 1
