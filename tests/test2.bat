@echo off
setlocal
cd /d "%~dp0.."

(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testcycle.json
echo repo_mode = file
echo max_depth = 5
echo filter_substring = _
) > _test_cycles.ini

echo === testcycle.json: cycles C -^> A and E -^> A ===
py main.py -c _test_cycles.ini
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%

del _test_cycles.ini
pause
endlocal