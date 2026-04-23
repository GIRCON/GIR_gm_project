@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "SPEC_PATH=%PROJECT_ROOT%texture_tool.spec"
set "BUILD_DIR=%PROJECT_ROOT%_build_temp"
set "DIST_DIR=%PROJECT_ROOT%_dist_temp"
set "TEMP_EXE_PATH=%DIST_DIR%\TextureTool.exe"
set "FINAL_EXE_PATH=%PROJECT_ROOT%TextureTool.exe"
set "PYCACHE_DIR=%PROJECT_ROOT%__pycache__"

echo [1/3] Cleaning previous build files...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%PYCACHE_DIR%" rmdir /s /q "%PYCACHE_DIR%"
if exist "%FINAL_EXE_PATH%" del /f /q "%FINAL_EXE_PATH%"

echo [2/3] Building exe with PyInstaller...
python -m PyInstaller --clean --noconfirm --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" "%SPEC_PATH%"
if errorlevel 1 goto :fail

if not exist "%TEMP_EXE_PATH%" (
    echo TextureTool.exe was not created.
    goto :fail
)

echo [3/3] Moving final exe next to build.bat...
move /y "%TEMP_EXE_PATH%" "%FINAL_EXE_PATH%" >nul
if errorlevel 1 goto :fail

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%PYCACHE_DIR%" rmdir /s /q "%PYCACHE_DIR%"

echo Build completed successfully: %FINAL_EXE_PATH%
exit /b 0

:fail
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%PYCACHE_DIR%" rmdir /s /q "%PYCACHE_DIR%"
exit /b 1
