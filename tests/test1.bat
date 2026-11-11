@echo off
setlocal
cd /d "%~dp0.."

(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testrep.json
echo repo_mode = file
echo max_depth = 5
echo filter_substring = _
) > _test_simple.ini

echo === testrep.json: A -^> B, A -^> C, B -^> D, C -^> D, D -^> E ===
echo.
echo --- GRAPH ---
py main.py -c _test_simple.ini
set "EXITCODE1=%ERRORLEVEL%"
echo exit code: %EXITCODE1%
echo.
echo --- LOAD ORDER ---
py main.py -c _test_simple.ini --order
set "EXITCODE2=%ERRORLEVEL%"
echo exit code: %EXITCODE2%
echo.

del _test_simple.ini
pause
endlocal