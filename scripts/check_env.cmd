@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
set "PYTHONPATH=src"
set /a FAIL_COUNT=0

call :check_no_bom
call :load_env

call :check_env_var ARI_URL required
call :check_env_var ARI_USER required
call :check_env_var ARI_PASSWORD required
call :check_env_var ASTERISK_SSH_HOST required
call :check_env_var ASTERISK_SSH_USER required
call :check_env_var ASTERISK_SSH_KEY required

call :check_env_var ARI_APP_NAME optional
call :check_env_var ASTERISK_SOUNDS_DIR optional
call :check_env_var ASTERISK_SOUNDS_SUBDIR optional
call :check_env_var ASTERISK_DOCKER_CONTAINER optional
call :check_env_var PLAY_TEST optional
call :check_env_var HF_TOKEN optional

call :check_python
call :check_ari
call :check_ssh_tools
call :check_keyonly

if %FAIL_COUNT% EQU 0 (
  echo ALL_OK
  exit /b 0
)

echo CHECKS FAILED
exit /b 1

:mark_ok
if "%~1"=="" exit /b 0
echo [OK] %~1
exit /b 0

:mark_fail
if "%~1"=="" (
  echo [FAIL] unknown
) else (
  echo [FAIL] %~1
)
set /a FAIL_COUNT+=1
exit /b 0

:check_no_bom
if not exist "%~dp0check_no_bom.ps1" (
  call :mark_fail "check_no_bom.ps1 not found"
  exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check_no_bom.ps1" -Paths "scripts\check_env.cmd,scripts\run_ari.cmd" 1>nul 2>nul
if errorlevel 1 (
  call :mark_fail "BOM detected in cmd scripts"
) else (
  call :mark_ok "BOM guard"
)
exit /b 0

:load_env
if not exist ".env" (
  call :mark_ok ".env not found (ok)"
  exit /b 0
)
set "ENV_TMP=%TEMP%\env_load_%RANDOM%%RANDOM%.cmd"
del "%ENV_TMP%" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0load_env.ps1" -Path ".env" -Out "%ENV_TMP%" 1>nul 2>nul
if not exist "%ENV_TMP%" (
  call :mark_fail ".env load failed"
  exit /b 0
)
call "%ENV_TMP%"
del "%ENV_TMP%" 2>nul
call :mark_ok ".env loaded"
exit /b 0

:check_env_var
call set "ENV_VALUE=%%%~1%%"
if /I "%~2"=="required" (
  if "%ENV_VALUE%"=="" (
    call :mark_fail "%~1 not set"
  ) else (
    call :mark_ok "%~1 set"
  )
  exit /b 0
)
if "%ENV_VALUE%"=="" (
  call :mark_ok "optional %~1 not set"
) else (
  call :mark_ok "optional %~1 set"
)
exit /b 0

:check_python
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import ai_secretary" 1>nul 2>nul
  if errorlevel 1 (
    call :mark_fail "python import ai_secretary"
  ) else (
    call :mark_ok "python import ai_secretary"
  )
) else (
  call :mark_fail ".venv\Scripts\python.exe not found"
)
exit /b 0

:check_ari
if "%ARI_URL%"=="" exit /b 0
if "%ARI_USER%"=="" exit /b 0
if "%ARI_PASSWORD%"=="" exit /b 0

set "ARI_CODE="
for /f %%C in ('curl.exe -s --connect-timeout 3 --max-time 5 -o NUL -w "%%{http_code}" -u "%ARI_USER%:%ARI_PASSWORD%" "%ARI_URL%/asterisk/info" 2^>nul') do set "ARI_CODE=%%C"
if "%ARI_CODE%"=="" set "ARI_CODE=000"

if "%ARI_CODE%"=="200" (
  call :mark_ok "ARI /asterisk/info - 200"
) else (
  call :mark_fail "ARI /asterisk/info - %ARI_CODE%"
)
exit /b 0

:check_ssh_tools
where ssh.exe 1>nul 2>nul
if errorlevel 1 (
  call :mark_fail "ssh.exe not found in PATH"
) else (
  call :mark_ok "SSH found"
)

where scp.exe 1>nul 2>nul
if errorlevel 1 (
  call :mark_fail "scp.exe not found in PATH"
) else (
  call :mark_ok "SCP found"
)
exit /b 0

:check_keyonly
if "%ASTERISK_SSH_KEY%"=="" exit /b 0
if "%ASTERISK_SSH_HOST%"=="" exit /b 0
if "%ASTERISK_SSH_USER%"=="" exit /b 0
if not exist "%~dp0ssh_key_check.ps1" (
  call :mark_fail "ssh_key_check.ps1 not found"
  exit /b 0
)

set "SSH_TMP=%TEMP%\ssh_key_check_%RANDOM%%RANDOM%.txt"
del "%SSH_TMP%" 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ssh_key_check.ps1" -User "%ASTERISK_SSH_USER%" -Host "%ASTERISK_SSH_HOST%" -Key "%ASTERISK_SSH_KEY%" -TimeoutMs 8000 -Out "%SSH_TMP%" 1>nul 2>nul
set "SSH_RC=%ERRORLEVEL%"

if "%SSH_RC%"=="0" (
  call :mark_ok "SSH key-only"
) else (
  if "%SSH_RC%"=="124" (
    call :mark_fail "SSH key-only (timeout)"
  ) else (
    call :mark_fail "SSH key-only"
  )
)

del "%SSH_TMP%" 2>nul
exit /b 0
