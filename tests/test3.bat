@echo off
setlocal
cd /d "%~dp0.."

echo === testdeep.json: A -^> B -^> C -^> D -^> E -^> F ===

call :run 1
call :run 3
call :run 6

del _test_deep.ini 2>nul
pause
endlocal
exit /b 0

:run
(
echo [app]
echo package_name = A
echo repository = C:\Users\ushak\Documents\KISproject\UshakovIlyaIKBO-60-25\testjsons\testdeep.json
echo repo_mode = file
echo max_depth = %~1
echo filter_substring = _
) > _test_deep.ini

echo --- max_depth = %~1 ---
py main.py -c _test_deep.ini
echo exit code: %ERRORLEVEL%
echo.
exit /b 0