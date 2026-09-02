@echo off
setlocal
cd /d "%~dp0\..\.."

set "PYTHON_CMD=python"
py -3.10 --version >nul 2>&1 && set "PYTHON_CMD=py -3.10"

set "NO_PAUSE="
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

echo ================================================
echo  MORDHEIM COMBAT LAB - BUILD WINDOWS INSTALLER
echo ================================================

set "ISCC_EXE="
for %%I in (ISCC.exe) do if not "%%~$PATH:I"=="" set "ISCC_EXE=%%~$PATH:I"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 7\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
if not defined ISCC_EXE if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE goto :inno_error

echo.
echo [1/3] Generating MordheimCombatLab.exe...
call tools\windows\build_MordheimCombatLab_ONEFILE.bat --no-pause
if errorlevel 1 goto :build_error

echo.
echo [2/3] Reading project version...
for /f "delims=" %%V in ('%PYTHON_CMD% -c "import sys; sys.path.insert(0, 'src'); import mordheim_combat_lab; print(mordheim_combat_lab.__version__)"') do set "APP_VERSION=%%V"
if not defined APP_VERSION goto :version_error
echo Version: %APP_VERSION%

echo.
echo [3/3] Generating installer...
"%ISCC_EXE%" "/DMyAppVersion=%APP_VERSION%" "tools\windows\MordheimCombatLab.iss"
if errorlevel 1 goto :installer_error

echo.
echo ================================================
echo  INSTALLER COMPLETE
echo ================================================
echo.
echo Output:
echo %CD%\dist\installer\Mordheim-Combat-Lab-Setup-%APP_VERSION%.exe
echo.
call :pause_if_needed
exit /b 0

:inno_error
echo.
echo ERROR: Inno Setup was not found.
echo Install it with:
echo winget install --id JRSoftware.InnoSetup.7 -e -s winget -i
goto :failed

:build_error
echo ERROR: MordheimCombatLab.exe could not be generated.
goto :failed

:version_error
echo ERROR: The project version could not be read.
goto :failed

:installer_error
echo ERROR: Inno Setup could not generate the installer.

:failed
call :pause_if_needed
exit /b 1

:pause_if_needed
if not defined NO_PAUSE pause
exit /b 0
