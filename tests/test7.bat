@echo off
setlocal
cd /d "%~dp0.."

where dot >nul 2>nul
if errorlevel 1 (
    echo [SKIP] Graphviz 'dot' not found in PATH.
    echo Install it from https://graphviz.org/download/ or use --dot instead.
    pause
    exit /b 1
)

if not exist output mkdir output

call :render express
call :render react
call :render chalk

pause
endlocal
exit /b 0

:render
(
echo [app]
echo package_name = %~1
echo repository = https://registry.npmjs.org
echo repo_mode = url
echo max_depth = 1
echo filter_substring = test
) > _demo_%~1.ini

echo ==========================================================
echo === %~1 (max_depth = 1) ===
echo ==========================================================
py src\main.py -c _demo_%~1.ini --png output\graph_%~1.png
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%

if exist output\graph_%~1.png (
    for %%F in (output\graph_%~1.png) do echo size: %%~zF bytes
) else (
    echo [FAIL] output\graph_%~1.png was not created
)
echo.

del _demo_%~1.ini
exit /b 0