@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Jump to project root (parent of scripts folder)
cd /d "%~dp0.."

set "PYTHONPATH=src"

REM Load .env if present (no pipe; generate temp cmd in ASCII and call it)
if exist ".env" (
  set "ENV_TMP=%TEMP%\env_load_%RANDOM%%RANDOM%.cmd"
  del "!ENV_TMP!" 2>nul
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0load_env.ps1" -Path ".env" -Out "!ENV_TMP!" 1>nul 2>nul
  if exist "!ENV_TMP!" (
    call "!ENV_TMP!"
    del "!ENV_TMP!" 2>nul
    echo .env loaded
  ) else (
    echo [FAIL] .env load failed (temp file not created)
  )
) else (
  echo .env not found (ok)
)

REM Activate venv (cmd)
if not exist ".venv\Scripts\activate.bat" (
  echo [FAIL] Venv not found: .venv\Scripts\activate.bat
  exit /b 1
)
call ".venv\Scripts\activate.bat"

REM Run ARI app
python -m ai_secretary.telephony.ari_app
exit /b %ERRORLEVEL%
