@echo off
setlocal
cd /d "%~dp0.."

echo === testdeep.json: A -^> B -^> C -^> D -^> E -^> F ===

call :graph 1
call :graph 3
call :graph 6
call :order 6

del _test_deep.ini 2>nul
pause
endlocal
exit /b 0

:graph
(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testdeep.json
echo repo_mode = file
echo max_depth = %~1
echo filter_substring = _
) > _test_deep.ini

echo --- GRAPH, max_depth = %~1 ---
py main.py -c _test_deep.ini
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%
echo.
exit /b 0

:order
(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testdeep.json
echo repo_mode = file
echo max_depth = %~1
echo filter_substring = _
) > _test_deep.ini

echo --- LOAD ORDER, max_depth = %~1 ---
py main.py -c _test_deep.ini --order
set "EXITCODE=%ERRORLEVEL%"
echo exit code: %EXITCODE%
echo.
exit /b 0