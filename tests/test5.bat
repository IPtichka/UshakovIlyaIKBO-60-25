@echo off
setlocal
cd /d "%~dp0.."

call :dot testrep.json test_simple A
call :dot testcycle.json test_cycles A
call :dot testdeep.json test_deep A
call :dot testfilter.json test_filter A

del _tmp_dot.ini 2>nul
pause
endlocal
exit /b 0

:dot
(
echo [app]
echo package_name = %~3
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\%~1
echo repo_mode = file
echo max_depth = 5
echo filter_substring = _
) > _tmp_dot.ini

echo ==========================================================
echo === DOT: %~1 ===
echo ==========================================================
py src\main.py -c _tmp_dot.ini --dot
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%
echo.
exit /b 0