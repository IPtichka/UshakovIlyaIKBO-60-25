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

call :png testrep.json test_simple
call :png testcycle.json test_cycles

del _tmp_png.ini 2>nul
pause
endlocal
exit /b 0

:png
(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\%~1
echo repo_mode = file
echo max_depth = 5
echo filter_substring = _
) > _tmp_png.ini

echo ==========================================================
echo === PNG: %~1 -^> output\graph_%~2.png ===
echo ==========================================================
py src\main.py -c _tmp_png.ini --png output\graph_%~2.png
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%

if exist output\graph_%~2.png (
    echo file exists: output\graph_%~2.png
    for %%F in (output\graph_%~2.png) do echo size: %%~zF bytes
) else (
    echo [FAIL] output\graph_%~2.png was not created
)
echo.
exit /b 0