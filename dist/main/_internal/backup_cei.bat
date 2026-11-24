@echo off
echo Iniciando copia de seguridad automatica de la base de datos...

:: Variables de conexion
set DB_NAME=gestion_comision_INGENIUM
set DB_USER=root
set DB_PASS=CEI_db_2026
set DB_HOST=192.168.0.110

:: Obtener fecha y hora exacta
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set datetime=%%I
if defined datetime (
    set FECHA=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%
) else (
    for /f %%I in ('powershell -Command "Get-Date -Format yyyy-MM-dd_HH-mm"') do set FECHA=%%I
)

set ARCHIVO_NOMBRE=Backup_CEI_%FECHA%.sql
set RUTA_LOCAL=C:\backups

:: Crear la carpeta si no existe en el disco C
if not exist "%RUTA_LOCAL%" mkdir "%RUTA_LOCAL%"

:: Localizar mysqldump (XAMPP o en PATH)
set DUMP_EXE="C:\xampp\mysql\bin\mysqldump.exe"
if not exist %DUMP_EXE% (
    set DUMP_EXE=mysqldump
)

:: Extraer base de datos con host y contraseña
%DUMP_EXE% -h %DB_HOST% -u %DB_USER% -p%DB_PASS% %DB_NAME% > "%RUTA_LOCAL%\%ARCHIVO_NOMBRE%"

exit