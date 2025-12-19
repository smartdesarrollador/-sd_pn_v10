@echo off
echo ========================================
echo Widget Sidebar - PyInstaller Build
echo ========================================
echo.

REM Step 1: Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /S /Q build
if exist "dist" rmdir /S /Q dist

REM Step 2: Migration disabled (base de datos se crea automáticamente)
echo Migration step skipped (database will be created on first run)
echo.

REM Step 3: Build con PyInstaller del venv (CRITICO)
echo Starting PyInstaller build...
echo Using venv PyInstaller...
.\venv\Scripts\pyinstaller.exe widget_sidebar.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo Executable location: dist\WidgetSidebar\WidgetSidebar.exe
echo.

REM Step 4: Copy README (opcional)
if exist "README.md" (
    copy README.md dist\WidgetSidebar\
    echo README.md copied to distribution folder
)

echo.
echo To create distribution package, run:
echo   xcopy /E /I /Y dist\WidgetSidebar WidgetSidebar_v3.0
echo.
pause
