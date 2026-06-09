@echo off
:: Устанавливаем кодировку UTF-8 для корректного отображения кириллицы
chcp 65001 >nul

:: Получаем динамический путь к папке, где лежит этот bat-файл (включая слеш на конце)
set "SCRIPT_DIR=%~dp0"

:menu
cls
echo ==========================================
echo             ConsoleDeck - Меню
echo ==========================================
echo 1. Запустить стримдек (в фоновом режиме)
echo 2. Настроить бинды (открыть GUI)
echo 3. Включить автозапуск вместе с Windows
echo 4. Выход
echo ==========================================
set /p choice="Выберите действие (1-4): "

if "%choice%"=="1" goto start_bg
if "%choice%"=="2" goto open_gui
if "%choice%"=="3" goto add_startup
if "%choice%"=="4" exit
goto menu

:start_bg
:: Запуск питона в фоне через pythonw
start "" /B pythonw "%SCRIPT_DIR%consoleDeckScriptGui.py"
echo.
echo [OK] Стримдек запущен в фоне! Окно можно закрывать.
timeout /t 3 >nul
exit

:open_gui
:: Запуск интерфейса
start "" python "%SCRIPT_DIR%consoleDeckScriptGui.py" --gui
exit

:add_startup
:: Путь к системной папке автозагрузки Windows
set "startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "vbs_file=%startup_folder%\ConsoleDeckScript.vbs"

:: Формируем VBS-скрипт. Используем Chr(34) для безопасной вставки кавычек
echo Set WshShell = CreateObject("WScript.Shell") > "%vbs_file%"
echo WshShell.Run "pythonw " ^& Chr(34) ^& "%SCRIPT_DIR%consoleDeckScriptGui.py" ^& Chr(34), 0, False >> "%vbs_file%"

echo.
echo [OK] Скрипт успешно добавлен в автозагрузку (ошибка с кавычками исправлена)!
timeout /t 3 >nul
goto menu
